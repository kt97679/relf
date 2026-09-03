/*
 *  RelF - Relative Forth
 *  Based on SOD32 by L.C. Benschop
 *  Copyright 2001 - 2005, Kirill Timofeev, kt97679@gmail.com
 *  The program is released under the GNU General Public License version 2.
 *  There is NO WARRANTY.
 *
 *  Phase 5 engine (see GOALS.md): portable across every architecture the
 *  build's libc supports. Cells are 8 bytes, matching the process's own
 *  pointer width on 64-bit hosts - see GOALS.md, "load-bearing facts",
 *  for why cell width and host pointer width must match in this design.
 *  Images are native host endianness (little-endian only - see GOALS.md
 *  non-goals), not a portable on-disk format; a magic header lets a
 *  mismatched image fail cleanly instead of silently misbehaving.
 *  Dispatch is computed-goto threaded code (GCC/Clang "labels as
 *  values"), not a function-pointer table - see PROGRESS.md for why.
 */

#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <string.h>

extern char **environ;

#define  UNS8 unsigned char   /*     Virtual    */
#define INT64 long            /*     machine    */
#define UNS64 unsigned long   /* internal types */

#define MEMSIZE (256 * 1024)  /* how much memory do we allocate for VM */
#define RSTACK_BYTES 2048     /* room reserved for the return stack     */

/*
 *  Macroses for memory access. Plain native access, both cell- and
 *  byte-granularity: no byte-order opinion of its own (see GOALS.md,
 *  phase 5). Correctness of any Forth-level code that compares whole
 *  cells of byte data (e.g. SEARCH-WORDLIST's name-comparison trick)
 *  doesn't depend on which convention this is, only that reads and
 *  writes agree with each other - which they trivially do here, since
 *  there's only one access path.
 */

#define CELL(reg) (*(UNS64*)(reg))
#define BYTE(reg) (*(UNS8*)(reg))

/*
 *  Macroses for stack access
 */

#define RS       CELL(rp)          /* top of return stack               */
#define DS0      CELL(dsp)         /* top of data stack                 */
#define DS1      CELL(dsp + 8)     /* 2nd element on data stack         */
#define DS2      CELL(dsp + 16)    /* 3d element on data stack          */
#define DS3      CELL(dsp + 24)    /* 4th element on data stack         */
#define PUSH(x)  dsp -= 8; DS0 = x /* pushes x to data stack            */
#define RPUSH(x) rp -= 8; RS = x   /* pushes x to return stack          */

/*
 *  VM memory. +7 is necessary to be able to allocate MEMSIZE bytes from
 *  an 8-aligned address in order to have native word access.
 */

static UNS8 mem[MEMSIZE + 7];

/*
 *  1st 8-aligned address in mem array. This is base address of the system.
 */

static UNS8 *base;

/* VM registers and related variables */

static UNS64  ip; /* instruction pointer               */
static UNS64  rp; /* return stack pointer              */
static UNS64 dsp; /* data stack pointer                */
static UNS64   t; /* variable for temporary storage    */

/*
 *  8-byte magic every image starts with: "RELF" + cell width (8) + 3
 *  reserved bytes. Plain byte comparison - see cross.4's SAVE-IMAGE for
 *  why this needs no endianness handling of its own.
 */

static const UNS8 IMAGE_MAGIC[8] = { 'R', 'E', 'L', 'F', 8, 0, 0, 0 };

/*
 *  write() wrapper: don't care about partial writes here, only used for
 *  short fixed error/usage messages before exit.
 */

static void write_str(int fd, const char *s);

/* Read/write the full requested amount, looping over short reads/writes.
 * Returns bytes transferred, or a negative value on a real error. */
static long full_read(int fd, void *buf, long count) {
    long total = 0, n;
    UNS8 *p = (UNS8*)buf;
    while (total < count) {
        n = read(fd, p + total, count - total);
        if (n == 0) break;   /* EOF, not an error */
        if (n < 0) return n; /* real error */
        total += n;
    }
    return total;
}

static long full_write(int fd, const void *buf, long count) {
    long total = 0, n;
    const UNS8 *p = (const UNS8*)buf;
    while (total < count) {
        n = write(fd, p + total, count - total);
        if (n < 0) return n;
        if (n == 0) return -1; /* no progress, avoid spinning forever */
        total += n;
    }
    return total;
}

static void write_str(int fd, const char *s) {
    (void)full_write(fd, s, (long)strlen(s));
}

/*
 *  Multiply two 64-bit unsigned numbers *a and *b.
 *  High half of 128-bit result in *a, low half in *b.
 */

static void umul(UNS64 *a, UNS64 *b) {
    unsigned __int128 p = (unsigned __int128)(*a) * (unsigned __int128)(*b);
    *a = (UNS64)(p >> 64);
    *b = (UNS64)p;
}

/*
 *  Divide 128-bit unsigned number (high half *b, low half *c) by
 *  64-bit unsigned number in *a. Quotient in *b, remainder in *c.
 */

static void udiv(UNS64 *a, UNS64 *b, UNS64 *c) {
    unsigned __int128 dividend =
        ((unsigned __int128)(*b) << 64) | (unsigned __int128)(*c);
    UNS64 divisor = *a;
    *b = (UNS64)(dividend / divisor);
    *c = (UNS64)(dividend % divisor);
}

/*
 *  virtual machine I/O primitives' shared state
 */

static const int open_flags[6] = {
    O_WRONLY | O_CREAT | O_TRUNC, /* w  */
    O_WRONLY | O_CREAT | O_TRUNC, /* wb : same, no text/binary distinction */
    O_RDONLY,                     /* r  */
    O_RDONLY,                     /* rb */
    O_RDWR,                       /* r+ */
    O_RDWR                        /* r+b */
};

/*
 *  This function reads binary forth image from file into memory.
 */

static void load_image(const char *name) {
    int fd;
    long len;
    UNS8 magic[8];

    fd = open(name, O_RDONLY);
    if (fd < 0) {
        write_str(2, "Cannot open image file.\n");
        exit(2);
    }
    if (full_read(fd, magic, 8) != 8 || memcmp(magic, IMAGE_MAGIC, 8) != 0) {
        write_str(2, "kernel.img: not a RelF image, or built for a "
                 "different cell width.\n");
        exit(2);
    }
    base = (UNS8*)(((UNS64)mem + 7) & ~(UNS64)7);
    len = full_read(fd, base, MEMSIZE);
    close(fd);
    if (len < 0) {
        write_str(2, "Error reading image file.\n");
        exit(2);
    }
}

/*
 *  Virtual machine itself: computed-goto threaded dispatch. Each
 *  primitive is a labeled block ending in NEXT; primitive tokens are
 *  (index * 8) + 1, matching cross.4's PRIMITIVE numbering (stride 8 =
 *  sizeof(void*) on every 64-bit host this targets).
 */

static void virtual_machine(void) {
    static const void *const dispatch[] = {
        &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop,
        &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch,
        &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr,
        &&L_tor, &&L_rfetch, &&L_eq, &&L_ugt, &&L_gt, &&L_plus,
        &&L_negate, &&L_lshift, &&L_rshift, &&L_ummult, &&L_umdiv,
        &&L_dplus, &&L_emit, &&L_key, &&L_bye, &&L_spfetch, &&L_spstore,
        &&L_rpfetch, &&L_rpstore, &&L_openfile, &&L_closefile,
        &&L_readline, &&L_writeline, &&L_readfile, &&L_writefile,
        &&L_system, &&L_reposfile, &&L_filepos, &&L_delfile, &&L_filesize
    };

#define NEXT() do { \
        t = CELL(ip); ip += 8; \
        if (t & 1) goto *dispatch[(t - 1) >> 3]; \
        RPUSH(ip); ip += t; \
        goto next; \
    } while (0)

next:
    NEXT();

L_noop:    /* noop    */ NEXT();
L_exit:    /* exit    */ ip = RS; rp += 8; NEXT();
L_lit:     /* lit     */ PUSH(CELL(ip)); ip += 8; NEXT();
L_branch:  /* branch  */ ip += CELL(ip); NEXT();
L_0branch: /* 0branch */
    if (DS0) ip += 8; else ip += CELL(ip);
    dsp += 8;
    NEXT();
L_drop:    /* drop    */ dsp += 8; NEXT();
L_dup:     /* dup     */ PUSH(DS1); NEXT();
L_swap:    /* swap    */ t = DS0; DS0 = DS1; DS1 = t; NEXT();
L_rot:     /* rot     */ t = DS2; DS2 = DS1; DS1 = DS0; DS0 = t; NEXT();
L_over:    /* over    */ PUSH(DS2); NEXT();
L_cfetch:  /* C@      */ DS0 = BYTE(DS0); NEXT();
L_fetch:   /* @       */ DS0 = CELL(DS0); NEXT();
L_cstore:  /* c!      */ BYTE(DS0) = (UNS8)DS1; dsp += 16; NEXT();
L_store:   /* !       */ CELL(DS0) = DS1; dsp += 16; NEXT();
L_and:     /* and     */ DS1 &= DS0; dsp += 8; NEXT();
L_or:      /* or      */ DS1 |= DS0; dsp += 8; NEXT();
L_xor:     /* xor     */ DS1 ^= DS0; dsp += 8; NEXT();
L_fromr:   /* r>      */ PUSH(RS); rp += 8; NEXT();
L_tor:     /* >r      */ RPUSH(DS0); dsp += 8; NEXT();
L_rfetch:  /* r@      */ PUSH(RS); NEXT();
L_eq:      /* =       */ DS1 = - (UNS64)(DS0 == DS1); dsp += 8; NEXT();
L_ugt:     /* u<      */ DS1 = - (UNS64)(DS1 < DS0); dsp += 8; NEXT();
L_gt:      /* <       */
    DS1 = - (UNS64)((INT64)DS1 < (INT64)DS0);
    dsp += 8;
    NEXT();
L_plus:    /* +       */ DS1 += DS0; dsp += 8; NEXT();
L_negate:  /* negate  */ DS0 = - DS0; NEXT();
L_lshift:  /* lshift  */ DS1 <<= DS0; dsp += 8; NEXT();
L_rshift:  /* rshift  */ DS1 >>= DS0; dsp += 8; NEXT();
L_ummult:  /* um*     */ umul(&DS0, &DS1); NEXT();
L_umdiv:   /* um/mod  */ udiv(&DS0, &DS1, &DS2); dsp += 8; NEXT();
L_dplus:   /* d+      */
    DS3 += DS1; DS2 += DS0; DS2 += (DS3 < DS1);
    dsp += 16;
    NEXT();

L_emit: { /* emit    */
    UNS8 c = (UNS8)DS0;
    full_write(1, &c, 1);
    dsp += 8;
    NEXT();
}
L_key: { /* key     */
    UNS8 c;
    long n = read(0, &c, 1);
    if (n <= 0) {
        /* Clean exit on stdin EOF (or a read error) instead of spinning
         * forever re-reading EOF - see GOALS.md / PROGRESS.md, Bug 3. */
        exit(0);
    }
    PUSH((UNS64)c);
    NEXT();
}
L_bye:     /* bye     */ exit(0);
L_spfetch: /* sp@     */ PUSH(dsp + 8); NEXT();
L_spstore: /* sp!     */ dsp = DS0; NEXT();
L_rpfetch: /* rp@     */ PUSH(rp); NEXT();
L_rpstore: /* rp!     */ rp = DS0; dsp += 8; NEXT();

L_openfile: { /* c-addr u fam --- fid ior */
    int fd;
    t = BYTE(DS2 + DS1);
    BYTE(DS2 + DS1) = 0;
    fd = open((char *)DS2, open_flags[DS0], 0644);
    BYTE(DS2 + DS1) = t;
    DS2 = (UNS64)fd;
    DS1 = (fd >= 0) ? 0 : 200;
    dsp += 8;
    NEXT();
}
L_closefile: /* fid --- ior */
    DS0 = (UNS64)close((int)DS0);
    NEXT();
L_readline: { /* c-addr u1 fid --- u2 flag ior */
    int fd = (int)DS0;
    UNS64 addr = DS2, max = DS1, count = 0;
    long n, err = 0, got_any = 0;
    UNS8 c;

    while (count < max) {
        n = read(fd, &c, 1);
        if (n < 0) { err = 1; break; }
        if (n == 0) break;      /* EOF */
        got_any = 1;
        if (c == '\n') break;   /* line terminator, not stored */
        BYTE(addr + count) = c;
        count++;
    }
    /* Tolerate CRLF files: a trailing \r right before the \n we just
     * stopped at is a line terminator too, not payload. */
    if (count > 0 && BYTE(addr + count - 1) == '\r') count--;
    DS2 = count;
    DS1 = got_any ? (UNS64)-1 : 0;
    DS0 = err ? (UNS64)-200 : 0;
    NEXT();
}
L_writeline: { /* c-addr u fid --- ior */
    int fd = (int)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    n = full_write(fd, (void*)addr, len);
    if (n == (long)len) {
        n = full_write(fd, "\n", 1);
        DS2 = (n == 1) ? 0 : (UNS64)-200;
    } else {
        DS2 = (UNS64)-200;
    }
    dsp += 16;
    NEXT();
}
L_readfile: { /* c-addr u1 fid --- u2 ior */
    int fd = (int)DS0;
    UNS64 addr = DS2, maxlen = DS1;
    long n;

    n = full_read(fd, (void*)addr, maxlen);
    if (n < 0) {
        DS2 = 0;
        DS1 = (UNS64)-200;
    } else {
        DS2 = (UNS64)n;
        DS1 = 0;
    }
    dsp += 8;
    NEXT();
}
L_writefile: { /* c-addr u fid --- ior */
    int fd = (int)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    n = full_write(fd, (void*)addr, len);
    DS2 = (n == (long)len) ? 0 : (UNS64)-200;
    dsp += 16;
    NEXT();
}
L_system: { /* c-addr u --- ior */
    UNS64 addr = DS1, len = DS0;
    UNS8 saved;
    pid_t pid;
    long ior;
    int status = 0;
    char *argv[4];

    saved = BYTE(addr + len);
    BYTE(addr + len) = 0;
    argv[0] = "/bin/sh";
    argv[1] = "-c";
    argv[2] = (char*)addr;
    argv[3] = 0;
    pid = fork();
    if (pid == 0) {
        execve("/bin/sh", argv, environ);
        _exit(127);
    }
    if (pid > 0) {
        waitpid(pid, &status, 0);
        ior = (status >> 8) & 0xff;
    } else {
        ior = 200;
    }
    BYTE(addr + len) = saved;
    DS1 = (UNS64)ior;
    dsp += 8;
    NEXT();
}
L_reposfile: /* offset fid --- ior */
    DS1 = (UNS64)lseek((int)DS0, (long)DS1, SEEK_SET);
    dsp += 8;
    NEXT();
L_filepos: /* fid --- u ior */
    DS0 = (UNS64)lseek((int)DS0, 0, SEEK_CUR);
    dsp -= 8;
    if ((INT64)DS1 == -1) {
        DS0 = 200;
    } else {
        DS0 = 0;
    }
    NEXT();
L_delfile: { /* c-addr u --- ior */
    t = BYTE(DS1 + DS0);
    BYTE(DS1 + DS0) = 0;
    DS1 = (UNS64)unlink((char*)DS1);
    BYTE(DS1 + DS0) = t;
    dsp += 8;
    NEXT();
}
L_filesize: { /* fid --- u ior */
    int fd = (int)DS0;
    long cur = lseek(fd, 0, SEEK_CUR);
    long size = lseek(fd, 0, SEEK_END);
    lseek(fd, cur, SEEK_SET);
    DS0 = (UNS64)size;
    PUSH(0);
    NEXT();
}
}

/*
 *  Program entry point.
 */

int main(int argc, char **argv) {
    if (argc < 2) {
        write_str(2, "Usage: relf <filename>\n");
        return 1;
    }
    load_image(argv[1]);
    ip = (UNS64)base;
    rp = ip + MEMSIZE;
    dsp = ip + MEMSIZE - RSTACK_BYTES;
    PUSH(ip);
    virtual_machine();
    return 0; /* unreachable: virtual_machine() only leaves via BYE/EOF */
}

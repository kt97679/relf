/*
 *  RelF - Relative Forth
 *  Based on SOD32 by L.C. Benschop
 *  Copyright 2001 - 2005, Kirill Timofeev, kt97679@gmail.com
 *  The program is released under the GNU General Public License version 2.
 *  There is NO WARRANTY.
 *
 *  Phase 5 engine (see GOALS.md): portable across every architecture the
 *  build's libc supports. Cell width is chosen at compile time to match
 *  the host's own pointer width (4 bytes on 32-bit hosts, 8 on 64-bit
 *  ones) - see GOALS.md, "load-bearing facts", for why cell width and
 *  host pointer width must match in this design. Images are native host
 *  endianness (little-endian only - see GOALS.md non-goals), not a
 *  portable on-disk format; a magic header records both cell width and
 *  a fixed tag, so a mismatched image fails cleanly instead of silently
 *  misbehaving. Dispatch is computed-goto threaded code (GCC/Clang
 *  "labels as values"), not a function-pointer table - see PROGRESS.md
 *  for why. kernel.img itself must be built for the same cell width as
 *  this binary (see README.md) - a 32-bit build needs its own image,
 *  cross-compiled with TARGET-CELL-BYTES set to 4 (see cross.4).
 */

#include <unistd.h>
#include <pwd.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

extern char **environ;

/* Process argv, exposed to Forth via SYS-ARGC/SYS-ARG below - argv[0]
 * and argv[1] (the program name and kernel-image path) are not part
 * of this; SYS-ARG(0) is argv[2], the first argument after the image
 * path, matching a shell's own convention of not exposing its own
 * name via the primitives that expose *its* arguments. */
static int g_argc;
static char **g_argv;

#define UNS8 unsigned char /* byte access; width-independent */

#if UINTPTR_MAX == 0xFFFFFFFFFFFFFFFFULL
typedef uint64_t UNS64; /* the VM's cell type - 8 bytes on this host */
typedef int64_t  INT64;
#define CELL_BYTES 8
#define CELL_SHIFT 3     /* log2(CELL_BYTES): primitive dispatch stride */
#elif UINTPTR_MAX == 0xFFFFFFFFUL
typedef uint32_t UNS64; /* the VM's cell type - 4 bytes on this host */
typedef int32_t  INT64;
#define CELL_BYTES 4
#define CELL_SHIFT 2
#else
#error "relf: unsupported pointer size (only 32-bit and 64-bit hosts are supported)"
#endif

/*  How much memory the VM gets: dictionary at the bottom, return and
 *  data stacks at the top (see rp/dsp below). Raised from 256K to 1M
 *  in Iteration 40, after a prebuilt shell image measured 253,256
 *  bytes - i.e. kernel.img plus locals.4 plus shell.4 had come within
 *  a few KB of the old ceiling, with the stacks living in what was
 *  left. Overflowing it does not fail cleanly: the symptom is
 *  corrupted compilation reported as "Undefined word" against an
 *  empty name, nowhere near the actual cause. 1M is still small
 *  enough to be unremarkable and leaves real headroom for shell.4 to
 *  keep growing.  */
#define MEMSIZE (1024 * 1024)
/*  Room reserved for the return stack. Raised from 2048 in Iteration
 *  90: 2048 bytes is 256 cells, and each level of shell function
 *  recursion nests roughly a dozen Forth calls, so the return stack
 *  overflowed - segfaulting - at around fifteen levels, before
 *  shell.4's own MAX-POS-PARAM-DEPTH guard of 32 could report
 *  "recursion too deep". A limit that pre-empts a higher-level one
 *  turns a diagnosable error into a crash.  */
#define RSTACK_BYTES 65536
/*  Room the data stack is allowed to occupy before it is declared
 *  overflowed. Nothing enforced this until Iteration 151: dsp simply
 *  descended out of its own region, through free space, and into the
 *  dictionary, silently rewriting compiled words from the top down
 *  until it eventually walked off the bottom of mem[] and took a
 *  SIGSEGV. The corruption came first and the crash came much later,
 *  which is why the symptom recorded above - "Undefined word" against
 *  an empty name - points nowhere near the cause.
 *
 *  256KB is 32768 cells at 8-byte width. The floor it puts under the
 *  data stack sits at MEMSIZE-RSTACK_BYTES-DSTACK_BYTES = 720,896
 *  bytes from base, and the largest image this project builds (the
 *  x86-64 prebuilt shell) ends at 206,024 - so the check fires with
 *  half a megabyte still between the stack and the dictionary, i.e.
 *  strictly BEFORE any corruption rather than after it. This reserves
 *  nothing and moves nothing: dsp and rp start exactly where they
 *  always did, so S0/R0 and every saved image are unaffected.  */
#define DSTACK_BYTES 262144

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

#define RS       CELL(rp)                    /* top of return stack     */
#define DS0      CELL(dsp)                   /* top of data stack       */
#define DS1      CELL(dsp + CELL_BYTES)      /* 2nd element on d.stack  */
#define DS2      CELL(dsp + 2 * CELL_BYTES)  /* 3d element on d.stack   */
#define DS3      CELL(dsp + 3 * CELL_BYTES)  /* 4th element on d.stack  */
/*  Both stacks grow DOWN, and both are checked on every push. A push
 *  is the only way either of them can grow, so this is the complete
 *  set of sites - there is no cheaper subset that still catches
 *  runaway recursion and runaway loops both. Measured on fib.4, which
 *  is call- and push-dense by construction: see PROGRESS.md's
 *  Iteration 151 entry for the numbers.  */
#define PUSH(x)  do { dsp -= CELL_BYTES;                              \
                      if (dsp < dsp_limit) stack_fault(0);            \
                      DS0 = x; } while (0)  /* pushes x to data stack  */
#define RPUSH(x) do { rp -= CELL_BYTES;                               \
                      if (rp < rp_limit) stack_fault(1);              \
                      RS = x; } while (0)   /* pushes x to return stack*/

/*
 *  VM memory. +(CELL_BYTES-1) is necessary to be able to allocate
 *  MEMSIZE bytes from a CELL_BYTES-aligned address in order to have
 *  native word access.
 */

static UNS8 mem[MEMSIZE + CELL_BYTES - 1];

/*
 *  1st CELL_BYTES-aligned address in mem array. Base address of the
 *  system.
 */

static UNS8 *base;

/* VM registers and related variables */

/*  Initial values only. The VM registers themselves - ip, rp, dsp, t
 *  and the two stack floors - are LOCALS of virtual_machine(), copied
 *  from these on entry.
 *
 *  Until Iteration 189 they were these statics, and that cost ~20% of
 *  every workload: a primitive's store through CELL() is a UNS64 store
 *  that C's aliasing rules allow to hit a UNS64 static, so GCC reloaded
 *  and re-stored ip, rp and dsp around every NEXT. Measured with
 *  tools/lab/bench-vm.py: 0.82x the time on x86-64 and 0.80x on i386,
 *  identical images. See CV8.md.  */
static UNS64 g_ip, g_rp, g_dsp;

/*  Floors for the two stacks, both set once in main() and never
 *  changed. Kept as plain variables rather than recomputed from base
 *  at each check so the hot path compares against something already
 *  in a register.  */
static UNS64 g_dsp_limit; /* data stack may not descend below this   */
static UNS64  g_rp_limit; /* return stack may not descend below this */

/*
 *  8-byte magic every image starts with: "RELF" + cell width + 3
 *  reserved bytes. Always 8 bytes on disk regardless of the engine's
 *  own cell width - it's a fixed file-format constant, not a cell.
 *  Plain byte comparison - see cross.4's SAVE-IMAGE for why this needs
 *  no endianness handling of its own.
 */

static const UNS8 IMAGE_MAGIC[8] = { 'R', 'E', 'L', 'F', CELL_BYTES, 0, 0, 0 };

/*
 *  write() wrapper: don't care about partial writes here, only used for
 *  short fixed error/usage messages before exit.
 */

static void write_str(int fd, const char *s);
static void stack_fault(int which) __attribute__((noreturn, cold));

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
 *  Report an exhausted stack and stop. There is deliberately no
 *  attempt to recover into the Forth interpreter: by the time either
 *  pointer is out of bounds the system has usually been running away
 *  for a while, and ABORTing back into QUIT would need a working data
 *  stack to do it with. Diagnosing the condition is the whole point -
 *  what this replaces is silent dictionary corruption followed much
 *  later by a bare "Segmentation fault", which named neither the
 *  stack involved nor the fact that a stack was involved at all.
 *
 *  Status 70 (EX_SOFTWARE) rather than 1, so a test harness can tell
 *  an engine fault from a Forth-level ABORT.
 */
static void stack_fault(int which) {
    write_str(2, which ? "relf: return stack overflow\n"
                       : "relf: data stack overflow\n");
    exit(70);
}

/*
 *  Multiply two cell-width unsigned numbers *a and *b.
 *  High half of the double-width result in *a, low half in *b.
 *  Divide a double-width unsigned number (high half *b, low half *c) by
 *  a cell-width unsigned number in *a. Quotient in *b, remainder in *c.
 *
 *  On a 64-bit host this needs a genuine 128-bit intermediate (the
 *  GCC/Clang __int128 extension); on a 32-bit host a plain "unsigned
 *  long long" (guaranteed >=64 bits by the C standard) is already wide
 *  enough for a 64-bit intermediate, no extension needed.
 */

#if CELL_BYTES == 8
static void umul(UNS64 *a, UNS64 *b) {
    unsigned __int128 p = (unsigned __int128)(*a) * (unsigned __int128)(*b);
    *a = (UNS64)(p >> 64);
    *b = (UNS64)p;
}
static void udiv(UNS64 *a, UNS64 *b, UNS64 *c) {
    unsigned __int128 dividend =
        ((unsigned __int128)(*b) << 64) | (unsigned __int128)(*c);
    UNS64 divisor = *a;
    *b = (UNS64)(dividend / divisor);
    *c = (UNS64)(dividend % divisor);
}
#else
static void umul(UNS64 *a, UNS64 *b) {
    unsigned long long p = (unsigned long long)(*a) * (unsigned long long)(*b);
    *a = (UNS64)(p >> 32);
    *b = (UNS64)p;
}
static void udiv(UNS64 *a, UNS64 *b, UNS64 *c) {
    unsigned long long dividend =
        ((unsigned long long)(*b) << 32) | (unsigned long long)(*c);
    UNS64 divisor = *a;
    *b = (UNS64)(dividend / divisor);
    *c = (UNS64)(dividend % divisor);
}
#endif

/*
 *  virtual machine I/O primitives' shared state
 */

static const int open_flags[8] = {
    O_WRONLY | O_CREAT | O_TRUNC,  /* w  */
    O_WRONLY | O_CREAT | O_TRUNC,  /* wb : same, no text/binary distinction */
    O_RDONLY,                      /* r  */
    O_RDONLY,                      /* rb */
    O_RDWR,                        /* r+ */
    O_RDWR,                        /* r+b */
    O_WRONLY | O_CREAT | O_APPEND, /* a  - added for shell.4's ">>" (see
                                       PROGRESS.md, Iteration 7): none of
                                       the original six modes create a
                                       missing file *without* truncating
                                       it, which append redirection needs */
    O_WRONLY | O_CREAT | O_APPEND  /* ab : same */
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
    base = (UNS8*)(((UNS64)(uintptr_t)mem + CELL_BYTES - 1)
                    & ~(UNS64)(CELL_BYTES - 1));
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
 *  (index * CELL_BYTES) + 1, matching cross.4's PRIMITIVE numbering
 *  (stride == sizeof(void*) on this host, since dispatch-table entries
 *  are pointer-sized - which is exactly CELL_BYTES on every host this
 *  targets).
 */


/*
 *  Buffered terminal I/O.
 *
 *  KEY and EMIT used to do one read(2) or write(2) PER CHARACTER. On a
 *  host where a syscall is cheap that is merely wasteful; on real
 *  hardware with the usual mitigations it dominates every workload that
 *  touches text. Running the 616-case CORE corpus made 26,950 one-byte
 *  reads of stdin and 5,373 one-byte writes: 32,357 syscalls against
 *  SOD32's 59 for the identical input, because SOD32 reads in blocks.
 *
 *  That is not a small constant. Measured on two machines, the same
 *  build was 5x slower on the faster CPU, purely because its syscalls
 *  cost more - and the constant is identical for every stage, so it also
 *  compressed every ratio in the comparison towards 1.0 and hid the
 *  differences the benchmarks exist to show.
 *
 *  Ordering is the thing to get right. Output is flushed before any
 *  read of stdin, so a prompt appears before the input it asks for;
 *  before any other write to fd 1, so interleaving is preserved; and
 *  before exit, fork and exec, so nothing is lost or duplicated into a
 *  child.
 */
#define TIOBUF 4096
static UNS8 t_obuf[TIOBUF];
static int  t_olen = 0;


/*
 *  Buffered READ-LINE for FILES, the same problem as KEY and EMIT and a
 *  larger one. Cross-compiling the kernel reads extend.4, cross.4 and
 *  kernel.4 - about 62 KB of source - and READ-LINE was doing
 *  read(fd, &c, 1) for every byte of it: 67,316 syscalls for one build.
 *
 *  The OS file offset has to stay honest, because REPOSITION-FILE,
 *  FILE-POSITION and READ-FILE all depend on it and none of them know
 *  about this buffer. So any of those drops the buffer first, seeking
 *  back over whatever was read ahead and not yet consumed.
 */
/*  These MUST NOT be inlined into virtual_machine(). They are cold I/O
 *  paths with loops and static state; inlined, they wreck register
 *  allocation across the whole dispatch function and the VM registers
 *  stop living in registers. Measured: the specialised CV8 engine went
 *  from 9.5 ms to 17.6 ms on a workload that reads no files at all,
 *  same image, same input - an 85% loss from adding a function nothing
 *  in that run ever called. Iteration 189a found the same class of
 *  problem from the other direction, when the VM registers were
 *  file-scope statics.  */
#define NOINLINE_IO __attribute__((noinline))
#define FBUFN  4
#define FBUFSZ 4096

/*  A small POOL of read buffers, not a table indexed by descriptor.
 *
 *  A process may hold 1024 descriptors by default and far more if the
 *  limit is raised, so anything sized by fd number is unbounded. This
 *  is sized by CONCURRENCY instead - how many files are being read at
 *  once - which is 2 or 3 in practice, INCLUDED nested inside
 *  INCLUDED. Memory is FBUFN * FBUFSZ whatever the descriptors are.
 *
 *  Eviction is what makes an arbitrary size safe: a slot gives back
 *  its unread bytes by seeking the descriptor backwards, so a file can
 *  lose its buffer at any moment and be left exactly where the reader
 *  had consumed to. Nothing above this notices. That is the same
 *  discipline t_fdrop applies on close, generalised.
 *
 *  Only SEEKABLE descriptors get a slot. A pipe cannot be seeked back,
 *  so read-ahead on one is theft - and pipes are inherited rather than
 *  opened by this system, which is the same distinction again.
 *
 *  Measured, reading a 7192-line source line by line:
 *      1 file            70 read()       0 lseek()    0.6 ms
 *      2 interleaved    140 read()       0 lseek()    1.1 ms
 *      4 interleaved    280 read()       0 lseek()    2.1 ms
 *      5 interleaved 35,965 read()  35,955 lseek()   25.6 ms
 *  Past the pool size it degrades to re-reading a block per line -
 *  slower, never wrong. The previous design was a fixed 8-entry table
 *  scanned linearly, which failed silently at the 9th file and used
 *  fd 0 as its "slot unused" marker, so descriptor 0 could never own
 *  a slot at all.  */
static struct fbuf { int fd, len, pos; unsigned long age; UNS8 b[FBUFSZ]; }
    t_fb[FBUFN];
static unsigned long t_clk;
static int t_fbinit;

NOINLINE_IO static void t_fevict(int i) {
    if (t_fb[i].fd >= 0 && t_fb[i].len > t_fb[i].pos)
        lseek(t_fb[i].fd, -(off_t)(t_fb[i].len - t_fb[i].pos), SEEK_CUR);
    t_fb[i].fd = -1; t_fb[i].len = t_fb[i].pos = 0;
}

NOINLINE_IO static struct fbuf *t_fslot(int fd) {
    int i, lru = 0;
    if (!t_fbinit) { for (i = 0; i < FBUFN; i++) t_fb[i].fd = -1; t_fbinit = 1; }
    for (i = 0; i < FBUFN; i++)
        if (t_fb[i].fd == fd) { t_fb[i].age = ++t_clk; return &t_fb[i]; }
    /*  Not buffered yet. A descriptor that cannot seek must not be
     *  buffered, because eviction could not give the bytes back.  */
    if (lseek(fd, 0, SEEK_CUR) < 0) return 0;
    for (i = 0; i < FBUFN; i++) {
        if (t_fb[i].fd < 0) { lru = i; goto take; }
        if (t_fb[i].age < t_fb[lru].age) lru = i;
    }
    t_fevict(lru);
take:
    t_fb[lru].fd = fd; t_fb[lru].len = t_fb[lru].pos = 0;
    t_fb[lru].age = ++t_clk;
    return &t_fb[lru];
}

NOINLINE_IO static void t_fdrop(int fd) {
    int i;
    for (i = 0; i < FBUFN; i++) if (t_fb[i].fd == fd) t_fevict(i);
}

/*  Next byte of fd: >=0 a character, -1 end of file, -2 error.  */
NOINLINE_IO static int t_fgetc(int fd) {
    struct fbuf *f = t_fslot(fd);
    long n;
    if (!f) { UNS8 c; n = read(fd, &c, 1);
              return n == 1 ? (int)c : (n == 0 ? -1 : -2); }
    if (f->pos >= f->len) {
        n = read(fd, f->b, FBUFSZ);
        if (n < 0) return -2;
        if (n == 0) return -1;
        f->len = (int)n; f->pos = 0;
    }
    return f->b[f->pos++];
}

NOINLINE_IO static void t_flush(void) {
    if (t_olen) { full_write(1, t_obuf, (size_t)t_olen); t_olen = 0; }
}

NOINLINE_IO static void t_put(UNS8 c) {
    if (t_olen == TIOBUF) t_flush();
    t_obuf[t_olen++] = c;
}

NOINLINE_IO static int t_getc(void) {
    /*  One byte, unbuffered. Descriptor 0 is INHERITED and shared with
     *  children, so bytes read ahead are bytes taken from them - the
     *  4096-byte buffer that used to be here made `read x; cat` swallow
     *  a whole pipe. bash, dash, gforth, SPF and lbForth all read fd 0
     *  a byte at a time for exactly this reason.
     *
     *  Descriptors this system OPENS are a different matter: it owns
     *  them, nobody else is reading, and t_fgetc buffers them.  */
    UNS8 c;
    t_flush();                         /* a prompt appears before the wait */
    if (read(0, &c, 1) != 1) return -1;
    return c;
}

/*  Is another byte already in the standard-input buffer? READ-STDIN uses
 *  this to return what is available rather than block until it has
 *  filled the caller's buffer - read(2) semantics. It deliberately does
 *  NOT consult the file descriptor: a byte the OS has but we have not
 *  read yet is not "ready" here, and asking would cost a syscall per
 *  character. ANS's KEY? is the word for that question, and this system
 *  does not have it yet.  */

static void virtual_machine(void) {
    UNS64 ip = g_ip, rp = g_rp, dsp = g_dsp, t;
    const UNS64 dsp_limit = g_dsp_limit, rp_limit = g_rp_limit;
    static const void *const dispatch[] = {
        &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop,
        &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch,
        &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr,
        &&L_tor, &&L_rfetch, &&L_eq, &&L_ugt, &&L_gt, &&L_plus,
        &&L_negate, &&L_lshift, &&L_rshift, &&L_ummult, &&L_umdiv,
        &&L_dplus, &&L_type, &&L_spfetch, &&L_spstore,
        &&L_rpfetch, &&L_rpstore, &&L_bye, &&L_openfile, &&L_closefile,
        &&L_readline, &&L_writeline, &&L_readfile, &&L_writefile,
        &&L_system, &&L_reposfile, &&L_filepos, &&L_delfile, &&L_filesize,
        &&L_fork, &&L_execve, &&L_waitpid, &&L_pipe, &&L_dup2,
        &&L_getenv, &&L_setenv, &&L_sysexit, &&L_chdir, &&L_getcwd,
        &&L_sysargc, &&L_sysarg, &&L_getpid, &&L_unsetenv,
        &&L_allocate, &&L_free, &&L_resize, &&L_getpwhome,
        &&L_getfsize, &&L_setfsize
    };

#define NEXT() do { \
        t = CELL(ip); ip += CELL_BYTES; \
        if (t & 1) goto *dispatch[(t - 1) >> CELL_SHIFT]; \
        RPUSH(ip); ip += t; \
        goto next; \
    } while (0)

next:
    NEXT();

L_noop:    /* noop    */ NEXT();
L_exit:    /* exit    */ ip = RS; rp += CELL_BYTES; NEXT();
L_lit:     /* lit     */ PUSH(CELL(ip)); ip += CELL_BYTES; NEXT();
L_branch:  /* branch  */ ip += CELL(ip); NEXT();
L_0branch: /* 0branch */
    if (DS0) ip += CELL_BYTES; else ip += CELL(ip);
    dsp += CELL_BYTES;
    NEXT();
L_drop:    /* drop    */ dsp += CELL_BYTES; NEXT();
L_dup:     /* dup     */ PUSH(DS1); NEXT();
L_swap:    /* swap    */ t = DS0; DS0 = DS1; DS1 = t; NEXT();
L_rot:     /* rot     */ t = DS2; DS2 = DS1; DS1 = DS0; DS0 = t; NEXT();
L_over:    /* over    */ PUSH(DS2); NEXT();
L_cfetch:  /* C@      */ DS0 = BYTE(DS0); NEXT();
L_fetch:   /* @       */ DS0 = CELL(DS0); NEXT();
L_cstore:  /* c!      */ BYTE(DS0) = (UNS8)DS1; dsp += 2 * CELL_BYTES; NEXT();
L_store:   /* !       */ CELL(DS0) = DS1; dsp += 2 * CELL_BYTES; NEXT();
L_and:     /* and     */ DS1 &= DS0; dsp += CELL_BYTES; NEXT();
L_or:      /* or      */ DS1 |= DS0; dsp += CELL_BYTES; NEXT();
L_xor:     /* xor     */ DS1 ^= DS0; dsp += CELL_BYTES; NEXT();
L_fromr:   /* r>      */ PUSH(RS); rp += CELL_BYTES; NEXT();
L_tor:     /* >r      */ RPUSH(DS0); dsp += CELL_BYTES; NEXT();
L_rfetch:  /* r@      */ PUSH(RS); NEXT();
L_eq:      /* =       */ DS1 = - (UNS64)(DS0 == DS1); dsp += CELL_BYTES; NEXT();
L_ugt:     /* u<      */ DS1 = - (UNS64)(DS1 < DS0); dsp += CELL_BYTES; NEXT();
L_gt:      /* <       */
    DS1 = - (UNS64)((INT64)DS1 < (INT64)DS0);
    dsp += CELL_BYTES;
    NEXT();
L_plus:    /* +       */ DS1 += DS0; dsp += CELL_BYTES; NEXT();
L_negate:  /* negate  */ DS0 = - DS0; NEXT();
L_lshift:  /* lshift  */ DS1 <<= DS0; dsp += CELL_BYTES; NEXT();
L_rshift:  /* rshift  */ DS1 >>= DS0; dsp += CELL_BYTES; NEXT();
L_ummult:  /* um*     */ umul(&DS0, &DS1); NEXT();
L_umdiv:   /* um/mod  */ udiv(&DS0, &DS1, &DS2); dsp += CELL_BYTES; NEXT();
L_dplus:   /* d+      */
    DS3 += DS1; DS2 += DS0; DS2 += (DS3 < DS1);
    dsp += 2 * CELL_BYTES;
    NEXT();

L_type: { /* type    */ /* c-addr u --- */
    /* TYPE and ACCEPT are the terminal primitives; EMIT and KEY are
     * colon definitions on top of them in kernel.4. That is the reverse
     * of the usual arrangement and it is deliberate: a primitive that
     * moves a WHOLE STRING costs one dispatch where a per-character
     * EMIT costs one per byte, and ACCEPT's line editing is a loop the
     * image no longer has to carry. */
    const UNS8 *p = (const UNS8 *)(uintptr_t)DS1;
    UNS64 u = DS0;
    for (UNS64 i = 0; i < u; i++) t_put(p[i]);
    dsp += 2 * CELL_BYTES;
    NEXT();
    }
L_bye:     /* bye     */ t_flush(); exit(0);
L_spfetch: /* sp@     */ PUSH(dsp + CELL_BYTES); NEXT();
L_spstore: /* sp!     */ dsp = DS0; NEXT();
L_rpfetch: /* rp@     */ PUSH(rp); NEXT();
L_rpstore: /* rp!     */ rp = DS0; dsp += CELL_BYTES; NEXT();

L_openfile: { /* c-addr u fam --- fid ior */
    int fd;
    t = BYTE(DS2 + DS1);
    BYTE(DS2 + DS1) = 0;
    fd = open((char *)(uintptr_t)DS2, open_flags[DS0], 0644);
    BYTE(DS2 + DS1) = t;
    DS2 = (UNS64)fd;
    DS1 = (fd >= 0) ? 0 : 200;
    dsp += CELL_BYTES;
    NEXT();
}
L_closefile: { /* fid --- ior */
    t_fdrop((int)DS0);
    DS0 = (UNS64)close((int)DS0);
    NEXT();
    }
L_readline: { /* c-addr u1 fid --- u2 flag ior */
    int fd = (int)DS0;
    UNS64 addr = DS2, max = DS1, count = 0;
    long n, err = 0, got_any = 0;
    UNS8 c;

    while (count < max) {
        int ch = (fd == 0) ? t_getc() : t_fgetc(fd);
        n = (ch == -2) ? -1 : (ch < 0 ? 0 : 1);
        c = (UNS8)ch;
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
    t_flush();
    int fd = (int)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    n = full_write(fd, (void*)(uintptr_t)addr, len);
    if (n == (long)len) {
        n = full_write(fd, "\n", 1);
        DS2 = (n == 1) ? 0 : (UNS64)-200;
    } else {
        DS2 = (UNS64)-200;
    }
    dsp += 2 * CELL_BYTES;
    NEXT();
}
L_readfile: { /* c-addr u1 fid --- u2 ior */
    t_fdrop((int)DS0);
    int fd = (int)DS0;
    UNS64 addr = DS2, maxlen = DS1;
    long n;

    n = full_read(fd, (void*)(uintptr_t)addr, maxlen);
    if (n < 0) {
        DS2 = 0;
        DS1 = (UNS64)-200;
    } else {
        DS2 = (UNS64)n;
        DS1 = 0;
    }
    dsp += CELL_BYTES;
    NEXT();
}
L_writefile: { /* c-addr u fid --- ior */
    t_fdrop((int)DS0);
    t_flush();
    int fd = (int)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    n = full_write(fd, (void*)(uintptr_t)addr, len);
    DS2 = (n == (long)len) ? 0 : (UNS64)-200;
    dsp += 2 * CELL_BYTES;
    NEXT();
}
L_system: { /* c-addr u --- ior */
    t_flush();
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
    argv[2] = (char*)(uintptr_t)addr;
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
    dsp += CELL_BYTES;
    NEXT();
}
L_reposfile: { /* offset fid --- ior */
    t_fdrop((int)DS0);
    DS1 = (UNS64)lseek((int)DS0, (long)DS1, SEEK_SET);
    dsp += CELL_BYTES;
    NEXT();
    }
L_filepos: { /* fid --- u ior */
    t_fdrop((int)DS0);
    DS0 = (UNS64)lseek((int)DS0, 0, SEEK_CUR);
    dsp -= CELL_BYTES;
    if ((INT64)DS1 == -1) {
        DS0 = 200;
    } else {
        DS0 = 0;
    }
    NEXT();
    }
L_delfile: { /* c-addr u --- ior */
    t = BYTE(DS1 + DS0);
    BYTE(DS1 + DS0) = 0;
    DS1 = (UNS64)unlink((char*)(uintptr_t)DS1);
    BYTE(DS1 + DS0) = t;
    dsp += CELL_BYTES;
    NEXT();
}
L_filesize: { /* fid --- u ior */
    t_fdrop((int)DS0);
    int fd = (int)DS0;
    long cur = lseek(fd, 0, SEEK_CUR);
    long size = lseek(fd, 0, SEEK_END);
    lseek(fd, cur, SEEK_SET);
    DS0 = (UNS64)size;
    PUSH(0);
    NEXT();
}
/*
 *  Process-control primitives (shell support). Callers are responsible
 *  for NUL-terminating any string these pass to libc (matching the
 *  existing OPEN-FILE/DELETE-FILE/SYSTEM convention above - none of
 *  these do their own save/restore-a-byte trick, since the strings
 *  they're given - paths, argv entries, env names/values - are usually
 *  already being built fresh in a scratch buffer, not sliced out of
 *  live source text the way OPEN-FILE's c-addr/u pair typically is).
 */
L_fork: /* --- pid */
    t_flush();
    PUSH((UNS64)(INT64)fork());
    NEXT();
L_execve: { /* argv-addr path-addr --- ior */
    t_flush();
    char *path = (char*)(uintptr_t)DS0;
    char **argv = (char**)(uintptr_t)DS1;
    execve(path, argv, environ);
    /* only reached if execve itself failed */
    DS1 = (UNS64)200;
    dsp += CELL_BYTES;
    NEXT();
}
L_waitpid: { /* pid --- status ior */
    int status = 0;
    pid_t r = waitpid((pid_t)(INT64)DS0, &status, 0);
    if (r < 0) {
        DS0 = (UNS64)(INT64)-1;
        PUSH(200);
    } else {
        DS0 = (UNS64)(INT64)status;
        PUSH(0);
    }
    NEXT();
}
L_pipe: { /* --- fd-read fd-write ior */
    int fds[2];
    if (pipe(fds) < 0) {
        PUSH(0); PUSH(0); PUSH(200);
    } else {
        PUSH((UNS64)fds[0]); PUSH((UNS64)fds[1]); PUSH(0);
    }
    NEXT();
}
L_dup2: /* oldfd newfd --- ior */
    DS1 = (UNS64)((dup2((int)DS1, (int)DS0) < 0) ? 200 : 0);
    dsp += CELL_BYTES;
    NEXT();
L_getenv: { /* c-addr --- addr */
    char *v = getenv((char*)(uintptr_t)DS0);
    DS0 = (UNS64)(uintptr_t)v;
    NEXT();
}
L_setenv: /* value-addr name-addr --- ior */
    DS1 = (UNS64)((setenv((char*)(uintptr_t)DS0, (char*)(uintptr_t)DS1, 1) < 0) ? 200 : 0);
    dsp += CELL_BYTES;
    NEXT();
L_sysexit: /* n --- */
    t_flush();
    _exit((int)DS0);
L_chdir: /* c-addr --- ior */
    DS0 = (UNS64)((chdir((char*)(uintptr_t)DS0) < 0) ? 200 : 0);
    NEXT();
L_getcwd: { /* addr max-len --- len ior */
    char *r = getcwd((char*)(uintptr_t)DS1, (size_t)DS0);
    if (r == 0) {
        DS1 = 0;
        DS0 = 200;
    } else {
        DS1 = (UNS64)strlen(r);
        DS0 = 0;
    }
    NEXT();
}
L_sysargc: /* --- n */
    PUSH((UNS64)(g_argc > 2 ? g_argc - 2 : 0));
    NEXT();
L_sysarg: { /* n --- c-addr */
    long n = (long)(INT64)DS0;
    if (n < 0 || n + 2 >= g_argc) {
        DS0 = 0;
    } else {
        DS0 = (UNS64)(uintptr_t)g_argv[n + 2];
    }
    NEXT();
}
L_getpwhome: { /* c-addr --- addr | 0 */
    /* A named user's home directory, via NSS rather than by reading
     * /etc/passwd. That file is one NSS source among several: on a
     * host using LDAP, SSSD, NIS or systemd-homed a real user may not
     * appear in it at all, and "~alice" would quietly stay literal.
     * getpwnam(3) returns whatever the system is actually configured
     * to use. The returned string is in getpwnam's own static
     * storage, valid until the next call - the caller copies it
     * immediately. */
    struct passwd *pw = getpwnam((const char *)(uintptr_t)DS0);
    DS0 = pw ? (UNS64)(uintptr_t)pw->pw_dir : 0;
    NEXT();
}
L_getfsize: { /* --- n */
    /* RLIMIT_FSIZE's soft limit in POSIX's 512-byte blocks, or -1 for
     * unlimited. Blocks rather than bytes deliberately: POSIX specifies
     * ulimit in 512-byte units (which is where bash differs, reporting
     * 1024), and a byte count of a large limit does not fit a 4-byte
     * cell on a 32-bit build. File size is the only resource POSIX's
     * own ulimit covers, so this pair is narrow on purpose - see
     * GOALS.md goal 3. */
    struct rlimit rl;
    if (getrlimit(RLIMIT_FSIZE, &rl) < 0 || rl.rlim_cur == RLIM_INFINITY) {
        PUSH((UNS64)(INT64)-1);
    } else {
        PUSH((UNS64)(rl.rlim_cur / 512));
    }
    NEXT();
}
L_setfsize: { /* n --- ior */
    struct rlimit rl;
    INT64 n = (INT64)DS0;
    if (getrlimit(RLIMIT_FSIZE, &rl) < 0) {
        DS0 = (UNS64)202;
    } else {
        /* POSIX: with neither -H nor -S, ulimit sets the soft *and*
         * hard limit. Setting only rlim_cur left the hard limit
         * untouched, which /proc/self/limits reports in a second
         * column - caught by mrsh's ulimit.sh, whose last assertion
         * greps that line. */
        rl.rlim_cur = (n < 0) ? RLIM_INFINITY : (rlim_t)n * 512;
        rl.rlim_max = rl.rlim_cur;
        DS0 = (UNS64)((setrlimit(RLIMIT_FSIZE, &rl) < 0) ? 202 : 0);
    }
    NEXT();
}
L_getpid: /* --- pid */
    PUSH((UNS64)(INT64)getpid());
    NEXT();
L_unsetenv: /* c-addr --- ior */
    DS0 = (UNS64)((unsetenv((char*)(uintptr_t)DS0) < 0) ? 200 : 0);
    NEXT();

/*
 *  ALLOCATE / FREE / RESIZE - the standard Forth-2012 memory-allocation
 *  wordset, backed by libc. This is memory OUTSIDE the image: it lives
 *  in the C heap, not in the VM's own mem[] region, so it does not
 *  consume dictionary space and is not written out by save-system.4's
 *  SAVE-SYSTEM.
 *
 *  The addresses handed back are absolute and process-local. They are
 *  therefore NOT valid across a save/reload, which is why buffer
 *  pointers are reset before an image is written - see pool.4.
 */
L_allocate: /* u --- a-addr ior */
{
    void *p = malloc((size_t)DS0);
    DS0 = (UNS64)(uintptr_t)p;
    PUSH((UNS64)(p == NULL ? 201 : 0));
    NEXT();
}
L_free: /* a-addr --- ior */
    free((void*)(uintptr_t)DS0);
    DS0 = 0;
    NEXT();
L_resize: /* a-addr u --- a-addr' ior */
{
    void *p = realloc((void*)(uintptr_t)DS1, (size_t)DS0);
    if (p == NULL) {
        /*  Forth-2012: on failure a-addr is unchanged and still valid,
         *  so the caller can carry on with the original block.  */
        DS0 = 202;
    } else {
        DS1 = (UNS64)(uintptr_t)p;
        DS0 = 0;
    }
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
    g_argc = argc;
    g_argv = argv;
    load_image(argv[1]);
    g_ip = (UNS64)(uintptr_t)base;
    g_rp = g_ip + MEMSIZE;
    g_rp_limit  = g_ip + MEMSIZE - RSTACK_BYTES;
    g_dsp_limit = g_ip + MEMSIZE - RSTACK_BYTES - DSTACK_BYTES;
    /*  The one boot-time push: the image's base address, which COLD
     *  reads as START. Done by hand because PUSH needs the VM's locals. */
    g_dsp = g_ip + MEMSIZE - RSTACK_BYTES - CELL_BYTES;
    CELL(g_dsp) = g_ip;
    virtual_machine();
    return 0; /* unreachable: virtual_machine() only leaves via BYE/EOF */
}

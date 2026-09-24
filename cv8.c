/*
 *  cv8.c - the RelF engine: a CV8 byte-stream interpreter.
 *
 *  RelF - Relative Forth
 *  Based on SOD32 by L.C. Benschop
 *  Copyright 2001 - 2005, Kirill Timofeev, kt97679@gmail.com
 *  The program is released under the GNU General Public License version 2.
 *  There is NO WARRANTY.
 *
 *  The only engine since Iteration 243, when it replaced relf.c (the
 *  cell engine). CV8.md describes the format and this engine in detail,
 *  and the measurements behind the design.
 *
 *  Code is a byte stream: one-byte opcodes, two- or three-byte calls
 *  to a byte offset from the image base, and a band of specialised
 *  opcodes for the kernel's hottest patterns. Dictionary headers are
 *  byte-granular and bodies unaligned, which is why the offset is not
 *  scaled; the engine never reads a header. Every reference in an
 *  image is relative, so an image loads anywhere with no relocation.
 *
 *  Cell width is the host's pointer width, chosen at compile time, and
 *  an image records the width it was built for. Images are native host
 *  endianness (little-endian only). Dispatch is computed-goto threaded
 *  code (GCC/Clang "labels as values").
 *
 *  Build:  cc -O2 -Wall -o relf cv8.c
 *          cc -m32 -O2 -Wall -fno-pie -no-pie -o relf32 cv8.c
 *  The i386 build is non-PIE because PIE spends ebx on the GOT, which
 *  costs the TOS cache more than it saves (CV8.md 3.3).
 *
 *  HISTORY OF THIS FILE. It was tools/lab/vm-lab.c, a lab engine with
 *  a dozen build-time knobs for measuring encodings, run through
 *  tools/lab/gen-tos.py (TOS caching) and gen-fold.py (the folded
 *  primitive;EXIT band). This file is that output, specialised to the
 *  one configuration that was measured best and the fold table
 *  inlined. The lab sources were removed with the attic at Iteration
 *  489; `git show 9513df0:attic/tools/lab/vm-lab.c` still has them,
 *  and nothing here depends on them.
 *
 *  ADDING A PRIMITIVE. An OS/libc one is escaped: append its PRIMITIVE
 *  line at the end of kernel.4's list, append its handler to
 *  escaped_prims[] and raise NESC. Nothing else moves; there are 256
 *  selectors. A hot one is direct: add it before ESCAPED in kernel.4,
 *  to direct_prims[] in the same position, and raise NDIRECT - which
 *  moves the synthetic opcodes and the folded band up by one. They must
 *  stay below the specialised band at 0x61; both cross.4 and this file
 *  check that.
 */

#include <unistd.h>
#include <termios.h>
#include <pwd.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <dirent.h>
#include <time.h>          /* LOCAL-TIME: time, localtime_r (Iteration 417) */
#include <sys/resource.h>
#include <sys/stat.h>
#include <poll.h>
#include <stddef.h>

/*  kernel.4's FD-POLL lays a struct pollfd out by hand, in two cells on
 *  the data stack: a 32-bit fd, then 16-bit events and revents, eight
 *  bytes in all. Refuse to build anywhere that is not the layout.  */
_Static_assert(sizeof(struct pollfd) == 8
               && offsetof(struct pollfd, events) == 4
               && offsetof(struct pollfd, revents) == 6
               && POLLIN == 1,
               "struct pollfd is not the layout kernel.4's FD-POLL assumes");

extern char **environ;

/* Process argv, exposed to Forth via SYS-ARGC/SYS-ARG below - argv[0]
 * and argv[1] (the program name and kernel-image path) are not part
 * of this; SYS-ARG(0) is argv[2], the first argument after the image
 * path, matching a shell's own convention of not exposing its own
 * name via the primitives that expose *its* arguments. */
static struct termios term_save;
static int term_saved;

static int g_argc;
static char **g_argv;


/*  Call and slot operands name a BYTE offset from the image base: the
 *  scale is 0, because dictionary headers are byte-granular and bodies
 *  are not aligned (Iteration 243). It was 3 or 2 - the cell shift -
 *  while bodies were cell-aligned.  */
#define SCALE 0

/*  kernel.4's primitives, in PRIMITIVE order. The first NDIRECT have
 *  one-byte opcodes 0..NDIRECT-1; the NESC declared after ESCAPED - the
 *  OS/libc interface - are reached as ESC + a selector byte, and use no
 *  opcode of their own. Everything synthetic (LIT32, DOVAR, DODOES, the
 *  literal forms and the folded band) is numbered from NSYN = NDIRECT,
 *  so adding an escaped primitive moves nothing (Iteration 247). Until
 *  then it was numbered from the TOTAL, which left NESC opcodes unused
 *  and let every escaped primitive push the map towards the fixed
 *  specialised band. Both counts are checked against the tables in
 *  virtual_machine().  */
#define NDIRECT 35
#define NESC    62
#define NSYN    NDIRECT
#define VMPUSH PUSH
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
/*  The whole VM: image, all dictionary growth, and the two stacks. This
 *  is the FIRST ceiling a growing system meets - far below the call
 *  reach - and it is a plain parameter: every reference in an image is
 *  relative, so raising it breaks nothing. Overridable at build time,
 *  and at run time with RELF_MEMSIZE (in MB).  */
#define MEMSIZE (16 * 1024 * 1024)
/*  Room reserved for the return stack. Raised from 2048 in Iteration
 *  90: 2048 bytes is 256 cells, and each level of shell function
 *  recursion nests roughly a dozen Forth calls, so the return stack
 *  overflowed - segfaulting - at around fifteen levels, before
 *  shell.4's own MAX-POS-PARAM-DEPTH guard of 32 could report
 *  "recursion too deep". A limit that pre-empts a higher-level one
 *  turns a diagnosable error into a crash.  */
/*  CV8 operands are unaligned little-endian. Composed from bytes, not
 *  memcpy'd: GCC merges this into one ldrh/movzwl on x86, ARMv7 and
 *  AArch64, while on RISC-V the memcpy form compiled to byte loads, a
 *  stack round trip and a stack-protector check on every operand.  */
static inline UNS64 LD16(UNS64 a) {
    const UNS8 *p = (const UNS8 *)(uintptr_t)a;
    return (UNS64)p[0] | (UNS64)p[1] << 8;
}
#define OPND16(a) LD16(a)
static inline UNS64 LD32(UNS64 a) {
    const UNS8 *p = (const UNS8 *)(uintptr_t)a;
    return (UNS64)p[0] | (UNS64)p[1] << 8 | (UNS64)p[2] << 16 | (UNS64)p[3] << 24;
}

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
/*  GUARD (Iteration 253): instead of those compares, one unreadable
 *  page below each stack, and a SIGSEGV handler that says which one was
 *  hit. The pushes cost nothing, and the guard catches every push at
 *  the push itself - the compares leave SPILL() (LIT32 and friends)
 *  to be caught by the next checked push. Needs an MMU; build with
 *  -DGUARD=0 for a
 *  target without one, and the compares come back.  */
#ifndef GUARD
#define GUARD 1
#endif
#if GUARD
#define STACK_CHECK(c, which)
#else
#define STACK_CHECK(c, which) if (c) stack_fault(which);
#endif
#define PUSH(x)  do { dsp -= CELL_BYTES;                              \
                      STACK_CHECK(dsp < dsp_limit, 0)                 \
                      DS0 = x; } while (0)  /* pushes x to data stack  */
#define RPUSH(x) do { rp -= CELL_BYTES;                               \
                      STACK_CHECK(rp < rp_limit, 1)                   \
                      RS = x; } while (0)   /* pushes x to return stack*/

/*
 *  VM memory. +(CELL_BYTES-1) is necessary to be able to allocate
 *  MEMSIZE bytes from a CELL_BYTES-aligned address in order to have
 *  native word access.
 */

#if GUARD
/*  Aligned to 64 KB, and every stack boundary is a multiple of 64 KB,
 *  so the guards start on a page boundary for any page size up to that
 *  (4 KB on x86, 16 or 64 KB on some ARM systems).  */
static UNS8 mem[MEMSIZE + CELL_BYTES - 1] __attribute__((aligned(65536)));
#else
static UNS8 mem[MEMSIZE + CELL_BYTES - 1];
#endif

/*
 *  1st CELL_BYTES-aligned address in mem array. Base address of the
 *  system.
 */

static UNS8 *base;

/* VM registers and related variables */

static UNS64  g_ip, g_rp, g_dsp;
#if GUARD
#define VMREGS UNS64 ip = g_ip, rp = g_rp, dsp = g_dsp, t;
#else
#define VMREGS UNS64 ip = g_ip, rp = g_rp, dsp = g_dsp, t; const UNS64 dsp_limit = g_dsp_limit, rp_limit = g_rp_limit;
#endif

/*  Floors for the two stacks, both set once in main() and never
 *  changed. Kept as plain variables rather than recomputed from base
 *  at each check so the hot path compares against something already
 *  in a register.  */
static UNS64 g_dsp_limit, g_rp_limit;

/*
 *  8-byte magic every image starts with: "RELF" + cell width + 3
 *  reserved bytes. Always 8 bytes on disk regardless of the engine's
 *  own cell width - it's a fixed file-format constant, not a cell.
 *  Plain byte comparison - see cross.4's SAVE-IMAGE for why this needs
 *  no endianness handling of its own.
 */

/*  Header bytes 0-7. Byte 6 is a FORMAT VERSION and byte 7 a FEATURE
 *  BITMAP, so an engine can tell what an image needs instead of the
 *  widths being implied by the magic string. Widening a field in future
 *  sets a bit here rather than breaking the format.  */
/*  Version 5 (Iteration 259): slot operands are relative to themselves.
 *  Version 4 (Iteration 258): the one-byte branches take two opcodes
 *  after the folded band, and loop and POSTPONE operands changed form.
 *  Version 2 (Iteration 243): the five locals cells moved out of the
 *  file header into the image itself, at offset 8 (see LOCHDR).
 *  Version 3 (Iteration 247): the synthetic opcodes are numbered from
 *  NDIRECT rather than from the total primitive count, so the same
 *  byte means something else in a version-2 image - measured, each way
 *  round it ran and crashed. */
#define CV8_VERSION 5
#define F_VARCALL 0x01   /* calls are 2 or 3 bytes                      */
#define F_VARSLOT 0x02   /* slot operands are 2 or 3 bytes              */
#define F_SPEC    0x04   /* specialised opcodes present                 */
#define F_LIT64   0x08   /* LIT64 may appear                            */
static const UNS8 IMAGE_MAGIC[8] = { 'C', 'V', '8', '0' + SCALE, CELL_BYTES,
    'L', CV8_VERSION, F_VARCALL | F_VARSLOT | F_SPEC | F_LIT64 };

/*
 *  write() wrapper: don't care about partial writes here, only used for
 *  short fixed error/usage messages before exit.
 */

static void write_str(int fd, const char *s);
#if !GUARD
static void stack_fault(int which) __attribute__((noreturn, cold));
#endif

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

#if !GUARD
static void stack_fault(int which) {
    write_str(2, which ? "relf: return stack overflow\n"
                       : "relf: data stack overflow\n");
    exit(70);
}
#endif

#if GUARD
#include <sys/mman.h>
#include <signal.h>
/*  The regions, top down:
 *      [rfloor, MEMSIZE)          return stack
 *      [rfloor - page, rfloor)    GUARD: return stack overflow
 *      [dfloor + page, ...)       data stack
 *      [dfloor, dfloor + page)    GUARD: data stack overflow - and the
 *                                 dictionary growing up into the stacks
 *  Both guard pages come out of the data stack's space, so nothing else
 *  moves; the data stack is two pages shallower. The messages and the
 *  status are stack_fault()'s. _exit, not exit: this runs in a signal
 *  handler, and the output buffer may be half-written.  */
static void term_restore(void);   /* the terminal, on the way out */
static UNS64 g_dguard, g_rguard, g_page;
static void guard_trap(int sig, siginfo_t *si, void *uc) {
    UNS64 a = (UNS64)(uintptr_t)si->si_addr;
    (void)sig; (void)uc;
    if (a >= g_dguard && a < g_dguard + g_page)
        write_str(2, "relf: data stack overflow\n");
    else if (a >= g_rguard && a < g_rguard + g_page)
        write_str(2, "relf: return stack overflow\n");
    else
        write_str(2, "relf: segmentation fault (not a stack guard)\n");
    term_restore();
    _exit(70);
}
static void install_guards(UNS8 *b) {
    UNS64 dfloor = (UNS64)(uintptr_t)b + MEMSIZE - RSTACK_BYTES - DSTACK_BYTES;
    UNS64 rfloor = (UNS64)(uintptr_t)b + MEMSIZE - RSTACK_BYTES;
    struct sigaction sa;
    g_page = (UNS64)sysconf(_SC_PAGESIZE);
    g_dguard = dfloor;
    g_rguard = rfloor - g_page;
    if (mprotect((void *)(uintptr_t)g_rguard, g_page, PROT_NONE) != 0
        || mprotect((void *)(uintptr_t)g_dguard, g_page, PROT_NONE) != 0) {
        write_str(2, "relf: cannot protect the stack guard pages\n");
        exit(70);
    }
    memset(&sa, 0, sizeof sa);
    sa.sa_sigaction = guard_trap;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, (struct sigaction *)0);
    sigaction(SIGBUS, &sa, (struct sigaction *)0);
}
#endif

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

#define NOPENMODES 11
static const int open_flags[NOPENMODES] = {
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
    O_WRONLY | O_CREAT | O_APPEND, /* ab : same */
    /*  CREATE-FILE's readable modes: kernel.4 maps R/O and R/W here.
     *  Until Iteration 245 it masked every mode down to w/wb, so a file
     *  created R/W could not be read back.  */
    O_RDWR | O_CREAT | O_TRUNC,    /* w+  */
    O_RDWR | O_CREAT | O_TRUNC,    /* w+b */
    /*  set -C: create, but refuse a file that is already there. POSIX
     *  gives the shell O_EXCL for noclobber, which also lets `> /dev/null`
     *  through, since the open succeeds on a device (Iteration 305).  */
    O_WRONLY | O_CREAT | O_EXCL,   /* x */
};

/*
 *  This function reads binary forth image from file into memory.
 */

#define MAX_THREADS 4096
#define MAX_TAILS 16
/*  The locals opcodes (CV8-REFERENCE.md 7.3) reach shadow.4's save
 *  stack through five cells at image offset 8, which kernel.4 reserves
 *  and shadow.4 fills in when it loads: the save-stack pointer and the
 *  buffer cell (both as offsets of their parameter fields), the limit,
 *  and the LSAVE and LRESTORE bodies the opcodes fall back to. They
 *  live in the image rather than the file header so that they are
 *  valid as soon as shadow.4 is loaded, not only after a save and
 *  reload - a word using locals can run while the shell is compiled. */
#define LOCHDR(k) CELL(cbase + 8 + (k) * CELL_BYTES)

static void load_image(const char *name) {
    int fd;
    long len;
    UNS8 magic[8];
    UNS64 ntails, nthreads;
    UNS64 heads[MAX_THREADS];
    long i;

    fd = open(name, O_RDONLY);
    if (fd < 0) {
        write_str(2, "Cannot open image file.\n");
        exit(2);
    }
    if (full_read(fd, magic, 8) != 8 || memcmp(magic, IMAGE_MAGIC, 5) != 0) {
        write_str(2, "not a RelF image, or built for a different encoding "
                     "or cell width.\n");
        exit(2);
    }
    /*  Bytes 6-7 are a format version and a FEATURE BITMAP. The engine
     *  runs any image whose required features it implements, so adding
     *  a feature does not invalidate older images. A VERSION change is a
     *  different matter - it is what changes when a byte's meaning
     *  does - so only this engine's own version is run, older or newer
     *  being refused alike. Until Iteration 247 only newer ones were.  */
    if (magic[6] != IMAGE_MAGIC[6]) {
        write_str(2, "image is a different CV8 format version than this engine\n");
        exit(2);
    }
    if (magic[7] & ~IMAGE_MAGIC[7]) {
        write_str(2, "image needs CV8 features this engine was not built "
                     "with (varcall/varslot/spec/lit64)\n");
        exit(2);
    }
    /*
     *  Header, after the magic: the newest word's NFA as an offset, the
     *  number of DOES> tail entries, then that many (word number, byte
     *  offset) pairs.
     *
     *  The word table is DERIVED, not saved - it holds absolute
     *  addresses and would not survive relocation. It is rebuilt here by
     *  walking the link chain, which is the same walk FIND does. The
     *  tail entries exist because a DOES>-created word's body begins
     *  with a call to a MID-WORD address, and a call token can only name
     *  a word start; there are exactly two such addresses in the image,
     *  so the header describes how to finish deriving the table rather
     *  than carrying the table itself.
     */
    /*  The word list is HASHED, so there is no single chain to walk and
     *  the header carries every thread head: a count, then that many
     *  START-relative offsets. Only SOD16 uses them - it is the one
     *  encoding that names a call by word NUMBER - but the header has
     *  one shape for every encoding.  */
    if (full_read(fd, (UNS8*)&nthreads, CELL_BYTES) != CELL_BYTES) {
        write_str(2, "Truncated image header.\n");
        exit(2);
    }
    if (nthreads < 1 || nthreads > MAX_THREADS) {
        write_str(2, "Image declares an impossible thread count.\n");
        exit(2);
    }
    for (i = 0; i < nthreads; i++)
        if (full_read(fd, (UNS8*)&heads[i], CELL_BYTES) != CELL_BYTES) {
            write_str(2, "Truncated image header.\n");
            exit(2);
        }
    if (full_read(fd, (UNS8*)&ntails, CELL_BYTES) != CELL_BYTES) {
        write_str(2, "Truncated image header.\n");
        exit(2);
    }
    if (ntails > MAX_TAILS) {
        write_str(2, "Image declares too many DOES> tails.\n");
        exit(2);
    }
    /*  The DOES> tail entries are SKIPPED, not stored. They named a word
     *  and an offset into it for the word table, which nothing builds
     *  any more; the bytes still have to be consumed to reach what
     *  follows. There were two copies of this loop - one under #if SPEC
     *  and one after it disabled by `if (0)` - which differed only in
     *  where they put a value neither of them needed.  */
    for (i = 0; i < (long)ntails; i++) {
        UNS64 w_, o_;
        if (full_read(fd, (UNS8*)&w_, CELL_BYTES) != CELL_BYTES ||
            full_read(fd, (UNS8*)&o_, CELL_BYTES) != CELL_BYTES) {
            write_str(2, "Truncated image header.\n");
            exit(2);
        }
    }
    base = (UNS8*)(((UNS64)(uintptr_t)mem + CELL_BYTES - 1)
                    & ~(UNS64)(CELL_BYTES - 1));
    len = full_read(fd, base, MEMSIZE);
    close(fd);
    if (len < 0) {
        write_str(2, "Error reading image file.\n");
        exit(2);
    }

    /*  Nothing here reads a dictionary link. Only SOD16 named a call by
     *  word NUMBER and so needed a number->address table built by
     *  walking the chain at load; CV8 computes a call target from the
     *  address. That is what lets the byte-header layout change a
     *  link's encoding without the engine knowing or caring, and it is
     *  why the header still carries the thread heads even though this
     *  loader ignores them.
     *
     *  The table construction was left here behind an unconditional
     *  `return` when SOD16 was retired from the engine; it is deleted
     *  now that SOD16 is retired from the tree.  */
}

/*
 *  Virtual machine itself: computed-goto threaded dispatch. Each
 *  handler is a labeled block ending in NEXT. A direct primitive's
 *  opcode is its position in kernel.4's PRIMITIVE list; an escaped
 *  one's selector is its position after ESCAPED (CV8.md 3.2).
 */

#define NSIG_FLAGS 65
static volatile sig_atomic_t sig_flag[NSIG_FLAGS];
static void sig_catch(int sig) { if (sig > 0 && sig < NSIG_FLAGS) sig_flag[sig] = 1; }

#define PROF(k)
#define PROFIP(a)
#define PROFDUMP

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


#define NOINLINE_IO __attribute__((noinline))
/*  One read(2) or write(2): the count, or -errno.  */
NOINLINE_IO static long t_read(int fd, UNS64 a, UNS64 u) {
    long n = read(fd, (void *)(uintptr_t)a, (size_t)u);
    return n < 0 ? -(long)errno : n;
}

/*  RAW-MODE's terminal state (Iteration 254). One saved setting, for
 *  the one descriptor raw mode was turned on for, and the process that
 *  did it: a forked child that exits must not hand its parent's
 *  terminal back to line mode. term_restore() is called on every way
 *  out - BYE, SYS-EXIT and the stack guard's handler, where tcsetattr
 *  is async-signal-safe - so a program that ends in raw mode does not
 *  leave the terminal that way.  */
static struct termios t_saved;
static int t_raw_fd = -1;
static pid_t t_raw_pid;

static void term_restore(void) {
    if (t_raw_fd >= 0 && getpid() == t_raw_pid)
        tcsetattr(t_raw_fd, TCSANOW, &t_saved);
}

/*  Raw mode is "cbreak": no line editing and no echo, a byte at a time,
 *  but signal keys still work - Ctrl-C still interrupts - and output
 *  processing is untouched, so newlines still print as newlines.  */
NOINLINE_IO static long t_rawmode(int fd, int on) {
    struct termios t;
    if (!on) {
        if (t_raw_fd != fd) return 0;
        if (tcsetattr(fd, TCSANOW, &t_saved) < 0) return -(long)errno;
        t_raw_fd = -1;
        return 0;
    }
    if (tcgetattr(fd, &t) < 0) return -(long)errno;
    if (t_raw_fd < 0) { t_saved = t; t_raw_fd = fd; t_raw_pid = getpid(); }
    t.c_lflag &= ~(tcflag_t)(ICANON | ECHO);
    t.c_cc[VMIN] = 1;
    t.c_cc[VTIME] = 0;
    if (tcsetattr(fd, TCSANOW, &t) < 0) return -(long)errno;
    return 0;
}

/*  poll(2) on n structs at a, waiting ms milliseconds (-1: for ever):
 *  the number ready, 0 on timeout, or -errno.  */
NOINLINE_IO static long t_poll(UNS64 a, UNS64 n, UNS64 ms) {
    int r = poll((struct pollfd *)(uintptr_t)a, (nfds_t)n, (int)(INT64)ms);
    return r < 0 ? -(long)errno : r;
}

NOINLINE_IO static long t_write(int fd, UNS64 a, UNS64 u) {
    long n = write(fd, (const void *)(uintptr_t)a, (size_t)u);
    return n < 0 ? -(long)errno : n;
}

NOINLINE_IO static void t_flush(void) {
    if (t_olen) { full_write(1, t_obuf, (size_t)t_olen); t_olen = 0; }
}

NOINLINE_IO static void t_put(UNS8 c) {
    if (t_olen == TIOBUF) t_flush();
    t_obuf[t_olen++] = c;
}

static void virtual_machine(void) {
    VMREGS
    UNS64 tos = CELL(dsp); dsp += CELL_BYTES;       /* fill */
#define NOS CELL(dsp)
#define PUSHT(x) do { UNS64 v_ = (x); dsp -= CELL_BYTES;         \
        STACK_CHECK(dsp < dsp_limit, 0)                              \
        CELL(dsp) = tos; tos = v_; } while (0)
#define POPT() do { tos = CELL(dsp); dsp += CELL_BYTES; } while (0)
#undef VMPUSH
#define VMPUSH PUSHT
#define SPILL() do { dsp -= CELL_BYTES; CELL(dsp) = tos; } while (0)
#define FILLNEXT() do { POPT(); NEXT(); } while (0)
/*  A CV8 branch operand is a signed 16-bit BYTE offset. The 16-bit
 *  encodings measured it in tokens and needed the doubling; they are
 *  retired, so there is one form.  */
#define BROFF(a) ((int16_t)LD16(a))
    /* CV8: byte stream. b < 0x80 is an opcode; otherwise b and the next
     * byte are a 15-bit scaled offset from the image base. */
    const UNS64 cbase = (UNS64)(uintptr_t)base;
    /*  The direct primitives, in kernel.4 order: opcodes 0..NDIRECT-1.  */
    static const void *const direct_prims[] = {
        &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop,
        &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch,
        &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr,
        &&L_tor, &&L_rfetch, &&L_eq, &&L_ugt, &&L_gt, &&L_plus,
        &&L_negate, &&L_lshift, &&L_rshift, &&L_ummult, &&L_umdiv,
        &&L_dplus, &&L_type, &&L_spfetch, &&L_spstore,
        &&L_rpfetch, &&L_rpstore,
    };
    /*  The escaped primitives, in kernel.4 order after ESCAPED:
     *  selectors 0..NESC-1.  */
    static const void *const escaped_prims[] = {
        &&L_bye, &&L_openfile, &&L_closefile,
        &&L_system, &&L_reposfile, &&L_filepos, &&L_delfile, &&L_filesize,
        &&L_fork, &&L_execve, &&L_waitpid, &&L_pipe, &&L_dup2,
        &&L_getenv, &&L_setenv, &&L_sysexit, &&L_chdir, &&L_getcwd,
        &&L_sysargc, &&L_sysarg, &&L_getpid, &&L_unsetenv,
        &&L_allocate, &&L_free, &&L_resize, &&L_getpwhome,
        &&L_getfsize, &&L_setfsize, &&L_read, &&L_write, &&L_poll,
        &&L_rawmode,
        &&L_move, &&L_fill, &&L_compare, &&L_scan, &&L_cstrlen,
        &&L_isatty, &&L_opendir, &&L_readdir, &&L_closedir, &&L_access,
        &&L_kill, &&L_umask, &&L_cputimes, &&L_sigaction, &&L_sigpending,
        &&L_termraw, &&L_termrestore,
        &&L_filekind,
        &&L_getrlimit, &&L_setrlimit, &&L_waitnohang,
        &&L_getppid, &&L_envat,
        &&L_setpgid, &&L_tcsetpgrp, &&L_tcgetpgrp, &&L_waitjob,
        &&L_filemode, &&L_localtime, &&L_dupfrom,
    };
    /*  Every opcode that is not a direct primitive. The synthetic ones
     *  and the folded band are numbered from NSYN, and move when a
     *  DIRECT primitive is added; the specialised band, LIT64 and ESC
     *  are fixed. The folded order is kernel.4's fold list.  */
    static const void *const other_ops[128] = {
        [NSYN] = &&L_lit32, &&L_dovar, &&L_dodoes, &&L_lit8, &&L_lit8x,
        /*  After the folded band: the one-byte-offset branches
         *  (Iteration 258).  */
        [NSYN + 5 + 23] = &&L_branch8, &&L_0branch8,
        [NSYN + 5 + 11] = &&LX_lit,
        [NSYN + 5 + 15] = &&LX_drop,
        [NSYN + 5 + 16] = &&LX_dup,
        [NSYN + 5 + 17] = &&LX_swap,
        [NSYN + 5 + 18] = &&LX_rot,
        [NSYN + 5 + 14] = &&LX_over,
        [NSYN + 5 + 6] = &&LX_cfetch,
        [NSYN + 5 + 3] = &&LX_fetch,
        [NSYN + 5 + 7] = &&LX_cstore,
        [NSYN + 5 + 2] = &&LX_store,
        [NSYN + 5 + 8] = &&LX_and,
        [NSYN + 5 + 9] = &&LX_or,
        [NSYN + 5 + 10] = &&LX_xor,
        [NSYN + 5 + 20] = &&LX_fromr,
        [NSYN + 5 + 19] = &&LX_tor,
        [NSYN + 5 + 21] = &&LX_rfetch,
        [NSYN + 5 + 1] = &&LX_eq,
        [NSYN + 5 + 13] = &&LX_ugt,
        [NSYN + 5 + 12] = &&LX_gt,
        [NSYN + 5 + 0] = &&LX_plus,
        [NSYN + 5 + 22] = &&LX_negate,
        [NSYN + 5 + 4] = &&LX_lshift,
        [NSYN + 5 + 5] = &&LX_rshift,
        [0x61] = &&L_lit0, &&L_lit1, &&L_litm1, &&L_vf, &&L_vs,
        &&L_lsave, &&L_lrest, &&L_lstore, &&L_lzero,
        &&L_zeq, &&L_sub, &&L_ne, &&L_zlt, &&L_sgt, &&L_2dup, &&L_2drop,
        &&L_charp, &&L_onep, &&L_cellp, &&L_cells, &&L_onem, &&L_invert,
        &&L_count, &&L_aligned, &&L_addi, &&L_addix, &&L_eqi, &&L_eqix,
        [0x7D] = &&L_lit64, [0x7E] = &&L_esc,
    };
    _Static_assert(sizeof direct_prims / sizeof *direct_prims == NDIRECT,
                   "NDIRECT does not match the direct primitive table");
    _Static_assert(sizeof escaped_prims / sizeof *escaped_prims == NESC,
                   "NESC does not match the escaped primitive table");
    _Static_assert(NSYN + 5 + 23 + 2 <= 0x61,
                   "the folded band has reached the specialised band");
    /*  The opcode table, and the selector table ESC indexes with a whole
     *  byte - so a selector past NESC lands on a diagnosis, not past
     *  the end of an array.  */
    const void *cv8_tab[128], *esc_tab[256];
    { int i_;
      for (i_ = 0; i_ < 128; i_++)
          cv8_tab[i_] = i_ < NDIRECT ? direct_prims[i_]
                      : other_ops[i_] ? other_ops[i_] : &&L_noop;
      for (i_ = 0; i_ < 256; i_++)
          esc_tab[i_] = i_ < NESC ? escaped_prims[i_] : &&L_badesc; }
#define dispatch cv8_tab
    /*  Same handlers, but indexed by the whole byte: 0x80-0xFF all land
     *  on do_call, so no test is needed to tell an opcode from a call. */
    const void *dtab256[256];
    { int i_, n_ = (int)(sizeof dispatch / sizeof dispatch[0]);
      for (i_ = 0; i_ < 256; i_++)
          dtab256[i_] = (i_ < n_ && i_ < 128) ? dispatch[i_] : &&do_call; }

/*  Every handler keeps its own opcode dispatch (what the branch predictor
 *  needs), but the call path - decode, RPUSH, limit check - exists once.
 *  GCC otherwise replicates ~50 bytes of it into all ~120 handlers.  */
#define NEXT() do { \
        PROFIP(ip); t = BYTE(ip); ip += 1; PROF(t); goto *dtab256[t]; \
    } while (0)

    NEXT();
do_call:
    /*  ip is already past the first byte here.  */
    if (t & 0x40) { t = ((t & 0x3F) << 16) | ((UNS64)BYTE(ip) << 8) | BYTE(ip + 1);
                    ip += 2; }
    else          { t = ((t & 0x3F) << 8) | BYTE(ip); ip += 1; }
    PROF(256); RPUSH(ip); ip = cbase + (t << SCALE);
    NEXT();

L_noop:    /* noop    */ NEXT();
L_exit:    /* exit    */ ip = RS; rp += CELL_BYTES; NEXT();
L_lit: PUSHT(OPND16(ip)); ip += 2; NEXT();
L_lit8: PUSHT(BYTE(ip)); ip += 1; NEXT();
L_lit8x: PUSHT(BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();
L_lit32: SPILL();   /* lit32   */ { UNS64 v = LD32(ip);
                           if (v & 0x80000000u) v |= ~(UNS64)0xFFFFFFFFu;
                           PUSH(v); ip += 4; } FILLNEXT();
/*  Specialised opcodes at 0x61 (they were at 0x60 until a 69th
 *  primitive pushed the folded band onto it), each borrowed from
 *  another VM (CV8.md 10).
 *  The slot/variable operand is a 16-bit little-endian value v; the
 *  address is base + (v << SCALE), the same compressed pointer calls use. */
/*  A slot operand is the variable's offset from the OPERAND itself
 *  (Iteration 259; from the image base until then): two bytes, 15 bits
 *  signed, or three with the top bit set, 23 bits signed. Code sits a
 *  few hundred bytes after the variables it uses, so nine in ten are the
 *  short form, where half were. SEXT sign-extends a b-bit field at
 *  either cell width.  */
#define SEXT(v, b) (((v) ^ ((UNS64)1 << ((b) - 1))) - ((UNS64)1 << ((b) - 1)))
#define SLOT() (t = BYTE(ip), \
        (t & 0x80) ? (t = ((t & 0x7F) << 16) | ((UNS64)BYTE(ip + 1) << 8) \
                         | BYTE(ip + 2), ip += 3, ip - 3 + (SEXT(t, 23) << SCALE)) \
                   : (t = (t << 8) | BYTE(ip + 1), ip += 2, ip - 2 + (SEXT(t, 15) << SCALE)))
L_lit0: PUSHT(0); NEXT();
L_lit1: PUSHT(1); NEXT();
L_litm1: PUSHT(~(UNS64)0); NEXT();
L_vf: { UNS64 a = SLOT(); PUSHT(CELL(a)); } NEXT();
L_vs: { UNS64 a = SLOT(); CELL(a) = tos; POPT(); } NEXT();
L_lsave: { UNS64 a = SLOT(), lsp = cbase + LOCHDR(0);
    UNS64 sp = CELL(lsp), stk = CELL(cbase + LOCHDR(1));
    if ((INT64)sp >= (INT64)LOCHDR(2) || (INT64)sp < 0 || !stk) {
        VMPUSH(a - cbase); RPUSH(ip); ip = cbase + LOCHDR(3); NEXT(); }
    CELL(stk + sp * CELL_BYTES) = CELL(a); CELL(lsp) = sp + 1; } NEXT();
L_lrest: { UNS64 a = SLOT(), lsp = cbase + LOCHDR(0);
    UNS64 sp = CELL(lsp), stk = CELL(cbase + LOCHDR(1));
    if ((INT64)sp <= 0 || !stk) {
        VMPUSH(a - cbase); RPUSH(ip); ip = cbase + LOCHDR(4); NEXT(); }
    CELL(lsp) = --sp; CELL(a) = CELL(stk + sp * CELL_BYTES); } NEXT();
L_lstore: { UNS64 a = SLOT(); CELL(a) = tos; POPT(); } NEXT();
L_lzero:  { UNS64 a = SLOT(); CELL(a) = 0; } NEXT();
/*  The kernel's hottest tiny colon words, as opcodes (Gforth-style
 *  primitive selection). The translator substitutes one only where the
 *  compiled body is exactly the definition implemented here.  */
L_zeq: tos = -(UNS64)(tos == 0); NEXT();
L_sub: tos = NOS - tos; dsp += CELL_BYTES; NEXT();
L_ne: tos = -(UNS64)(NOS != tos); dsp += CELL_BYTES; NEXT();
L_zlt: tos = -(UNS64)((INT64)tos < 0); NEXT();
L_sgt: tos = -(UNS64)((INT64)tos < (INT64)NOS); dsp += CELL_BYTES; NEXT();
L_2dup: { UNS64 a_ = NOS, b_ = tos; PUSHT(a_); PUSHT(b_); } NEXT();
L_2drop: tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();
L_charp: tos += 1; NEXT();
L_onep: tos += 1; NEXT();
L_cellp: tos += CELL_BYTES; NEXT();
L_cells: tos <<= CELL_SHIFT; NEXT();
L_onem: tos -= 1; NEXT();
L_invert: tos = ~tos; NEXT();
L_count: { UNS64 a_ = tos; tos = a_ + 1; PUSHT(BYTE(a_)); } NEXT();
L_aligned: tos = (tos + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1); NEXT();
L_addi: tos += (UNS64)(INT64)(int8_t)BYTE(ip); ip += 1; NEXT();
L_addix: tos += (UNS64)(INT64)(int8_t)BYTE(ip); ip = RS; rp += CELL_BYTES; NEXT();
L_eqi: tos = -(UNS64)(tos == (UNS64)(INT64)(int8_t)BYTE(ip)); ip += 1; NEXT();
L_eqix: tos = -(UNS64)(tos == (UNS64)(INT64)(int8_t)BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();
L_lit64: SPILL();   /* lit64: a full cell, little-endian. CELL_BYTES bytes.      */
    { UNS64 v = 0; int i_;
      for (i_ = CELL_BYTES - 1; i_ >= 0; i_--) v = (v << 8) | BYTE(ip + i_);
      PUSH(v); ip += CELL_BYTES; } FILLNEXT();
L_esc:     /*  The escaped band: one more byte selects an OS/libc
            *  primitive. Half the primitive band was these, for 3.2% of
            *  static sites and 0.006% of dispatches; behind an escape
            *  they cost a byte each and free 32 opcodes.  */
    t = BYTE(ip); ip += 1; PROF(t); goto *esc_tab[t];
L_badesc:
    write_str(2, "relf: image uses an escaped primitive this engine does not have\n");
    exit(2);
L_dovar: PUSHT((ip + 3 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1)); ip = RS; rp += CELL_BYTES; NEXT();
L_dodoes:  /* [DODOES][tail][pad][PFA] -> the tail's R> finds the PFA */
    if (BYTE(ip) & 0x40) {
        t = ((BYTE(ip) & 0x3F) << 16) | ((UNS64)BYTE(ip + 1) << 8) | BYTE(ip + 2);
        RPUSH((ip + 3 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
    } else {
        t = ((BYTE(ip) & 0x3F) << 8) | BYTE(ip + 1);
        RPUSH((ip + 2 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
    }
    ip = cbase + (t << SCALE); NEXT();
L_branch:  /* branch  */ ip += (int16_t)LD16(ip); NEXT();
/*  BRANCH8 and ?BRANCH8: the same, with a one-byte signed offset, also
 *  from the operand. The compiler uses them for backward branches, whose
 *  distance it knows - nine in ten fit (Iteration 258).  */
L_branch8:  ip += (int8_t)BYTE(ip); NEXT();
L_0branch8: t = tos; POPT(); if (t) ip += 1; else ip += (int8_t)BYTE(ip); NEXT();
L_0branch: t = tos; POPT(); if (t) ip += 2; else ip += BROFF(ip); NEXT();
L_drop: POPT(); NEXT();
L_dup: PUSHT(tos); NEXT();
L_swap: t = NOS; NOS = tos; tos = t; NEXT();
L_rot: t = CELL(dsp + CELL_BYTES); CELL(dsp + CELL_BYTES) = NOS; NOS = tos; tos = t; NEXT();
L_over: t = NOS; PUSHT(t); NEXT();
L_cfetch: tos = BYTE(tos); NEXT();
L_fetch: tos = CELL(tos); NEXT();
L_cstore: BYTE(tos) = (UNS8)NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();
L_store: CELL(tos) = NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; NEXT();
L_and: tos &= NOS; dsp += CELL_BYTES; NEXT();
L_or: tos |= NOS; dsp += CELL_BYTES; NEXT();
L_xor: tos ^= NOS; dsp += CELL_BYTES; NEXT();
L_fromr: PUSHT(RS); rp += CELL_BYTES; NEXT();
L_tor: RPUSH(tos); POPT(); NEXT();
L_rfetch: PUSHT(RS); NEXT();
L_eq: tos = -(UNS64)(NOS == tos); dsp += CELL_BYTES; NEXT();
L_ugt: tos = -(UNS64)(NOS < tos); dsp += CELL_BYTES; NEXT();
L_gt: tos = -(UNS64)((INT64)NOS < (INT64)tos); dsp += CELL_BYTES; NEXT();
L_plus: tos += NOS; dsp += CELL_BYTES; NEXT();
L_negate: tos = -tos; NEXT();
L_lshift: tos = NOS << tos; dsp += CELL_BYTES; NEXT();
L_rshift: tos = NOS >> tos; dsp += CELL_BYTES; NEXT();
L_ummult: SPILL();  /* um*     */ umul(&DS0, &DS1); FILLNEXT();
L_umdiv: SPILL();   /* um/mod  */ udiv(&DS0, &DS1, &DS2); dsp += CELL_BYTES; FILLNEXT();
L_dplus: SPILL();   /* d+      */
    DS3 += DS1; DS2 += DS0; DS2 += (DS3 < DS1);
    dsp += 2 * CELL_BYTES;
    FILLNEXT();

L_type: SPILL(); { /* type    */ /* c-addr u --- */
    /* TYPE is the terminal output primitive and EMIT is built on it
     * in kernel.4: a primitive that moves a WHOLE STRING costs one
     * dispatch where a per-character EMIT costs one per byte. Its
     * output is buffered here (t_obuf) and flushed by every primitive
     * that reads, writes, forks, execs or exits. Input has no such
     * buffer: see KEY. */
    const UNS8 *p = (const UNS8 *)(uintptr_t)DS1;
    UNS64 u = DS0;
    for (UNS64 i = 0; i < u; i++) t_put(p[i]);
    dsp += 2 * CELL_BYTES;
    FILLNEXT();
    }
L_bye: SPILL();     /* bye     */ t_flush(); term_restore(); PROFDUMP; exit(0);
L_spfetch: SPILL(); /* sp@     */ PUSH(dsp + CELL_BYTES); FILLNEXT();
L_spstore: SPILL(); /* sp!     */ dsp = DS0; FILLNEXT();
L_rpfetch: SPILL(); /* rp@     */ PUSH(rp); FILLNEXT();
L_rpstore: SPILL(); /* rp!     */ rp = DS0; dsp += CELL_BYTES; FILLNEXT();

L_openfile: SPILL(); { /* c-addr u fam --- fid ior */
    int fd;
    t = BYTE(DS2 + DS1);
    BYTE(DS2 + DS1) = 0;
    fd = DS0 < NOPENMODES
        ? open((char *)(uintptr_t)DS2, open_flags[DS0], 0644) : -1;
    BYTE(DS2 + DS1) = t;
    DS2 = (UNS64)fd;
    DS1 = (fd >= 0) ? 0 : 200;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_closefile: SPILL(); {/* fid --- ior */
    DS0 = (UNS64)close((int)DS0);
    FILLNEXT();
    }
L_system: SPILL(); { t_flush(); /* c-addr u --- ior */
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
    FILLNEXT();
}
L_reposfile: SPILL(); { /* ud fid --- ior */
    /*  ANS: ( ud fileid -- ior ) - the offset is a DOUBLE, low cell
     *  under high cell. See L_filepos. */
    int fd = (int)DS0;
    unsigned long long off = (CELL_BYTES == 8)
        ? (unsigned long long)DS2
        : ((unsigned long long)DS2 | ((unsigned long long)DS1 << 32));
    off_t r = lseek(fd, (off_t)off, SEEK_SET);
    dsp += 2 * CELL_BYTES;
    DS0 = (r < 0) ? 200 : 0;
    FILLNEXT();
    }
L_filepos: SPILL(); { /* fid --- ud ior */
    /*  ANS: ( fileid -- ud ior ) - the position is a DOUBLE, low cell
     *  then high cell. This returned a single cell until the Forth
     *  Standard file tests were adopted and said so; nothing in Forth
     *  called it, which is why it went unnoticed. */
    off_t p = lseek((int)DS0, 0, SEEK_CUR);
    dsp -= 2 * CELL_BYTES;
    if (p < 0) { DS2 = 0; DS1 = 0; DS0 = 200; }
    else {
        unsigned long long q = (unsigned long long)p;
        DS2 = (UNS64)q;
        DS1 = (UNS64)(CELL_BYTES == 8 ? 0ULL : (q >> 32));
        DS0 = 0;
    }
    FILLNEXT();
    }
L_delfile: SPILL(); { /* c-addr u --- ior */
    /*  The byte past the name is borrowed for a NUL and put back. It
     *  was put back AFTER DS1 had been overwritten with unlink()'s
     *  result, so the write went to address 0 + u and DELETE-FILE
     *  segfaulted on success (found in Iteration 245).  */
    long r;
    t = BYTE(DS1 + DS0);
    BYTE(DS1 + DS0) = 0;
    r = unlink((char*)(uintptr_t)DS1);
    BYTE(DS1 + DS0) = t;
    DS1 = (UNS64)(INT64)r;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_filesize: SPILL(); { /* fid --- ud ior */
    /*  ANS: ( fileid -- ud ior ), a DOUBLE - see L_filepos. */
    int fd = (int)DS0;
    off_t cur = lseek(fd, 0, SEEK_CUR), end = -1;
    if (cur >= 0) { end = lseek(fd, 0, SEEK_END); lseek(fd, cur, SEEK_SET); }
    dsp -= 2 * CELL_BYTES;
    if (end < 0) { DS2 = 0; DS1 = 0; DS0 = 200; }
    else {
        unsigned long long q = (unsigned long long)end;
        DS2 = (UNS64)q;
        DS1 = (UNS64)(CELL_BYTES == 8 ? 0ULL : (q >> 32));
        DS0 = 0;
    }
    FILLNEXT();
    }
/*  READ and WRITE: read(2) and write(2), once each. Everything that
 *  reads or writes a descriptor is Forth on top of these - buffering,
 *  line splitting, retrying a signal, looping over short counts - so
 *  that policy is in kernel.4 where it can be read (Iteration 245).
 *  Both flush the terminal output buffer first: a prompt must appear
 *  before the read that waits for its answer, and TYPE's bytes must
 *  keep their place among everything else written.  */
L_read: SPILL(); { /* c-addr u fd --- n : n < 0 is -errno */
    t_flush();
    DS2 = (UNS64)(INT64)t_read((int)DS0, DS2, DS1);
    dsp += 2 * CELL_BYTES;
    FILLNEXT();
}
/*  POLL: poll(2), once. With it, Forth can wait for a descriptor
 *  without changing anything shared - KEY waits on a non-blocking
 *  stdin, KEY? asks without taking a byte, and MS is a poll on no
 *  descriptors (Iteration 246). Flushes first, as READ does: this is a
 *  wait.  */
L_poll: SPILL(); { /* a-addr n ms --- n' : n' < 0 is -errno */
    t_flush();
    DS2 = (UNS64)(INT64)t_poll(DS2, DS1, DS0);
    dsp += 2 * CELL_BYTES;
    FILLNEXT();
}
/*  RAW-MODE: the terminal on fd a byte at a time without echo (flag
 *  true), or back as it was (flag false). ior is 0 or -errno - -ENOTTY
 *  for a descriptor that is not a terminal.  */
L_rawmode: SPILL(); { /* fd flag --- ior */
    t_flush();
    DS1 = (UNS64)(INT64)t_rawmode((int)DS1, DS0 != 0);
    dsp += CELL_BYTES;
    FILLNEXT();
}
/*  Memory and strings, from libc (Iteration 260). The kernel had them
 *  as byte-at-a-time threaded loops, and after one fix to 2SWAP the
 *  shell's two hottest words by dispatch count were string loops.  */
L_move: SPILL(); { /* c-addr1 c-addr2 u --- */
    if (DS0) memmove((void *)(uintptr_t)DS1, (void *)(uintptr_t)DS2, (size_t)DS0);
    dsp += 3 * CELL_BYTES;
    FILLNEXT();
}
L_fill: SPILL(); { /* c-addr u c --- */
    if (DS1) memset((void *)(uintptr_t)DS2, (int)(DS0 & 255), (size_t)DS1);
    dsp += 3 * CELL_BYTES;
    FILLNEXT();
}
L_compare: SPILL(); { /* c-addr1 u1 c-addr2 u2 --- n : -1, 0 or 1 */
    size_t u1 = (size_t)DS2, u2 = (size_t)DS0;
    int r = memcmp((void *)(uintptr_t)DS3, (void *)(uintptr_t)DS1, u1 < u2 ? u1 : u2);
    DS3 = (UNS64)(INT64)(r < 0 ? -1 : r > 0 ? 1 : u1 < u2 ? -1 : u1 > u2 ? 1 : 0);
    dsp += 3 * CELL_BYTES;
    FILLNEXT();
}
L_scan: SPILL(); { /* c-addr1 u1 c --- c-addr2 u2 : from the first c, or the end and 0 */
    UNS64 a = DS2, u = DS1;
    const char *p = u ? memchr((void *)(uintptr_t)a, (int)(DS0 & 255), (size_t)u) : 0;
    if (p) { DS1 = a + u - (UNS64)(uintptr_t)p; DS2 = (UNS64)(uintptr_t)p; }
    else   { DS1 = 0; DS2 = a + u; }
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_cstrlen: SPILL(); /* c-addr --- u : a NUL-terminated string's length */
    DS0 = (UNS64)strlen((const char *)(uintptr_t)DS0);
    FILLNEXT();
/*  Directories, for pathname expansion (Iteration 267): libc's
 *  opendir/readdir/closedir. READ-DIR's name is valid until the next
 *  READ-DIR on that directory.  */
L_opendir: SPILL(); /* c-addr --- dirp | 0 : a NUL-terminated path */
    DS0 = (UNS64)(uintptr_t)opendir((const char *)(uintptr_t)DS0);
    FILLNEXT();
L_readdir: SPILL(); { /* dirp --- c-addr | 0 */
    struct dirent *e = readdir((DIR *)(uintptr_t)DS0);
    DS0 = e ? (UNS64)(uintptr_t)e->d_name : 0;
    FILLNEXT();
}
L_closedir: SPILL(); /* dirp --- */
    closedir((DIR *)(uintptr_t)DS0);
    dsp += CELL_BYTES;
    FILLNEXT();
/*  Signals, kill, umask, times (Iteration 271: the shell's trap, kill,
 *  umask and times). A caught signal only raises a flag; the shell
 *  looks at the flags between commands, which is when POSIX runs a
 *  trap's action. SIGSEGV and SIGBUS stay with the stack guard.  */
L_kill: SPILL(); /* pid sig --- ior */
    DS1 = kill((pid_t)(INT64)DS1, (int)DS0) ? (UNS64)(INT64)-errno : 0;
    dsp += CELL_BYTES;
    FILLNEXT();
L_umask: SPILL(); /* mask --- old */
    DS0 = (UNS64)umask((mode_t)DS0);
    FILLNEXT();
L_cputimes: SPILL(); { /* --- user sys child-user child-sys : milliseconds */
    struct rusage s, c;
    getrusage(RUSAGE_SELF, &s);
    getrusage(RUSAGE_CHILDREN, &c);
    PUSH((UNS64)(s.ru_utime.tv_sec * 1000 + s.ru_utime.tv_usec / 1000));
    PUSH((UNS64)(s.ru_stime.tv_sec * 1000 + s.ru_stime.tv_usec / 1000));
    PUSH((UNS64)(c.ru_utime.tv_sec * 1000 + c.ru_utime.tv_usec / 1000));
    PUSH((UNS64)(c.ru_stime.tv_sec * 1000 + c.ru_stime.tv_usec / 1000));
    FILLNEXT();
}
L_sigaction: SPILL(); { /* signo action --- ior : 0 default, 1 ignore,
                          2 catch, 3 catch WITHOUT SA_RESTART, so a read
                          in progress fails with EINTR instead of being
                          resumed - what an interactive shell needs to
                          notice ^C at its prompt (Iteration 302) */
    int sig = (int)DS1, act = (int)DS0;
    if (sig <= 0 || sig >= NSIG_FLAGS || sig == SIGSEGV || sig == SIGBUS
        || sig == SIGKILL || sig == SIGSTOP) {
        DS1 = (UNS64)(INT64)-EINVAL;
    } else {
        struct sigaction sa;
        memset(&sa, 0, sizeof sa);
        sigemptyset(&sa.sa_mask);
        sa.sa_flags = act == 3 ? 0 : SA_RESTART;
        sa.sa_handler = act == 1 ? SIG_IGN
                      : (act == 2 || act == 3) ? sig_catch : SIG_DFL;
        sig_flag[sig] = 0;
        DS1 = sigaction(sig, &sa, (struct sigaction *)0) ? (UNS64)(INT64)-errno : 0;
    }
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_sigpending: SPILL(); { /* --- signo | 0 : the lowest caught signal, now cleared */
    int i;
    UNS64 r = 0;
    for (i = 1; i < NSIG_FLAGS; i++)
        if (sig_flag[i]) { sig_flag[i] = 0; r = (UNS64)i; break; }
    PUSH(r);
    FILLNEXT();
}
L_access: SPILL(); /* c-addr mode --- ior : access(2); 0 or -errno (Iteration 269) */
    DS1 = access((const char *)(uintptr_t)DS1, (int)DS0) ? (UNS64)(INT64)-errno : 0;
    dsp += CELL_BYTES;
    FILLNEXT();
L_isatty: SPILL(); /* fd --- flag (Iteration 264: is the shell interactive?) */
    DS0 = isatty((int)DS0) ? ~(UNS64)0 : 0;
    FILLNEXT();
L_setpgid: SPILL(); { /* pid pgid --- ior : job control (Iteration 320) */
    DS1 = setpgid((pid_t)DS1, (pid_t)DS0) ? (UNS64)(INT64)-errno : 0;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_tcsetpgrp: SPILL(); { /* fd pgid --- ior : hand the terminal over */
    sigset_t block, old;
    int r;
    /*  A shell that is not the foreground group is stopped by SIGTTOU
     *  when it calls this, which is exactly what it is trying to
     *  prevent, so the signal is blocked across the call.  */
    sigemptyset(&block);
    sigaddset(&block, SIGTTOU);
    sigprocmask(SIG_BLOCK, &block, &old);
    r = tcsetpgrp((int)DS1, (pid_t)DS0);
    sigprocmask(SIG_SETMASK, &old, (sigset_t *)0);
    DS1 = r ? (UNS64)(INT64)-errno : 0;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_tcgetpgrp: SPILL(); /* fd --- pgid | -1 */
    DS0 = (UNS64)(INT64)tcgetpgrp((int)DS0);
    FILLNEXT();
L_waitjob: SPILL(); { /* pid --- status raw : waits, reporting a stop too */
    int status = 0;
    pid_t pid = waitpid((pid_t)DS0, &status, WUNTRACED);
    DS0 = (pid > 0) ? (UNS64)(INT64)pid : (UNS64)(INT64)-1;
    PUSH((UNS64)status);
    FILLNEXT();
}
L_getppid: SPILL(); /* --- pid : for $PPID (Iteration 318) */
    PUSH((UNS64)(INT64)getppid());
    FILLNEXT();
L_envat: SPILL(); { /* i --- c-addr | 0 : environ[i], for `export -p` */
    UNS64 i = DS0, n = 0;
    char **e = environ;
    while (e[n] && n < i) n++;
    DS0 = (e[n] && n == i) ? (UNS64)(uintptr_t)e[n] : 0;
    FILLNEXT();
}
L_getrlimit: SPILL(); { /* resource --- soft hard ior : RLIM_INFINITY
                         comes back as -1 (Iteration 308, for ulimit) */
    struct rlimit rl;
    int r = (int)DS0;
    if (getrlimit(r, &rl)) {
        DS0 = 0; PUSH(0); PUSH((UNS64)(INT64)-errno);
    } else {
        DS0 = (rl.rlim_cur == RLIM_INFINITY) ? (UNS64)(INT64)-1 : (UNS64)rl.rlim_cur;
        PUSH((rl.rlim_max == RLIM_INFINITY) ? (UNS64)(INT64)-1 : (UNS64)rl.rlim_max);
        PUSH(0);
    }
    FILLNEXT();
}
L_setrlimit: SPILL(); { /* soft hard resource --- ior : -1 means infinity */
    struct rlimit rl;
    int r = (int)DS0;
    rl.rlim_cur = ((INT64)DS2 == -1) ? RLIM_INFINITY : (rlim_t)DS2;
    rl.rlim_max = ((INT64)DS1 == -1) ? RLIM_INFINITY : (rlim_t)DS1;
    DS2 = setrlimit(r, &rl) ? (UNS64)(INT64)-errno : 0;
    dsp += 2 * CELL_BYTES;
    FILLNEXT();
}
L_waitnohang: SPILL(); { /* --- pid status : 0 0 when nothing has finished
                          (Iteration 308, for the job notices) */
    int status = 0;
    pid_t pid = waitpid(-1, &status, WNOHANG);
    PUSH((pid > 0) ? (UNS64)(INT64)pid : 0);
    PUSH((pid > 0) ? (UNS64)status : 0);
    FILLNEXT();
}
L_filekind: SPILL(); { /* c-addr --- kind : 0 none, 1 regular, 2 directory,
                        3 anything else. `set -C` has to tell a regular
                        file from a device: O_EXCL alone would refuse
                        `> /dev/null`, which no reference shell does
                        (Iteration 307). */
    struct stat st;
    const char *path = (const char *)(uintptr_t)DS0;
    if (stat(path, &st)) DS0 = 0;
    else if (S_ISREG(st.st_mode)) DS0 = 1;
    else if (S_ISDIR(st.st_mode)) DS0 = 2;
    else DS0 = 3;
    FILLNEXT();
}
L_filemode: SPILL(); { /* c-addr follow? --- mode : the file's st_mode, or
                          0 if it cannot be read. follow? false uses
                          lstat, so `test -h` can see a symbolic link.
                          The shell decodes the bits, which is why this
                          returns the mode rather than a kind
                          (Iteration 378). */
    struct stat st;
    const char *path = (const char *)(uintptr_t)DS1;
    int r = DS0 ? stat(path, &st) : lstat(path, &st);
    DS1 = r ? 0 : (UNS64)st.st_mode;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_localtime: SPILL(); { /* --- sec min hour mday mon year wday : the local
                          time, broken down as C has it - mon 0..11, year
                          less 1900, wday 0 for Sunday. The engine had no
                          wall clock at all; the prompt's time and date
                          escapes, \\t \\T \\@ \\A \\d, are what asked for
                          one (Iteration 417). */
    time_t now = time(NULL);
    struct tm tm;
    localtime_r(&now, &tm);
    PUSH((UNS64)tm.tm_sec);
    PUSH((UNS64)tm.tm_min);
    PUSH((UNS64)tm.tm_hour);
    PUSH((UNS64)tm.tm_mday);
    PUSH((UNS64)tm.tm_mon);
    PUSH((UNS64)tm.tm_year);
    PUSH((UNS64)tm.tm_wday);
    FILLNEXT();
}
L_termraw: SPILL(); { /* fd --- ior : character-at-a-time input for the
                        line editor (Iteration 303). ICANON and ECHO go;
                        ISIG stays, so ^C still raises SIGINT, and OPOST
                        stays, so a newline still writes CR LF. */
    int fd = (int)DS0;
    struct termios tio;          /* not `t`: the dispatch loop owns that */
    if (tcgetattr(fd, &tio)) { DS0 = (UNS64)(INT64)-errno; FILLNEXT(); }
    if (!term_saved) { term_save = tio; term_saved = 1; }
    tio.c_lflag &= ~(ICANON | ECHO | IEXTEN);
    tio.c_iflag &= ~(ICRNL | INLCR);
    tio.c_cc[VMIN] = 1;
    tio.c_cc[VTIME] = 0;
    DS0 = tcsetattr(fd, TCSADRAIN, &tio) ? (UNS64)(INT64)-errno : 0;
    FILLNEXT();
}
L_termrestore: SPILL(); { /* fd --- ior : back to the settings TERM-RAW saw */
    int fd = (int)DS0;
    DS0 = term_saved && tcsetattr(fd, TCSADRAIN, &term_save)
          ? (UNS64)(INT64)-errno : 0;
    FILLNEXT();
}
L_write: SPILL(); { /* c-addr u fd --- n : n < 0 is -errno */
    t_flush();
    DS2 = (UNS64)(INT64)t_write((int)DS0, DS2, DS1);
    dsp += 2 * CELL_BYTES;
    FILLNEXT();
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
L_fork: SPILL(); /* --- pid */
     t_flush();PUSH((UNS64)(INT64)fork());
    FILLNEXT();
L_execve: SPILL(); { t_flush(); /* argv-addr path-addr --- ior */
    char *path = (char*)(uintptr_t)DS0;
    char **argv = (char**)(uintptr_t)DS1;
    execve(path, argv, environ);
    /* only reached if execve itself failed: -errno, as READ and WRITE
     * report (Iteration 265; it was a constant 200, so the shell could
     * not tell "not found" from "found but cannot run").  */
    DS1 = (UNS64)(INT64)-errno;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_waitpid: SPILL(); { /* pid --- status ior */
    int status = 0;
    pid_t r = waitpid((pid_t)(INT64)DS0, &status, 0);
    if (r < 0) {
        DS0 = (UNS64)(INT64)-1;
        PUSH(200);
    } else {
        DS0 = (UNS64)(INT64)status;
        PUSH(0);
    }
    FILLNEXT();
}
L_pipe: SPILL(); { /* --- fd-read fd-write ior */
    int fds[2];
    if (pipe(fds) < 0) {
        PUSH(0); PUSH(0); PUSH(200);
    } else {
        PUSH((UNS64)fds[0]); PUSH((UNS64)fds[1]); PUSH(0);
    }
    FILLNEXT();
}
L_dup2: SPILL(); /* oldfd newfd --- ior */
    DS1 = (UNS64)((dup2((int)DS1, (int)DS0) < 0) ? 200 : 0);
    dsp += CELL_BYTES;
    FILLNEXT();
L_dupfrom: SPILL(); { /* fd floor --- fd' | -1 : the lowest FREE descriptor
                         at or above floor, a copy of fd, closed on exec.
                         The shell saved a redirected descriptor by dup2 onto
                         a fixed slot, 64 + i, which overwrote a script's own
                         descriptor there; dash asks for a free one, and so
                         does the shell now (Iteration 486). */
    int fd = (int)DS1, floor = (int)DS0, r;
#ifdef F_DUPFD_CLOEXEC
    r = fcntl(fd, F_DUPFD_CLOEXEC, floor);
#else
    r = fcntl(fd, F_DUPFD, floor);
    if (r >= 0) fcntl(r, F_SETFD, FD_CLOEXEC);
#endif
    DS1 = (UNS64)(INT64)r;
    dsp += CELL_BYTES;
    FILLNEXT();
}
L_getenv: SPILL(); { /* c-addr --- addr */
    char *v = getenv((char*)(uintptr_t)DS0);
    DS0 = (UNS64)(uintptr_t)v;
    FILLNEXT();
}
L_setenv: SPILL(); /* value-addr name-addr --- ior */
    DS1 = (UNS64)((setenv((char*)(uintptr_t)DS0, (char*)(uintptr_t)DS1, 1) < 0) ? 200 : 0);
    dsp += CELL_BYTES;
    FILLNEXT();
L_sysexit: SPILL(); /* n --- */
     t_flush(); term_restore(); PROFDUMP; _exit((int)DS0);
L_chdir: SPILL(); /* c-addr --- ior */
    DS0 = (UNS64)((chdir((char*)(uintptr_t)DS0) < 0) ? 200 : 0);
    FILLNEXT();
L_getcwd: SPILL(); { /* addr max-len --- len ior */
    char *r = getcwd((char*)(uintptr_t)DS1, (size_t)DS0);
    if (r == 0) {
        DS1 = 0;
        DS0 = 200;
    } else {
        DS1 = (UNS64)strlen(r);
        DS0 = 0;
    }
    FILLNEXT();
}
L_sysargc: SPILL(); /* --- n */
    PUSH((UNS64)(g_argc > 2 ? g_argc - 2 : 0));
    FILLNEXT();
L_sysarg: SPILL(); { /* n --- c-addr */
    long n = (long)(INT64)DS0;
    if (n < 0 || n + 2 >= g_argc) {
        DS0 = 0;
    } else {
        DS0 = (UNS64)(uintptr_t)g_argv[n + 2];
    }
    FILLNEXT();
}
L_getpwhome: SPILL(); { /* c-addr --- addr | 0 */
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
    FILLNEXT();
}
L_getfsize: SPILL(); { /* --- n */
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
    FILLNEXT();
}
L_setfsize: SPILL(); { /* n --- ior */
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
    FILLNEXT();
}
L_getpid: SPILL(); /* --- pid */
    PUSH((UNS64)(INT64)getpid());
    FILLNEXT();
L_unsetenv: SPILL(); /* c-addr --- ior */
    DS0 = (UNS64)((unsetenv((char*)(uintptr_t)DS0) < 0) ? 200 : 0);
    FILLNEXT();

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
L_allocate: SPILL(); /* u --- a-addr ior */
{
    void *p = malloc((size_t)DS0);
    DS0 = (UNS64)(uintptr_t)p;
    PUSH((UNS64)(p == NULL ? 201 : 0));
    FILLNEXT();
}
L_free: SPILL(); /* a-addr --- ior */
    free((void*)(uintptr_t)DS0);
    DS0 = 0;
    FILLNEXT();
L_resize: SPILL(); /* a-addr u --- a-addr' ior */
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
    FILLNEXT();
}
#define EXITNEXT() do { ip = RS; rp += CELL_BYTES; NEXT(); } while (0)
LX_lit: PUSHT(OPND16(ip)); ip += 2; EXITNEXT();
LX_drop: POPT(); EXITNEXT();
LX_dup: PUSHT(tos); EXITNEXT();
LX_swap: t = NOS; NOS = tos; tos = t; EXITNEXT();
LX_rot: t = CELL(dsp + CELL_BYTES); CELL(dsp + CELL_BYTES) = NOS; NOS = tos; tos = t; EXITNEXT();
LX_over: t = NOS; PUSHT(t); EXITNEXT();
LX_cfetch: tos = BYTE(tos); EXITNEXT();
LX_fetch: tos = CELL(tos); EXITNEXT();
LX_cstore: BYTE(tos) = (UNS8)NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; EXITNEXT();
LX_store: CELL(tos) = NOS; tos = CELL(dsp + CELL_BYTES); dsp += 2 * CELL_BYTES; EXITNEXT();
LX_and: tos &= NOS; dsp += CELL_BYTES; EXITNEXT();
LX_or: tos |= NOS; dsp += CELL_BYTES; EXITNEXT();
LX_xor: tos ^= NOS; dsp += CELL_BYTES; EXITNEXT();
LX_fromr: PUSHT(RS); rp += CELL_BYTES; EXITNEXT();
LX_tor: RPUSH(tos); POPT(); EXITNEXT();
LX_rfetch: PUSHT(RS); EXITNEXT();
LX_eq: tos = -(UNS64)(NOS == tos); dsp += CELL_BYTES; EXITNEXT();
LX_ugt: tos = -(UNS64)(NOS < tos); dsp += CELL_BYTES; EXITNEXT();
LX_gt: tos = -(UNS64)((INT64)NOS < (INT64)tos); dsp += CELL_BYTES; EXITNEXT();
LX_plus: tos += NOS; dsp += CELL_BYTES; EXITNEXT();
LX_negate: tos = -tos; EXITNEXT();
LX_lshift: tos = NOS << tos; dsp += CELL_BYTES; EXITNEXT();
LX_rshift: tos = NOS >> tos; dsp += CELL_BYTES; EXITNEXT();

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
#if GUARD
    install_guards(base);
    /*  Below the return stack's guard page. TWO cells of slack, not
     *  one: with TOS caching dsp sits a cell ABOVE the logical top, so
     *  with one the empty stack would put dsp on the guard and the first
     *  read of the second item would trap (PROGRESS.md 206).  */
    g_dsp = g_ip + MEMSIZE - RSTACK_BYTES - g_page - 2 * CELL_BYTES;
#else
    g_dsp = g_ip + MEMSIZE - RSTACK_BYTES - CELL_BYTES;
#endif
    g_rp_limit  = g_ip + MEMSIZE - RSTACK_BYTES;
    g_dsp_limit = g_ip + MEMSIZE - RSTACK_BYTES - DSTACK_BYTES;
    CELL(g_dsp) = g_ip;
    virtual_machine();
    return 0; /* unreachable: virtual_machine() only leaves via BYE/EOF */
}

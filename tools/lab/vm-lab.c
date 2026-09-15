/*
 *  sod16.c - RelF's engine with SOD16 code: one 16-bit token per
 *  operation instead of one host cell.
 *
 *  DERIVED FROM relf.c, DELIBERATELY BY MINIMAL EDIT. The point of this
 *  file is how little of it differs. 64 of the 68 primitives are
 *  byte-for-byte identical to relf.c's, because a primitive's body does
 *  not depend on how code is represented - only on the stacks and
 *  memory, which are unchanged. Just four touch `ip`: exit, lit,
 *  branch, ?branch. Plus NEXT() and the boot sequence.
 *
 *  That is the argument for SOD16 as a change to this project rather
 *  than a rewrite of it, and it should stay true: if this file starts
 *  diverging from relf.c anywhere except the marked places, something
 *  has gone wrong.
 *
 *  WHAT CHANGED
 *
 *    NEXT()     reads a 16-bit token. t < 256 is a primitive index;
 *               t >= 256 is word number t-256, and the target comes
 *               from wordtab[] - one load, no base add, no shift.
 *    L_lit      operand is a 16-bit token, not a cell.
 *    L_branch   offset is in TOKEN units, signed 16-bit. Measured on
 *               the real image, zero branches need more than that.
 *    L_0branch  same.
 *    L_exit     unchanged - the return stack holds ip values either way.
 *
 *  WHAT IS NOT DONE YET
 *
 *    Loading. A token image's bodies are a different size from a cell
 *    image's, so every address in the dictionary moves: link fields,
 *    HERE, and anything a VARIABLE holds that points into the image.
 *    It BOOTS (Iteration 179). Both cell widths run every word that
 *    was compiled into the image: arithmetic, strings, HEX/DECIMAL,
 *    tick, and the whole pre-compiled shell.
 *
 *    It CANNOT COMPILE. `,` and `COMPILE,` write CELLS, so a new
 *    definition lays down cell-threaded code that this engine then
 *    reads as tokens. `: SQ DUP * ;` segfaults. Making the compiler
 *    emit tokens is the next piece, and it is the same work as
 *    GOALS.md's phase 3.
 */
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
typedef uint16_t UNS16;   /* SOD16: a code token */

extern char **environ;

/* Process argv, exposed to Forth via SYS-ARGC/SYS-ARG below - argv[0]
 * and argv[1] (the program name and kernel-image path) are not part
 * of this; SYS-ARG(0) is argv[2], the first argument after the image
 * path, matching a shell's own convention of not exposing its own
 * name via the primitives that expose *its* arguments. */
static int g_argc;
static char **g_argv;

#define FOLDBASE 128

/*  Number of PRIMITIVE lines in kernel.4. gen-tos.py overrides this on
 *  the generated copy, so the value here is only a fallback for reading
 *  vm-lab.c directly. Everything synthetic - LIT32, DOVAR, DODOES,
 *  LIT64, FARCALL, the CV8 literal forms and the folded band - is
 *  numbered RELATIVE to it, and sod16.py derives the same way from the
 *  same count. These were written out as 68..73, correct for exactly as
 *  long as the count stayed 68: adding one primitive put DODOES at 71
 *  and left [71] = &&L_lit64t overwriting it, with no build error and a
 *  return stack overflow at run time.  */
#ifndef NPRIM
#define NPRIM 69
#endif

/*  The escaped band: the OS/libc primitives, contiguous at the end of
 *  kernel.4's PRIMITIVE list. NESC is fixed by that list - sod16.py's
 *  ESC_PRIMS_ALL names the same 32 words - and NDIRECT is whatever is
 *  left below them.  */
#define NESC    32
#define NDIRECT (NPRIM - NESC)
#ifndef ESCAPE
/*  ESCAPE: the 32 OS/libc primitives move behind ESC + a selector,
 *  which renumbers the primitive band. Both the engine and the
 *  translator (--escape) must agree, so this is off until the fault in
 *  BUF-ALLOC is found.  */
#define ESCAPE 1
#endif
#ifndef DISPATCH256
/*  DISPATCH256: no opcode-vs-call test at all. The table gets 256
 *  entries, every one with the top bit set pointing at do_call, so
 *  NEXT is load / increment / indirect jump. Suggested in review:
 *  the CPU should not have to learn whether this is a one- or
 *  two-byte instruction before it can jump. Costs 1 KB more table.  */
#define DISPATCH256 0
#endif
#ifndef VARSLOT
/*  VARSLOT: slot operands (VAR@/VAR!, the locals opcodes) are variable
 *  too. 0xxxxxxx + 1 byte is a 15-bit payload; 1xxxxxx + 2 bytes is
 *  23-bit. Without this a slot is a fixed 16 bits, so variables had to
 *  live in the first 512 KB (64-bit) / 256 KB (32-bit) while VARCALL
 *  let code span 32 MB - an asymmetry that fails silently.  */
#define VARSLOT 1
#endif
#ifndef DOESFAR
/*  DOESFAR: CREATE reserves THREE bytes after the DOVAR opcode and
 *  DOES> writes the three-byte far call, so the parameter field is at
 *  align(body+4). Needed when the call scale is 0, where the two-byte
 *  near form reaches only 16 KB and the cross-compiler's dictionary is
 *  far larger. Without it CREATE reserves two and the field is at
 *  align(body+3), which is what every other CV8 stage uses.  */
#define DOESFAR 0
#endif
#ifndef VARCALL
/*  VARCALL: the call form is variable too. 10xxxxxx takes one more byte
 *  (14-bit payload), 11xxxxxx takes two (22-bit). Costs one extra test
 *  on the call path; buys a far call without spending an opcode.
 *  VARCALL=0 is the fixed 15-bit form.  */
#define VARCALL 1
#endif
#ifndef SIGNTEST
/*  Measured in guest instructions (tools/lab/xarch, qemu): -3.6% on
 *  AArch64, -4.2% on RISC-V 64, +/-0.3% on x86, but +3.0% on ARMv7.  */
#if defined(__arm__) && !defined(__aarch64__)
#define SIGNTEST 0
#else
#define SIGNTEST 1
#endif
#endif
#ifndef SPEC
#define SPEC 0     /* 1: CV8 specialised opcodes 0x60-0x77 (CV8.md 10) */
#endif
#ifndef VMPUSH
#define VMPUSH PUSH
#endif
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
#ifndef MEMSIZE
#define MEMSIZE (16 * 1024 * 1024)
#endif
/*  Room reserved for the return stack. Raised from 2048 in Iteration
 *  90: 2048 bytes is 256 cells, and each level of shell function
 *  recursion nests roughly a dozen Forth calls, so the return stack
 *  overflowed - segfaulting - at around fifteen levels, before
 *  shell.4's own MAX-POS-PARAM-DEPTH guard of 32 could report
 *  "recursion too deep". A limit that pre-empts a higher-level one
 *  turns a diagnosable error into a crash.  */
/*  SOD16: code is 16-bit tokens, and the word table is DERIVED - it is
 *  rebuilt at load by walking the dictionary link chain, holds absolute
 *  addresses because it is rebuilt after relocation, and is never
 *  saved. Nothing about it goes in the image.  */
#define TOK(a)   (*(UNS16 *)(uintptr_t)(a))
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
#define MAXWORDS 65280

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
#if GUARD
#define PUSH(x)  do { dsp -= CELL_BYTES; DS0 = x; } while (0)
#else
#define PUSH(x)  do { dsp -= CELL_BYTES;                              \
                      if (dsp < dsp_limit) stack_fault(0);            \
                      DS0 = x; } while (0)  /* pushes x to data stack  */
#endif
#if GUARD
#define RPUSH(x) do { rp -= CELL_BYTES; RS = x; } while (0)
#else
#define RPUSH(x) do { rp -= CELL_BYTES;                               \
                      if (rp < rp_limit) stack_fault(1);              \
                      RS = x; } while (0)   /* pushes x to return stack*/
#endif

/*
 *  VM memory. +(CELL_BYTES-1) is necessary to be able to allocate
 *  MEMSIZE bytes from a CELL_BYTES-aligned address in order to have
 *  native word access.
 */

#ifndef GUARD
/*  GUARD: catch stack overflow with an unreadable page below each
 *  stack instead of a compare on every push. The checks cost 5-6% of
 *  run time (measured); a guard page costs nothing in the loop and is
 *  exact rather than probabilistic. Needs an MMU, so a target without
 *  one (MSP430) builds with GUARD=0 and keeps the checks.  */
#define GUARD 0   /* 1: guard pages. See PROGRESS.md 206 - one
                    * tests/diff case (tilde) regresses, not yet diagnosed. */
#endif
#if GUARD
#include <sys/mman.h>
#include <signal.h>
#define PAGE 4096
static UNS8 mem[MEMSIZE + CELL_BYTES - 1] __attribute__((aligned(PAGE)));
#else
static UNS8 mem[MEMSIZE + CELL_BYTES - 1];
#endif

/*
 *  1st CELL_BYTES-aligned address in mem array. Base address of the
 *  system.
 */

static UNS8 *base;

/* VM registers and related variables */

#if REG
static UNS64  g_ip, g_rp, g_dsp;
#define VMREGS UNS64 ip = g_ip, rp = g_rp, dsp = g_dsp, t; const UNS64 dsp_limit = g_dsp_limit, rp_limit = g_rp_limit;
#else
static UNS64 ip, rp, dsp, t;
#define g_ip ip
#define g_rp rp
#define g_dsp dsp
#define g_dsp_limit dsp_limit
#define g_rp_limit rp_limit
#define VMREGS
#endif

/*  Floors for the two stacks, both set once in main() and never
 *  changed. Kept as plain variables rather than recomputed from base
 *  at each check so the hot path compares against something already
 *  in a register.  */
#if REG
static UNS64 g_dsp_limit, g_rp_limit;
#else
static UNS64 dsp_limit, rp_limit;
#endif

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
#define CV8_VERSION 1
#define F_VARCALL 0x01   /* calls are 2 or 3 bytes                      */
#define F_VARSLOT 0x02   /* slot operands are 2 or 3 bytes              */
#define F_SPEC    0x04   /* specialised opcodes present (locals header) */
#define F_LIT64   0x08   /* LIT64 may appear                            */
#define F_BYTEHDR 0x10   /* dictionary headers are byte-granular: a 1-3
                            byte link with its tag last, unpadded names.
                            The engine never reads a link in this
                            encoding, so it accepts this unconditionally;
                            the flag exists so that an engine which DID
                            walk links could refuse such an image. */
static const UNS8 IMAGE_MAGIC[8] = { 'C', 'V', '8', '0' + SCALE, CELL_BYTES,
    SPEC ? 'L' : 0, CV8_VERSION,
    (VARCALL ? F_VARCALL : 0) | (VARSLOT ? F_VARSLOT : 0)
        | (SPEC ? F_SPEC : 0) | F_LIT64 | F_BYTEHDR };

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
#if GUARD
/*  One unreadable page below each stack. The data stack's guard sits
 *  below its floor; the return stack's sits between the two stacks, so
 *  a return-stack overflow traps instead of quietly eating the data
 *  stack. Both are inside mem, so nothing else has to move.  */
static UNS64 g_dguard, g_rguard;
static void guard_trap(int sig, siginfo_t *si, void *uc) {
    UNS64 a = (UNS64)(uintptr_t)si->si_addr;
    (void)sig; (void)uc;
    if (a >= g_dguard && a < g_dguard + PAGE)
        write_str(2, "relf: data stack overflow\n");
    else if (a >= g_rguard && a < g_rguard + PAGE)
        write_str(2, "relf: return stack overflow\n");
    else
        write_str(2, "relf: segmentation fault (not a stack guard)\n");
    _exit(1);
}
/*  The regions, top down:
 *      [rfloor, MEMSIZE)        return stack
 *      [rfloor - PAGE, rfloor)  GUARD - return stack overflow
 *      [dfloor, rfloor - PAGE)  data stack
 *      [dfloor - PAGE, dfloor)  GUARD - data stack overflow (and the
 *                               dictionary growing up into the stacks)
 *  The two guard pages come out of the data stack, so the stacks stay
 *  where they were and only the usable data depth shrinks by 8 KB. */
static void install_guards(UNS8 *b) {
    UNS64 dfloor = (UNS64)(uintptr_t)b + MEMSIZE - RSTACK_BYTES - DSTACK_BYTES;
    UNS64 rfloor = (UNS64)(uintptr_t)b + MEMSIZE - RSTACK_BYTES;
    struct sigaction sa;
    mprotect((void *)(uintptr_t)(rfloor - PAGE), PAGE, PROT_NONE);
    mprotect((void *)(uintptr_t)dfloor, PAGE, PROT_NONE);
    g_dguard = dfloor; g_rguard = rfloor - PAGE;
    sa.sa_sigaction = guard_trap;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, (struct sigaction *)0);
    sigaction(SIGBUS, &sa, (struct sigaction *)0);
}
#endif

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

#define MAX_THREADS 4096
#define MAX_TAILS 16
static UNS64 loc_hdr[5];   /* SPEC: lsp, lstk, lmax, lsave, lrestore (offsets) */

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
     *  a feature later does not invalidate older images, and an older
     *  engine refuses a newer image cleanly instead of misreading it. */
    if (magic[6] > IMAGE_MAGIC[6]) {
        write_str(2, "image is a newer CV8 format version than this engine\n");
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
#if SPEC
    /*  The locals header - save-stack variable, buffer, limit, and the
     *  LSAVE/LRESTORE fallbacks - is present only if the image was
     *  built from a dictionary that had locals.4 loaded; a bare kernel
     *  has none. */
    if (full_read(fd, (UNS8*)loc_hdr, 5 * CELL_BYTES) != 5 * CELL_BYTES)
        loc_hdr[0] = loc_hdr[1] = 0;
#endif

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
     *  now that SOD16 is retired from the tree. See attic/.  */
}

/*
 *  Virtual machine itself: computed-goto threaded dispatch. Each
 *  primitive is a labeled block ending in NEXT; primitive tokens are
 *  (index * CELL_BYTES) + 1, matching cross.4's PRIMITIVE numbering
 *  (stride == sizeof(void*) on this host, since dispatch-table entries
 *  are pointer-sized - which is exactly CELL_BYTES on every host this
 *  targets).
 */

#if PROFILE
#include <stdio.h>
#define PROFDUMP dump_prof()
static unsigned long long prof[258], pair[258][258], callc[65536], ipc[1 << 20];
static const char *prof_names[258];
static void dump_prof(void) {
    const char *f = getenv("VMPROF"); if (!f) return;
    int fd = open(f, O_WRONLY|O_CREAT|O_APPEND, 0644); char b[128];
    for (int i = 0; i < 258; i++) for (int j = 0; j < 258; j++) if (pair[i][j]) {
        int n = snprintf(b, sizeof b, "%d %d %llu\n", i, j, pair[i][j]); write(fd, b, n); }
    for (int i = 0; i < (1 << 20); i++) if (ipc[i]) {   /* per-address: patterns.py */
        int n = snprintf(b, sizeof b, "I %d %llu\n", i, ipc[i]); write(fd, b, n); }
    for (int i = 0; i < 65536; i++) if (callc[i]) {
        int n = snprintf(b, sizeof b, "C %d %llu\n", i, callc[i]); write(fd, b, n); }
    close(fd);
}
static int prev_op = 257;
#define PROFC(t) (callc[t]++)
#define PROFIP(a) (ipc[((a) - (UNS64)(uintptr_t)base) & ((1 << 20) - 1)]++)
#define PROF(k) do { pair[prev_op][k]++; prev_op = (k); } while (0)
#else
#define PROF(k)
#define PROFC(t)
#define PROFIP(a)
#define PROFDUMP
#endif

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
static UNS8 t_ibuf[TIOBUF];
static int  t_ipos = 0, t_ilen = 0;
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
#define FBUFN  8
#define FBUFSZ 4096
static struct fbuf { int fd, len, pos; UNS8 b[FBUFSZ]; } t_fb[FBUFN];

NOINLINE_IO static struct fbuf *t_fslot(int fd) {
    int i, free_ = -1;
    for (i = 0; i < FBUFN; i++) {
        if (t_fb[i].fd == fd) return &t_fb[i];
        if (t_fb[i].fd == 0 && free_ < 0) free_ = i;   /* 0 marks unused */
    }
    if (free_ < 0) return 0;                           /* fall back to raw */
    t_fb[free_].fd = fd; t_fb[free_].len = t_fb[free_].pos = 0;
    return &t_fb[free_];
}

NOINLINE_IO static void t_fdrop(int fd) {
    int i;
    for (i = 0; i < FBUFN; i++) if (t_fb[i].fd == fd) {
        int un = t_fb[i].len - t_fb[i].pos;
        if (un > 0) lseek(fd, -(off_t)un, SEEK_CUR);
        t_fb[i].fd = 0; t_fb[i].len = t_fb[i].pos = 0;
    }
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
    if (t_ipos >= t_ilen) {
        t_flush();                     /* prompt before blocking */
        t_ilen = (int)read(0, t_ibuf, TIOBUF);
        t_ipos = 0;
        if (t_ilen <= 0) { t_ilen = 0; return -1; }
    }
    return t_ibuf[t_ipos++];
}

static void virtual_machine(void) {
    VMREGS
    /* CV8: byte stream. b < 0x80 is an opcode; otherwise b and the next
     * byte are a 15-bit scaled offset from the image base. */
    const UNS64 cbase = (UNS64)(uintptr_t)base;
    static const void *const dispatch[] = {
        &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop,
        &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch,
        &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr,
        &&L_tor, &&L_rfetch, &&L_eq, &&L_ugt, &&L_gt, &&L_plus,
        &&L_negate, &&L_lshift, &&L_rshift, &&L_ummult, &&L_umdiv,
        &&L_dplus, &&L_type, &&L_accept, &&L_spfetch, &&L_spstore,
        &&L_rpfetch, &&L_rpstore, &&L_key, &&L_bye, &&L_openfile, &&L_closefile,
        &&L_readline, &&L_writeline, &&L_readfile, &&L_writefile,
        &&L_system, &&L_reposfile, &&L_filepos, &&L_delfile, &&L_filesize,
        &&L_fork, &&L_execve, &&L_waitpid, &&L_pipe, &&L_dup2,
        &&L_getenv, &&L_setenv, &&L_sysexit, &&L_chdir, &&L_getcwd,
        &&L_sysargc, &&L_sysarg, &&L_getpid, &&L_unsetenv,
        &&L_allocate, &&L_free, &&L_resize, &&L_getpwhome,
        &&L_getfsize, &&L_setfsize, &&L_key,
        /*  LIT32 is not one of kernel.4's primitives. It is appended
         *  past the real ones so the table has no hole - `dispatch[255]`
         *  would have read past the end.  */
        [NPRIM] = &&L_lit32, &&L_dovar, &&L_dodoes,
        [NPRIM + 3] = &&L_lit8, &&L_lit8x,
        [0x7D] = &&L_lit64, [0x7E] = &&L_esc,
#if SPEC
        [0x61] = &&L_lit0, &&L_lit1, &&L_litm1, &&L_vf, &&L_vs,
        &&L_lsave, &&L_lrest, &&L_lstore, &&L_lzero,
        &&L_zeq, &&L_sub, &&L_ne, &&L_zlt, &&L_sgt, &&L_2dup, &&L_2drop,
        &&L_charp, &&L_onep, &&L_cellp, &&L_cells, &&L_onem, &&L_invert,
        &&L_count, &&L_aligned, &&L_addi, &&L_addix, &&L_eqi, &&L_eqix,
#endif
#if FOLD
#include "vm-fold-table.h"
#endif
    };
#if ESCAPE
    /*  CV8 renumbers the primitive band: the 36 non-escaped primitives
     *  keep kernel.4's order compacted into 0..35, and the 32 escaped
     *  ones are reached as ESC + index. dispatch[] is in kernel.4
     *  order, so both tables are derived from it here rather than
     *  written out twice.  */
    /*  The escaped primitives are CONTIGUOUS at the end of kernel.4's
     *  list, so the partition is a property of the ORDER and needs no
     *  table: direct opcodes are an identity mapping, and selector t is
     *  simply the primitive at NDIRECT + t.
     *
     *  This used to be a hand-written esc_k[32] listing 32 and 37..67,
     *  because BYE sat below SP@/SP!/RP@/RP! and KEY sat above the file
     *  primitives, leaving the escaped set interleaved. Moving those
     *  five declarations in kernel.4 removed the table and three of the
     *  four loops - and removed the possibility of the table and the
     *  order disagreeing, which nothing would have caught.  */
    const void *cv8_tab[128], *esc_tab[NESC];
    { int i_, n_ = (int)(sizeof dispatch / sizeof dispatch[0]);
      /*  Copy the whole table first: everything ABOVE the primitives -
       *  LIT32, DOVAR, DODOES, the literal forms, the folded band and
       *  the specialised band - keeps its slot and must be carried
       *  over. Leaving that out is what a first attempt did, and every
       *  translated image died with a return stack overflow.  */
      for (i_ = 0; i_ < 128; i_++) cv8_tab[i_] = (i_ < n_) ? dispatch[i_] : &&L_noop;
      /*  Direct primitives are already an identity mapping. The escaped
       *  ones vacate their slots, and selector t is the primitive at
       *  NDIRECT + t - no table, because the order says it.  */
      for (i_ = NDIRECT; i_ < NPRIM; i_++) cv8_tab[i_] = &&L_noop;
      for (i_ = 0; i_ < NESC; i_++) esc_tab[i_] = dispatch[NDIRECT + i_]; }
#define dispatch cv8_tab
#endif
#if SHAREDCALL && DISPATCH256
    /*  Same handlers, but indexed by the whole byte: 0x80-0xFF all land
     *  on do_call, so no test is needed to tell an opcode from a call. */
    const void *dtab256[256];
    { int i_, n_ = (int)(sizeof dispatch / sizeof dispatch[0]);
      for (i_ = 0; i_ < 256; i_++)
          dtab256[i_] = (i_ < n_ && i_ < 128) ? dispatch[i_] : &&do_call; }
#endif

#if SHAREDCALL
/*  Every handler keeps its own opcode dispatch (what the branch predictor
 *  needs), but the call path - decode, RPUSH, limit check - exists once.
 *  GCC otherwise replicates ~50 bytes of it into all ~120 handlers.  */
#if DISPATCH256
#define NEXT() do { \
        PROFIP(ip); t = BYTE(ip); ip += 1; PROF(t); goto *dtab256[t]; \
    } while (0)
#elif SIGNTEST
/*  Load the byte sign-extended: an opcode is then just t >= 0, one
 *  branch-on-sign (bgez / tbz / js) with no constant and no compare.
 *  RISC-V otherwise rematerialises 127 for bltu on every dispatch.  */
#define NEXT() do { \
        PROFIP(ip); t = (UNS64)(INT64)(int8_t)BYTE(ip); \
        if ((INT64)t >= 0) { ip += 1; PROF(t); goto *dispatch[t]; } \
        goto do_call; \
    } while (0)
#else
#define NEXT() do { \
        PROFIP(ip); t = BYTE(ip); \
        if (t < 0x80) { ip += 1; PROF(t); goto *dispatch[t]; } \
        goto do_call; \
    } while (0)
#endif
#else
#define NEXT() do { \
        PROFIP(ip); t = BYTE(ip); \
        if (t < 0x80) { ip += 1; PROF(t); goto *dispatch[t]; } \
        t = ((t & 0x7F) << 8) | BYTE(ip + 1); ip += 2; \
        PROF(256); RPUSH(ip); ip = cbase + (t << SCALE); \
        goto next; \
    } while (0)
#endif

next:
    NEXT();
#if SHAREDCALL
do_call:
#if DISPATCH256
    /*  ip is already past the first byte here.  */
    if (t & 0x40) { t = ((t & 0x3F) << 16) | ((UNS64)BYTE(ip) << 8) | BYTE(ip + 1);
                    ip += 2; }
    else          { t = ((t & 0x3F) << 8) | BYTE(ip); ip += 1; }
#elif VARCALL
    if (t & 0x40) {                       /* 11xxxxxx: 22-bit target */
        t = ((t & 0x3F) << 16) | ((UNS64)BYTE(ip + 1) << 8) | BYTE(ip + 2);
        ip += 3;
    } else {                              /* 10xxxxxx: 14-bit target */
        t = ((t & 0x3F) << 8) | BYTE(ip + 1);
        ip += 2;
    }
#else
    t = ((t & 0x7F) << 8) | BYTE(ip + 1); ip += 2;
#endif
    PROF(256); RPUSH(ip); ip = cbase + (t << SCALE);
    NEXT();
#endif

L_noop:    /* noop    */ NEXT();
L_exit:    /* exit    */ ip = RS; rp += CELL_BYTES; NEXT();
L_lit:     /* lit     */ PUSH(OPND16(ip)); ip += 2; NEXT();
L_lit8:    /* lit8    */ PUSH(BYTE(ip)); ip += 1; NEXT();
L_lit8x:   /* lit8;exit */ PUSH(BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();
L_lit32:   /* lit32   */ { UNS64 v = LD32(ip);
                           if (v & 0x80000000u) v |= ~(UNS64)0xFFFFFFFFu;
                           PUSH(v); ip += 4; } NEXT();
#if SPEC
/*  Specialised opcodes at 0x61 (they were at 0x60 until a 69th
 *  primitive pushed the folded band onto it), each borrowed from
 *  another VM (CV8.md 10).
 *  The slot/variable operand is a 16-bit little-endian value v; the
 *  address is base + (v << SCALE), the same compressed pointer calls use. */
#if VARSLOT
#define SLOT() (t = BYTE(ip), \
        (t & 0x80) ? (t = ((t & 0x7F) << 16) | ((UNS64)BYTE(ip + 1) << 8) \
                         | BYTE(ip + 2), ip += 3, cbase + (t << SCALE)) \
                   : (t = (t << 8) | BYTE(ip + 1), ip += 2, cbase + (t << SCALE)))
#else
#define SLOT() (t = LD16(ip), ip += 2, cbase + (t << SCALE))
#endif
L_lit0:   VMPUSH(0); NEXT();                          /* JVM iconst_0  */
L_lit1:   VMPUSH(1); NEXT();
L_litm1:  VMPUSH(~(UNS64)0); NEXT();
L_vf:     { UNS64 a = SLOT(); VMPUSH(CELL(a)); } NEXT();   /* getstatic */
L_vs:     { UNS64 a = SLOT(); CELL(a) = DS0; dsp += CELL_BYTES; } NEXT();
/*  Locals are shallow-bound VARIABLEs (locals.4). These do LSAVE,
 *  LRESTORE, L! and LZERO in one dispatch, on the SAME Forth-visible save
 *  stack (LSAVE-SP, LSAVE-STACK), and fall back to the Forth word itself
 *  - pushing the START offset exactly as `LIT off` did - whenever the
 *  Forth version would take its ABORT" path. Specialise, and deoptimise
 *  to the general code on the rare case: CPython 3.11's pattern.  */
L_lsave: { UNS64 a = SLOT(), lsp = cbase + loc_hdr[0];
    UNS64 sp = CELL(lsp), stk = CELL(cbase + loc_hdr[1]);
    if ((INT64)sp >= (INT64)loc_hdr[2] || (INT64)sp < 0 || !stk) {
        VMPUSH(a - cbase); RPUSH(ip); ip = cbase + loc_hdr[3]; NEXT(); }
    CELL(stk + sp * CELL_BYTES) = CELL(a); CELL(lsp) = sp + 1; } NEXT();
L_lrest: { UNS64 a = SLOT(), lsp = cbase + loc_hdr[0];
    UNS64 sp = CELL(lsp), stk = CELL(cbase + loc_hdr[1]);
    if ((INT64)sp <= 0 || !stk) {
        VMPUSH(a - cbase); RPUSH(ip); ip = cbase + loc_hdr[4]; NEXT(); }
    CELL(lsp) = --sp; CELL(a) = CELL(stk + sp * CELL_BYTES); } NEXT();
L_lstore: { UNS64 a = SLOT(); CELL(a) = DS0; dsp += CELL_BYTES; } NEXT();
L_lzero:  { UNS64 a = SLOT(); CELL(a) = 0; } NEXT();
/*  The kernel's hottest tiny colon words, as opcodes (Gforth-style
 *  primitive selection). The translator substitutes one only where the
 *  compiled body is exactly the definition implemented here.  */
L_zeq:    DS0 = -(UNS64)(DS0 == 0); NEXT();                     /* 0=  */
L_sub:    DS1 -= DS0; dsp += CELL_BYTES; NEXT();                /* -   */
L_ne:     DS1 = -(UNS64)(DS1 != DS0); dsp += CELL_BYTES; NEXT(); /* <> */
L_zlt:    DS0 = -(UNS64)((INT64)DS0 < 0); NEXT();               /* 0<  */
L_sgt:    DS1 = -(UNS64)((INT64)DS0 < (INT64)DS1); dsp += CELL_BYTES; NEXT();
L_2dup:   { UNS64 a_ = DS1, b_ = DS0; PUSH(a_); PUSH(b_); } NEXT();
L_2drop:  dsp += 2 * CELL_BYTES; NEXT();
L_charp:  DS0 += 1; NEXT();                                     /* CHAR+ */
L_onep:   DS0 += 1; NEXT();                                     /* 1+  */
L_cellp:  DS0 += CELL_BYTES; NEXT();                            /* CELL+ */
L_cells:  DS0 <<= CELL_SHIFT; NEXT();
L_onem:   DS0 -= 1; NEXT();                                     /* 1-  */
L_invert: DS0 = ~DS0; NEXT();
L_count:  { UNS64 a_ = DS0; DS0 = a_ + 1; PUSH(BYTE(a_)); } NEXT();
L_aligned: DS0 = (DS0 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1); NEXT();
/*  Lua 5.4's OP_ADDI / OP_EQI: a signed 8-bit immediate. Lua added
 *  immediate forms for every operator and kept only these.  */
L_addi:   DS0 += (UNS64)(INT64)(int8_t)BYTE(ip); ip += 1; NEXT();
L_addix:  DS0 += (UNS64)(INT64)(int8_t)BYTE(ip); ip = RS; rp += CELL_BYTES; NEXT();
L_eqi:    DS0 = -(UNS64)(DS0 == (UNS64)(INT64)(int8_t)BYTE(ip)); ip += 1; NEXT();
L_eqix:   DS0 = -(UNS64)(DS0 == (UNS64)(INT64)(int8_t)BYTE(ip)); ip = RS; rp += CELL_BYTES; NEXT();
#endif
L_lit64:   /* lit64: a full cell, little-endian. CELL_BYTES bytes.      */
    { UNS64 v = 0; int i_;
      for (i_ = CELL_BYTES - 1; i_ >= 0; i_--) v = (v << 8) | BYTE(ip + i_);
      PUSH(v); ip += CELL_BYTES; } NEXT();
L_esc:     /*  The escaped band: one more byte selects an OS/libc
            *  primitive. Half the primitive band was these, for 3.2% of
            *  static sites and 0.006% of dispatches; behind an escape
            *  they cost a byte each and free 32 opcodes.  */
#if ESCAPE
    t = BYTE(ip); ip += 1; PROF(t); goto *esc_tab[t];
#else
    write_str(2, "CV8: image uses the escaped band, engine built without it\n");
    exit(2);
#endif
L_dovar:   /* DOVAR as a primitive: [DOVAR][pad][PFA] -> push PFA, return */
    /*  The PFA is align(body+3), not align(body+1), so that it is the
     *  SAME address DODOES computes after overwriting the front of the
     *  body with a 2-byte call. With bodies always cell-aligned the two
     *  agreed by accident; the byte-header layout leaves bodies wherever
     *  the name ends, and a DOES> word created at run time then found
     *  its parameter field one cell away from where CREATE had put it.
     *  cv8.4's CREATE8 reserves the two bytes.  */
    PUSH((ip + (DOESFAR ? 3 : 2) + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
    ip = RS; rp += CELL_BYTES; NEXT();
L_dodoes:  /* [DODOES][tail][pad][PFA] -> the tail's R> finds the PFA */
#if VARCALL
    if (BYTE(ip) & 0x40) {
        t = ((BYTE(ip) & 0x3F) << 16) | ((UNS64)BYTE(ip + 1) << 8) | BYTE(ip + 2);
        RPUSH((ip + 3 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
    } else {
        t = ((BYTE(ip) & 0x3F) << 8) | BYTE(ip + 1);
        RPUSH((ip + 2 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
    }
#else
    t = ((BYTE(ip) & 0x7F) << 8) | BYTE(ip + 1);
    RPUSH((ip + 2 + CELL_BYTES - 1) & ~(UNS64)(CELL_BYTES - 1));
#endif
    ip = cbase + (t << SCALE); NEXT();
L_branch:  /* branch  */ ip += (int16_t)LD16(ip); NEXT();
L_0branch: /* 0branch */
    if (DS0) ip += 2; else ip += (int16_t)LD16(ip);
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
     * built on them in kernel.4. That is the reverse of the usual
     * arrangement and it is deliberate: a primitive that moves a WHOLE
     * STRING costs one dispatch where a per-character EMIT costs one
     * per byte, and ACCEPT's editing loop leaves the image. */
    const UNS8 *p = (const UNS8 *)(uintptr_t)DS1;
    UNS64 u = DS0;
    for (UNS64 i = 0; i < u; i++) t_put(p[i]);
    dsp += 2 * CELL_BYTES;
    NEXT();
    }
L_accept: { /* accept  */ /* c-addr n1 --- n2 */
    /* Must match the Forth ACCEPT this replaces character for
     * character, because shell.4 depends on the editing: backspace and
     * DEL erase one character if there is one, CR or LF end the line
     * and are NOT stored, and a character that would overflow the
     * buffer is DROPPED rather than ending the line.
     *
     * EOF exits, as KEY did. Re-reading EOF forever is GOALS.md Bug 3,
     * and moving the read into a new primitive is exactly the kind of
     * change that would quietly reintroduce it. */
    UNS8 *buf = (UNS8 *)(uintptr_t)DS1;
    UNS64 max = DS0, n = 0;
    for (;;) {
        int ch = t_getc();
        if (ch < 0) { t_flush(); exit(0); }
        if (ch == 8 || ch == 127) { if (n) n--; }
        else if (ch == 10 || ch == 13) break;
        else if (n < max) buf[n++] = (UNS8)ch;
    }
    dsp += CELL_BYTES;
    DS0 = n;
    NEXT();
    }
L_key: { /* key     */ /* --- c */
    /* Raw: one character, no line buffering and no editing. It cannot
     * be a colon definition on ACCEPT - ACCEPT returns a finished,
     * edited LINE, so a KEY built on it could not return a keystroke
     * until Enter, which is the property interactive line editing needs
     * it not to have. Appended at the END of the primitive list so
     * every other opcode number is untouched. */
    int ch = t_getc();
    if (ch < 0) { t_flush(); exit(0); }   /* GOALS.md Bug 3 */
    PUSH((UNS64)(UNS8)ch);
    NEXT();
    }
L_bye:     /* bye     */ t_flush(); PROFDUMP; exit(0);
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
L_closefile: {/* fid --- ior */
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
L_system: { t_flush(); /* c-addr u --- ior */
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
L_reposfile: {/* offset fid --- ior */
    t_fdrop((int)DS0);

    DS1 = (UNS64)lseek((int)DS0, (long)DS1, SEEK_SET);
    dsp += CELL_BYTES;
    NEXT();
    }
L_filepos: {/* fid --- u ior */
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
     t_flush();PUSH((UNS64)(INT64)fork());
    NEXT();
L_execve: { t_flush(); /* argv-addr path-addr --- ior */
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
     t_flush();PROFDUMP; _exit((int)DS0);
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
#if FOLD
#define EXITNEXT() do { ip = RS; rp += CELL_BYTES; NEXT(); } while (0)
#include "vm-fold-bodies.h"
#endif

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
    /*  Below the return stack's guard page, not below the return stack.
     *  TWO cells of slack, not one: with TOS caching dsp sits one cell
     *  ABOVE the logical top, so with one cell the empty stack would
     *  put dsp exactly on the guard and any NOS read would trap. */
    g_dsp = g_ip + MEMSIZE - RSTACK_BYTES - PAGE - 2 * CELL_BYTES;
#else
    g_dsp = g_ip + MEMSIZE - RSTACK_BYTES - CELL_BYTES;
#endif
    g_rp_limit  = g_ip + MEMSIZE - RSTACK_BYTES;
    g_dsp_limit = g_ip + MEMSIZE - RSTACK_BYTES - DSTACK_BYTES
#if GUARD
                  + PAGE
#endif
                  ;
    CELL(g_dsp) = g_ip;
    virtual_machine();
    return 0; /* unreachable: virtual_machine() only leaves via BYE/EOF */
}

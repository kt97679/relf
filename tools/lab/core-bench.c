/*  core-bench.c - asm core vs C core, same token stream, same binary.
 *
 *  tools/lab/cv8-core.S showed hand-written asm is no SMALLER than what
 *  GCC emits (2512 B vs 2351 B for the same 63 handlers). This asks
 *  whether it is FASTER.
 *
 *  Both cores run the identical CV8 token program from the identical
 *  entry point, in one process, interleaved. The C core is copied from
 *  tools/lab/vm-lab.c: same NEXT, same TOS caching, same VM registers as
 *  locals, same handler bodies - so this compares the CODE GENERATOR,
 *  not two different interpreter designs.
 *
 *  The program is a counted loop doing arithmetic, a call and a return
 *  per iteration, which is the dispatch mix the shell actually runs
 *  (VM-SURVEY.md: calls ~22%, EXIT ~17%, arithmetic and literals the
 *  rest). It never touches a syscall, so neither core takes a slow path.
 *
 *  usage: core-bench [ROUNDS]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef unsigned long long U;
typedef long long I;
typedef unsigned char U8;

#define CELL(a) (*(U *)(size_t)(a))
#define BYTE(a) (*(U8 *)(size_t)(a))

extern void vm_run(U *regs);
int vm_slow(int op);
static U *g;
static U g_result;

/*  The asm core leaves through vm_slow; opcode 32 is BYE.  */
int vm_slow(int op) {
    if (op == 32) { g_result = CELL(g[2]); return 1; }
    fprintf(stderr, "core-bench: unexpected slow op %d\n", op);
    exit(2);
}

/* ------------------------------------------------------------------ */
/*  C core: the ENC==3 / REG=1 / TOS path of vm-lab.c, verbatim in
 *  structure. Kept in one function so GCC has the same freedom it has
 *  in the real engine.                                                */
static U c_core(U *regs) {
    static const void *const dtab[128] = {
        [0]  = &&c_noop,  [1]  = &&c_exit,  [2]  = &&c_lit,
        [3]  = &&c_branch,[4]  = &&c_qbranch,
        [5]  = &&c_drop,  [6]  = &&c_dup,   [7]  = &&c_swap,
        [8]  = &&c_rot,   [9]  = &&c_over,
        [10] = &&c_cfetch,[11] = &&c_fetch, [12] = &&c_cstore,
        [13] = &&c_store, [14] = &&c_and,   [15] = &&c_or,
        [16] = &&c_xor,   [17] = &&c_fromr, [18] = &&c_tor,
        [19] = &&c_rat,   [20] = &&c_eq,    [21] = &&c_ult,
        [22] = &&c_lt,    [23] = &&c_plus,  [24] = &&c_neg,
        [25] = &&c_lsh,   [26] = &&c_rsh,   [32] = &&c_bye,
        [68] = &&c_lit32, [71] = &&c_lit8,  [72] = &&c_lit8x,
        [0x69 + 8] = &&c_1p, [0x69 + 11] = &&c_1m, [0x69] = &&c_zeq,
        [0x69 + 1] = &&c_sub,
    };
    U ip = regs[0], rp = regs[1], dsp = regs[2], t;
    const U cbase = regs[3];
    U tos = CELL(dsp); dsp += 8;
#define C_NEXT() do { \
        t = (U)(I)(signed char)BYTE(ip); \
        if ((I)t >= 0) { ip += 1; goto *dtab[t]; } \
        t = ((t & 0x7F) << 8) | BYTE(ip + 1); ip += 2; \
        rp -= 8; CELL(rp) = ip; ip = cbase + (t << 3); \
        goto next; } while (0)
#define PUSHT(x) do { U v_ = (x); dsp -= 8; CELL(dsp) = tos; tos = v_; } while (0)
#define NOS CELL(dsp)
next:
    C_NEXT();
c_noop:   C_NEXT();
c_exit:   ip = CELL(rp); rp += 8; C_NEXT();
c_drop:   tos = NOS; dsp += 8; C_NEXT();
c_dup:    PUSHT(tos); C_NEXT();
c_swap:   t = NOS; NOS = tos; tos = t; C_NEXT();
c_over:   t = NOS; PUSHT(t); C_NEXT();
c_rot:    t = CELL(dsp + 8); CELL(dsp + 8) = NOS; NOS = tos; tos = t; C_NEXT();
c_cfetch: tos = BYTE(tos); C_NEXT();
c_fetch:  tos = CELL(tos); C_NEXT();
c_cstore: BYTE(tos) = (U8)NOS; tos = CELL(dsp + 8); dsp += 16; C_NEXT();
c_store:  CELL(tos) = NOS; tos = CELL(dsp + 8); dsp += 16; C_NEXT();
c_and:    tos &= NOS; dsp += 8; C_NEXT();
c_or:     tos |= NOS; dsp += 8; C_NEXT();
c_xor:    tos ^= NOS; dsp += 8; C_NEXT();
c_fromr:  PUSHT(CELL(rp)); rp += 8; C_NEXT();
c_tor:    rp -= 8; CELL(rp) = tos; tos = NOS; dsp += 8; C_NEXT();
c_rat:    PUSHT(CELL(rp)); C_NEXT();
c_eq:     tos = -(U)(NOS == tos); dsp += 8; C_NEXT();
c_ult:    tos = -(U)(NOS < tos); dsp += 8; C_NEXT();
c_lt:     tos = -(U)((I)NOS < (I)tos); dsp += 8; C_NEXT();
c_plus:   tos += NOS; dsp += 8; C_NEXT();
c_neg:    tos = -tos; C_NEXT();
c_lsh:    tos = NOS << tos; dsp += 8; C_NEXT();
c_rsh:    tos = NOS >> tos; dsp += 8; C_NEXT();
c_lit:    { U v = (U)BYTE(ip) | ((U)BYTE(ip + 1) << 8);
            PUSHT(v); ip += 2; } C_NEXT();
c_lit8:   PUSHT(BYTE(ip)); ip += 1; C_NEXT();
c_lit8x:  PUSHT(BYTE(ip)); ip = CELL(rp); rp += 8; C_NEXT();
c_lit32:  { U v = (U)BYTE(ip) | ((U)BYTE(ip+1) << 8) | ((U)BYTE(ip+2) << 16)
                | ((U)BYTE(ip+3) << 24);
            if (v & 0x80000000u) v |= ~(U)0xFFFFFFFFu;
            PUSHT(v); ip += 4; } C_NEXT();
c_branch: ip += (short)((U)BYTE(ip) | ((U)BYTE(ip + 1) << 8)); C_NEXT();
c_qbranch: t = tos; tos = NOS; dsp += 8;
           if (t) ip += 2;
           else ip += (short)((U)BYTE(ip) | ((U)BYTE(ip + 1) << 8));
           C_NEXT();
c_1p:     tos += 1; C_NEXT();
c_1m:     tos -= 1; C_NEXT();
c_zeq:    tos = -(U)(tos == 0); C_NEXT();
c_sub:    tos = NOS - tos; dsp += 8; C_NEXT();
c_bye:    dsp -= 8; CELL(dsp) = tos; return CELL(dsp);
}

/* ------------------------------------------------------------------ */
/*  The token program, built by hand so both cores see identical bytes.
 *
 *      : INNER  ( n -- n' )  1+ 1+ 1- ;            a call + EXIT
 *      : LOOPB  0 BEGIN INNER 1+ DUP LIMIT = UNTIL ;
 *
 *  Per iteration: 1 call, 1 EXIT, 5 arithmetic opcodes, 1 literal,
 *  1 DUP, 1 = and 1 ?BRANCH - close to the measured shell mix.        */
#define OP_EXIT 1
#define OP_DUP 6
#define OP_EQ 20
#define OP_QBR 4
#define OP_LIT32 68
#define OP_LIT8 71
#define OP_BYE 32
#define OP_1P (0x69 + 8)
#define OP_1M (0x69 + 11)

static U8 *mem;
static U build(U limit) {          /* returns the entry ip */
    U8 *p;
    /* INNER at base+64 (8-aligned, so a 2-byte call can reach it) */
    p = mem + 64;
    *p++ = OP_1P; *p++ = OP_1P; *p++ = OP_1M; *p++ = OP_EXIT;
    /* LOOPB at base+128 */
    U8 *start = mem + 128; p = start;
    *p++ = OP_LIT8; *p++ = 0;                       /* 0 */
    U8 *loop = p;
    U call = 0x8000 | (64 >> 3);                    /* call INNER */
    *p++ = (U8)(call >> 8); *p++ = (U8)(call & 0xFF);
    *p++ = OP_1P;
    *p++ = OP_DUP;
    *p++ = OP_LIT32;
    *p++ = (U8)limit; *p++ = (U8)(limit >> 8);
    *p++ = (U8)(limit >> 16); *p++ = (U8)(limit >> 24);
    *p++ = OP_EQ;
    *p++ = OP_QBR;
    { short off = (short)(loop - p);   /* offset is from the operand itself */
      *p++ = (U8)off; *p++ = (U8)((unsigned short)off >> 8); }
    *p++ = OP_BYE;
    return (U)(size_t)start;
}

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char **argv) {
    int rounds = argc > 1 ? atoi(argv[1]) : 7;
    U limit = argc > 2 ? strtoull(argv[2], 0, 0) : 3000000;
    mem = aligned_alloc(4096, 1 << 20); memset(mem, 0, 1 << 20);
    U entry = build(limit);
    double bc = 1e18, ba = 1e18;
    U rc = 0, ra = 0;
    for (int r = 0; r <= rounds; r++) {
        U regs[16] = {0};
        double t0;
        /* C core */
        regs[0] = entry; regs[1] = (U)(size_t)(mem + (1 << 20));
        regs[2] = (U)(size_t)(mem + (1 << 20) - 65536); regs[3] = (U)(size_t)mem;
        CELL(regs[2]) = 0;
        t0 = now(); rc = c_core(regs); t0 = now() - t0;
        if (r && t0 < bc) bc = t0;
        /* asm core */
        regs[0] = entry; regs[1] = (U)(size_t)(mem + (1 << 20));
        regs[2] = (U)(size_t)(mem + (1 << 20) - 65536); regs[3] = (U)(size_t)mem;
        CELL(regs[2]) = 0;
        g = regs;
        t0 = now(); vm_run(regs); t0 = now() - t0;
        ra = g_result;
        if (r && t0 < ba) ba = t0;
    }
    printf("result: C=%llu asm=%llu %s\n", rc, ra, rc == ra ? "(agree)" : "MISMATCH");
    printf("min ms: C %.2f   asm %.2f   asm/C %.3f\n", bc, ba, ba / bc);
    return rc != ra;
}

/* tools/pack-bench.c - what does UNPACKING cost?
 *
 * Iteration 157. ENCODING-COMPARISON.md sized five encodings and could
 * not choose between them, because every number there was bytes and
 * the open objection is about time: Iteration 134 argued that a tag
 * plus a packed field adds a second data-dependent test to the two
 * hottest paths in the interpreter. This measures that directly.
 *
 * Four inner loops, doing IDENTICAL work on the SAME operation stream,
 * differing only in how the next operation is fetched and decoded:
 *
 *   CELL    one host cell per operation, low bit selects primitive vs
 *           call, the offset IS the instruction. RelF today.
 *   PACK5   SOD32 authentic: bit0=1 selects a pack of six 5-bit
 *           subinstructions, bit31 is a return flag. 32 opcodes.
 *   PACK4   the tagged-nibble proposal: 4-bit tag, seven 4-bit fields
 *           in a 32-bit cell. 16 opcodes.
 *   PACK8   the tagged-byte proposal: a tag byte then three opcode
 *           bytes. 256 opcodes, so no escape for cold primitives.
 *
 * THE OPERATION MIX IS DYNAMIC, NOT STATIC, and that is the point.
 * tools/dispatch-bench.c uses the static mix (35% calls) because it
 * was answering a size-driven question. Dispatch cost depends on what
 * EXECUTES, and the two differ sharply - measured over three workloads
 * with an instrumented engine in Iteration 155:
 *
 *              static   dynamic
 *   calls       46.3%     24.9%
 *   EXIT         3.6%     17.3%
 *   LIT         12.4%     11.5%
 *   R>           2.1%      9.1%
 *   @           30.6%      7.4%
 *   DROP         5.4%      0.16%
 *
 * Using the static mix here would overstate calls by nearly 2x, and
 * calls are the operation packing cannot help with - they end a pack.
 * That would flatter the packed schemes.
 *
 * WHAT THIS DOES NOT MEASURE
 *
 * Cache effects. A denser encoding touches less memory, and on a real
 * workload that is a large part of why density matters at all. This
 * benchmark's streams are sized to run hot, so it isolates decode cost
 * and deliberately ignores the advantage density would bring. Read it
 * as "what does unpacking cost when memory is free", i.e. the
 * pessimistic case for the packed schemes.
 *
 * Build: cc -O2 -o pack-bench tools/pack-bench.c
 *        cc -O2 -m32 -o pack-bench32 tools/pack-bench.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define NOPS  (1 << 22)
#define NPRIM 32

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;
}

/* op kinds */
enum { K_PRIM, K_CALL, K_EXIT, K_LIT };

static unsigned char kind[NOPS];
static unsigned char op[NOPS];        /* primitive index when K_PRIM */
static unsigned int  nops;

/* Dynamic mix, Iteration 155, rounded: 25% call, 17% exit, 12% lit,
 * 46% primitive. The primitive index is drawn from a skewed
 * distribution so the hot handful dominate, as they do in the real
 * profile (R> 9.1%, + 8.6%, @ 7.4% of all operations). */
static void gen(void) {
    unsigned int s = 12345;
    for (unsigned int i = 0; i < NOPS; i++) {
        s = s * 1103515245 + 12345;
        unsigned int r = (s >> 16) % 100;
        if      (r < 25) kind[i] = K_CALL;
        else if (r < 42) kind[i] = K_EXIT;
        else if (r < 54) kind[i] = K_LIT;
        else {
            kind[i] = K_PRIM;
            s = s * 1103515245 + 12345;
            unsigned int t = (s >> 16) % 1000;
            /* skewed: ~60% of primitives land in the top 8 */
            op[i] = (t < 600) ? (t % 8) : (unsigned char)(t % NPRIM);
        }
    }
    nops = NOPS;
}

/* ---- encoded streams ---------------------------------------------- */
static uintptr_t cellcode[NOPS + 16];
static uint32_t  p5[NOPS + 16], p4[NOPS + 16], p8[NOPS + 16];
static unsigned  n_cell, n_p5, n_p4, n_p8;

static void encode(void) {
    unsigned i, n;
    /* CELL: one per op; LIT takes two (operand cell) */
    for (i = 0, n = 0; i < nops; i++) {
        if (kind[i] == K_CALL)      cellcode[n++] = 8;          /* even = call */
        else if (kind[i] == K_EXIT) cellcode[n++] = (NPRIM - 1) * 4 + 1;
        else if (kind[i] == K_LIT) { cellcode[n++] = 1; cellcode[n++] = 7; }
        else                        cellcode[n++] = op[i] * 4 + 1;
    }
    n_cell = n;

    /* PACK5: 6 x 5-bit, bit0 tag, bit31 return. LIT is a subinstruction
     * whose operand is the following cell. Call/exit close the pack. */
    unsigned used = 0; uint32_t acc = 1;
    for (i = 0, n = 0; i < nops; i++) {
        if (kind[i] == K_CALL) {
            if (used) { p5[n++] = acc; acc = 1; used = 0; }
            p5[n++] = 0;                                  /* call cell */
        } else if (kind[i] == K_EXIT) {
            p5[n++] = acc | 0x80000000u; acc = 1; used = 0;
        } else if (kind[i] == K_LIT) {
            if (used == 6) { p5[n++] = acc; acc = 1; used = 0; }
            acc |= (uint32_t)31 << (1 + 5 * used); used++;
            p5[n++] = acc; acc = 1; used = 0;             /* operand cell follows */
            p5[n++] = 12345;
        } else {
            if (used == 6) { p5[n++] = acc; acc = 1; used = 0; }
            acc |= (uint32_t)(op[i] % 31) << (1 + 5 * used); used++;
        }
    }
    if (used) p5[n++] = acc;
    n_p5 = n;

    /* PACK4: 4-bit tag then 7 x 4-bit. 15 opcodes; cold ones escape. */
    used = 0; acc = 7;
    for (i = 0, n = 0; i < nops; i++) {
        if (kind[i] == K_CALL) {
            if (used) { p4[n++] = acc; acc = 7; used = 0; }
            p4[n++] = 0;
        } else if (kind[i] == K_EXIT) {
            p4[n++] = acc | 8; acc = 7; used = 0;
        } else if (kind[i] == K_LIT) {
            if (used) { p4[n++] = acc; acc = 7; used = 0; }
            p4[n++] = 3; p4[n++] = 12345;
        } else {
            unsigned o = op[i];
            if (o >= 15) { if (used) { p4[n++] = acc; acc = 7; used = 0; } p4[n++] = 11; }
            else {
                if (used == 7) { p4[n++] = acc; acc = 7; used = 0; }
                acc |= (uint32_t)(o + 1) << (4 + 4 * used); used++;
            }
        }
    }
    if (used) p4[n++] = acc;
    n_p4 = n;

    /* PACK8: tag byte then 3 opcode bytes. All primitives fit. */
    used = 0; acc = 3;
    for (i = 0, n = 0; i < nops; i++) {
        if (kind[i] == K_CALL) {
            if (used) { p8[n++] = acc; acc = 3; used = 0; }
            p8[n++] = 0;
        } else if (kind[i] == K_EXIT) {
            p8[n++] = acc | 4; acc = 3; used = 0;
        } else if (kind[i] == K_LIT) {
            if (used == 3) { p8[n++] = acc; acc = 3; used = 0; }
            acc |= (uint32_t)200 << (8 + 8 * used); used++;
            p8[n++] = acc; acc = 3; used = 0;
            p8[n++] = 12345;
        } else {
            if (used == 3) { p8[n++] = acc; acc = 3; used = 0; }
            acc |= (uint32_t)(op[i] + 1) << (8 + 8 * used); used++;
        }
    }
    if (used) p8[n++] = acc;
    n_p8 = n;
}

/* ---- the four loops ------------------------------------------------ */
static uintptr_t stack[256];
static int sp;
static uintptr_t sink;

#define WORK(x) do { stack[sp & 255] = (x); sp++; sink += stack[(sp - 1) & 255]; } while (0)

static double run_cell(void) {
    double t0 = now();
    for (unsigned i = 0; i < n_cell; i++) {
        uintptr_t t = cellcode[i];
        if (t & 1) { unsigned o = (unsigned)(t >> 2); if (o == 1) { i++; WORK(cellcode[i]); } else WORK(o); }
        else WORK(t);
    }
    return now() - t0;
}
static double run_p5(void) {
    double t0 = now();
    for (unsigned i = 0; i < n_p5; i++) {
        uint32_t c = p5[i];
        if (!(c & 1)) { WORK(c); continue; }
        uint32_t r = c >> 1;
        for (int f = 0; f < 6; f++) {
            unsigned o = r & 31; r >>= 5;
            if (!o) break;
            if (o == 31) { i++; WORK(p5[i]); } else WORK(o);
        }
        if (c & 0x80000000u) WORK(0);
    }
    return now() - t0;
}
static double run_p4(void) {
    double t0 = now();
    for (unsigned i = 0; i < n_p4; i++) {
        uint32_t c = p4[i];
        if ((c & 3) != 3) { WORK(c); continue; }
        if ((c & 15) == 3) { i++; WORK(p4[i]); continue; }
        uint32_t r = c >> 4;
        for (int f = 0; f < 7; f++) {
            unsigned o = r & 15; r >>= 4;
            if (!o) break;
            WORK(o);
        }
        if (c & 8) WORK(0);
    }
    return now() - t0;
}
static double run_p8(void) {
    double t0 = now();
    for (unsigned i = 0; i < n_p8; i++) {
        uint32_t c = p8[i];
        if ((c & 3) != 3) { WORK(c); continue; }
        uint32_t r = c >> 8;
        for (int f = 0; f < 3; f++) {
            unsigned o = r & 255; r >>= 8;
            if (!o) break;
            if (o == 200) { i++; WORK(p8[i]); } else WORK(o);
        }
        if (c & 4) WORK(0);
    }
    return now() - t0;
}

int main(void) {
    gen(); encode();
    printf("ops %u   cells: cell %u  pack5 %u  pack4 %u  pack8 %u\n",
           nops, n_cell, n_p5, n_p4, n_p8);
    printf("bytes(32-bit cell): cell %u  pack5 %u  pack4 %u  pack8 %u\n",
           n_cell * 4, n_p5 * 4, n_p4 * 4, n_p8 * 4);
    double bc = 1e30, b5 = 1e30, b4 = 1e30, b8 = 1e30, t;
    /* Interleaved rounds, min of each: the run-to-run drift on a shared
     * machine is larger than the effects being measured, and taking the
     * minimum of interleaved rounds is the standard defence. */
    for (int rep = 0; rep < 9; rep++) {
        t = run_cell(); if (t < bc) bc = t;
        t = run_p5();   if (t < b5) b5 = t;
        t = run_p4();   if (t < b4) b4 = t;
        t = run_p8();   if (t < b8) b8 = t;
    }
    printf("min ms   cell %.1f   pack5 %.1f   pack4 %.1f   pack8 %.1f\n", bc, b5, b4, b8);
    printf("vs cell  pack5 %.3f  pack4 %.3f  pack8 %.3f\n", b5 / bc, b4 / bc, b8 / bc);
    printf("(sink %llu)\n", (unsigned long long)sink);
    return 0;
}

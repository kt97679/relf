/* tools/varint-bench.c - what does a UTF-8-style variable-length token
 * cost, against a fixed-width one?
 *
 * Iteration 158. TOKEN-THREADING.md's call encoding is a fixed 2-byte
 * form: a 4-value prefix plus an index byte, reaching 1,024 targets.
 * That is already under water - the image has 1,060 dictionary entries,
 * and variables count because a variable reference compiles as a call
 * (measured, Iteration 156). Widening it by allocating more prefixes
 * costs 256 targets per first-byte value spent, and first-byte values
 * are the scarce resource.
 *
 * A continuation-bit encoding removes the ceiling entirely:
 *
 *     0xxxxxxx                 opcode 0..127, one byte
 *     1xxxxxxx 0yyyyyyy        14-bit token
 *     1xxxxxxx 1yyyyyyy 0zzz.. 21-bit, and so on without limit
 *
 * That matters for a system meant to grow to bash compatibility and
 * busybox-style applets, where the definition count is not known in
 * advance and runtime-defined words need indices too.
 *
 * The cost is a data-dependent loop on the multi-byte path where the
 * fixed form has a single shift-and-or. This measures it.
 *
 * FOUR LOOPS, identical work, same operation stream:
 *
 *   CELL     one host cell per operation. RelF today.
 *   FIXED1   one-byte opcode, or 2-byte fixed extended call.
 *   VARINT   one-byte opcode, or continuation-bit token, unbounded.
 *   VARINT2  as VARINT but with the two-byte case peeled out of the
 *            loop, since that is overwhelmingly the common width.
 *
 * MEASURED AT SEVERAL STREAM SIZES, and this is not optional. The
 * first version of this comparison quoted a single figure taken at a
 * 32MB stream and reported byte threading as FASTER than cell
 * threading. It is not: at that size the cell stream's 4.9x larger
 * footprint dominates, and the result was a memory-traffic effect
 * being read as a decode result. At L1-resident sizes the same
 * comparison shows byte threading ~6% slower. A dispatch benchmark
 * that does not vary the working set is measuring the cache.
 *
 * Build: cc -O2 -o varint-bench tools/varint-bench.c
 */
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#ifndef FORCEW
#define FORCEW 0   /* 0 = natural mix; 2,3,4 = force every cold call to that byte width */
#endif
#ifndef NWORDS
#define NWORDS 20000   /* distinct call targets; the table scales with this */
#endif
#ifndef NOPS
#define NOPS (1 << 14)
#endif
#ifndef REPS
#define REPS 64
#endif

#define NPRIM 64

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;
}

enum { K_PRIM, K_CALL, K_EXIT, K_LIT };
static unsigned char kind[NOPS];
static unsigned int  arg[NOPS];

/* Dynamic mix (Iteration 155): 25% call, 17% exit, 12% lit, 46% prim.
 * Call targets are Zipf-ish: top 32 are 45% of sites, so most calls
 * land in the one-byte band and only the tail goes wide. */
static void gen(void) {
    unsigned s = 12345;
    for (unsigned i = 0; i < NOPS; i++) {
        s = s * 1103515245 + 12345;
        unsigned r = (s >> 16) % 100;
        s = s * 1103515245 + 12345;
        unsigned t = (s >> 16) % 1000;
        if (r < 25) {
            kind[i] = K_CALL;
            /* 45% into the hot 32; the rest spread over 20,000 words,
             * which is the bash+busybox scale this is sized for */
            if (FORCEW == 0) arg[i] = (t < 450) ? (t % 32) : 32 + (t * 37 + i) % NWORDS;
            else if (FORCEW == 1) arg[i] = t % 32;
            else if (FORCEW == 2) arg[i] = 128 + (t * 37 + i) % (16384 - 128);
            else if (FORCEW == 3) arg[i] = 16384 + (t * 37 + i) % (2097152 - 16384);
            else                  arg[i] = 2097152 + (t * 37 + i) % 1000000;
        } else if (r < 42) kind[i] = K_EXIT;
        else if (r < 54) { kind[i] = K_LIT; arg[i] = t & 0x7f; }
        else { kind[i] = K_PRIM; arg[i] = (t < 600) ? (t % 8) : (t % NPRIM); }
    }
}

static uintptr_t cellcode[NOPS * 2];
static unsigned char fx[NOPS * 4], vi[NOPS * 4], f3[NOPS * 4];
static unsigned short u16[NOPS * 2];
static unsigned n_cell, n_fx, n_vi, n_f3, n_u16;

static unsigned put_varint(unsigned char *b, unsigned n, unsigned v) {
    /* high bit set on all but the last byte */
    unsigned char tmp[5]; int k = 0;
    do { tmp[k++] = v & 0x7f; v >>= 7; } while (v);
    while (k--) b[n++] = tmp[k] | (k ? 0x80 : 0);
    return n;
}

static void encode(void) {
    unsigned i, n;
    for (i = 0, n = 0; i < NOPS; i++) {
        if (kind[i] == K_CALL)      cellcode[n++] = 8;
        else if (kind[i] == K_EXIT) cellcode[n++] = 5;
        else if (kind[i] == K_LIT) { cellcode[n++] = 1; cellcode[n++] = arg[i]; }
        else                        cellcode[n++] = arg[i] * 4 + 1;
    }
    n_cell = n;
    /* FIXED1: 0x00-0x3F prim, 0x40-0x5F hot call, 0x60-0x6F lit,
     * 0x7E exit, 0x80.. two-byte extended call (10 bits) */
    for (i = 0, n = 0; i < NOPS; i++) {
        if (kind[i] == K_CALL) {
            if (arg[i] < 32) fx[n++] = 0x40 + arg[i];
            else { unsigned v = arg[i] & 1023; fx[n++] = 0x80 | (v >> 8); fx[n++] = v & 255; }
        } else if (kind[i] == K_EXIT) fx[n++] = 0x7E;
        else if (kind[i] == K_LIT) { fx[n++] = 0x7D; fx[n++] = arg[i]; }
        else fx[n++] = arg[i] & 0x3F;
    }
    n_fx = n;
    /* VARINT: same one-byte band; calls beyond it are continuation-coded */
    for (i = 0, n = 0; i < NOPS; i++) {
        if (kind[i] == K_CALL) {
            if (arg[i] < 32) vi[n++] = 0x40 + arg[i];
            else n = put_varint(vi, n, arg[i]);
        } else if (kind[i] == K_EXIT) vi[n++] = 0x7E;
        else if (kind[i] == K_LIT) { vi[n++] = 0x7D; vi[n++] = arg[i]; }
        else vi[n++] = arg[i] & 0x3F;
    }
    n_vi = n;
    /* FIXED3: one-byte band, else 0x80 + three index bytes (24 bits) */
    for (i = 0, n = 0; i < NOPS; i++) {
        if (kind[i] == K_CALL) {
            if (arg[i] < 32) f3[n++] = 0x40 + arg[i];
            else { unsigned v = arg[i]; f3[n++] = 0x80 | (v >> 16); f3[n++] = (v >> 8) & 255; f3[n++] = v & 255; }
        } else if (kind[i] == K_EXIT) f3[n++] = 0x7E;
        else if (kind[i] == K_LIT) { f3[n++] = 0x7D; f3[n++] = arg[i]; }
        else f3[n++] = arg[i] & 0x3F;
    }
    n_f3 = n;
    /* U16: every operation is one 16-bit token. 0..255 primitive and
     * inline forms, 256.. is a word number. Operands follow as tokens. */
    for (i = 0, n = 0; i < NOPS; i++) {
        if (kind[i] == K_CALL)      u16[n++] = 256 + (arg[i] & 0x7fff);
        else if (kind[i] == K_EXIT) u16[n++] = 5;
        else if (kind[i] == K_LIT) { u16[n++] = 1; u16[n++] = arg[i]; }
        else                        u16[n++] = 8 + (arg[i] & 63);
    }
    n_u16 = n;
}

static uintptr_t stack[256]; static int sp; static uintptr_t sink;
static uintptr_t wordtab[1<<22];
#define WORK(x) do { stack[sp & 255] = (x); sp++; sink += stack[(sp-1) & 255]; } while (0)

static double run_cell(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_cell; i++) {
            uintptr_t t = cellcode[i];
            if (t & 1) { unsigned o = (unsigned)(t >> 2); if (t == 1) { i++; WORK(cellcode[i]); } else WORK(o); }
            else WORK(t);
        }
    return now() - t0;
}
static double run_fixed(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_fx; i++) {
            unsigned b = fx[i];
            if (b < 0x80) { if (b == 0x7D) { i++; WORK(fx[i]); } else WORK(b); }
            else { unsigned v = ((b & 0x7F) << 8) | fx[++i]; WORK(wordtab[v & ((1<<22)-1)] + v); }
        }
    return now() - t0;
}
static double run_varint(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_vi; i++) {
            unsigned b = vi[i];
            if (b < 0x80) { if (b == 0x7D) { i++; WORK(vi[i]); } else WORK(b); }
            else {
                unsigned v = b & 0x7F;
                do { b = vi[++i]; v = (v << 7) | (b & 0x7F); } while (b & 0x80);
                WORK(wordtab[v & ((1<<22)-1)] + v);
            }
        }
    return now() - t0;
}
static double run_varint2(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_vi; i++) {
            unsigned b = vi[i];
            if (b < 0x80) { if (b == 0x7D) { i++; WORK(vi[i]); } else WORK(b); }
            else {
                unsigned c = vi[++i];
                unsigned v = ((b & 0x7F) << 7) | (c & 0x7F);
                if (c & 0x80) { do { c = vi[++i]; v = (v << 7) | (c & 0x7F); } while (c & 0x80); }
                WORK(wordtab[v & ((1<<22)-1)] + v);
            }
        }
    return now() - t0;
}

static double run_fixed3(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_f3; i++) {
            unsigned b = f3[i];
            if (b < 0x80) { if (b == 0x7D) { i++; WORK(f3[i]); } else WORK(b); }
            else { unsigned v = ((b & 0x7F) << 16) | (f3[i+1] << 8) | f3[i+2]; i += 2;
                   WORK(wordtab[v & ((1<<22)-1)] + v); }
        }
    return now() - t0;
}

static double run_u16(void) {
    double t0 = now();
    for (int r = 0; r < REPS; r++)
        for (unsigned i = 0; i < n_u16; i++) {
            unsigned v = u16[i];
            if (v < 256) { if (v == 1) { i++; WORK(u16[i]); } else WORK(v); }
            else WORK(wordtab[v & ((1<<22)-1)]);
        }
    return now() - t0;
}

int main(void) {
    gen(); encode();
    for (unsigned i = 0; i < (1<<22); i++) wordtab[i] = i * 3;
    double bc = 1e30, bf = 1e30, bv = 1e30, bv2 = 1e30, b3 = 1e30, bu = 1e30, t;
    for (int rep = 0; rep < 7; rep++) {
        t = run_cell();    if (t < bc)  bc = t;
        t = run_fixed();   if (t < bf)  bf = t;
        t = run_varint();  if (t < bv)  bv = t;
        t = run_varint2(); if (t < bv2) bv2 = t;
        t = run_fixed3();  if (t < b3)  b3 = t;
        t = run_u16();     if (t < bu)  bu = t;
    }
    printf("words %d  ops %d  bytes: cell %u  fixed %u  varint %u   (cell/varint %.2fx)\n",
           NWORDS, NOPS, n_cell * (unsigned)sizeof(uintptr_t), n_fx, n_vi,
           (double)(n_cell * sizeof(uintptr_t)) / n_vi);
    printf("  cell %.1f  fixed %.1f  varint %.1f  varint-peeled %.1f ms\n", bc, bf, bv, bv2);
    printf("  vs cell:  fixed %.3f  varint %.3f  peeled %.3f\n", bf / bc, bv / bc, bv2 / bc);
    printf("  fixed2 %.1f  fixed3 %.1f ms   fixed3/fixed2 %.3f   varint/fixed2 %.3f\n", bf, b3, b3/bf, bv/bf);
    printf("  u16 %.1f ms  u16/cell %.3f  u16/fixed2 %.3f\n", bu, bu/bc, bu/bf);
    printf("  bytes: cell %u  u16 %u  fixed2 %u  fixed3 %u  varint %u\n", (unsigned)(n_cell*sizeof(uintptr_t)), n_u16*2, n_fx, n_f3, n_vi);
    return 0;
}

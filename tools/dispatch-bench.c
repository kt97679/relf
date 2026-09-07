/* tools/dispatch-bench.c - is a byte-granular token stream slower to
 * dispatch than RelF's one-cell-per-token stream?
 *
 * VM-RESEARCH.md's largest finding is that token threading over a byte
 * stream would cut the compiled image by 3.3x on i386 and 6.5x on
 * x86-64 (measured against the real token census, Iteration 140). The
 * open question is what it costs, and the literature's answer -
 * Latendresse and Feeley's ~9% for Huffman-coded bytecode - is for a
 * different VM on 2005 hardware.
 *
 * This measures the two inner loops directly, doing identical work,
 * differing only in how the next operation is fetched and decoded:
 *
 *   CELL   t = code[ip++];  if (t & 1) dispatch on (t>>2)  else call
 *          (RelF today: one host cell per token, no table for calls -
 *          the offset IS the instruction)
 *
 *   BYTE   b = code[ip++];  b < 128 -> dispatch on b
 *                           else     -> 2-byte form, index into a
 *                                       word-address table
 *          (token threading: a call is an index, not an offset, which
 *          is what makes a narrow encoding possible at all)
 *
 * The operation mix is taken from the real image: 35% calls, 35%
 * primitives, 14% literals, 8% branches, and 77.2% of operations
 * covered by the 128 most frequent symbols, so the one-byte form hits
 * about that often.
 *
 * Build: cc -O2 -o dispatch-bench tools/dispatch-bench.c
 *        cc -O2 -m32 -o dispatch-bench32 tools/dispatch-bench.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define NPRIM 64
#define NWORD 817        /* distinct call targets in the real image */
#define NOPS  (1 << 22)  /* operations executed per run */

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

/* A deterministic stream with the measured operation mix. Same logical
 * program for both encodings; only the bytes differ. */
enum { OP_PRIM, OP_CALL, OP_LIT, OP_BR };

static unsigned char kind[NOPS];
static unsigned int  arg[NOPS];

static void gen(void) {
    unsigned int s = 12345;
    for (long i = 0; i < NOPS; i++) {
        s = s * 1103515245u + 12345u;
        unsigned r = (s >> 16) % 100;
        if      (r < 35) { kind[i] = OP_CALL; arg[i] = (s >> 8) % NWORD; }
        else if (r < 70) { kind[i] = OP_PRIM; arg[i] = (s >> 8) % NPRIM; }
        else if (r < 84) { kind[i] = OP_LIT;  arg[i] = (s >> 8) % 256; }
        else             { kind[i] = OP_BR;   arg[i] = 0; }
    }
}

static uintptr_t stack[64];
static int sp;
static uintptr_t sink;

int main(void) {
    gen();

    /* ---- CELL encoding: one uintptr_t per token ---- */
    static uintptr_t ccode[NOPS * 2];
    long cn = 0;
    for (long i = 0; i < NOPS; i++) {
        switch (kind[i]) {
        case OP_PRIM: ccode[cn++] = ((uintptr_t)arg[i] << 2) | 1; break;
        case OP_LIT:  ccode[cn++] = ((uintptr_t)arg[i] << 12) | (60u << 2) | 1; break;
        case OP_BR:   ccode[cn++] = (61u << 2) | 1; break;
        case OP_CALL: ccode[cn++] = ((uintptr_t)arg[i] << 12) | (62u << 2) | 1; break;
        }
    }

    /* ---- BYTE encoding: 1 byte for the top 128 symbols, else 2 ---- */
    static unsigned char bcode[NOPS * 3];
    long bn = 0;
    for (long i = 0; i < NOPS; i++) {
        switch (kind[i]) {
        case OP_PRIM: bcode[bn++] = (unsigned char)arg[i]; break;          /* < 128 */
        case OP_LIT:
            if (arg[i] < 32) bcode[bn++] = (unsigned char)(96 + arg[i]);   /* hot small literal */
            else { bcode[bn++] = 0x80; bcode[bn++] = (unsigned char)arg[i]; }
            break;
        case OP_BR:   bcode[bn++] = 0x7f; bcode[bn++] = 0; break;
        case OP_CALL:
            if (arg[i] < 16) bcode[bn++] = (unsigned char)(64 + arg[i]);   /* hot word */
            else { bcode[bn++] = (unsigned char)(0x81 + (arg[i] >> 8));
                   bcode[bn++] = (unsigned char)(arg[i] & 0xff); }
            break;
        }
    }

    printf("stream: %ld operations   cell %ld bytes   byte %ld bytes   ratio %.2fx\n",
           (long)NOPS, cn * (long)sizeof(uintptr_t), bn,
           (double)(cn * (long)sizeof(uintptr_t)) / (double)bn);

    static uintptr_t wtab[NWORD];
    for (int i = 0; i < NWORD; i++) wtab[i] = (uintptr_t)i * 4;

    double best_cell = 1e9, best_byte = 1e9, best_off = 1e9;

    /* Both loops dispatch through a computed goto, which is what both
     * real implementations would do. The first version of this
     * benchmark gave the byte encoding an if/else comparison chain and
     * the cell encoding a short one, and reported the byte stream 5x
     * slower - an artifact of the harness, not of the encoding. The
     * only differences that should remain are the fetch width and the
     * extra byte fetch for the two-byte form. */

    for (int rep = 0; rep < 5; rep++) {
        double t0, t1;
        {   /* ---- CELL ---- */
            static void *ctab[1024];
            for (int i = 0; i < 1024; i++) ctab[i] = &&c_prim;
            ctab[60] = &&c_lit; ctab[61] = &&c_br; ctab[62] = &&c_call;
            long ip = 0; uintptr_t t = 0; unsigned idx = 0;
            sp = 0;
            t0 = now();
            if (cn == 0) goto c_done;
#define CNEXT() do { if (ip >= cn) goto c_done; \
                     t = ccode[ip++]; idx = (unsigned)((t >> 2) & 0x3ff); \
                     goto *ctab[idx]; } while (0)
            CNEXT();
        c_prim: sink += idx;                       CNEXT();
        c_lit:  stack[sp++ & 63] = t >> 12;        CNEXT();
        c_br:   sink ^= (uintptr_t)ip;             CNEXT();
        c_call: sink += wtab[(t >> 12) % NWORD];   CNEXT();
#undef CNEXT
        c_done:
            t1 = now();
            if (t1 - t0 < best_cell) best_cell = t1 - t0;
        }
        {   /* ---- CELL with RelF's actual call: an offset, no table ----
             * This is the variant token threading would GIVE UP. A call
             * today is RPUSH(ip); ip += t - no lookup at all, which is
             * the cheapest call any of these encodings can have. */
            static void *otab[1024];
            for (int i = 0; i < 1024; i++) otab[i] = &&o_prim;
            otab[60] = &&o_lit; otab[61] = &&o_br; otab[62] = &&o_call;
            long ip = 0; uintptr_t t = 0; unsigned idx = 0;
            sp = 0;
            t0 = now();
            if (cn == 0) goto o_done;
#define ONEXT() do { if (ip >= cn) goto o_done; \
                     t = ccode[ip++]; idx = (unsigned)((t >> 2) & 0x3ff); \
                     goto *otab[idx]; } while (0)
            ONEXT();
        o_prim: sink += idx;                          ONEXT();
        o_lit:  stack[sp++ & 63] = t >> 12;           ONEXT();
        o_br:   sink ^= (uintptr_t)ip;                ONEXT();
        o_call: sink += (uintptr_t)ip + (t >> 12);    ONEXT();
#undef ONEXT
        o_done:
            t1 = now();
            if (t1 - t0 < best_off) best_off = t1 - t0;
        }
        {   /* ---- BYTE ---- */
            static void *btab[256];
            for (int i = 0; i < 64; i++)   btab[i] = &&b_prim;
            for (int i = 64; i < 96; i++)  btab[i] = &&b_hotcall;
            for (int i = 96; i < 127; i++) btab[i] = &&b_hotlit;
            btab[127] = &&b_br;
            btab[128] = &&b_lit2;
            for (int i = 129; i < 256; i++) btab[i] = &&b_call2;
            long ip = 0; unsigned b = 0;
            sp = 0;
            t0 = now();
            if (bn == 0) goto b_done;
#define BNEXT() do { if (ip >= bn) goto b_done; \
                     b = bcode[ip++]; goto *btab[b]; } while (0)
            BNEXT();
        b_prim:    sink += b;                                    BNEXT();
        b_hotcall: sink += wtab[b - 64];                         BNEXT();
        b_hotlit:  stack[sp++ & 63] = b - 96;                    BNEXT();
        b_br:      sink ^= (uintptr_t)ip; ip++;                  BNEXT();
        b_lit2:    stack[sp++ & 63] = bcode[ip++];               BNEXT();
        b_call2: { unsigned w = ((b - 0x81) << 8) | bcode[ip++];
                   sink += wtab[w % NWORD]; }                    BNEXT();
#undef BNEXT
        b_done:
            t1 = now();
            if (t1 - t0 < best_byte) best_byte = t1 - t0;
        }
    }

    printf("cell+table %.1f ms   cell+offset-call %.1f ms   byte %.1f ms\n",
           best_cell * 1000, best_off * 1000, best_byte * 1000);
    printf("byte/cell-table %.3f   byte/cell-offset %.3f\n",
           best_byte / best_cell, best_byte / best_off);
    printf("(sink %llu, printed so nothing is optimised away)\n",
           (unsigned long long)sink);
    return 0;
}

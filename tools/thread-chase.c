/*
 *  tools/thread-chase.c - driver for thread-chase.S.
 *
 *  Builds a cell-threaded and a token-threaded structure that visit the
 *  SAME pseudo-random sequence of slots, so the two differ only in how
 *  a call finds its target. Reports the ratio, which is the quantity
 *  tests/bench showed drifting and SOD16.md says to quote.
 *
 *  Both a C and an asm version of each chase are timed. If the asm
 *  ratio matches the C ratio, the cost is in the mechanism and no
 *  amount of compiler work will remove it.
 *
 *  cc -O2 -o thread-chase tools/thread-chase.c tools/thread-chase.S
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void *cell_chase(void *ip, long n);
void *tok_chase(void *ip, long n, void **wordtab);

/*  The same two loops in C, to separate "the mechanism costs this" from
 *  "the compiler did something unfortunate".  */
static void *cell_chase_c(void *ip, long n) {
    unsigned char *p = ip;
    while (n--) p += 8 + *(long *)p;
    return p;
}
static void *tok_chase_c(void *ip, long n, void **wordtab) {
    unsigned char *p = ip;
    while (n--) p = wordtab[*(unsigned short *)p];
    return p;
}

/*  GCC assumes pointer arithmetic on a valid pointer stays non-null, so
 *  a `if (!p)` liveness check is dead code and the whole cell loop was
 *  deleted - it timed 0.0ms and produced a ratio of 979779. The token
 *  loop survived only because it loads through wordtab, which the
 *  compiler cannot assume non-null. A volatile sink is the fix: the
 *  result has to be observably stored.  */
static void * volatile sink;

static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    long slots = argc > 1 ? atol(argv[1]) : 4096;
    long iters = argc > 2 ? atol(argv[2]) : 50000000;
    long reps  = argc > 3 ? atol(argv[3]) : 5;

    /*  One permutation, followed by both structures, so the sequence of
     *  slot visits - and therefore the cache behaviour - is identical.  */
    long *next = malloc(slots * sizeof *next);
    for (long i = 0; i < slots; i++) next[i] = i;
    unsigned s = 12345;
    for (long i = slots - 1; i > 0; i--) {         /* Fisher-Yates */
        s = s * 1103515245u + 12345u;
        long j = (s >> 8) % (i + 1);
        long t = next[i]; next[i] = next[j]; next[j] = t;
    }
    /*  next[i] = the slot visited after slot i, as a cycle.  */
    long *order = next, *succ = malloc(slots * sizeof *succ);
    for (long i = 0; i < slots; i++) succ[order[i]] = order[(i + 1) % slots];

    long  *cells = aligned_alloc(64, slots * 8);
    unsigned short *toks = aligned_alloc(64, slots * 2 + 64);
    void **wordtab = aligned_alloc(64, slots * sizeof *wordtab);
    if (!cells || !toks || !wordtab) { puts("oom"); return 1; }

    for (long i = 0; i < slots; i++) {
        /*  cell: the offset from this cell to the next one, less the
         *  CELL_BYTES the engine has already added.  */
        cells[i] = (long)((char *)&cells[succ[i]] - (char *)&cells[i]) - 8;
        toks[i] = (unsigned short)succ[i];
        wordtab[i] = &toks[i];
    }
    if (slots > 65535) { puts("slots must fit a 16-bit token"); return 1; }

    double bc = 1e30, bt = 1e30, bcc = 1e30, btc = 1e30;
    for (long r = 0; r < reps; r++) {
        double t0 = now(); void *a = cell_chase(&cells[0], iters);
        double t1 = now(); void *b = tok_chase(&toks[0], iters, wordtab);
        double t2 = now(); void *c = cell_chase_c(&cells[0], iters);
        double t3 = now(); void *d = tok_chase_c(&toks[0], iters, wordtab);
        double t4 = now();
        sink = a; sink = b; sink = c; sink = d;     /* keep them live */
        if (t1 - t0 < bc)  bc  = t1 - t0;
        if (t2 - t1 < bt)  bt  = t2 - t1;
        if (t3 - t2 < bcc) bcc = t3 - t2;
        if (t4 - t3 < btc) btc = t4 - t3;
    }

    printf("slots %ld (%ld KB of cells, %ld KB of tokens + %ld KB table)\n",
           slots, slots * 8 / 1024, slots * 2 / 1024, slots * 8 / 1024);
    printf("iterations %ld, best of %ld\n\n", iters, reps);
    printf("%-14s %10s %10s %8s\n", "", "cell", "token", "ratio");
    printf("%-14s %9.1fms %9.1fms %8.3f\n", "asm",
           bc * 1e3, bt * 1e3, bt / bc);
    printf("%-14s %9.1fms %9.1fms %8.3f\n", "C",
           bcc * 1e3, btc * 1e3, btc / bcc);
    printf("\nns per step: asm cell %.2f  token %.2f\n",
           bc * 1e9 / iters, bt * 1e9 / iters);
    return 0;
}

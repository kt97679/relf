/* tools/sod16-engine.c - SOD16: the dispatch core for uniform 16-bit
 * tokens.
 *
 * Named for SOD32, whose encoding this replaces rather than extends:
 * SOD32 packed six 5-bit subinstructions into a 32-bit cell and paid
 * shift/mask/counter work per operation; SOD16 spends a whole 16-bit
 * token per operation and pays none. Measured, that trade is worth
 * taking - the packed form costs 21-68% in dispatch (Iteration 157)
 * to buy density that a plain 16-bit token gets more of anyway.
 *
 * running REAL translated word bodies from tools/sod16.py.
 *
 * Iterations 162-163, branch token16.
 *
 * This is the engine's decode loop and its table rebuild, not a whole
 * engine. It loads a .tk file, rebuilds the word table the way a real
 * load would, and executes tokens. Primitives are stubs that touch the
 * data stack so the dispatch cannot be optimised away, but do not
 * implement Forth semantics - the question here is what the DECODE
 * costs on real instruction mixes, and a stubbed primitive answers it
 * exactly as well as a real one while keeping the prototype small.
 *
 * WHAT IS BEING DEMONSTRATED
 *
 *   1. The encoding round-trips (proved in token16.py) and loads.
 *   2. The table is DERIVED: word N is the Nth record in chain order,
 *      so nothing about it is stored in the image. Here that is the
 *      Nth W record; in the real engine it is the Nth entry walking
 *      the dictionary link chain. Same numbering, same rebuild, and
 *      the image carries none of it.
 *   3. The table holds ABSOLUTE addresses, because it is rebuilt after
 *      load. Dispatch is one load with no base add and no shift.
 *   4. Decode is one 16-bit read, one compare against 256, one branch.
 *
 * WHAT IS NOT
 *
 *   Real primitive semantics, so this cannot run the shell. Compiling
 *   new definitions, since the Forth compiler still emits cells. Both
 *   are the next problems, and both are larger than this file.
 *
 * Build: cc -O2 -o sod16-engine tools/sod16-engine.c
 * Run:   ./sod16-engine /tmp/shell.tk [reps]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define MAXW   4096
#define MAXTOK (1 << 20)

static uint16_t code[MAXTOK];
static unsigned n_code;

/* The derived table. Rebuilt at load; never stored. */
static uint16_t *wordtab[MAXW];      /* absolute pointers */
static unsigned  wordlen[MAXW];
static char      wordname[MAXW][32];
static unsigned  n_words;

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;
}

static int load(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return -1; }
    char line[1 << 16];
    unsigned wn = 0, nt = 0;
    while (fgets(line, sizeof line, f)) {
        if (line[0] == 'W') {
            char nm[32];
            if (sscanf(line, "W %u %u %31s", &wn, &nt, nm) != 3) continue;
            if (wn >= MAXW) { fprintf(stderr, "word %u exceeds MAXW\n", wn); return -1; }
            /* Absolute pointer into the loaded code, fixed up here -
             * exactly what a real rebuild does after the image lands
             * at whatever base it landed at. */
            wordtab[wn] = &code[n_code];
            wordlen[wn] = nt;
            snprintf(wordname[wn], sizeof wordname[wn], "%s", nm);
            if (wn + 1 > n_words) n_words = wn + 1;
        } else if (line[0] == 'T') {
            char *p = line + 1;
            for (;;) {
                while (*p == ' ') p++;
                if (*p == '\n' || *p == 0) break;
                long v = strtol(p, &p, 10);
                if (n_code >= MAXTOK) { fprintf(stderr, "code overflow\n"); return -1; }
                code[n_code++] = (uint16_t)v;
            }
        }
    }
    fclose(f);
    return 0;
}

/* ---- execution ---------------------------------------------------- */
static uintptr_t ds[4096];
static int dsp;
static uint16_t *rs[4096];
static int rsp;
static uintptr_t sink;
static unsigned long executed;

/* Stubbed primitives. Each touches the stack so the loop is real work,
 * but none implements Forth. See the header. */
#define WORK(x) do { ds[dsp & 4095] = (x); dsp++; sink += ds[(dsp - 1) & 4095]; } while (0)

/* Token 0..255 is a primitive index; 256.. is word number token-256.
 * A handful of indices carry operands and must consume them, because
 * operands are positional - the same lesson that cost two bugs in the
 * translator. These indices come from kernel.4's PRIMITIVE order. */
static int TOK_LIT, TOK_BR, TOK_QBR, TOK_EXIT;
static int TOK_LIT32 = 255, TOK_STR = 254;

static void run(unsigned wn, unsigned long budget) {
    uint16_t *ip = wordtab[wn];
    if (!ip) return;
    rsp = 0;
    unsigned long steps = 0;
    for (;;) {
        if (++steps > budget) return;
        unsigned v = *ip++;
        executed++;
        if (v >= 256) {
            unsigned w = v - 256;
            if (w >= n_words || !wordtab[w]) { WORK(w); continue; }  /* unresolved */
            if (rsp >= 4000) return;
            rs[rsp++] = ip;
            ip = wordtab[w];                    /* one load, no base add */
            continue;
        }
        if (v == (unsigned)TOK_LIT)   { WORK(*ip++); continue; }
        if (v == (unsigned)TOK_LIT32) { WORK(ip[0] | (ip[1] << 16)); ip += 2; continue; }
        if (v == (unsigned)TOK_BR)    { int16_t o = (int16_t)*ip++; ip += o; continue; }
        if (v == (unsigned)TOK_QBR)   { int16_t o = (int16_t)*ip++; if (!(sink & 7)) ip += o; continue; }
        if (v == (unsigned)TOK_STR)   { unsigned n = *ip++; ip += (n + 2) / 2; WORK(n); continue; }
        if (v == (unsigned)TOK_EXIT) {
            if (rsp == 0) return;
            ip = rs[--rsp];
            continue;
        }
        WORK(v);
    }
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s file.tk [reps]\n", argv[0]); return 2; }
    /* Primitive indices, read from kernel.4 so this cannot drift from
     * the translator's view of the opcode numbering. */
    FILE *k = fopen("kernel.4", "r");
    if (k) {
        char line[512]; int i = 0;
        while (fgets(line, sizeof line, k)) {
            if (strncmp(line, "PRIMITIVE ", 10)) continue;
            char nm[64]; sscanf(line + 10, "%63s", nm);
            if (!strcmp(nm, "LIT")) TOK_LIT = i;
            else if (!strcmp(nm, "BRANCH")) TOK_BR = i;
            else if (!strcmp(nm, "?BRANCH")) TOK_QBR = i;
            else if (!strcmp(nm, "EXIT")) TOK_EXIT = i;
            i++;
        }
        fclose(k);
    }
    if (load(argv[1])) return 1;
    unsigned long reps = (argc > 2) ? strtoul(argv[2], 0, 10) : 200;

    printf("loaded %u words, %u tokens (%u bytes of code)\n",
           n_words, n_code, n_code * 2);
    printf("table: %u entries x %zu B = %zu B, OUTSIDE the image\n",
           n_words, sizeof(void *), n_words * sizeof(void *));
    printf("opcodes: LIT %d  BRANCH %d  ?BRANCH %d  EXIT %d\n",
           TOK_LIT, TOK_BR, TOK_QBR, TOK_EXIT);

    /* Execute every word for a bounded number of steps. Words are not
     * being run for their meaning - primitives are stubs - so a step
     * budget keeps a loop in one word from dominating. */
    double best = 1e30;
    for (int r = 0; r < 5; r++) {
        executed = 0; dsp = 0; sink = 0;
        double t0 = now();
        for (unsigned long q = 0; q < reps; q++)
            for (unsigned w = 0; w < n_words; w++)
                if (wordtab[w]) run(w, 2000);
        double t = now() - t0;
        if (t < best) best = t;
    }
    printf("executed %lu operations in %.1f ms  -> %.1f Mops/s\n",
           executed, best, executed / best / 1000.0);
    printf("(sink %llu)\n", (unsigned long long)sink);
    return 0;
}

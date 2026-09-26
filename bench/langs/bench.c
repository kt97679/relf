/* bench.c - the programs of bench.4, in C (bench/langs/run.py) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static long fib(long n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static long sieve(void) { enum { N = 5000000 }; static char f[N]; memset(f, 1, N); long c = 0;
  for (long i = 2; i < N; i++) if (f[i]) { c++; for (long j = i * i; j < N; j += i) f[j] = 0; } return c; }
static long bubble(void) { enum { NB = 3000 }; static long a[NB]; long seed = 74755;
  for (int i = 0; i < NB; i++) { seed = (seed * 1103515245 + 12345) & 2147483647; a[i] = seed % 1000000; }
  for (int i = 1; i < NB; i++) for (int j = 0; j < NB - i; j++) if (a[j] > a[j + 1]) { long t = a[j]; a[j] = a[j + 1]; a[j + 1] = t; }
  long s = 0; for (int i = 0; i < NB; i++) s += a[i] * (i + 1); return s; }
static long matrix(void) { enum { NM = 150 }; static long A[NM][NM], B[NM][NM]; long s = 0;
  for (int r = 0; r < NM; r++) for (int c = 0; c < NM; c++) { A[r][c] = r + c; B[r][c] = c - r; }
  for (int r = 0; r < NM; r++) for (int c = 0; c < NM; c++) { long d = 0; for (int k = 0; k < NM; k++) d += A[r][k] * B[k][c]; s += d; }
  return s; }
static long fannkuch(void) { enum { n = 9 }; int p1[n], p[n], cnt[n], r = n, maxf = 0, pc = 0; long cs = 0;
  for (int i = 0; i < n; i++) p1[i] = i;
  for (;;) { while (r != 1) { cnt[r - 1] = r; r--; }
    memcpy(p, p1, sizeof p); int f = 0, k;
    while ((k = p[0])) { for (int lo = 0, hi = k; lo < hi; lo++, hi--) { int t = p[lo]; p[lo] = p[hi]; p[hi] = t; } f++; }
    if (f > maxf) maxf = f; cs += (pc & 1) ? -f : f;
    for (;;) { if (r == n) return cs * 1000 + maxf;
      int p0 = p1[0]; for (int i = 0; i < r; i++) p1[i] = p1[i + 1]; p1[r] = p0;
      if (--cnt[r] > 0) break; r++; }
    pc++; } }
static long collatz(void) { long t = 0; for (long i = 1; i < 100000; i++) { long n = i, s = 0;
  while (n > 1) { n = (n & 1) ? n * 3 + 1 : n >> 1; s++; } t += s; } return t; }
int main(int argc, char **argv) { const char *w = argv[1]; long r = 0;
  if (!strcmp(w, "fib")) r = fib(32);
  if (!strcmp(w, "loop")) { volatile long s = 0; for (long i = 0; i < 30000000; i++) s += i; r = s; }
  if (!strcmp(w, "sieve")) r = sieve();   if (!strcmp(w, "bubble")) r = bubble();
  if (!strcmp(w, "matrix")) r = matrix(); if (!strcmp(w, "fannkuch")) r = fannkuch();
  if (!strcmp(w, "collatz")) r = collatz();
  printf("%ld\n", r); return 0; }

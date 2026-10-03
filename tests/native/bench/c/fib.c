/* fib.c - fib.4 in C: recursive Fibonacci (tools/native-bench.py) */
#include <stdio.h>
static long fib(long n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
int main(void) { printf("%ld \n", fib(32)); return 0; }

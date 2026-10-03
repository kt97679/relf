/* sieve.c - sieve.4 in C: the classic byte sieve, 8190 flags, 3000 times
 * (tools/native-bench.py) */
#include <stdio.h>
#include <string.h>
#define SIZE 8190
static char flags[SIZE];
static int sieve(void) {
    int count = 0;
    memset(flags, 1, SIZE);
    for (int i = 0; i < SIZE; i++)
        if (flags[i]) {
            int prime = i + i + 3;
            for (int k = i + prime; k < SIZE; k += prime) flags[k] = 0;
            count++;
        }
    return count;
}
int main(void) { int n = 0; for (int r = 0; r < 3000; r++) n = sieve(); printf("%d \n", n); return 0; }

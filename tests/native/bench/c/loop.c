/* loop.c - loop.4 in C: 200 million iterations summing the index. The
 * empty asm keeps the sum a real loop: gcc would otherwise replace it by
 * the closed form, which is no measure of a loop (tools/native-bench.py) */
#include <stdio.h>
int main(void) {
    long s = 0;
    for (long i = 0; i < 200000000; i++) { s += i; __asm__ volatile("" : "+r"(s)); }
    printf("%ld \n", s); return 0;
}

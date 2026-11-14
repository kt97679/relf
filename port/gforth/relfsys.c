/* port/gforth/relfsys.c - SYSCALL and CSTRLEN for relfsh on gforth 0.7.3.
 *
 * Built as a shared library (port/gforth/build.sh: cc -shared -fPIC) and
 * called through gforth's call-c, which runs a C function that takes its
 * arguments from gforth's data stack, gforth_SP - the convention gforth's
 * own C interface (libcc) compiles its wrappers to. libcc itself is not
 * used: an image saved after a libcc call keeps the function's address
 * from the process that saved it, and crashes; sys.fs opens this library
 * at boot instead (open-lib, lib-sym).
 *
 *   SYSCALL ( block num --- r )   Linux system call num, its six arguments
 *                                 the cells at block, r its result or
 *                                 -errno; num -3 gives the initial environ
 *                                 (sys.fs answers -1 and -2, argc and argv).
 * gforth's own output is buffered in C's stdout; relf's engines flush
 * theirs before every system call, so this does too. */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>

typedef long Cell;
extern Cell *gforth_SP;          /* the engine's, exported (libcc.h's HAS_BACKLINK) */
extern char **environ;

void relf_syscall(void) {
    Cell *sp = gforth_SP;        /* sp[0] num, sp[1] block */
    Cell n = sp[0], *b = (Cell *)sp[1], r;
    if (n == -3) r = (Cell)environ;
    else {
        fflush(stdout);
        r = syscall(n, b[0], b[1], b[2], b[3], b[4], b[5]);
        if (r == -1) r = -errno;
    }
    sp[1] = r;
    gforth_SP = sp + 1;
}

void relf_calloc(void) {         /* ALLOCATE's: zeroed, as relf's engines' calloc */
    Cell *sp = gforth_SP;
    sp[0] = (Cell)calloc(1, (size_t)sp[0]);
}

void relf_strlen(void) {         /* CSTRLEN ( c-addr --- u ) */
    Cell *sp = gforth_SP;
    sp[0] = (Cell)strlen((const char *)sp[0]);
}

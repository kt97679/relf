/* rsstrace FILE CMD... - run CMD with FILE on stdin, stopped at its exit (ptrace's exit event), and
   print what is resident then, from /proc/PID/smaps_rollup - the page tables walked, so exact - as
   Rss, Anonymous and private-file KB, and VmHWM. The programs measured free nothing, so what is
   resident at exit is their peak. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
static long field(const char *path, const char *key) {
    FILE *f = fopen(path, "r"); char l[256]; long v = -1;
    if (!f) return -1;
    while (fgets(l, sizeof l, f)) if (!strncmp(l, key, strlen(key))) { v = atol(l + strlen(key)); break; }
    fclose(f); return v;
}
int main(int argc, char **argv) {
    pid_t p = fork();
    if (p == 0) {
        int in = open(argv[1], O_RDONLY), out = open("/dev/null", O_WRONLY);
        dup2(in, 0); dup2(out, 1); dup2(out, 2);
        ptrace(PTRACE_TRACEME, 0, 0, 0);
        execv(argv[2], argv + 2); _exit(127);
    }
    int st; waitpid(p, &st, 0);                                   /* stopped at the exec */
    ptrace(PTRACE_SETOPTIONS, p, 0, PTRACE_O_TRACEEXIT);
    ptrace(PTRACE_CONT, p, 0, 0);
    for (;;) {
        waitpid(p, &st, 0);
        if (WIFEXITED(st) || WIFSIGNALED(st)) { puts("no exit event"); return 1; }
        if (st >> 8 == (SIGTRAP | (PTRACE_EVENT_EXIT << 8))) {
            char a[64], b[64]; sprintf(a, "/proc/%d/smaps_rollup", p); sprintf(b, "/proc/%d/status", p);
            printf("%ld %ld %ld\n", field(a, "Rss:"), field(a, "Anonymous:"), field(b, "VmHWM:"));
            ptrace(PTRACE_CONT, p, 0, 0); waitpid(p, &st, 0); return 0;
        }
        int sig = WIFSTOPPED(st) ? WSTOPSIG(st) : 0;
        ptrace(PTRACE_CONT, p, 0, sig == SIGTRAP ? 0 : sig);
    }
}

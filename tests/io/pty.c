/*
 *  tests/io/pty.c - run a command on a pseudo-terminal.
 *
 *      pty KEYS DELAY-MS program args...
 *
 *  The command gets a new terminal as its stdin, stdout and stderr, in
 *  its own session. Everything on this program's stdin is typed first;
 *  DELAY-MS milliseconds later KEYS are typed, with no newline - which a
 *  terminal in its usual line mode never delivers. The command's output
 *  is copied to stdout until it exits, followed by one line saying
 *  whether the terminal was left in line mode with echo:
 *
 *      [pty: icanon=1 echo=1]
 *
 *  The exit status is the command's; 124 if it ran past ten seconds, or
 *  past PTY_TIMEOUT_MS if that is set.
 *  POSIX only - posix_openpt, grantpt, unlockpt, ptsname - so no
 *  libutil. Written for tests/io/run (Iteration 254).
 */
#define _XOPEN_SOURCE 600
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static long now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000L + t.tv_nsec / 1000000L;
}

/* Copy the command's output until `until` (ms), or until it is gone. */
static int copy_output(int m, long until) {
    char buf[4096];
    for (;;) {
        long left = until - now_ms();
        struct pollfd p = { m, POLLIN, 0 };
        if (left <= 0) return 0;
        if (poll(&p, 1, (int)left) <= 0) continue;
        ssize_t n = read(m, buf, sizeof buf);
        if (n <= 0) return -1;              /* EIO: the terminal is closed */
        if (write(1, buf, (size_t)n) < 0) return -1;
    }
}

int main(int argc, char **argv) {
    static char in[65536];
    ssize_t inl = 0, r;
    int m, st = 0;
    pid_t pid;
    char *slave;
    struct termios t;

    if (argc < 4) return 125;
    m = posix_openpt(O_RDWR | O_NOCTTY);
    if (m < 0 || grantpt(m) != 0 || unlockpt(m) != 0) return 125;
    slave = ptsname(m);
    if (!slave) return 125;
    while (inl < (ssize_t)sizeof in && (r = read(0, in + inl, sizeof in - (size_t)inl)) > 0)
        inl += r;

    pid = fork();
    if (pid < 0) return 125;
    if (pid == 0) {
        int s;
        setsid();
        s = open(slave, O_RDWR);
        if (s < 0) _exit(125);
#ifdef TIOCSCTTY
        ioctl(s, TIOCSCTTY, 0);
#endif
        dup2(s, 0); dup2(s, 1); dup2(s, 2);
        if (s > 2) close(s);
        close(m);
        execv(argv[3], argv + 3);
        _exit(126);
    }

    {
        const char *lim = getenv("PTY_TIMEOUT_MS");
        long deadline = now_ms() + (lim ? atol(lim) : 10000);
        pid_t w;
        if (write(m, in, (size_t)inl) < 0) return 125;
        if (copy_output(m, now_ms() + atol(argv[2])) == 0)
            if (write(m, argv[1], strlen(argv[1])) < 0) return 125;
        copy_output(m, deadline);
        /* The terminal closes a moment before the command can be reaped:
         * wait for it, but not past the deadline. */
        while ((w = waitpid(pid, &st, WNOHANG)) == 0 && now_ms() < deadline)
            usleep(10000);
        if (w == 0) {
            kill(pid, SIGKILL);
            waitpid(pid, &st, 0);
            st = 124 << 8;
        }
    }
    {
        int s = open(slave, O_RDWR | O_NOCTTY);
        if (s >= 0 && tcgetattr(s, &t) == 0)
            printf("\n[pty: icanon=%d echo=%d]\n",
                   (t.c_lflag & ICANON) != 0, (t.c_lflag & ECHO) != 0);
        else
            printf("\n[pty: terminal state unknown]\n");
    }
    return WIFEXITED(st) ? WEXITSTATUS(st) : 125;
}

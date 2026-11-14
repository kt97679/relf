/*
 *  rt-linux.c - what engine/cv8.c needs from a C library, over Linux's
 *  system calls, for x86-64, i386, AArch64 and RISC-V (Iteration 945).
 *
 *  RelF - Relative Forth
 *  Copyright 2001 - 2005, Kirill Timofeev, kt97679@gmail.com
 *  The program is released under the GNU General Public License version 2.
 *  There is NO WARRANTY.
 *
 *  WHY. The C engine linked against the C library is 1.9 MB resident at
 *  start, and nearly all of it is the library and the dynamic loader: the
 *  assembly engine, with no library, runs the same image in 232 KB. The
 *  engine uses the library thinly - system calls, an allocator, the
 *  environment, one user-database lookup, a calendar, a handful of string
 *  functions - so this file is exactly that, over raw system calls. Linked
 *
 *      -static -no-pie -nostdlib -fno-stack-protector -D_FORTIFY_SOURCE=0
 *      engine/cv8.c engine/rt-linux.c -lgcc        (-D_FILE_OFFSET_BITS=64 on i386)
 *
 *  the engine has no C library at all; libgcc gives the double-width
 *  division helpers. The Makefile does that by default on Linux on these
 *  four architectures (ENGINE_RT=nolibc); ENGINE_RT=libc links the
 *  library as before, and is what anywhere else gets. The model was
 *  forth-vm-evolution's engine/rt-linux-x86_64.c, written for its copy
 *  of this engine; this one is relf's own, and covers the four.
 *
 *  It compiles against the C library's HEADERS, so each definition has
 *  the prototype cv8.c was compiled with, and every type and constant is
 *  the target's own; only the library is left out. On i386 the headers
 *  are taken with _FILE_OFFSET_BITS=64, whose struct stat and struct
 *  dirent are the kernel's stat64 and dirent64 - the definitions here
 *  then carry the 64 names (open64, stat64 ...) through the headers' own
 *  renaming. Failures follow the library's convention - -1 or NULL, and
 *  errno - not the kernel's negative numbers.
 *
 *  WHAT IS GIVEN UP. getpwnam reads /etc/passwd only: the library's goes
 *  through NSS (LDAP, SSSD, systemd-homed), and resolves ~name for users
 *  this one cannot see - QUESTIONS.md A9, decided for the assembly engine
 *  at 523, which reads /etc/passwd the same way. inet_pton takes IPv4
 *  only, which is all TCP-CONNECT asks of it. Nothing else differs.
 */
#define _GNU_SOURCE
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <setjmp.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <pwd.h>
#include <termios.h>
#include <time.h>
#include <poll.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#if defined(__i386__) && (!defined(_FILE_OFFSET_BITS) || _FILE_OFFSET_BITS != 64)
#error "rt-linux.c on i386 needs -D_FILE_OFFSET_BITS=64, for cv8.c as for this file"
#endif
#if !defined(__x86_64__) && !defined(__i386__) && !defined(__aarch64__) && !(defined(__riscv) && __riscv_xlen == 64)
#error "rt-linux.c: x86-64, i386, AArch64 and RISC-V 64 only - build with ENGINE_RT=libc"
#endif

/*  A function GCC or Clang must not turn into a call of itself: a copying
 *  or filling loop is recognised as memcpy or memset, which here is the
 *  function being compiled.  */
#if defined(__clang__)
#define NOIDIOM __attribute__((no_builtin))
#else
#define NOIDIOM __attribute__((optimize("no-tree-loop-distribute-patterns")))
#endif

char **environ;
static int rt_errno;
int *__errno_location(void) { return &rt_errno; }
static unsigned long rt_pagesize = 4096;   /* the auxiliary vector's AT_PAGESZ */

/* ---- system calls ------------------------------------------------------ */
#if defined(__x86_64__)
static long sc(long n, long a, long b, long c, long d, long e, long f) {
    register long r10 __asm__("r10") = d;
    register long r8 __asm__("r8") = e;
    register long r9 __asm__("r9") = f;
    long r;
    __asm__ volatile ("syscall" : "=a"(r)
                      : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8), "r"(r9)
                      : "rcx", "r11", "memory");
    return r;
}
#elif defined(__i386__)
/*  Out of line: the sixth argument goes in ebp, which inline assembly
 *  cannot name. int $0x80 - the vDSO's sysenter would be quicker, and no
 *  system call this engine makes is hot enough to tell.  */
long rt_sc(long n, long a, long b, long c, long d, long e, long f);
__asm__(".text\n.globl rt_sc\n.type rt_sc,@function\nrt_sc:\n"
        "\tpush %ebp\n\tpush %edi\n\tpush %esi\n\tpush %ebx\n"
        "\tmov 20(%esp),%eax\n\tmov 24(%esp),%ebx\n\tmov 28(%esp),%ecx\n\tmov 32(%esp),%edx\n"
        "\tmov 36(%esp),%esi\n\tmov 40(%esp),%edi\n\tmov 44(%esp),%ebp\n"
        "\tint $0x80\n"
        "\tpop %ebx\n\tpop %esi\n\tpop %edi\n\tpop %ebp\n\tret\n");
#define sc rt_sc
#elif defined(__aarch64__)
static long sc(long n, long a, long b, long c, long d, long e, long f) {
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    __asm__ volatile ("svc 0" : "+r"(x0)
                      : "r"(x8), "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5) : "memory");
    return x0;
}
#else   /* RISC-V 64 */
static long sc(long n, long a, long b, long c, long d, long e, long f) {
    register long a7 __asm__("a7") = n;
    register long a0 __asm__("a0") = a;
    register long a1 __asm__("a1") = b;
    register long a2 __asm__("a2") = c;
    register long a3 __asm__("a3") = d;
    register long a4 __asm__("a4") = e;
    register long a5 __asm__("a5") = f;
    __asm__ volatile ("ecall" : "+r"(a0)
                      : "r"(a7), "r"(a1), "r"(a2), "r"(a3), "r"(a4), "r"(a5) : "memory");
    return a0;
}
#endif
static long ok(long r) {      /* the kernel's -errno to the library's -1 and errno */
    if (r < 0 && r > -4096) { rt_errno = (int)-r; return -1; }
    return r;
}
#define S0(n)                ok(sc((n), 0, 0, 0, 0, 0, 0))
#define S1(n, a)             ok(sc((n), (long)(a), 0, 0, 0, 0, 0))
#define S2(n, a, b)          ok(sc((n), (long)(a), (long)(b), 0, 0, 0, 0))
#define S3(n, a, b, c)       ok(sc((n), (long)(a), (long)(b), (long)(c), 0, 0, 0))
#define S4(n, a, b, c, d)    ok(sc((n), (long)(a), (long)(b), (long)(c), (long)(d), 0, 0))
#define S5(n, a, b, c, d, e) ok(sc((n), (long)(a), (long)(b), (long)(c), (long)(d), (long)(e), 0))

/*  The calls the older ABIs have and AArch64 and RISC-V replaced:
 *  dup2, fork, poll, and stat by path (the newer ones have only the *at
 *  forms and ppoll, which x86 has too - used everywhere they serve).  */
#if defined(__x86_64__) || defined(__i386__)
#define RT_LEGACY 1
#endif
#if defined(__x86_64__) || defined(__aarch64__)
#define RT_UNALIGNED 1      /* word loads at any address are cheap */
#elif defined(__i386__)
#define RT_UNALIGNED 1
#endif

ssize_t read(int fd, void *b, size_t n)        { return S3(SYS_read, fd, b, n); }
ssize_t write(int fd, const void *b, size_t n) { return S3(SYS_write, fd, b, n); }
int close(int fd)                              { return (int)S1(SYS_close, fd); }
int open(const char *p, int flags, ...) {
    int mode = 0;
    if (flags & (O_CREAT | O_TMPFILE)) {
        va_list ap; va_start(ap, flags); mode = va_arg(ap, int); va_end(ap);
    }
#if defined(__i386__)
    flags |= 0100000;                    /* O_LARGEFILE, as the library's open64 */
#endif
    return (int)S4(SYS_openat, AT_FDCWD, p, flags, mode);
}
off_t lseek(int fd, off_t o, int whence) {
#if defined(__i386__)
    long long r;
    if (S5(SYS__llseek, fd, (long)(o >> 32), (long)(o & 0xffffffff), &r, whence) < 0) return -1;
    return r;
#else
    return S3(SYS_lseek, fd, o, whence);
#endif
}
int fcntl(int fd, int cmd, ...) {
    long arg;
    va_list ap; va_start(ap, cmd); arg = va_arg(ap, long); va_end(ap);
    return (int)S3(SYS_fcntl, fd, cmd, arg);
}
int dup2(int a, int b) {
#ifdef RT_LEGACY
    return (int)S2(SYS_dup2, a, b);
#else
    if (a == b) return fcntl(a, F_GETFD) < 0 ? -1 : b;   /* dup3 refuses equal descriptors */
    return (int)S3(SYS_dup3, a, b, 0);
#endif
}
int pipe(int fd[2])                            { return (int)S2(SYS_pipe2, fd, 0); }
pid_t getpid(void)                             { return (pid_t)S0(SYS_getpid); }
pid_t getppid(void)                            { return (pid_t)S0(SYS_getppid); }
int setpgid(pid_t p, pid_t g)                  { return (int)S2(SYS_setpgid, p, g); }
mode_t umask(mode_t m)                         { return (mode_t)S1(SYS_umask, m); }
int kill(pid_t p, int s)                       { return (int)S2(SYS_kill, p, s); }
pid_t fork(void) {
#ifdef RT_LEGACY
    return (pid_t)S0(SYS_fork);
#else
    return (pid_t)S2(SYS_clone, SIGCHLD, 0);
#endif
}
int execve(const char *p, char *const a[], char *const e[]) { return (int)S3(SYS_execve, p, a, e); }
pid_t waitpid(pid_t p, int *s, int o)          { return (pid_t)S4(SYS_wait4, p, s, o, 0); }
char *getcwd(char *b, size_t n)                { return S2(SYS_getcwd, b, n) < 0 ? NULL : b; }
int chdir(const char *p)                       { return (int)S1(SYS_chdir, p); }
int unlink(const char *p)                      { return (int)S3(SYS_unlinkat, AT_FDCWD, p, 0); }
int chmod(const char *p, mode_t m)             { return (int)S3(SYS_fchmodat, AT_FDCWD, p, m); }
int access(const char *p, int m)               { return (int)S3(SYS_faccessat, AT_FDCWD, p, m); }
int stat(const char *restrict p, struct stat *restrict st) {
#if defined(__i386__)
    return (int)S4(SYS_fstatat64, AT_FDCWD, p, st, 0);
#else
    return (int)S4(SYS_newfstatat, AT_FDCWD, p, st, 0);
#endif
}
int lstat(const char *restrict p, struct stat *restrict st) {
#if defined(__i386__)
    return (int)S4(SYS_fstatat64, AT_FDCWD, p, st, AT_SYMLINK_NOFOLLOW);
#else
    return (int)S4(SYS_newfstatat, AT_FDCWD, p, st, AT_SYMLINK_NOFOLLOW);
#endif
}
int poll(struct pollfd *f, nfds_t n, int ms) {
#ifdef RT_LEGACY
    return (int)S3(SYS_poll, f, n, ms);
#else
    struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000 };
    return (int)S5(SYS_ppoll, f, n, ms < 0 ? NULL : &ts, NULL, 8);
#endif
}
int getrlimit(__rlimit_resource_t r, struct rlimit *l)       { return (int)S4(SYS_prlimit64, 0, r, 0, l); }
int setrlimit(__rlimit_resource_t r, const struct rlimit *l) { return (int)S4(SYS_prlimit64, 0, r, l, 0); }
int getrusage(__rusage_who_t w, struct rusage *u)            { return (int)S2(SYS_getrusage, w, u); }
time_t time(time_t *t) {
    struct timespec ts;
    if (S2(SYS_clock_gettime, CLOCK_REALTIME, &ts) < 0) return (time_t)-1;
    if (t) *t = ts.tv_sec;
    return ts.tv_sec;
}
long sysconf(int name) {
    if (name == _SC_PAGESIZE) return (long)rt_pagesize;
    rt_errno = EINVAL;
    return -1;
}
void *mmap(void *a, size_t n, int prot, int flags, int fd, off_t o) {
#if defined(__i386__)
    long r = sc(SYS_mmap2, (long)a, (long)n, prot, flags, fd, (long)(o >> 12));
#else
    long r = sc(SYS_mmap, (long)a, (long)n, prot, flags, fd, (long)o);
#endif
    if (r < 0 && r > -4096) { rt_errno = (int)-r; return MAP_FAILED; }
    return (void *)r;
}
int munmap(void *a, size_t n)                  { return (int)S2(SYS_munmap, a, n); }
int mprotect(void *a, size_t n, int p)         { return (int)S3(SYS_mprotect, a, n, p); }
void _exit(int s)                              { for (;;) sc(SYS_exit_group, s, 0, 0, 0, 0, 0); }
void exit(int s)                               { _exit(s); }   /* no stdio to flush */

/* ---- the terminal: the kernel's termios is the library's, less its tail - */
#define RT_TCGETS 0x5401
#define RT_TCSETS 0x5402          /* +1 TCSETSW (TCSADRAIN), +2 TCSETSF (TCSAFLUSH) */
#define RT_TIOCGPGRP 0x540F
#define RT_TIOCSPGRP 0x5410
int tcgetattr(int fd, struct termios *t) {
    memset(t, 0, sizeof *t);
    return (int)S3(SYS_ioctl, fd, RT_TCGETS, t);
}
int tcsetattr(int fd, int how, const struct termios *t) {
    if (how < 0 || how > 2) { rt_errno = EINVAL; return -1; }
    return (int)S3(SYS_ioctl, fd, RT_TCSETS + how, t);
}
int isatty(int fd) {
    struct termios t;
    return tcgetattr(fd, &t) == 0;
}
pid_t tcgetpgrp(int fd) {
    int p;
    return S3(SYS_ioctl, fd, RT_TIOCGPGRP, &p) < 0 ? -1 : (pid_t)p;
}
int tcsetpgrp(int fd, pid_t g) {
    int p = (int)g;
    return (int)S3(SYS_ioctl, fd, RT_TIOCSPGRP, &p);
}

/* ---- sockets: TCP-LISTEN, -ACCEPT, -CONNECT ------------------------------ */
int socket(int d, int t, int p)                { return (int)S3(SYS_socket, d, t, p); }
int bind(int s, const struct sockaddr *a, socklen_t n)    { return (int)S3(SYS_bind, s, a, n); }
int listen(int s, int n)                       { return (int)S2(SYS_listen, s, n); }
int accept(int s, struct sockaddr *restrict a, socklen_t *restrict n) { return (int)S4(SYS_accept4, s, a, n, 0); }
int connect(int s, const struct sockaddr *a, socklen_t n) { return (int)S3(SYS_connect, s, a, n); }
int setsockopt(int s, int l, int o, const void *v, socklen_t n) { return (int)S5(SYS_setsockopt, s, l, o, v, n); }
/*  IPv4's dotted quad, as the library's: four decimal parts of 0-255, no
 *  leading zero in a part of two digits or more, nothing after.  */
int inet_pton(int af, const char *restrict s, void *restrict dst) {
    unsigned char q[4];
    int i;
    if (af != AF_INET) { rt_errno = EAFNOSUPPORT; return -1; }
    for (i = 0; i < 4; i++) {
        unsigned v = 0, digits = 0;
        if (i && *s++ != '.') return 0;
        while (*s >= '0' && *s <= '9') {
            if (digits && v == 0) return 0;
            v = v * 10 + (unsigned)(*s++ - '0');
            if (v > 255) return 0;
            digits++;
        }
        if (!digits) return 0;
        q[i] = (unsigned char)v;
    }
    if (*s) return 0;
    memcpy(dst, q, 4);
    return 1;
}

/* ---- signals: the kernel's struct, and a restorer to return through ---- */
#define RT_SA_RESTORER 0x04000000UL
#if defined(__x86_64__)
__asm__(".text\n.globl rt_restorer\n.type rt_restorer,@function\nrt_restorer:\n"
        "\tmov $15, %eax\n\tsyscall\n\thlt\n");
#elif defined(__i386__)
/*  i386 lays an old-style frame for a handler without SA_SIGINFO, and
 *  that one returns through sigreturn, its signal number popped first;
 *  rt_sigreturn is for the SA_SIGINFO frame (as the library's __restore
 *  and __restore_rt).  */
__asm__(".text\n.globl rt_restorer\n.type rt_restorer,@function\nrt_restorer:\n"
        "\tmov $173, %eax\n\tint $0x80\n\thlt\n"
        ".globl rt_restorer_old\n.type rt_restorer_old,@function\nrt_restorer_old:\n"
        "\tpop %eax\n\tmov $119, %eax\n\tint $0x80\n\thlt\n");
void rt_restorer_old(void);
#elif defined(__aarch64__)
__asm__(".text\n.globl rt_restorer\n.type rt_restorer,%function\nrt_restorer:\n"
        "\tmov x8, #139\n\tsvc 0\n");
#endif
#if defined(__riscv)
/*  RISC-V has no SA_RESTORER: the kernel returns through the vDSO.  */
struct k_sigaction { void *handler; unsigned long flags; unsigned mask[2]; };
#else
void rt_restorer(void);
struct k_sigaction { void *handler; unsigned long flags; void *restorer; unsigned mask[2]; };
#endif
int sigemptyset(sigset_t *s) { memset(s, 0, sizeof *s); return 0; }
int sigaddset(sigset_t *s, int sig) {
    unsigned long *w = (unsigned long *)s;
    if (sig <= 0 || sig > 64) { rt_errno = EINVAL; return -1; }
    w[(sig - 1) / (8 * sizeof(long))] |= 1UL << ((sig - 1) % (8 * sizeof(long)));
    return 0;
}
int sigaction(int sig, const struct sigaction *restrict act, struct sigaction *restrict old) {
    struct k_sigaction k, ko;
    long r;
    if (act) {
        k.handler = (void *)act->sa_handler;      /* a union with sa_sigaction */
        k.flags = (unsigned long)act->sa_flags;
#if !defined(__riscv)
        k.flags |= RT_SA_RESTORER;
        k.restorer = (void *)rt_restorer;
#if defined(__i386__)
        if (!(act->sa_flags & SA_SIGINFO)) k.restorer = (void *)rt_restorer_old;
#endif
#endif
        memcpy(k.mask, &act->sa_mask, 8);         /* the kernel's 64 signals */
    }
    r = S4(SYS_rt_sigaction, sig, act ? &k : 0, old ? &ko : 0, 8);
    if (r == 0 && old) {
        memset(old, 0, sizeof *old);
        old->sa_handler = (void (*)(int))ko.handler;
        old->sa_flags = (int)(ko.flags & ~RT_SA_RESTORER);
        memcpy(&old->sa_mask, ko.mask, 8);
    }
    return (int)r;
}
int sigprocmask(int how, const sigset_t *restrict set, sigset_t *restrict old) {
    if (old) memset(old, 0, sizeof *old);
    return (int)S4(SYS_rt_sigprocmask, how, set, old, 8);
}

/*  sigsetjmp and siglongjmp: the registers a call preserves, the stack
 *  pointer and the return address, into the jmp_buf's own array (each
 *  architecture's is large enough - the library's sizes); then a jump to
 *  rt_sigjmp_save, which keeps the signal mask when asked and returns 0
 *  to sigsetjmp's caller. The trap route (cv8.c's trap_restart) leaves a
 *  signal handler through siglongjmp, so the mask must come back.  */
int rt_sigjmp_save(sigjmp_buf env, int savemask) {
    env->__mask_was_saved = savemask && sigprocmask(SIG_BLOCK, NULL, &env->__saved_mask) == 0;
    return 0;
}
void rt_jump(sigjmp_buf env, int val) __attribute__((noreturn));
void siglongjmp(sigjmp_buf env, int val) {
    if (env->__mask_was_saved) sigprocmask(SIG_SETMASK, &env->__saved_mask, NULL);
    rt_jump(env, val);
}
#if defined(__x86_64__)
__asm__(".text\n.globl __sigsetjmp\n.type __sigsetjmp,@function\n__sigsetjmp:\n"
        "\tmov %rbx,0(%rdi)\n\tmov %rbp,8(%rdi)\n\tmov %r12,16(%rdi)\n\tmov %r13,24(%rdi)\n"
        "\tmov %r14,32(%rdi)\n\tmov %r15,40(%rdi)\n\tlea 8(%rsp),%rdx\n\tmov %rdx,48(%rdi)\n"
        "\tmov (%rsp),%rdx\n\tmov %rdx,56(%rdi)\n\tjmp rt_sigjmp_save\n"
        ".globl rt_jump\n.type rt_jump,@function\nrt_jump:\n"
        "\tmov %esi,%eax\n\ttest %eax,%eax\n\tjnz 1f\n\tinc %eax\n1:\n"
        "\tmov 0(%rdi),%rbx\n\tmov 8(%rdi),%rbp\n\tmov 16(%rdi),%r12\n\tmov 24(%rdi),%r13\n"
        "\tmov 32(%rdi),%r14\n\tmov 40(%rdi),%r15\n\tmov 48(%rdi),%rsp\n\tjmp *56(%rdi)\n");
#elif defined(__i386__)
__asm__(".text\n.globl __sigsetjmp\n.type __sigsetjmp,@function\n__sigsetjmp:\n"
        "\tmov 4(%esp),%eax\n\tmov %ebx,0(%eax)\n\tmov %esi,4(%eax)\n\tmov %edi,8(%eax)\n"
        "\tmov %ebp,12(%eax)\n\tlea 4(%esp),%ecx\n\tmov %ecx,16(%eax)\n\tmov (%esp),%ecx\n"
        "\tmov %ecx,20(%eax)\n\tjmp rt_sigjmp_save\n"
        ".globl rt_jump\n.type rt_jump,@function\nrt_jump:\n"
        "\tmov 4(%esp),%edx\n\tmov 8(%esp),%eax\n\ttest %eax,%eax\n\tjnz 1f\n\tinc %eax\n1:\n"
        "\tmov 0(%edx),%ebx\n\tmov 4(%edx),%esi\n\tmov 8(%edx),%edi\n\tmov 12(%edx),%ebp\n"
        "\tmov 16(%edx),%esp\n\tjmp *20(%edx)\n");
#elif defined(__aarch64__)
__asm__(".text\n.globl __sigsetjmp\n.type __sigsetjmp,%function\n__sigsetjmp:\n"
        "\tstp x19, x20, [x0, #0]\n\tstp x21, x22, [x0, #16]\n\tstp x23, x24, [x0, #32]\n"
        "\tstp x25, x26, [x0, #48]\n\tstp x27, x28, [x0, #64]\n\tstp x29, x30, [x0, #80]\n"
        "\tmov x2, sp\n\tstr x2, [x0, #96]\n\tstp d8, d9, [x0, #104]\n\tstp d10, d11, [x0, #120]\n"
        "\tstp d12, d13, [x0, #136]\n\tstp d14, d15, [x0, #152]\n\tb rt_sigjmp_save\n"
        ".globl rt_jump\n.type rt_jump,%function\nrt_jump:\n"
        "\tldp x19, x20, [x0, #0]\n\tldp x21, x22, [x0, #16]\n\tldp x23, x24, [x0, #32]\n"
        "\tldp x25, x26, [x0, #48]\n\tldp x27, x28, [x0, #64]\n\tldp x29, x30, [x0, #80]\n"
        "\tldr x2, [x0, #96]\n\tmov sp, x2\n\tldp d8, d9, [x0, #104]\n\tldp d10, d11, [x0, #120]\n"
        "\tldp d12, d13, [x0, #136]\n\tldp d14, d15, [x0, #152]\n"
        "\tcmp w1, #0\n\tcsinc w0, w1, wzr, ne\n\tbr x30\n");
#else   /* RISC-V 64, the D extension's callee-saved registers too */
__asm__(".text\n.globl __sigsetjmp\n.type __sigsetjmp,@function\n__sigsetjmp:\n"
        "\tsd ra, 0(a0)\n\tsd s0, 8(a0)\n\tsd s1, 16(a0)\n\tsd s2, 24(a0)\n\tsd s3, 32(a0)\n"
        "\tsd s4, 40(a0)\n\tsd s5, 48(a0)\n\tsd s6, 56(a0)\n\tsd s7, 64(a0)\n\tsd s8, 72(a0)\n"
        "\tsd s9, 80(a0)\n\tsd s10, 88(a0)\n\tsd s11, 96(a0)\n\tsd sp, 104(a0)\n"
        "\tfsd fs0, 112(a0)\n\tfsd fs1, 120(a0)\n\tfsd fs2, 128(a0)\n\tfsd fs3, 136(a0)\n"
        "\tfsd fs4, 144(a0)\n\tfsd fs5, 152(a0)\n\tfsd fs6, 160(a0)\n\tfsd fs7, 168(a0)\n"
        "\tfsd fs8, 176(a0)\n\tfsd fs9, 184(a0)\n\tfsd fs10, 192(a0)\n\tfsd fs11, 200(a0)\n"
        "\ttail rt_sigjmp_save\n"
        ".globl rt_jump\n.type rt_jump,@function\nrt_jump:\n"
        "\tld ra, 0(a0)\n\tld s0, 8(a0)\n\tld s1, 16(a0)\n\tld s2, 24(a0)\n\tld s3, 32(a0)\n"
        "\tld s4, 40(a0)\n\tld s5, 48(a0)\n\tld s6, 56(a0)\n\tld s7, 64(a0)\n\tld s8, 72(a0)\n"
        "\tld s9, 80(a0)\n\tld s10, 88(a0)\n\tld s11, 96(a0)\n\tld sp, 104(a0)\n"
        "\tfld fs0, 112(a0)\n\tfld fs1, 120(a0)\n\tfld fs2, 128(a0)\n\tfld fs3, 136(a0)\n"
        "\tfld fs4, 144(a0)\n\tfld fs5, 152(a0)\n\tfld fs6, 160(a0)\n\tfld fs7, 168(a0)\n"
        "\tfld fs8, 176(a0)\n\tfld fs9, 184(a0)\n\tfld fs10, 192(a0)\n\tfld fs11, 200(a0)\n"
        "\tseqz a0, a1\n\tadd a0, a0, a1\n\tret\n");
#endif

/* ---- memory and strings ---------------------------------------------------
 *  MOVE, FILL, COMPARE, SCAN and CSTRLEN are these, mostly on strings of
 *  a few dozen bytes, and the library's are vectorised: the first plain
 *  loops here cost the realistic script 3 % (callgrind: twice the
 *  library's instructions in them). So a word at a time, little-endian:
 *  the first zero or differing byte is the lowest set bit's. strlen and
 *  memchr load aligned words only, the first one masked below the start,
 *  so they never read across a page; the others, where loads at any
 *  address are cheap (x86, AArch64), take a short copy or compare as two
 *  overlapping words and a long one's tail as one, as the library does;
 *  RISC-V keeps word loops for co-aligned operands and bytes otherwise.  */
typedef size_t __attribute__((may_alias)) rt_word;
#define W sizeof(size_t)
#define ONES ((size_t)-1 / 255)
#define HIGHS (ONES << 7)
#define HASZERO(x) (((x) - ONES) & ~(x) & HIGHS)     /* exact at its lowest set bit */
static inline size_t ldw(const unsigned char *p) { size_t w; __builtin_memcpy(&w, p, W); return w; }
static inline void stw(unsigned char *p, size_t w) { __builtin_memcpy(p, &w, W); }
static inline unsigned firstbyte(size_t m) {   /* the byte of m's lowest set bit */
    return (sizeof(size_t) == 8 ? (unsigned)__builtin_ctzll((unsigned long long)m)
                                : (unsigned)__builtin_ctz((unsigned)m)) >> 3;
}
static inline size_t below(unsigned bytes) {   /* ones in the low bytes, which lie before the start */
    return bytes ? ((size_t)1 << (bytes * 8)) - 1 : 0;
}

NOIDIOM void *memmove(void *d, const void *s, size_t n) {
    unsigned char *p = d;
    const unsigned char *q = s;
#ifdef RT_UNALIGNED
    if (n <= 2 * W) {                       /* every load before any store: overlap is safe */
        if (n >= W) {
            size_t a = ldw(q), b = ldw(q + n - W);
            stw(p, a); stw(p + n - W, b);
        } else if (n >= 4) {
            uint32_t a, b;
            __builtin_memcpy(&a, q, 4); __builtin_memcpy(&b, q + n - 4, 4);
            __builtin_memcpy(p, &a, 4); __builtin_memcpy(p + n - 4, &b, 4);
        } else if (n) {
            unsigned char a = q[0], b = q[n / 2], c = q[n - 1];
            p[0] = a; p[n / 2] = b; p[n - 1] = c;
        }
        return d;
    }
    if ((uintptr_t)p - (uintptr_t)q >= n) {  /* forward: d below s, or past its end */
        size_t tail = ldw(q + n - W);
        unsigned char *pe = p + n - W;
        for (; n > W; n -= W, p += W, q += W) stw(p, ldw(q));
        stw(pe, tail);
    } else {                                 /* backward: d inside (s, s + n) */
        size_t head = ldw(q);
        unsigned char *p0 = p;
        p += n; q += n;
        for (; n > W; n -= W) { p -= W; q -= W; stw(p, ldw(q)); }
        stw(p0, head);
    }
#else
#define COALIGNED(a, b) ((((uintptr_t)(a) | (uintptr_t)(b)) & (W - 1)) == 0)
    if ((uintptr_t)p - (uintptr_t)q >= n) {
        if (COALIGNED(p, q))
            for (; n >= W; n -= W, p += W, q += W) stw(p, ldw(q));
        for (; n; n--) *p++ = *q++;
    } else {
        p += n; q += n;
        if (COALIGNED(p, q))
            for (; n >= W; n -= W) { p -= W; q -= W; stw(p, ldw(q)); }
        while (n--) *--p = *--q;
    }
#endif
    return d;
}
/*  memcpy is memmove, by name: written as a call, Clang made the call a
 *  memcpy - itself - since the arguments are restrict.  */
void *memcpy(void *restrict d, const void *restrict s, size_t n) __attribute__((alias("memmove")));
NOIDIOM void *memset(void *d, int c, size_t n) {
    unsigned char *p = d;
    size_t w = ONES * (unsigned char)c;
#ifdef RT_UNALIGNED
    if (n >= W) {
        unsigned char *e = p + n - W;
        for (; p < e; p += W) stw(p, w);
        stw(e, w);
        return d;
    }
#else
    for (; n && ((uintptr_t)p & (W - 1)); n--) *p++ = (unsigned char)c;
    for (; n >= W; n -= W, p += W) *(rt_word *)p = w;
#endif
    for (; n; n--) *p++ = (unsigned char)c;
    return d;
}
NOIDIOM int memcmp(const void *a, const void *b, size_t n) {
    const unsigned char *p = a, *q = b;
#ifdef RT_UNALIGNED
    if (n >= W) {
        const unsigned char *pe = p + n - W, *qe = q + n - W;
        size_t x, y;
        for (; p < pe; p += W, q += W)
            if ((x = ldw(p)) != (y = ldw(q))) { unsigned i = firstbyte(x ^ y); return p[i] - q[i]; }
        if ((x = ldw(pe)) != (y = ldw(qe))) { unsigned i = firstbyte(x ^ y); return pe[i] - qe[i]; }
        return 0;                            /* the last word overlaps bytes already equal */
    }
#else
    if (COALIGNED(p, q))
        for (; n >= W && ldw(p) == ldw(q); n -= W, p += W, q += W) ;
#endif
    for (; n; n--, p++, q++) if (*p != *q) return *p - *q;
    return 0;
}
int bcmp(const void *a, const void *b, size_t n) { return memcmp(a, b, n); }   /* Clang's, for memcmp() == 0 */
NOIDIOM void *memchr(const void *s, int c, size_t n) {
    uintptr_t p = (uintptr_t)s, a = p & ~(uintptr_t)(W - 1), end = p + n, r;
    size_t k = ONES * (unsigned char)c, z;
    if (!n) return NULL;
    z = HASZERO((*(const rt_word *)a ^ k) | below((unsigned)(p - a)));
    while (!z) {
        a += W;
        if (a >= end) return NULL;
        z = HASZERO(*(const rt_word *)a ^ k);
    }
    r = a + firstbyte(z);
    return r < end ? (void *)r : NULL;
}
NOIDIOM size_t strlen(const char *s) {
    uintptr_t p = (uintptr_t)s, a = p & ~(uintptr_t)(W - 1);
    size_t z = HASZERO(*(const rt_word *)a | below((unsigned)(p - a)));
    while (!z) { a += W; z = HASZERO(*(const rt_word *)a); }
    return a + firstbyte(z) - p;
}
int strcmp(const char *a, const char *b) {
    const unsigned char *p = (const unsigned char *)a, *q = (const unsigned char *)b;
    while (*p && *p == *q) p++, q++;
    return *p - *q;
}
char *strchr(const char *s, int c) {
    for (;; s++) {
        if (*s == (char)c) return (char *)s;
        if (!*s) return NULL;
    }
}

/* ---- the allocator ---------------------------------------------------------
 *  Blocks of a power of two, 32 bytes to 32 KB, each with a 16-byte
 *  header, cut from 256 KB regions and kept on a free list per size once
 *  freed; a larger request is its own mapping, given back on free. Pages
 *  count as resident only once touched, so a region costs nothing until
 *  used. Single-threaded, as the engine is; cv8.c's g_in_alloc keeps a ^C
 *  from jumping out of one.  */
#define HDR 16
#define BIG 32768
#define REGION (256 * 1024)
struct hdr { size_t size; size_t cls; };       /* usable bytes; class, or 0: its own mapping */
static void *freel[16];
static char *bump, *bump_end;
static void *alloc(size_t n, int *fresh) {
    size_t total, sz;
    struct hdr *h;
    int c;
    if (n > (size_t)PTRDIFF_MAX / 2) { rt_errno = ENOMEM; return NULL; }
    total = n + HDR;
    *fresh = 1;
    if (total > BIG) {
        size_t len = (total + rt_pagesize - 1) & ~(size_t)(rt_pagesize - 1);
        void *m = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (m == MAP_FAILED) { rt_errno = ENOMEM; return NULL; }
        h = m; h->size = len - HDR; h->cls = 0;
        return (char *)h + HDR;
    }
    for (c = 5; ((size_t)1 << c) < total; c++) ;
    sz = (size_t)1 << c;
    if (freel[c]) {
        h = freel[c]; freel[c] = *(void **)((char *)h + HDR);
        *fresh = 0;
    } else {
        if (!bump || (size_t)(bump_end - bump) < sz) {
            void *m = mmap(NULL, REGION, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (m == MAP_FAILED) { rt_errno = ENOMEM; return NULL; }
            bump = m; bump_end = bump + REGION;     /* the old region's tail is left unused */
        }
        h = (struct hdr *)bump; bump += sz;
    }
    h->size = sz - HDR; h->cls = (size_t)c;
    return (char *)h + HDR;
}
void *malloc(size_t n) { int fresh; return alloc(n, &fresh); }
void *calloc(size_t k, size_t n) {
    int fresh;
    void *p;
    if (n && k > (size_t)-1 / n) { rt_errno = ENOMEM; return NULL; }
    p = alloc(k * n, &fresh);
    if (p && !fresh) memset(p, 0, k * n);         /* new pages are zero already */
    return p;
}
void free(void *p) {
    struct hdr *h;
    if (!p) return;
    h = (struct hdr *)((char *)p - HDR);
    if (h->cls == 0) { munmap(h, h->size + HDR); return; }
    *(void **)p = freel[h->cls]; freel[h->cls] = h;
}
void *realloc(void *p, size_t n) {
    struct hdr *h;
    void *q;
    if (!p) return malloc(n);
    h = (struct hdr *)((char *)p - HDR);
    if (n <= h->size) return p;
    q = malloc(n);
    if (!q) return NULL;
    memcpy(q, p, h->size);
    free(p);
    return q;
}

/* ---- the environment --------------------------------------------------------
 *  environ starts as the kernel's array on the stack; the first setenv
 *  that adds a name copies it to the heap, with room to grow.  */
static size_t env_cap;                /* 0 while environ is the kernel's */
static int env_name_ok(const char *n) { return n && *n && !strchr(n, '='); }
static char **env_find(const char *n, size_t len) {
    char **e;
    for (e = environ; e && *e; e++)
        if (memcmp(*e, n, len) == 0 && (*e)[len] == '=') return e;
    return NULL;
}
char *getenv(const char *n) {
    size_t len = strlen(n);
    char **e = *n ? env_find(n, len) : NULL;
    return e ? *e + len + 1 : NULL;
}
int setenv(const char *n, const char *v, int overwrite) {
    size_t ln, lv, count;
    char *s, **e;
    if (!env_name_ok(n)) { rt_errno = EINVAL; return -1; }
    ln = strlen(n); lv = strlen(v);
    e = env_find(n, ln);
    if (e && !overwrite) return 0;
    s = malloc(ln + lv + 2);
    if (!s) return -1;
    memcpy(s, n, ln); s[ln] = '='; memcpy(s + ln + 1, v, lv + 1);
    if (e) { *e = s; return 0; }       /* the old string is left, as the library leaves it */
    for (count = 0; environ && environ[count]; count++) ;
    if (count + 2 > env_cap) {
        size_t cap = (count + 2) * 2;
        char **ne = malloc(cap * sizeof *ne);
        if (!ne) { free(s); return -1; }
        if (count) memcpy(ne, environ, count * sizeof *ne);
        if (env_cap) free(environ);
        environ = ne; env_cap = cap;
    }
    environ[count] = s; environ[count + 1] = NULL;
    return 0;
}
int unsetenv(const char *n) {
    size_t len;
    char **e;
    if (!env_name_ok(n)) { rt_errno = EINVAL; return -1; }
    len = strlen(n);
    while ((e = env_find(n, len)))
        do e[0] = e[1]; while (*e++);
    return 0;
}

/* ---- directories: getdents64, whose entry is the headers' struct dirent - */
struct __dirstream { int fd, pos, len; char buf[2048] __attribute__((aligned(8))); };
DIR *opendir(const char *p) {
    DIR *d;
    int fd = (int)S4(SYS_openat, AT_FDCWD, p, O_RDONLY | O_DIRECTORY | O_CLOEXEC, 0);
    if (fd < 0) return NULL;
    d = malloc(sizeof *d);
    if (!d) { close(fd); return NULL; }
    d->fd = fd; d->pos = d->len = 0;
    return d;
}
struct dirent *readdir(DIR *d) {
    struct dirent *e;
    if (d->pos >= d->len) {
        long n = S3(SYS_getdents64, d->fd, d->buf, sizeof d->buf);
        if (n <= 0) return NULL;
        d->len = (int)n; d->pos = 0;
    }
    e = (struct dirent *)(d->buf + d->pos);
    d->pos += e->d_reclen;
    return e;
}
int closedir(DIR *d) {
    int r = close(d->fd);
    free(d);
    return r;
}

/* ---- ~user: /etc/passwd, read whole, kept until the next call (A9) ------ */
static char *pw_file;
static struct passwd pw_ent;
static unsigned long strtoul_rt(const char *s) {
    unsigned long v = 0;
    while (*s >= '0' && *s <= '9') v = v * 10 + (unsigned long)(*s++ - '0');
    return v;
}
struct passwd *getpwnam(const char *name) {
    size_t cap = 4096, len = 0, ln = strlen(name);
    char *p, *end;
    int fd = open("/etc/passwd", O_RDONLY | O_CLOEXEC);
    long n;
    free(pw_file); pw_file = NULL;
    if (fd < 0) return NULL;
    for (;;) {
        char *b = realloc(pw_file, cap + 1);
        if (!b) { close(fd); return NULL; }
        pw_file = b;
        n = read(fd, pw_file + len, cap - len);
        if (n <= 0) break;
        len += (size_t)n;
        if (len == cap) cap *= 2;
    }
    close(fd);
    if (!pw_file) return NULL;
    pw_file[len] = 0;
    for (p = pw_file; p < pw_file + len; p = end + 1) {
        char *f[7];
        int i;
        end = strchr(p, '\n');
        if (!end) end = pw_file + len;
        *end = 0;
        if (memcmp(p, name, ln) != 0 || p[ln] != ':' || !ln) continue;
        for (i = 0, f[0] = p; i < 6; i++) {
            char *c = strchr(f[i], ':');
            if (!c) break;
            *c = 0; f[i + 1] = c + 1;
        }
        if (i < 6) continue;
        pw_ent.pw_name = f[0]; pw_ent.pw_passwd = f[1];
        pw_ent.pw_uid = (uid_t)strtoul_rt(f[2]); pw_ent.pw_gid = (gid_t)strtoul_rt(f[3]);
        pw_ent.pw_gecos = f[4]; pw_ent.pw_dir = f[5]; pw_ent.pw_shell = f[6];
        return &pw_ent;
    }
    return NULL;
}

/* ---- the calendar: UTC, as the assembly engine has it (A16) ------------- */
struct tm *gmtime_r(const time_t *restrict t, struct tm *restrict tm) {
    static const short cum[12] = { 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334 };
    long long s = (long long)*t, days = s / 86400, z, era, y;
    long rem = (long)(s % 86400);
    unsigned doe, yoe, doy, mp, d, m;
    int leap;
    if (rem < 0) { rem += 86400; days--; }
    tm->tm_hour = (int)(rem / 3600); tm->tm_min = (int)(rem / 60 % 60); tm->tm_sec = (int)(rem % 60);
    tm->tm_wday = (int)((days % 7 + 11) % 7);          /* 1970-01-01 was a Thursday */
    z = days + 719468;                                   /* civil from days: H. Hinnant's */
    era = (z >= 0 ? z : z - 146096) / 146097;
    doe = (unsigned)(z - era * 146097);
    yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    y = (long long)yoe + era * 400;
    doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    mp = (5 * doy + 2) / 153;
    d = doy - (153 * mp + 2) / 5 + 1;
    m = mp < 10 ? mp + 3 : mp - 9;
    y += m <= 2;
    leap = y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
    tm->tm_year = (int)(y - 1900); tm->tm_mon = (int)m - 1; tm->tm_mday = (int)d;
    tm->tm_yday = cum[m - 1] + (int)d - 1 + (m > 2 && leap);
    tm->tm_isdst = 0; tm->tm_gmtoff = 0; tm->tm_zone = "GMT";
    return tm;
}

/* ---- the start ----------------------------------------------------------- */
int main(int argc, char **argv);
void rt_start(long *sp) __attribute__((noreturn, used));
void rt_start(long *sp) {
    int argc = (int)sp[0];
    char **argv = (char **)(sp + 1), **e;
    unsigned long *aux;
    environ = argv + argc + 1;
    for (e = environ; *e; e++) ;
    for (aux = (unsigned long *)(e + 1); aux[0]; aux += 2)
        if (aux[0] == 6) rt_pagesize = aux[1];          /* AT_PAGESZ */
    exit(main(argc, argv));
}
#if defined(__x86_64__)
__asm__(".text\n.globl _start\n.type _start,@function\n_start:\n"
        "\txor %ebp,%ebp\n\tmov %rsp,%rdi\n\tand $-16,%rsp\n\tcall rt_start\n\thlt\n");
#elif defined(__i386__)
__asm__(".text\n.globl _start\n.type _start,@function\n_start:\n"
        "\txor %ebp,%ebp\n\tmov %esp,%eax\n\tand $-16,%esp\n\tsub $12,%esp\n\tpush %eax\n"
        "\tcall rt_start\n\thlt\n");
#elif defined(__aarch64__)
__asm__(".text\n.globl _start\n.type _start,%function\n_start:\n"
        "\tmov x29, #0\n\tmov x30, #0\n\tmov x0, sp\n\tbl rt_start\n");
#else
__asm__(".text\n.globl _start\n.type _start,@function\n_start:\n"
        ".option push\n.option norelax\n\tlla gp, __global_pointer$\n.option pop\n"
        "\tmv a0, sp\n\tandi sp, sp, -16\n\tcall rt_start\n");
#endif

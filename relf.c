/*
 *  RelF - Relative Forth
 *  Based on SOD32 by L.C. Benschop
 *  Copyright 2001 - 2005, Kirill Timofeev, kt97679@gmail.com
 *  The program is released under the GNU General Public License version 2.
 *  There is NO WARRANTY.
 *
 *  Phase 2 engine: a genuine x86-64 process, talking to the OS via raw
 *  Linux syscalls only (no libc, no crt0). Cells are 8 bytes, matching
 *  the process's own pointer width - see GOALS.md, "load-bearing facts",
 *  for why cell width and host pointer width must match in this design.
 *  Built with -nostdlib -static; see tests/run_tests.sh for the exact
 *  command line.
 */

#define  UNS8 unsigned char   /*     Virtual    */
#define INT64 long            /*     machine    */
#define UNS64 unsigned long   /* internal types */

#define MEMSIZE (256 * 1024)  /* how much memory do we allocate for VM */
#define RSTACK_BYTES 2048     /* room reserved for the return stack     */

/*
 *  Macroses for memory access
 */

#define CELL(reg) (*(UNS64*)(reg)) /* cell (word) memory access macros */
#define BYTE(reg) (*(UNS8*)((reg) ^ 7)) /* VM is 64-bit, big endian, see  */
                                         /* swap_mem() below               */

/*
 *  Macroses for stack access
 */

#define RS       CELL(rp)          /* top of return stack               */
#define DS0      CELL(dsp)         /* top of data stack                 */
#define DS1      CELL(dsp + 8)     /* 2nd element on data stack         */
#define DS2      CELL(dsp + 16)    /* 3d element on data stack          */
#define DS3      CELL(dsp + 24)    /* 4th element on data stack         */
#define PUSH(x)  dsp -= 8; DS0 = x /* pushes x to data stack            */
#define RPUSH(x) rp -= 8; RS = x   /* pushes x to return stack          */

/*
 *  VM memory. +7 is necessary to be able to allocate MEMSIZE bytes from
 *  an 8-aligned address in order to have native word access.
 */

static UNS8 mem[MEMSIZE + 7];

/*
 *  1st 8-aligned address in mem array. This is base address of the system.
 */

static UNS8 *base;

/* VM registers and related variables */

static UNS64  ip; /* instruction pointer               */
static UNS64  rp; /* return stack pointer              */
static UNS64 dsp; /* data stack pointer                */
static UNS64   t; /* variable for temporary storage    */

/* argv/envp captured by _start, needed by vmsystem() */
static char **g_argv;
static char **g_envp;

/*
 *  Raw Linux x86-64 syscalls. No libc anywhere in this file.
 */

static long sys_read(long fd, void *buf, long count) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(0L), "D"(fd), "S"(buf), "d"(count) : "rcx", "r11", "memory");
    return ret;
}

static long sys_write(long fd, const void *buf, long count) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(1L), "D"(fd), "S"(buf), "d"(count) : "rcx", "r11", "memory");
    return ret;
}

static long sys_open(const char *path, long flags, long mode) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(2L), "D"(path), "S"(flags), "d"(mode) : "rcx", "r11", "memory");
    return ret;
}

static long sys_close(long fd) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(3L), "D"(fd) : "rcx", "r11", "memory");
    return ret;
}

static long sys_lseek(long fd, long offset, long whence) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(8L), "D"(fd), "S"(offset), "d"(whence) : "rcx", "r11", "memory");
    return ret;
}

static void sys_exit_group(long code) {
    __asm__ volatile ("syscall" : : "a"(231L), "D"(code) : "memory");
    __builtin_unreachable();
}

static long sys_unlink(const char *path) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(87L), "D"(path) : "rcx", "r11", "memory");
    return ret;
}

static long sys_fork(void) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(57L) : "rcx", "r11", "memory");
    return ret;
}

static long sys_execve(const char *path, char *const argv[], char *const envp[]) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(59L), "D"(path), "S"(argv), "d"(envp) : "rcx", "r11", "memory");
    return ret;
}

static long sys_wait4(long pid, int *status, long options, void *rusage) {
    long ret;
    register void *r10 __asm__("r10") = rusage;
    __asm__ volatile ("syscall" : "=a"(ret)
        : "a"(61L), "D"(pid), "S"(status), "d"(options), "r"(r10)
        : "rcx", "r11", "memory");
    return ret;
}

/*
 *  Small helpers replacing the bits of libc we no longer link.
 */

static long str_len(const char *s) {
    long n = 0;
    while (s[n]) n++;
    return n;
}

static void write_str(long fd, const char *s) {
    sys_write(fd, s, str_len(s));
}

/* Read/write the full requested amount, looping over short reads/writes.
 * Returns bytes transferred, or a negative value on a real error. */
static long full_read(long fd, void *buf, long count) {
    long total = 0, n;
    UNS8 *p = (UNS8*)buf;
    while (total < count) {
        n = sys_read(fd, p + total, count - total);
        if (n == 0) break;   /* EOF, not an error */
        if (n < 0) return n; /* real error */
        total += n;
    }
    return total;
}

static long full_write(long fd, const void *buf, long count) {
    long total = 0, n;
    const UNS8 *p = (const UNS8*)buf;
    while (total < count) {
        n = sys_write(fd, p + total, count - total);
        if (n < 0) return n;
        if (n == 0) return -1; /* no progress, avoid spinning forever */
        total += n;
    }
    return total;
}

/*
 *  Perform byte swap of 64-bit words in region
 *  of memory of virtual machine.
 */

static void swap_mem(UNS64 start, UNS64 len) {
    UNS64 i;

    for (i = start & ~(UNS64)7; i < len + start; i += 8) {
        CELL(i) = __builtin_bswap64(CELL(i));
    }
}

/*
 *  Multiply two 64-bit unsigned numbers *a and *b.
 *  High half of 128-bit result in *a, low half in *b.
 */

static void umul(UNS64 *a, UNS64 *b) {
    UNS64 x = *a, y = *b, hi, lo;
    __asm__ ("mulq %3" : "=a"(lo), "=d"(hi) : "a"(x), "rm"(y));
    *a = hi;
    *b = lo;
}

/*
 *  Divide 128-bit unsigned number (high half *b, low half *c) by
 *  64-bit unsigned number in *a. Quotient in *b, remainder in *c.
 */

static void udiv(UNS64 *a, UNS64 *b, UNS64 *c) {
    UNS64 divisor = *a, hi = *b, lo = *c, q, r;
    __asm__ ("divq %4" : "=a"(q), "=d"(r)
        : "a"(lo), "d"(hi), "rm"(divisor));
    *b = q;
    *c = r;
}

/*
 *  Functions, implementing forth virtual machine primitives.
 */

static void vmnoop()    {/* noop    */ }
static void vmexit()    {/* exit    */ ip = RS; rp += 8; }
static void vmlit()     {/* lit     */ PUSH(CELL(ip)); ip += 8; }
static void vmbranch()  {/* branch  */ ip += CELL(ip); }
static void vm0branch() {/* 0branch */ if (DS0) ip += 8; else ip += CELL(ip); dsp += 8; }
static void vmdrop()    {/* drop    */ dsp += 8; }
static void vmdup()     {/* dup     */ PUSH(DS1); }
static void vmswap()    {/* swap    */ t = DS0; DS0 = DS1; DS1 = t; }
static void vmrot()     {/* rot     */ t = DS2; DS2 = DS1; DS1 = DS0; DS0 = t; }
static void vmover()    {/* over    */ PUSH(DS2); }
static void vmcfetch()  {/* C@      */ DS0 = BYTE(DS0); }
static void vmfetch()   {/* @       */ DS0 = CELL(DS0); }
static void vmcstore()  {/* c!      */ BYTE(DS0) = (UNS8)DS1; dsp += 16; }
static void vmstore()   {/* !       */ CELL(DS0) = DS1; dsp += 16; }
static void vmand()     {/* and     */ DS1 &= DS0; dsp += 8; }
static void vmor()      {/* or      */ DS1 |= DS0; dsp += 8; }
static void vmxor()     {/* xor     */ DS1 ^= DS0; dsp += 8; }
static void vmfromr()   {/* r>      */ PUSH(RS); rp += 8; }
static void vmtor()     {/* >r      */ RPUSH(DS0); dsp += 8; }
static void vmrfetch()  {/* r@      */ PUSH(RS); }
static void vmeq()      {/* =       */ DS1 = - (UNS64)(DS0 == DS1); dsp += 8; }
static void vmugt()     {/* u<      */ DS1 = - (UNS64)(DS1 < DS0); dsp += 8; }
static void vmgt()      {/* <       */ DS1 = - (UNS64)((INT64)DS1 < (INT64)DS0); dsp += 8; }
static void vmplus()    {/* +       */ DS1 += DS0; dsp += 8; }
static void vmnegate()  {/* negate  */ DS0 = - DS0; }
static void vmlshift()  {/* lshift  */ DS1 <<= DS0; dsp += 8; }
static void vmrshift()  {/* rshift  */ DS1 >>= DS0; dsp += 8; }
static void vmummult()  {/* um*     */ umul(&DS0, &DS1); }
static void vmumdiv()   {/* um/mod  */ udiv(&DS0, &DS1, &DS2); dsp += 8; }
static void vmdplus()   {/* d+      */ DS3 += DS1; DS2 += DS0; DS2 += (DS3 < DS1); dsp += 16; }

static void vmemit()    {/* emit    */
    UNS8 c = (UNS8)DS0;
    sys_write(1, &c, 1);
    dsp += 8;
}

static void vmkey()     {/* key     */
    UNS8 c;
    long n = sys_read(0, &c, 1);
    if (n <= 0) {
        /* Clean exit on stdin EOF (or a read error) instead of spinning
         * forever re-reading EOF - see GOALS.md / PROGRESS.md, Bug 3. */
        sys_exit_group(0);
    }
    PUSH((UNS64)c);
}

static void vmbye()     {/* bye     */ sys_exit_group(0); }
static void vmspfetch() {/* sp@     */ PUSH(dsp + 8); }
static void vmspstore() {/* sp!     */ dsp = DS0; }
static void vmrpfetch() {/* rp@     */ PUSH(rp); }
static void vmrpstore() {/* rp!     */ rp = DS0; dsp += 8; }

/*
 *  virtual machine I/O primitives
 */

static const long open_flags[6] = {
    0101000, /* w  : O_WRONLY|O_CREAT|O_TRUNC */
    0101000, /* wb : same, no text/binary distinction on Linux */
    0,       /* r  : O_RDONLY */
    0,       /* rb : O_RDONLY */
    02,      /* r+ : O_RDWR   */
    02       /* r+b: O_RDWR   */
};

static void vmopenfile() { /* c-addr u fam --- fid ior */
    long fd;
    t = BYTE(DS2 + DS1);
    BYTE(DS2 + DS1) = 0;
    swap_mem(DS2, DS1);
    fd = sys_open((char *)DS2, open_flags[DS0], 0644);
    swap_mem(DS2, DS1);
    BYTE(DS2 + DS1) = t;
    DS2 = (UNS64)fd;
    DS1 = (fd >= 0) ? 0 : 200;
    dsp += 8;
}

static void vmclosefile() { /* fid --- ior */
    DS0 = (UNS64)sys_close((long)DS0);
}

static void vmreadline() { /* c-addr u1 fid --- u2 flag ior */
    long fd = (long)DS0;
    UNS64 addr = DS2, max = DS1, count = 0;
    long n, err = 0, got_any = 0;
    UNS8 c;

    while (count < max) {
        n = sys_read(fd, &c, 1);
        if (n < 0) { err = 1; break; }
        if (n == 0) break;      /* EOF */
        got_any = 1;
        if (c == '\n') break;   /* line terminator, not stored */
        BYTE(addr + count) = c;
        count++;
    }
    /* Tolerate CRLF files: a trailing \r right before the \n we just
     * stopped at is a line terminator too, not payload. */
    if (count > 0 && BYTE(addr + count - 1) == '\r') count--;
    DS2 = count;
    DS1 = got_any ? (UNS64)-1 : 0;
    DS0 = err ? (UNS64)-200 : 0;
}

static void vmwriteline() { /* c-addr u fid --- ior */
    long fd = (long)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    swap_mem(addr, len);
    n = full_write(fd, (void*)addr, len);
    swap_mem(addr, len);
    if (n == (long)len) {
        n = full_write(fd, "\n", 1);
        DS2 = (n == 1) ? 0 : (UNS64)-200;
    } else {
        DS2 = (UNS64)-200;
    }
    dsp += 16;
}

static void vmreadfile() { /* c-addr u1 fid --- u2 ior */
    long fd = (long)DS0;
    UNS64 addr = DS2, maxlen = DS1;
    long n;

    swap_mem(addr, maxlen);
    n = full_read(fd, (void*)addr, maxlen);
    swap_mem(addr, maxlen);
    if (n < 0) {
        DS2 = 0;
        DS1 = (UNS64)-200;
    } else {
        DS2 = (UNS64)n;
        DS1 = 0;
    }
    dsp += 8;
}

static void vmwritefile() { /* c-addr u fid --- ior */
    long fd = (long)DS0;
    UNS64 addr = DS2, len = DS1;
    long n;

    swap_mem(addr, len);
    n = full_write(fd, (void*)addr, len);
    swap_mem(addr, len);
    DS2 = (n == (long)len) ? 0 : (UNS64)-200;
    dsp += 16;
}

static void vmsystem() { /* c-addr u --- ior */
    UNS64 addr = DS1, len = DS0;
    UNS8 saved;
    long pid, ior;
    int status = 0;
    char *argv[4];

    saved = BYTE(addr + len);
    BYTE(addr + len) = 0;
    swap_mem(addr, len);
    argv[0] = "/bin/sh";
    argv[1] = "-c";
    argv[2] = (char*)addr;
    argv[3] = 0;
    pid = sys_fork();
    if (pid == 0) {
        sys_execve("/bin/sh", argv, g_envp);
        sys_exit_group(127);
    }
    if (pid > 0) {
        sys_wait4(pid, &status, 0, 0);
        ior = (status >> 8) & 0xff;
    } else {
        ior = 200;
    }
    swap_mem(addr, len);
    BYTE(addr + len) = saved;
    DS1 = (UNS64)ior;
    dsp += 8;
}

static void vmreposfile() { /* offset fid --- ior */
    DS1 = (UNS64)sys_lseek((long)DS0, (long)DS1, 0 /* SEEK_SET */);
    dsp += 8;
}

static void vmfilepos() { /* fid --- u ior */
    DS0 = (UNS64)sys_lseek((long)DS0, 0, 1 /* SEEK_CUR */);
    dsp -= 8;
    if ((INT64)DS1 == -1) {
        DS0 = 200;
    } else {
        DS0 = 0;
    }
}

static void vmdelfile() { /* c-addr u --- ior */
    t = BYTE(DS1 + DS0);
    BYTE(DS1 + DS0) = 0;
    swap_mem(DS1, DS0);
    DS1 = (UNS64)sys_unlink((char*)DS1);
    swap_mem(DS1, DS0);
    BYTE(DS1 + DS0) = t;
    dsp += 8;
}

static void vmfilesize() { /* fid --- u ior */
    long fd = (long)DS0;
    long cur = sys_lseek(fd, 0, 1  /* SEEK_CUR */);
    long size = sys_lseek(fd, 0, 2 /* SEEK_END */);
    sys_lseek(fd, cur, 0 /* SEEK_SET */);
    DS0 = (UNS64)size;
    PUSH(0);
}

/*
 *  Virtual machine itself.
 */

typedef void (*vmop)(void);

static void virtual_machine(void) {
    static const vmop _vmops[] = {
        vmnoop, vmexit, vmlit, vmbranch, vm0branch, vmdrop,
        vmdup, vmswap, vmrot, vmover, vmcfetch, vmfetch, vmcstore, vmstore,
        vmand, vmor, vmxor, vmfromr, vmtor, vmrfetch, vmeq, vmugt, vmgt,
        vmplus, vmnegate, vmlshift, vmrshift, vmummult, vmumdiv, vmdplus,
        vmemit, vmkey, vmbye, vmspfetch, vmspstore, vmrpfetch, vmrpstore,
        vmopenfile, vmclosefile, vmreadline, vmwriteline, vmreadfile,
        vmwritefile, vmsystem, vmreposfile, vmfilepos, vmdelfile, vmfilesize
    };
    /* Primitive tokens are (index * sizeof(vmop)) + 1; sizeof(vmop) is 8
     * on x86-64, so cross.4's PRIMITIVE stride (8) must match this. */
    UNS64 vmops = (UNS64)_vmops - 1;

    while (1) {
        t = CELL(ip);
        ip += 8;
        if (t & 1) {
            (*(vmop*)(vmops + t))();
        } else {
            RPUSH(ip);
            ip += t;
        }
    }
}

/*
 *  This function reads binary forth image from file into memory.
 */

static void load_image(const char *name) {
    long fd, len;

    fd = sys_open(name, 0 /* O_RDONLY */, 0);
    if (fd < 0) {
        write_str(2, "Cannot open image file.\n");
        sys_exit_group(2);
    }
    base = (UNS8*)(((UNS64)mem + 7) & ~(UNS64)7);
    len = full_read(fd, base, MEMSIZE);
    sys_close(fd);
    if (len < 0) {
        write_str(2, "Error reading image file.\n");
        sys_exit_group(2);
    }
    swap_mem((UNS64)base, (UNS64)len);
}

/*
 *  Program entry point (called from _start below).
 */

long relf_main(long argc, char **argv, char **envp) {
    g_argv = argv;
    g_envp = envp;
    if (argc < 2) {
        write_str(2, "Usage: relf <filename>\n");
        return 1;
    }
    load_image(argv[1]);
    ip = (UNS64)base;
    rp = ip + MEMSIZE;
    dsp = ip + MEMSIZE - RSTACK_BYTES;
    PUSH(ip);
    virtual_machine();
    return 0; /* unreachable: virtual_machine() only leaves via BYE/EOF */
}

/*
 *  Raw process entry point: no crt0, no libc. Extracts argc/argv/envp
 *  from the initial stack layout the kernel sets up, aligns the stack,
 *  and calls relf_main(). See GOALS.md, phase 2.
 */

__asm__ (
    ".global _start\n"
    "_start:\n"
    "    xor %ebp, %ebp\n"
    "    mov (%rsp), %rdi\n"          /* argc            */
    "    lea 8(%rsp), %rsi\n"         /* argv            */
    "    lea 8(%rsi,%rdi,8), %rdx\n"  /* envp = argv+argc+1 */
    "    and $-16, %rsp\n"
    "    call relf_main\n"
    "    mov %eax, %edi\n"
    "    mov $231, %eax\n"            /* exit_group */
    "    syscall\n"
);

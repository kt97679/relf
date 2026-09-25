/*  relfasm64.S - the CV8 engine in x86-64 assembly, on raw Linux system
 *  calls, with no libc (ASM-ENGINE.md; GOALS.md "What comes next", item
 *  5). It runs the same images as cv8.c and must behave exactly as it
 *  does; cv8.c is the reference for every handler here.
 *
 *  Milestone 1 (Iteration 519): the core - loading, dispatch, calls and
 *  every opcode that is not an escaped primitive - and the few escaped
 *  ones the bare kernel needs to talk. The dispatch tables come from
 *  opcodes.tab (tools/gen-opcodes.sh --asm), with a stub for every
 *  handler not written yet, which names its opcode and exits 99.
 *
 *  Registers, for the life of the machine:
 *      r14  ip       r13  data-stack pointer (the second item)
 *      r12  tos      r15  return-stack pointer    rbx  the image base
 *  `syscall` clobbers only rax, rcx and r11, so none of them is saved.
 *
 *  The binary is as small as it can be made without changing what runs
 *  (Iteration 520, after kt97679/itsy-linux): no linker output to trim,
 *  but a hand-written ELF header and ONE program header - a single
 *  loadable segment, readable, writable and executable, whose memory
 *  size runs past its file size. The zero-filled tail holds the engine's
 *  variables and the machine's 16 MB, so there is no mmap, no section
 *  table, and no padding between sections.
 *
 *  Build (the Makefile does it):
 *      cc -c -o relfasm64.o relfasm64.S
 *      ld -Ttext=0x400000 --oformat binary -o relfasm64 relfasm64.o
 */
    .intel_syntax noprefix

    .equ MEMSIZE,      16*1024*1024
    .equ RSTACK_BYTES, 65536
    .equ PAGE,         4096
    .equ CELL,         8
    .equ LSAVE_MAX,    4096
    .equ CV8_VERSION,  6
    .equ FEATURES,     15            /* varcall varslot spec lit64 */

    .equ SYS_read,     0
    .equ SYS_write,    1
    .equ SYS_open,     2
    .equ SYS_close,    3
    .equ SYS_exit,     231           /* exit_group */
    .equ SYS_lseek,    8
    .equ SYS_mmap,     9
    .equ SYS_unlink,   87
    .equ SYS_execve,   59
    .equ SYS_stat,     4
    .equ SYS_lstat,    6
    .equ SYS_ioctl,    16
    .equ SYS_access,   21
    .equ SYS_pipe,     22
    .equ SYS_dup2,     33
    .equ SYS_getpid,   39
    .equ SYS_fork,     57
    .equ SYS_wait4,    61
    .equ SYS_kill,     62
    .equ SYS_fcntl,    72
    .equ SYS_getcwd,   79
    .equ SYS_umask,    95
    .equ SYS_setpgid,  109
    .equ SYS_getppid,  110
    .equ SYS_chdir,    80
    .equ SYS_rt_sigaction, 13
    .equ SYS_rt_sigreturn, 15
    .equ NSIG_FLAGS,   65
    .equ SYS_getdents64, 217
    .equ DIRBUF,       4096

/* ---- the stack, as cv8.c's macros ------------------------------------ */
    .macro NEXT
    movzx eax, byte ptr [r14]
    inc r14
    jmp qword ptr [dispatch256 + rax*8]
    .endm
    .macro PUSHT reg                 /* tos to memory, reg the new tos */
    sub r13, CELL
    mov [r13], r12
    mov r12, \reg
    .endm
    .macro POPT
    mov r12, [r13]
    add r13, CELL
    .endm
    .macro EXITNEXT                  /* the folded ;EXIT: return, then next */
    mov r14, [r15]
    add r15, CELL
    NEXT
    .endm
    .macro RPUSH reg
    sub r15, CELL
    mov [r15], \reg
    .endm
    /* SLOT: a variable's address from a 2- or 3-byte self-relative
     * operand at ip (cv8.c's SLOT()); result in rdx, ip past it. */
    .macro SLOT
    movzx eax, byte ptr [r14]
    test al, al
    js 1f
    shl eax, 8
    movzx ecx, byte ptr [r14+1]
    or eax, ecx
    shl eax, 17
    sar eax, 17                      /* 15 bits, signed */
    movsxd rdx, eax
    add rdx, r14
    add r14, 2
    jmp 2f
1:  and eax, 0x7F
    shl eax, 16
    movzx ecx, byte ptr [r14+1]
    shl ecx, 8
    or eax, ecx
    movzx ecx, byte ptr [r14+2]
    or eax, ecx
    shl eax, 9
    sar eax, 9                       /* 23 bits, signed */
    movsxd rdx, eax
    add rdx, r14
    add r14, 3
2:
    .endm
    .macro FLAG cc                   /* tos = -(NOS cc tos), pop one */
    xor eax, eax
    cmp [r13], r12
    set\cc al
    neg rax
    mov r12, rax
    add r13, CELL
    .endm

    .equ TEXTORG,      0x400000
    /* The segment's layout, fixed, and defined before any use: GAS picks
     * an instruction's form where it meets it, and in Intel syntax an
     * unknown symbol is taken for memory - so a variable defined after
     * the code that uses it assembled as a load from a wrong address.
     * The file must end below BSS_BASE, which the Makefile checks once
     * it is linked - a label difference is not final while assembling. */
    .equ BSS_BASE,     TEXTORG + 0x10000
    .equ argc_v,       BSS_BASE
    .equ argv_v,       BSS_BASE + 8
    .equ envp_v,       BSS_BASE + 16
    .equ argbase,      BSS_BASE + 24
    .equ lsave_sp,     BSS_BASE + 32
    .equ heap_top,     BSS_BASE + 40
    .equ heap_end,     BSS_BASE + 48
    .equ env_ptr,      BSS_BASE + 56     /* the environment: an array of */
    .equ env_n,        BSS_BASE + 64 + 64   /* NAME=value pointers, its */
    .equ env_cap,      BSS_BASE + 64 + 72   /* count and capacity */
    .equ hdr,          BSS_BASE + 64
    .equ lsave_stack,  BSS_BASE + 256
    .equ free_lists,   lsave_stack + LSAVE_MAX*CELL    /* 64 lists, by class */
    .equ HEAP_RESERVE, 0x40000000       /* 1 GB of address space, not memory */
    .equ scratch,      free_lists + 64*8   /* 256 bytes: a struct stat, a termios */
    .equ sig_flag,     scratch + 256       /* 65 bytes: which signals were caught */
    .equ VM_OFF,       0x20000          /* 64 KB-aligned */
    .equ VM_BASE,      TEXTORG + VM_OFF
    .equ MEM_SIZE,     VM_OFF + MEMSIZE

    .text
/* ---- the ELF header and the one program header ------------------------ */
ehdr:
    .byte 0x7F, 'E', 'L', 'F', 2, 1, 1, 0    /* 64-bit, little-endian, SysV */
    .quad 0
    .word 2                          /* e_type: an executable */
    .word 62                         /* e_machine: x86-64 */
    .long 1                          /* e_version */
    .quad _start                     /* e_entry */
    .quad phdr - ehdr                /* e_phoff */
    .quad 0                          /* e_shoff: no section table */
    .long 0                          /* e_flags */
    .word 64                         /* e_ehsize */
    .word 56                         /* e_phentsize */
    .word 1                          /* e_phnum */
    .word 64                         /* e_shentsize - 0 would do; `file` prefers it */
    .word 0                          /* e_shnum */
    .word 0                          /* e_shstrndx */
phdr:
    .long 1                          /* p_type: PT_LOAD */
    .long 7                          /* p_flags: read, write, execute */
    .quad 0                          /* p_offset: the file maps onto itself */
    .quad TEXTORG                    /* p_vaddr */
    .quad TEXTORG                    /* p_paddr */
    .quad FILE_SIZE                  /* p_filesz */
    .quad MEM_SIZE                   /* p_memsz: the tail is zero-filled */
    .quad 0x1000                     /* p_align */

m_usage:     .ascii "Usage: relfasm64 IMAGE [ARGUMENT...]\n"
    .equ m_usage_len, . - m_usage
m_open:      .ascii "Cannot open image file.\n"
    .equ m_open_len, . - m_open
m_magic:     .ascii "not a RelF image, or built for a different encoding or cell width.\n"
    .equ m_magic_len, . - m_magic
m_version:   .ascii "image is a different CV8 format version than this engine\n"
    .equ m_version_len, . - m_version
m_hdr:       .ascii "Truncated image header.\n"
    .equ m_hdr_len, . - m_hdr
m_unimpl:    .ascii "relfasm64: not written yet: "
    .equ m_unimpl_len, . - m_unimpl
m_badesc:    .ascii "relf: image uses an escaped primitive this engine does not have\n"
    .equ m_badesc_len, . - m_badesc
m_locals:    .ascii "relf: locals save stack overflow or underflow\n"
    .equ m_locals_len, . - m_locals
m_nl:        .ascii "\n"

/* ---- helpers, outside the machine ------------------------------------ */
/* die: write rsi/rdx to stderr, exit with edi */
die:
    push rdi
    mov edi, 2
    mov eax, SYS_write
    syscall
    pop rdi
    mov eax, SYS_exit
    syscall
/* read_all: read rdx bytes from fd edi into rsi; rax = bytes read */
read_all:
    push rbx
    xor ebx, ebx
1:  cmp rbx, rdx
    jae 2f
    push rdx
    push rsi
    push rdi
    sub rdx, rbx
    add rsi, rbx
    mov eax, SYS_read
    syscall
    pop rdi
    pop rsi
    pop rdx
    test rax, rax
    jle 2f
    add rbx, rax
    jmp 1b
2:  mov rax, rbx
    pop rbx
    ret
/* unimpl: rsi -> the stub's NUL-terminated name */
unimpl:
    mov r8, rsi
    xor ecx, ecx
1:  cmp byte ptr [r8 + rcx], 0
    je 2f
    inc rcx
    jmp 1b
2:  push rcx
    lea rsi, [rip + m_unimpl]
    mov edx, m_unimpl_len
    mov edi, 2
    mov eax, SYS_write
    syscall
    pop rdx
    mov rsi, r8
    mov edi, 2
    mov eax, SYS_write
    syscall
    lea rsi, [rip + m_nl]
    mov edx, 1
    mov edi, 99
    jmp die

/* ---- start: arguments, the image, the memory ------------------------- */
    .globl _start
_start:
    mov rax, [rsp]
    mov [argc_v], rax
    lea rcx, [rsp + 8]
    mov [argv_v], rcx
    lea rdx, [rcx + rax*8 + 8]
    mov [envp_v], rdx
    mov qword ptr [argbase], 2
    cmp rax, 2
    jae 1f
    lea rsi, [rip + m_usage]
    mov edx, m_usage_len
    mov edi, 1
    jmp die
1:  mov rdi, [rcx + 8]               /* argv[1], the image */
    xor esi, esi                     /* O_RDONLY */
    mov eax, SYS_open
    syscall
    test rax, rax
    jns 2f
    lea rsi, [rip + m_open]
    mov edx, m_open_len
    mov edi, 2
    jmp die
2:  mov rbp, rax                     /* the image's descriptor, until loaded */
    mov rdi, rbp
    lea rsi, [hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_magic
    /* 'C' 'V' '8' '0' 8, then 'L', the version, the features */
    cmp dword ptr [hdr], 0x30385643
    jne bad_magic
    cmp byte ptr [hdr + 4], CELL
    jne bad_magic
    cmp byte ptr [hdr + 6], CV8_VERSION
    jne bad_version
    movzx eax, byte ptr [hdr + 7]
    test eax, ~FEATURES
    jnz bad_magic
    /* the thread count and heads, then the DOES> tails: read and skipped */
    mov rdi, rbp
    lea rsi, [hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    mov r12, [hdr]             /* thread heads to skip */
3:  test r12, r12
    jz 4f
    mov rdi, rbp
    lea rsi, [hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    dec r12
    jmp 3b
4:  mov rdi, rbp
    lea rsi, [hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    mov r12, [hdr]
    add r12, r12                     /* two cells per tail */
5:  test r12, r12
    jz 6f
    mov rdi, rbp
    lea rsi, [hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    dec r12
    jmp 5b
    /* the memory: 16 MB, 64 KB-aligned, in the segment's zero-filled
     * tail - the kernel provided it when it loaded this file */
6:  mov ebx, VM_BASE                 /* the image base, for good */
    mov rdi, rbp
    mov rsi, rbx
    mov edx, MEMSIZE
    call read_all
    mov rdi, rbp
    mov eax, SYS_close
    syscall
    /* as cv8.c: ip at the base, the return stack at the top, the data
     * stack below the return stack and a guard page, the base on it */
    mov r14, rbx
    lea r15, [rbx + MEMSIZE]
    lea r13, [rbx + MEMSIZE - RSTACK_BYTES - PAGE - 2*CELL]
    mov [r13], rbx
    mov r12, [r13]
    add r13, CELL
    NEXT

bad_magic:
    lea rsi, [rip + m_magic]
    mov edx, m_magic_len
    mov edi, 2
    jmp die
bad_version:
    lea rsi, [rip + m_version]
    mov edx, m_version_len
    mov edi, 2
    jmp die
bad_hdr:
    lea rsi, [rip + m_hdr]
    mov edx, m_hdr_len
    mov edi, 2
    jmp die

/* ---- the machine ------------------------------------------------------ */
do_call:                             /* eax: the first byte, 0x80-0xFF */
    test al, 0x40
    jnz 1f
    and eax, 0x3F                    /* two bytes: 14 bits */
    shl eax, 8
    movzx ecx, byte ptr [r14]
    or eax, ecx
    inc r14
    jmp 2f
1:  and eax, 0x3F                    /* three bytes: 22 bits */
    shl eax, 16
    movzx ecx, byte ptr [r14]
    shl ecx, 8
    or eax, ecx
    movzx ecx, byte ptr [r14+1]
    or eax, ecx
    add r14, 2
2:  RPUSH r14
    lea r14, [rbx + rax]
    NEXT

L_noop:     NEXT
L_exit:     EXITNEXT
L_lit:      movzx eax, word ptr [r14]
            add r14, 2
            PUSHT rax
            NEXT
L_branch:   movsx rax, word ptr [r14]
            add r14, rax
            NEXT
L_0branch:  mov rax, r12
            POPT
            test rax, rax
            jz 1f
            add r14, 2
            NEXT
1:          movsx rax, word ptr [r14]
            add r14, rax
            NEXT
L_drop:     POPT
            NEXT
L_dup:      PUSHT r12
            NEXT
L_swap:     mov rax, [r13]
            mov [r13], r12
            mov r12, rax
            NEXT
L_rot:      mov rax, [r13 + CELL]
            mov rcx, [r13]
            mov [r13 + CELL], rcx
            mov [r13], r12
            mov r12, rax
            NEXT
L_over:     mov rax, [r13]
            PUSHT rax
            NEXT
L_cfetch:   movzx r12, byte ptr [r12]
            NEXT
L_fetch:    mov r12, [r12]
            NEXT
L_cstore:   mov al, [r13]
            mov [r12], al
            mov r12, [r13 + CELL]
            add r13, 2*CELL
            NEXT
L_store:    mov rax, [r13]
            mov [r12], rax
            mov r12, [r13 + CELL]
            add r13, 2*CELL
            NEXT
L_and:      and r12, [r13]
            add r13, CELL
            NEXT
L_or:       or r12, [r13]
            add r13, CELL
            NEXT
L_xor:      xor r12, [r13]
            add r13, CELL
            NEXT
L_fromr:    mov rax, [r15]
            add r15, CELL
            PUSHT rax
            NEXT
L_tor:      RPUSH r12
            POPT
            NEXT
L_rfetch:   mov rax, [r15]
            PUSHT rax
            NEXT
L_eq:       FLAG e
            NEXT
L_ult:      FLAG b
            NEXT
L_lt:       FLAG l
            NEXT
L_plus:     add r12, [r13]
            add r13, CELL
            NEXT
L_negate:   neg r12
            NEXT
L_lshift:   mov rcx, r12
            mov r12, [r13]
            shl r12, cl
            add r13, CELL
            NEXT
L_rshift:   mov rcx, r12
            mov r12, [r13]
            shr r12, cl
            add r13, CELL
            NEXT
L_ummult:   mov rax, [r13]           /* ( u1 u2 --- ud ): low under high */
            mul r12
            mov [r13], rax
            mov r12, rdx
            NEXT
L_umdiv:    mov rdx, [r13]           /* ( ud u --- rem quot ) */
            mov rax, [r13 + CELL]
            cmp rdx, r12
            jb 1f
            /* A quotient wider than a cell: cv8.c divides 128 bits and
             * truncates, where `div` would trap. Reducing the high half
             * first gives the same truncated quotient and remainder. */
            mov rax, rdx
            xor edx, edx
            div r12
            mov rax, [r13 + CELL]
1:          div r12
            mov [r13 + CELL], rdx
            mov r12, rax
            add r13, CELL
            NEXT
L_dplus:    mov rax, [r13]           /* ( d1 d2 --- d3 ) */
            add [r13 + 2*CELL], rax
            adc [r13 + CELL], r12
            mov r12, [r13 + CELL]
            add r13, 2*CELL
            NEXT
L_type:     mov rsi, [r13]           /* ( c-addr u --- ), unbuffered for now */
            mov rdx, r12
1:          test rdx, rdx
            jz 2f
            mov edi, 1
            mov eax, SYS_write
            push rsi
            push rdx
            syscall
            pop rdx
            pop rsi
            test rax, rax
            jle 2f
            add rsi, rax
            sub rdx, rax
            jmp 1b
2:          mov r12, [r13 + CELL]
            add r13, 2*CELL
            NEXT
L_spfetch:  lea rax, [r13 - CELL]     /* where the top item is about to be */
            PUSHT rax                /* stored: cv8.c's PUSH computes      */
            NEXT                     /* dsp + CELL after the decrement     */
L_spstore:  mov r13, r12
            POPT
            NEXT
L_rpfetch:  PUSHT r15
            NEXT
L_rpstore:  mov r15, r12
            POPT
            NEXT

/* the synthetic band */
L_lit32:    movsxd rax, dword ptr [r14]
            add r14, 4
            PUSHT rax
            NEXT
L_dovar:    lea rax, [r14 + 3 + CELL - 1]
            and rax, -CELL
            PUSHT rax
            EXITNEXT
L_dodoes:   movzx eax, byte ptr [r14]
            test al, 0x40
            jz 1f
            and eax, 0x3F
            shl eax, 16
            movzx ecx, byte ptr [r14+1]
            shl ecx, 8
            or eax, ecx
            movzx ecx, byte ptr [r14+2]
            or eax, ecx
            lea rcx, [r14 + 3 + CELL - 1]
            jmp 2f
1:          and eax, 0x3F
            shl eax, 8
            movzx ecx, byte ptr [r14+1]
            or eax, ecx
            lea rcx, [r14 + 2 + CELL - 1]
2:          and rcx, -CELL
            RPUSH rcx
            lea r14, [rbx + rax]
            NEXT
L_lit8:     movzx eax, byte ptr [r14]
            inc r14
            PUSHT rax
            NEXT
L_lit8x:    movzx eax, byte ptr [r14]
            PUSHT rax
            EXITNEXT

/* the folded band: a primitive, then EXIT */
LX_plus:    add r12, [r13]
            add r13, CELL
            EXITNEXT
LX_eq:      FLAG e
            EXITNEXT
LX_store:   mov rax, [r13]
            mov [r12], rax
            mov r12, [r13 + CELL]
            add r13, 2*CELL
            EXITNEXT
LX_fetch:   mov r12, [r12]
            EXITNEXT
LX_lshift:  mov rcx, r12
            mov r12, [r13]
            shl r12, cl
            add r13, CELL
            EXITNEXT
LX_rshift:  mov rcx, r12
            mov r12, [r13]
            shr r12, cl
            add r13, CELL
            EXITNEXT
LX_cfetch:  movzx r12, byte ptr [r12]
            EXITNEXT
LX_cstore:  mov al, [r13]
            mov [r12], al
            mov r12, [r13 + CELL]
            add r13, 2*CELL
            EXITNEXT
LX_and:     and r12, [r13]
            add r13, CELL
            EXITNEXT
LX_or:      or r12, [r13]
            add r13, CELL
            EXITNEXT
LX_xor:     xor r12, [r13]
            add r13, CELL
            EXITNEXT
LX_lit:     movzx eax, word ptr [r14]
            add r14, 2
            PUSHT rax
            EXITNEXT
LX_lt:      FLAG l
            EXITNEXT
LX_ult:     FLAG b
            EXITNEXT
LX_over:    mov rax, [r13]
            PUSHT rax
            EXITNEXT
LX_drop:    POPT
            EXITNEXT
LX_dup:     PUSHT r12
            EXITNEXT
LX_swap:    mov rax, [r13]
            mov [r13], r12
            mov r12, rax
            EXITNEXT
LX_rot:     mov rax, [r13 + CELL]
            mov rcx, [r13]
            mov [r13 + CELL], rcx
            mov [r13], r12
            mov r12, rax
            EXITNEXT
LX_tor:     RPUSH r12
            POPT
            EXITNEXT
LX_fromr:   mov rax, [r15]
            add r15, CELL
            PUSHT rax
            EXITNEXT
LX_rfetch:  mov rax, [r15]
            PUSHT rax
            EXITNEXT
LX_negate:  neg r12
            EXITNEXT

/* one-byte branches */
L_branch8:  movsx rax, byte ptr [r14]
            add r14, rax
            NEXT
L_0branch8: mov rax, r12
            POPT
            test rax, rax
            jz 1f
            inc r14
            NEXT
1:          movsx rax, byte ptr [r14]
            add r14, rax
            NEXT

/* the specialised band */
L_lit0:     xor eax, eax
            PUSHT rax
            NEXT
L_lit1:     mov eax, 1
            PUSHT rax
            NEXT
L_litm1:    mov rax, -1
            PUSHT rax
            NEXT
L_vf:       SLOT
            mov rax, [rdx]
            PUSHT rax
            NEXT
L_vs:       SLOT
            mov [rdx], r12
            POPT
            NEXT
L_lsave:    SLOT
            mov rcx, [lsave_sp]
            cmp rcx, LSAVE_MAX
            jae 1f
            mov rax, [rdx]
            lea r8, [lsave_stack]
            mov [r8 + rcx*8], rax
            inc rcx
            mov [lsave_sp], rcx
            NEXT
1:          mov eax, 1
            PUSHT rax
            jmp locals_failed
L_lrest:    SLOT
            mov rcx, [lsave_sp]
            test rcx, rcx
            jle 1f
            dec rcx
            mov [lsave_sp], rcx
            lea r8, [lsave_stack]
            mov rax, [r8 + rcx*8]
            mov [rdx], rax
            NEXT
1:          mov eax, 2
            PUSHT rax
            jmp locals_failed
locals_failed:
            mov rax, [rbx + 8]
            test rax, rax
            jnz 1f
            lea rsi, [rip + m_locals]
            mov edx, m_locals_len
            mov edi, 70
            jmp die
1:          RPUSH r14
            lea r14, [rbx + rax]
            NEXT
L_lstore:   SLOT
            mov [rdx], r12
            POPT
            NEXT
L_lzero:    SLOT
            mov qword ptr [rdx], 0
            NEXT
L_zeq:      xor eax, eax
            test r12, r12
            sete al
            neg rax
            mov r12, rax
            NEXT
L_sub:      mov rax, [r13]
            sub rax, r12
            mov r12, rax
            add r13, CELL
            NEXT
L_ne:       FLAG ne
            NEXT
L_zlt:      sar r12, 63
            NEXT
L_sgt:      FLAG g
            NEXT
L_2dup:     mov rax, [r13]
            sub r13, 2*CELL
            mov [r13 + CELL], r12
            mov [r13], rax
            NEXT
L_2drop:    mov r12, [r13 + CELL]
            add r13, 2*CELL
            NEXT
L_charp:
L_onep:     inc r12
            NEXT
L_cellp:    add r12, CELL
            NEXT
L_cells:    shl r12, 3
            NEXT
L_onem:     dec r12
            NEXT
L_invert:   not r12
            NEXT
L_count:    movzx eax, byte ptr [r12]
            inc r12
            PUSHT rax
            NEXT
L_aligned:  add r12, CELL - 1
            and r12, -CELL
            NEXT
L_addi:     movsx rax, byte ptr [r14]
            inc r14
            add r12, rax
            NEXT
L_addix:    movsx rax, byte ptr [r14]
            add r12, rax
            EXITNEXT
L_eqi:      movsx rcx, byte ptr [r14]
            inc r14
            xor eax, eax
            cmp r12, rcx
            sete al
            neg rax
            mov r12, rax
            NEXT
L_eqix:     movsx rcx, byte ptr [r14]
            xor eax, eax
            cmp r12, rcx
            sete al
            neg rax
            mov r12, rax
            EXITNEXT
L_lit64:    mov rax, [r14]
            add r14, CELL
            PUSHT rax
            NEXT
L_esc:      movzx eax, byte ptr [r14]
            inc r14
            jmp qword ptr [esc_tab + rax*8]
L_badesc:   lea rsi, [rip + m_badesc]
            mov edx, m_badesc_len
            mov edi, 2
            jmp die

/* ---- the escaped primitives, as far as Milestone 1 goes --------------- */
L_bye:      xor edi, edi
            mov eax, SYS_exit
            syscall
L_sysexit:  mov rdi, r12
            mov eax, SYS_exit
            syscall
L_read:     mov rdi, r12             /* ( c-addr u fd --- n ), n < 0 is -errno */
            mov rdx, [r13]
            mov rsi, [r13 + CELL]
            mov eax, SYS_read
            syscall
            mov r12, rax
            add r13, 2*CELL
            NEXT
L_write:    mov rdi, r12
            mov rdx, [r13]
            mov rsi, [r13 + CELL]
            mov eax, SYS_write
            syscall
            mov r12, rax
            add r13, 2*CELL
            NEXT
L_sysargc:  mov rax, [argc_v]  /* ( --- n ): the program's arguments */
            sub rax, [argbase]
            jge 1f
            xor eax, eax
1:          PUSHT rax
            NEXT
L_sysarg:   mov rax, r12             /* ( n --- c-addr ), 0 past the end */
            add rax, [argbase]
            test r12, r12
            js 1f
            cmp rax, [argc_v]
            jae 1f
            mov rcx, [argv_v]
            mov r12, [rcx + rax*8]
            NEXT
1:          xor r12d, r12d
            NEXT

/* the memory primitives (cv8.c: memmove, memset, memcmp, memchr, strlen) */
L_move:     mov rcx, r12             /* ( c-addr1 c-addr2 u --- ), overlap-safe */
            mov rdi, [r13]
            mov rsi, [r13 + CELL]
            test rcx, rcx
            jz 2f
            cmp rdi, rsi
            jbe 1f                   /* destination below the source: forwards */
            lea rax, [rsi + rcx]
            cmp rdi, rax
            jae 1f                   /* no overlap: forwards */
            lea rsi, [rsi + rcx - 1] /* overlapping from above: backwards */
            lea rdi, [rdi + rcx - 1]
            std
            rep movsb
            cld
            jmp 2f
1:          rep movsb
2:          mov r12, [r13 + 2*CELL]
            add r13, 3*CELL
            NEXT
L_fill:     mov rax, r12             /* ( c-addr u c --- ) */
            mov rcx, [r13]
            mov rdi, [r13 + CELL]
            rep stosb
            mov r12, [r13 + 2*CELL]
            add r13, 3*CELL
            NEXT
L_compare:  mov rsi, [r13 + 2*CELL]  /* ( c-addr1 u1 c-addr2 u2 --- -1|0|1 ) */
            mov rdi, [r13]
            mov rcx, [r13 + CELL]    /* u1 */
            cmp rcx, r12
            cmova rcx, r12           /* min(u1, u2) */
            test rcx, rcx
            jz 3f
            repe cmpsb
            ja 1f                    /* the first difference decides */
            jb 2f
3:          mov rax, [r13 + CELL]    /* equal so far: the shorter is less */
            cmp rax, r12
            ja 1f
            jb 2f
            xor r12d, r12d
            jmp 4f
1:          mov r12, 1
            jmp 4f
2:          mov r12, -1
4:          add r13, 3*CELL
            NEXT
L_scan:     mov rdi, [r13 + CELL]    /* ( c-addr1 u1 c --- c-addr2 u2 ) */
            mov rcx, [r13]
            mov rax, r12
            lea r8, [rdi + rcx]      /* the end */
            test rcx, rcx
            jz 1f
            repne scasb
            jne 1f
            dec rdi                  /* found: from it to the end */
            mov [r13 + CELL], rdi
            mov r12, r8
            sub r12, rdi
            add r13, CELL
            NEXT
1:          mov [r13 + CELL], r8     /* not found: the end, and 0 */
            xor r12d, r12d
            add r13, CELL
            NEXT
L_cstrlen:  mov rdi, r12             /* ( c-addr --- u ) */
            xor eax, eax
            mov rcx, -1
            repne scasb
            not rcx
            dec rcx
            mov r12, rcx
            NEXT

/* the file primitives (Milestone 2): cv8.c's stack effects and ior
 * values exactly - 200 where cv8.c says 200, and where it passes on
 * libc's -1, -1, which the raw system calls' -errno is mapped to */
    .balign 4
open_modes:                          /* cv8.c's open_flags[], by fam */
    .long 577, 577                   /* w w/b   O_WRONLY|O_CREAT|O_TRUNC */
    .long 0, 0                       /* r r/b   O_RDONLY */
    .long 2, 2                       /* r+ r+b  O_RDWR */
    .long 1089, 1089                 /* a a/b   O_WRONLY|O_CREAT|O_APPEND */
    .long 578, 578                   /* w+ w+b  O_RDWR|O_CREAT|O_TRUNC */
    .long 193                        /* x       O_WRONLY|O_CREAT|O_EXCL */
    .equ NOPENMODES, 11
L_openfile: mov rdi, [r13 + CELL]    /* ( c-addr u fam --- fid ior ) */
            mov rcx, [r13]
            lea r8, [rdi + rcx]      /* the byte after the name: NUL for */
            movzx r9d, byte ptr [r8] /* the call, then put back */
            mov byte ptr [r8], 0
            mov rax, -1
            cmp r12, NOPENMODES
            jae 1f
            mov esi, dword ptr [open_modes + r12*4]
            mov edx, 420             /* 0644 */
            mov eax, SYS_open
            syscall
1:          mov [r8], r9b
            add r13, CELL
            test rax, rax
            js 2f
            mov [r13], rax
            xor r12d, r12d
            NEXT
2:          mov qword ptr [r13], -1
            mov r12d, 200
            NEXT
L_closefile: mov rdi, r12            /* ( fid --- ior ): 0, or libc's -1 */
            mov eax, SYS_close
            syscall
            mov r12, rax
            sar r12, 63
            NEXT
L_delfile:  mov rdi, [r13]           /* ( c-addr u --- ior ): 0, or -1 */
            lea r8, [rdi + r12]
            movzx r9d, byte ptr [r8]
            mov byte ptr [r8], 0
            mov eax, SYS_unlink
            syscall
            mov [r8], r9b
            mov r12, rax
            sar r12, 63
            add r13, CELL
            NEXT
L_reposfile: mov rdi, r12            /* ( ud fid --- ior ) */
            mov rsi, [r13 + CELL]    /* the low cell; a 64-bit offset */
            xor edx, edx             /* SEEK_SET */
            mov eax, SYS_lseek
            syscall
            add r13, 2*CELL
            xor r12d, r12d
            test rax, rax
            jns 1f
            mov r12d, 200
1:          NEXT
L_filepos:  mov rdi, r12             /* ( fid --- ud ior ) */
            xor esi, esi
            mov edx, 1               /* SEEK_CUR */
            mov eax, SYS_lseek
            syscall
            jmp ud_ior
L_filesize: mov rdi, r12             /* ( fid --- ud ior ): the end, the */
            push rdi                 /* position put back as it was */
            xor esi, esi
            mov edx, 1
            mov eax, SYS_lseek
            syscall
            pop rdi
            test rax, rax
            js ud_ior
            push rax                 /* where it was */
            push rdi
            xor esi, esi
            mov edx, 2               /* SEEK_END */
            mov eax, SYS_lseek
            syscall
            pop rdi
            pop rsi
            push rax                 /* the size */
            xor edx, edx
            mov eax, SYS_lseek
            syscall
            pop rax
ud_ior:     sub r13, 2*CELL          /* rax: an offset, or -errno */
            test rax, rax
            js 1f
            mov [r13 + CELL], rax    /* ud: low, then high - 0 at 64 bits */
            mov qword ptr [r13], 0
            xor r12d, r12d
            NEXT
1:          mov qword ptr [r13 + CELL], 0
            mov qword ptr [r13], 0
            mov r12d, 200
            NEXT

/* the allocator (cv8.c: malloc, free, realloc). Power-of-two classes
 * from 32 bytes: a block is a 16-byte header - its class, and the free
 * list's link - then what was asked for, 16-byte aligned as malloc's.
 * Freed blocks go on their class's list and are the next of that class
 * handed out; new ones come from one reservation of address space,
 * MAP_NORESERVE, whose pages cost nothing until touched. RESIZE keeps a
 * block while the new size still fits its class - the shell's buffers
 * grow by doubling. One difference from glibc, on purpose: realloc(p, 0)
 * frees p and returns NULL there, so cv8.c reports failure with the
 * block gone; here the block is kept. */
alloc_block:                         /* rdi bytes -> rax pointer, or 0 */
            lea rcx, [rdi + 16]
            mov eax, 5
            cmp rcx, 32
            jbe 1f
            dec rcx
            bsr rax, rcx
            inc eax                  /* the smallest 2^k that holds it */
1:          cmp eax, 30
            ja 9f
            lea r8, [free_lists + rax*8]
            mov rdx, [r8]
            test rdx, rdx
            jz 2f
            mov rcx, [rdx + 8]       /* one of this class, given back before */
            mov [r8], rcx
            jmp 3f
2:          mov rdx, [heap_top]
            test rdx, rdx
            jnz 4f
            push rax
            call heap_init
            pop rax
            mov rdx, [heap_top]
            test rdx, rdx
            jz 9f
4:          mov ecx, eax
            mov r9d, 1
            shl r9, cl
            lea r10, [rdx + r9]
            cmp r10, [heap_end]
            ja 9f
            mov [heap_top], r10
3:          mov [rdx], rax           /* the class, in the header */
            lea rax, [rdx + 16]
            ret
9:          xor eax, eax
            ret
heap_init:                           /* the reservation, at first use */
            xor edi, edi
            mov esi, HEAP_RESERVE
            mov edx, 3               /* PROT_READ | PROT_WRITE */
            mov r10d, 0x4022         /* MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE */
            mov r8, -1
            xor r9d, r9d
            mov eax, SYS_mmap
            syscall
            cmp rax, -4096
            jae 1f
            mov [heap_top], rax
            add rax, HEAP_RESERVE
            mov [heap_end], rax
1:          ret
free_block:                          /* rdi: a pointer from alloc_block, or 0 */
            test rdi, rdi
            jz 1f
            lea rdx, [rdi - 16]
            mov rax, [rdx]
            lea r8, [free_lists + rax*8]
            mov rcx, [r8]
            mov [rdx + 8], rcx
            mov [r8], rdx
1:          ret
L_allocate: mov rdi, r12             /* ( u --- a-addr ior ) */
            call alloc_block
            sub r13, CELL
            mov [r13], rax
            xor r12d, r12d
            test rax, rax
            jnz 1f
            mov r12d, 201
1:          NEXT
L_free:     mov rdi, r12             /* ( a-addr --- ior ): always 0 */
            call free_block
            xor r12d, r12d
            NEXT
L_resize:   mov rdi, [r13]           /* ( a-addr u --- a-addr' ior ) */
            test rdi, rdi
            jz 5f
            mov rax, [rdi - 16]
            mov ecx, eax
            mov r9d, 1
            shl r9, cl
            sub r9, 16               /* what the block holds */
            cmp r12, r9
            jbe 4f                   /* still fits: the same block */
            push r9
            push rdi
            mov rdi, r12
            call alloc_block
            pop rsi
            pop rcx
            test rax, rax
            jz 6f
            push rax
            mov rdi, rax
            push rsi
            rep movsb                /* the old block's contents */
            pop rdi
            call free_block
            pop rax
            mov [r13], rax
4:          xor r12d, r12d
            NEXT
5:          mov rdi, r12             /* realloc(NULL, u) is malloc(u) */
            call alloc_block
            mov [r13], rax
            xor r12d, r12d
            test rax, rax
            jnz 7f
6:          mov r12d, 202            /* failed: the old block stays, valid */
7:          NEXT

/* the environment (decided at 514: kept by the engine, as libc keeps it,
 * so the two engines stay interchangeable): an array of NAME=value
 * pointers, made from envp at first use and passed by EXECVE */
env_init:                            /* the array, if there is none yet */
            cmp qword ptr [env_ptr], 0
            jne 9f
            mov rsi, [envp_v]
            xor ecx, ecx
1:          cmp qword ptr [rsi + rcx*8], 0
            je 2f
            inc rcx
            jmp 1b
2:          mov [env_n], rcx
            lea rdi, [rcx + 16]
            mov [env_cap], rdi
            shl rdi, 3
            add rdi, 8
            call alloc_block
            mov [env_ptr], rax
            mov rdi, rax
            mov rsi, [envp_v]
            mov rcx, [env_n]
            inc rcx                  /* and its NULL */
            rep movsq
9:          ret
env_find:                            /* rdi: a name -> rax its index or -1, rdx its value */
            push rbx
            mov r8, [env_ptr]
            xor r9d, r9d
1:          cmp r9, [env_n]
            jae 8f
            mov rsi, [r8 + r9*8]
            xor ecx, ecx
2:          mov al, [rdi + rcx]
            test al, al
            jz 3f
            cmp al, [rsi + rcx]
            jne 4f
            inc rcx
            jmp 2b
3:          cmp byte ptr [rsi + rcx], '='
            jne 4f
            lea rdx, [rsi + rcx + 1]
            mov rax, r9
            pop rbx
            ret
4:          inc r9
            jmp 1b
8:          mov rax, -1
            xor edx, edx
            pop rbx
            ret
env_badname:                         /* rdi: a name -> ZF clear if it is not */
            cmp byte ptr [rdi], 0    /* one setenv accepts: empty, or with = */
            je 1f
            mov rsi, rdi
2:          mov al, [rsi]
            test al, al
            jz 3f
            cmp al, '='
            je 1f
            inc rsi
            jmp 2b
3:          xor eax, eax             /* ZF set: a good name */
            ret
1:          or eax, 1                /* ZF clear */
            ret
L_getenv:   call env_init            /* ( c-addr --- addr|0 ) */
            mov rdi, r12
            call env_find
            mov r12, rdx
            NEXT
L_envat:    call env_init            /* ( i --- c-addr|0 ) */
            xor eax, eax
            cmp r12, [env_n]
            jae 1f
            mov rcx, [env_ptr]
            mov rax, [rcx + r12*8]
1:          mov r12, rax
            NEXT
L_unsetenv: call env_init            /* ( c-addr --- ior ) */
            mov rdi, r12
            call env_badname
            jnz 8f
1:          mov rdi, r12
            call env_find            /* every entry of that name */
            test rax, rax
            js 7f
            mov rcx, [env_ptr]       /* shift the rest down, the NULL too */
            mov rdx, [env_n]
2:          mov r8, [rcx + rax*8 + 8]
            mov [rcx + rax*8], r8
            inc rax
            cmp rax, rdx
            jb 2b
            dec qword ptr [env_n]
            jmp 1b
7:          xor r12d, r12d
            NEXT
8:          mov r12d, 200
            NEXT
L_setenv:   call env_init            /* ( value-addr name-addr --- ior ) */
            mov rdi, r12
            call env_badname
            jnz 8f
            mov rdi, r12             /* name=value, on the heap */
            call strlen_rdi
            mov r10, rax
            mov rdi, [r13]
            call strlen_rdi
            lea rdi, [r10 + rax + 2]
            push rax
            push r10
            call alloc_block
            pop r10
            pop r11
            test rax, rax
            jz 8f
            mov rdi, rax
            mov rsi, r12
            mov rcx, r10
            rep movsb
            mov byte ptr [rdi], '='
            inc rdi
            mov rsi, [r13]
            lea rcx, [r11 + 1]       /* the value and its NUL */
            rep movsb
            push rax
            mov rdi, r12
            call env_find
            pop r9                   /* the new string */
            test rax, rax
            js 2f
            mov rcx, [env_ptr]       /* replace the old one */
            mov [rcx + rax*8], r9
            jmp 7f
2:          mov rax, [env_n]         /* append: grow first if full */
            inc rax
            cmp rax, [env_cap]
            jb 3f
            push r9
            mov rdi, [env_cap]
            shl rdi, 4               /* twice the capacity, in bytes */
            add rdi, 8
            call alloc_block
            pop r9
            test rax, rax
            jz 8f
            mov rdi, rax
            mov rsi, [env_ptr]
            mov rcx, [env_n]
            inc rcx
            rep movsq
            mov rdi, [env_ptr]
            mov [env_ptr], rax
            push r9
            call free_block
            pop r9
            shl qword ptr [env_cap], 1
3:          mov rcx, [env_ptr]
            mov rax, [env_n]
            mov [rcx + rax*8], r9
            inc rax
            mov [env_n], rax
            mov qword ptr [rcx + rax*8], 0
7:          add r13, CELL
            xor r12d, r12d
            NEXT
8:          add r13, CELL
            mov r12d, 200
            NEXT
strlen_rdi:                          /* rdi: a NUL-terminated string -> rax */
            xor eax, eax
1:          cmp byte ptr [rdi + rax], 0
            je 2f
            inc rax
            jmp 1b
2:          ret
L_execve:   call env_init            /* ( argv-addr path-addr --- ior ): -errno */
            mov rdi, r12
            mov rsi, [r13]
            mov rdx, [env_ptr]
            mov eax, SYS_execve
            syscall
            mov r12, rax
            add r13, CELL
            NEXT

/* processes and descriptors (Milestone 3), each with cv8.c's result:
 * -errno where cv8.c gives -errno, 200 or -1 where it gives those */
    .macro SYSCALL1 nr               /* one argument from tos, result to tos */
    mov rdi, r12
    mov eax, \nr
    syscall
    mov r12, rax
    .endm
L_getpid:   mov eax, SYS_getpid
            syscall
            PUSHT rax
            NEXT
L_getppid:  mov eax, SYS_getppid
            syscall
            PUSHT rax
            NEXT
L_isatty:   mov rdi, r12             /* ( fd --- flag ): what isatty(3) asks */
            mov esi, 0x5401          /* TCGETS */
            lea rdx, [scratch]
            mov eax, SYS_ioctl
            syscall
            xor r12d, r12d
            test rax, rax
            jnz 1f
            not r12
1:          NEXT
L_getcwd:   mov rdi, [r13]           /* ( addr max --- len ior ) */
            mov rsi, r12
            mov eax, SYS_getcwd
            syscall
            test rax, rax
            jle 1f
            dec rax                  /* the kernel counts the NUL */
            mov [r13], rax
            xor r12d, r12d
            NEXT
1:          mov qword ptr [r13], 0
            mov r12d, 200
            NEXT
L_umask:    SYSCALL1 SYS_umask       /* ( mask --- old ) */
            NEXT
L_access:   mov rdi, [r13]           /* ( c-addr mode --- ior ): 0 or -errno */
            mov rsi, r12
            mov eax, SYS_access
            syscall
            mov r12, rax
            add r13, CELL
            NEXT
L_kill:     mov rdi, [r13]           /* ( pid sig --- ior ): 0 or -errno */
            mov rsi, r12
            mov eax, SYS_kill
            syscall
            mov r12, rax
            add r13, CELL
            NEXT
L_setpgid:  mov rdi, [r13]           /* ( pid pgid --- ior ): 0 or -errno */
            mov rsi, r12
            mov eax, SYS_setpgid
            syscall
            mov r12, rax
            add r13, CELL
            NEXT
L_pipe:     lea rdi, [scratch]       /* ( --- fd-read fd-write ior ) */
            mov eax, SYS_pipe
            syscall
            sub r13, 3*CELL
            mov [r13 + 2*CELL], r12
            test rax, rax
            js 1f
            movsxd rax, dword ptr [scratch]
            mov [r13 + CELL], rax
            movsxd rax, dword ptr [scratch + 4]
            mov [r13], rax
            xor r12d, r12d
            NEXT
1:          mov qword ptr [r13 + CELL], 0
            mov qword ptr [r13], 0
            mov r12d, 200
            NEXT
L_dup2:     mov rdi, [r13]           /* ( oldfd newfd --- ior ): 0 or 200 */
            mov rsi, r12
            mov eax, SYS_dup2
            syscall
            add r13, CELL
            xor r12d, r12d
            test rax, rax
            jns 1f
            mov r12d, 200
1:          NEXT
L_dupfrom:  mov rdi, [r13]           /* ( fd floor --- fd' | -1 ) */
            mov edx, r12d
            mov esi, 1030            /* F_DUPFD_CLOEXEC */
            mov eax, SYS_fcntl
            syscall
            add r13, CELL
            mov r12, rax
            test rax, rax
            jns 1f
            mov r12, -1
1:          NEXT
L_fork:     mov eax, SYS_fork        /* ( --- pid ): -1 if it failed */
            syscall
            test rax, rax
            jns 1f
            mov rax, -1
1:          PUSHT rax
            NEXT
L_waitpid:  mov rdi, r12             /* ( pid --- status ior ) */
            lea rsi, [scratch]
            mov dword ptr [rsi], 0
            xor edx, edx
            xor r10d, r10d
            mov eax, SYS_wait4
            syscall
            sub r13, CELL
            test rax, rax
            js 1f
            movsxd rax, dword ptr [scratch]
            mov [r13], rax
            xor r12d, r12d
            NEXT
1:          mov qword ptr [r13], -1
            mov r12d, 200
            NEXT
L_waitnohang: mov rdi, -1            /* ( --- pid status ): 0 0 if none has ended */
            lea rsi, [scratch]
            mov dword ptr [rsi], 0
            mov edx, 1               /* WNOHANG */
            xor r10d, r10d
            mov eax, SYS_wait4
            syscall
            sub r13, 2*CELL
            mov [r13 + CELL], r12
            test rax, rax
            jle 1f
            mov [r13], rax
            mov r12d, dword ptr [scratch]
            NEXT
1:          mov qword ptr [r13], 0
            xor r12d, r12d
            NEXT
L_filekind: mov rdi, r12             /* ( c-addr --- 0 none, 1 file, 2 dir, 3 other ) */
            lea rsi, [scratch]
            mov eax, SYS_stat
            syscall
            xor r12d, r12d
            test rax, rax
            jnz 1f
            mov eax, dword ptr [scratch + 24]   /* st_mode */
            and eax, 0xF000
            mov r12d, 3
            cmp eax, 0x8000
            jne 2f
            mov r12d, 1
2:          cmp eax, 0x4000
            jne 1f
            mov r12d, 2
1:          NEXT
L_filemode: mov rdi, [r13]           /* ( c-addr follow? --- st_mode | 0 ) */
            lea rsi, [scratch]
            mov eax, SYS_lstat
            test r12, r12
            jz 1f
            mov eax, SYS_stat
1:          syscall
            add r13, CELL
            xor r12d, r12d
            test rax, rax
            jnz 2f
            mov r12d, dword ptr [scratch + 24]
2:          NEXT

/* signals (cv8.c: sig_catch, SIGACTION, SIGNALS-PENDING). A caught
 * signal only sets its flag; the shell asks between commands. With no
 * libc the restorer is ours: x86-64 Linux requires SA_RESTORER, a stub
 * the handler returns to that calls rt_sigreturn - which then restores
 * every register the signal found, so the handler may use any. */
sig_catch:                           /* edi: the signal */
            cmp edi, 0
            jle 1f
            cmp edi, NSIG_FLAGS
            jge 1f
            mov byte ptr [sig_flag + rdi], 1
1:          ret
sig_restorer:
            mov eax, SYS_rt_sigreturn
            syscall
L_sigaction: mov rdi, [r13]          /* ( signo action --- ior ): 0 default, */
            add r13, CELL            /* 1 ignore, 2 catch, 3 catch without */
            cmp rdi, 0               /* SA_RESTART; 0 or -errno */
            jle 8f
            cmp rdi, NSIG_FLAGS
            jge 8f
            cmp rdi, 11              /* SIGSEGV */
            je 8f
            cmp rdi, 7               /* SIGBUS */
            je 8f
            cmp rdi, 9               /* SIGKILL */
            je 8f
            cmp rdi, 19              /* SIGSTOP */
            je 8f
            lea rsi, [scratch]       /* struct kernel_sigaction: handler, */
            xor eax, eax             /* flags, restorer, mask */
            cmp r12, 1
            jne 1f
            mov eax, 1               /* SIG_IGN */
1:          cmp r12, 2
            jb 2f
            lea rax, [sig_catch]
2:          mov [rsi], rax
            mov eax, 0x14000000      /* SA_RESTART | SA_RESTORER */
            cmp r12, 3
            jne 3f
            mov eax, 0x04000000      /* SA_RESTORER only */
3:          mov [rsi + 8], rax
            lea rax, [sig_restorer]
            mov [rsi + 16], rax
            mov qword ptr [rsi + 24], 0
            mov byte ptr [sig_flag + rdi], 0
            xor edx, edx
            mov r10d, 8              /* sizeof the kernel's sigset */
            mov eax, SYS_rt_sigaction
            syscall
            mov r12, rax
            NEXT
8:          mov r12, -22             /* -EINVAL */
            NEXT
L_sigpending: xor eax, eax           /* ( --- signo | 0 ): the lowest caught, */
            mov ecx, 1               /* now cleared */
1:          cmp ecx, NSIG_FLAGS
            jge 2f
            cmp byte ptr [sig_flag + rcx], 0
            jne 3f
            inc ecx
            jmp 1b
3:          mov byte ptr [sig_flag + rcx], 0
            mov eax, ecx
2:          PUSHT rax
            NEXT

/* directories (cv8.c: opendir, readdir, closedir): a handle is a heap
 * block - the descriptor, a read position, the end of what was read,
 * then a buffer of getdents64 entries whose names are handed out in
 * place, as readdir hands out d_name */
L_opendir:  mov rdi, r12             /* ( c-addr --- dirp | 0 ) */
            mov esi, 0x90000         /* O_RDONLY | O_DIRECTORY | O_CLOEXEC */
            mov eax, SYS_open
            syscall
            test rax, rax
            js 8f
            push rax
            mov edi, 24 + DIRBUF
            call alloc_block
            pop rdi
            test rax, rax
            jz 7f
            mov [rax], rdi
            mov qword ptr [rax + 8], 0
            mov qword ptr [rax + 16], 0
            mov r12, rax
            NEXT
7:          mov eax, SYS_close       /* no memory: give the descriptor back */
            syscall
8:          xor r12d, r12d
            NEXT
L_readdir:  mov r8, r12              /* ( dirp --- c-addr | 0 ) */
            mov rax, [r8 + 8]
            cmp rax, [r8 + 16]
            jb 2f
            mov rdi, [r8]            /* the buffer is used up: read more */
            lea rsi, [r8 + 24]
            mov edx, DIRBUF
            mov eax, SYS_getdents64
            syscall
            test rax, rax
            jle 8f
            mov [r8 + 16], rax
            xor eax, eax
            mov [r8 + 8], rax
2:          lea rcx, [r8 + 24 + rax] /* struct linux_dirent64 */
            movzx edx, word ptr [rcx + 16]   /* d_reclen */
            add rax, rdx
            mov [r8 + 8], rax
            lea r12, [rcx + 19]      /* d_name */
            NEXT
8:          xor r12d, r12d
            NEXT
L_closedir: mov rdi, [r12]           /* ( dirp --- ) */
            mov eax, SYS_close
            syscall
            mov rdi, r12
            call free_block
            POPT
            NEXT

L_chdir:    mov rdi, r12             /* ( c-addr --- ior ): 0 or 200 */
            mov eax, SYS_chdir
            syscall
            xor r12d, r12d
            test rax, rax
            jns 1f
            mov r12d, 200
1:          NEXT
L_waitjob:  mov rdi, r12             /* ( pid --- pid' raw ): waits, a stop */
            lea rsi, [scratch]       /* reported too (WUNTRACED); pid' is */
            mov dword ptr [rsi], 0   /* -1 if the wait failed */
            mov edx, 2               /* WUNTRACED */
            xor r10d, r10d
            mov eax, SYS_wait4
            syscall
            test rax, rax
            jg 1f
            mov rax, -1
1:          mov r12, rax
            mov eax, dword ptr [scratch]
            PUSHT rax
            NEXT

#include "relfasm-ops.S"

/* ---- the end of the file, and the zero-filled tail after it ----------- */
file_end:
    .equ FILE_SIZE,  file_end - ehdr   /* under 64 KB: the Makefile checks */
    .if 256 + LSAVE_MAX*CELL + 64*8 + 256 + 72 > VM_OFF - (BSS_BASE - TEXTORG)
    .error "the variables no longer fit below the machine's memory"
    .endif

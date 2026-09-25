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
 *  Build:  cc -nostdlib -static -no-pie -o relfasm64 relfasm64.S
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
    .equ SYS_mmap,     9
    .equ SYS_exit,     231           /* exit_group */

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

    .bss
    .balign 64
argc_v:      .quad 0
argv_v:      .quad 0
envp_v:      .quad 0
argbase:     .quad 0
lsave_sp:    .quad 0
hdr:         .skip 64
    .balign 64
lsave_stack: .skip LSAVE_MAX*CELL

    .section .rodata
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
m_mem:       .ascii "relfasm64: cannot map the machine's memory\n"
    .equ m_mem_len, . - m_mem
m_unimpl:    .ascii "relfasm64: not written yet: "
    .equ m_unimpl_len, . - m_unimpl
m_badesc:    .ascii "relf: image uses an escaped primitive this engine does not have\n"
    .equ m_badesc_len, . - m_badesc
m_locals:    .ascii "relf: locals save stack overflow or underflow\n"
    .equ m_locals_len, . - m_locals
m_nl:        .ascii "\n"

    .text
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
    mov [rip + argc_v], rax
    lea rcx, [rsp + 8]
    mov [rip + argv_v], rcx
    lea rdx, [rcx + rax*8 + 8]
    mov [rip + envp_v], rdx
    mov qword ptr [rip + argbase], 2
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
    lea rsi, [rip + hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_magic
    /* 'C' 'V' '8' '0' 8, then 'L', the version, the features */
    cmp dword ptr [rip + hdr], 0x30385643
    jne bad_magic
    cmp byte ptr [rip + hdr + 4], CELL
    jne bad_magic
    cmp byte ptr [rip + hdr + 6], CV8_VERSION
    jne bad_version
    movzx eax, byte ptr [rip + hdr + 7]
    test eax, ~FEATURES
    jnz bad_magic
    /* the thread count and heads, then the DOES> tails: read and skipped */
    mov rdi, rbp
    lea rsi, [rip + hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    mov r12, [rip + hdr]             /* thread heads to skip */
3:  test r12, r12
    jz 4f
    mov rdi, rbp
    lea rsi, [rip + hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    dec r12
    jmp 3b
4:  mov rdi, rbp
    lea rsi, [rip + hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    mov r12, [rip + hdr]
    add r12, r12                     /* two cells per tail */
5:  test r12, r12
    jz 6f
    mov rdi, rbp
    lea rsi, [rip + hdr]
    mov edx, 8
    call read_all
    cmp rax, 8
    jne bad_hdr
    dec r12
    jmp 5b
    /* the memory: 16 MB, 64 KB-aligned, zeroed by the kernel */
6:  xor edi, edi
    mov esi, MEMSIZE + 65536
    mov edx, 3                       /* PROT_READ | PROT_WRITE */
    mov r10d, 0x22                   /* MAP_PRIVATE | MAP_ANONYMOUS */
    mov r8, -1
    xor r9d, r9d
    mov eax, SYS_mmap
    syscall
    cmp rax, -4096
    jb 7f
    lea rsi, [rip + m_mem]
    mov edx, m_mem_len
    mov edi, 2
    jmp die
7:  add rax, 65535
    and rax, -65536
    mov rbx, rax                     /* the image base, for good */
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
            mov rcx, [rip + lsave_sp]
            cmp rcx, LSAVE_MAX
            jae 1f
            mov rax, [rdx]
            lea r8, [rip + lsave_stack]
            mov [r8 + rcx*8], rax
            inc rcx
            mov [rip + lsave_sp], rcx
            NEXT
1:          mov eax, 1
            PUSHT rax
            jmp locals_failed
L_lrest:    SLOT
            mov rcx, [rip + lsave_sp]
            test rcx, rcx
            jle 1f
            dec rcx
            mov [rip + lsave_sp], rcx
            lea r8, [rip + lsave_stack]
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
L_sysargc:  mov rax, [rip + argc_v]  /* ( --- n ): the program's arguments */
            sub rax, [rip + argbase]
            jge 1f
            xor eax, eax
1:          PUSHT rax
            NEXT
L_sysarg:   mov rax, r12             /* ( n --- c-addr ), 0 past the end */
            add rax, [rip + argbase]
            test r12, r12
            js 1f
            cmp rax, [rip + argc_v]
            jae 1f
            mov rcx, [rip + argv_v]
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

#include "relfasm-ops.S"

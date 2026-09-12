/*  cv8-core.S - the CV8 inner interpreter in x86-64 assembly.
 *
 *  WHAT THIS IS FOR. tools/lab/figure-of-merit.py scores engine
 *  complexity by .text size. That is a poor proxy, and this measures how
 *  poor: how much of the C engine's .text is the interpreter's actual
 *  work, and how much is codegen - CET landing pads, the dispatch tail
 *  replicated into every handler, spills GCC chose.
 *
 *  SCOPE. Dispatch plus every primitive that is pure register/memory
 *  work: the 0x00-0x2A arithmetic/stack/memory band, the CV8 literal and
 *  call forms, DOVAR/DODOES, the folded prim;EXIT opcodes, and the
 *  specialised opcodes. Anything needing libc or a syscall (EMIT, KEY,
 *  the file and process words, ALLOCATE) stays in C: vm_slow() is called
 *  with the VM registers in memory and returns the new ip. That is the
 *  same split vm.asm used before phase 2, and it keeps this comparable -
 *  both engines then contain the same C for the same words.
 *
 *  REGISTERS (System V, callee-saved where they must survive vm_slow)
 *      rbx  ip       instruction pointer, into the image
 *      rbp  dsp      data stack pointer
 *      r12  rp       return stack pointer
 *      r13  cbase    image base (call/slot targets are cbase + (v << 3))
 *      r14  tos      top of data stack, cached
 *      r15  dtab     dispatch table
 *      rax  t        scratch: the opcode byte, then targets
 *      rcx, rdx, rsi, rdi  scratch
 *
 *  The data stack grows DOWN and holds the second element at 0(rbp);
 *  tos is in r14. The return stack grows down from 0(r12).
 *
 *  Assemble for the same image format the C engine reads. Cell width is
 *  8 and SCALE is 3, so this file is x86-64 only by construction.
 */

        .intel_syntax noprefix
        .text
        .globl  vm_run
        .type   vm_run, @function

/*  void vm_run(UNS64 *regs)  - regs: [0]=ip [1]=rp [2]=dsp [3]=base
 *  [4]=dsp_limit [5]=rp_limit [6..10]=loc_hdr. Never returns; leaves
 *  through BYE/SYS-EXIT inside vm_slow.  */
vm_run:
        push    rbx
        push    rbp
        push    r12
        push    r13
        push    r14
        push    r15
        mov     r11, rdi                /* keep regs block for vm_slow  */
        mov     [rip + g_regs], r11
        mov     rbx, [r11 + 0]          /* ip                           */
        mov     r12, [r11 + 8]          /* rp                           */
        mov     rbp, [r11 + 16]         /* dsp                          */
        mov     r13, [r11 + 24]         /* cbase                        */
        lea     r15, [rip + dtab]
        mov     r14, [rbp]              /* fill tos                     */
        add     rbp, 8

/*  NEXT. One byte: sign says opcode or call. movsx gives the sign test
 *  for free, so the hot path is load / test / jump - three instructions
 *  before the indirect jump, against the C engine's five.  */
.macro  NEXT
        movsx   rax, byte ptr [rbx]
        test    eax, eax
        js      2f
        inc     rbx
        jmp     [r15 + rax*8]
2:      jmp     do_call
.endm

next:   NEXT

/*  A call: 15-bit target, scaled. One shared copy (SHAREDCALL=1 in the C
 *  engine does the same), because replicating it bought nothing.  */
do_call:
        movzx   ecx, byte ptr [rbx + 1]
        and     eax, 0x7f
        shl     eax, 8
        or      eax, ecx
        add     rbx, 2
        sub     r12, 8                  /* RPUSH(ip)                    */
        mov     [r12], rbx
        lea     rbx, [r13 + rax*8]
        NEXT

/*  ---- stack and memory ------------------------------------------- */
o_noop: NEXT
o_exit: mov     rbx, [r12]
        add     r12, 8
        NEXT
o_drop: mov     r14, [rbp]
        add     rbp, 8
        NEXT
o_dup:  sub     rbp, 8
        mov     [rbp], r14
        NEXT
o_swap: mov     rax, [rbp]
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_over: mov     rax, [rbp]
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_rot:  mov     rax, [rbp + 8]
        mov     rcx, [rbp]
        mov     [rbp + 8], rcx
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_cfetch:
        movzx   r14d, byte ptr [r14]
        NEXT
o_fetch:
        mov     r14, [r14]
        NEXT
o_cstore:
        mov     rax, [rbp]
        mov     [r14], al
        mov     r14, [rbp + 8]
        add     rbp, 16
        NEXT
o_store:
        mov     rax, [rbp]
        mov     [r14], rax
        mov     r14, [rbp + 8]
        add     rbp, 16
        NEXT
/*  ---- logic and arithmetic --------------------------------------- */
o_and:  and     r14, [rbp]
        add     rbp, 8
        NEXT
o_or:   or      r14, [rbp]
        add     rbp, 8
        NEXT
o_xor:  xor     r14, [rbp]
        add     rbp, 8
        NEXT
o_plus: add     r14, [rbp]
        add     rbp, 8
        NEXT
o_neg:  neg     r14
        NEXT
o_lsh:  mov     rcx, r14
        mov     r14, [rbp]
        add     rbp, 8
        shl     r14, cl
        NEXT
o_rsh:  mov     rcx, r14
        mov     r14, [rbp]
        add     rbp, 8
        shr     r14, cl
        NEXT
o_eq:   xor     eax, eax
        cmp     [rbp], r14
        sete    al
        add     rbp, 8
        neg     rax
        mov     r14, rax
        NEXT
o_ult:  xor     eax, eax
        cmp     [rbp], r14
        setb    al
        add     rbp, 8
        neg     rax
        mov     r14, rax
        NEXT
o_lt:   xor     eax, eax
        cmp     [rbp], r14
        setl    al
        add     rbp, 8
        neg     rax
        mov     r14, rax
        NEXT
/*  ---- return stack ------------------------------------------------ */
o_tor:  sub     r12, 8
        mov     [r12], r14
        mov     r14, [rbp]
        add     rbp, 8
        NEXT
o_fromr:
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, [r12]
        add     r12, 8
        NEXT
o_rat:  sub     rbp, 8
        mov     [rbp], r14
        mov     r14, [r12]
        NEXT
o_spat: sub     rbp, 8
        mov     [rbp], r14
        lea     r14, [rbp + 8]
        NEXT
o_spstore:
        mov     rbp, r14
        mov     r14, [rbp]
        add     rbp, 8
        NEXT
o_rpat: sub     rbp, 8
        mov     [rbp], r14
        mov     r14, r12
        NEXT
o_rpstore:
        mov     r12, r14
        mov     r14, [rbp]
        add     rbp, 8
        NEXT
/*  ---- literals, branches, data ------------------------------------ */
o_lit:  movzx   eax, word ptr [rbx]
        add     rbx, 2
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_lit8: movzx   eax, byte ptr [rbx]
        inc     rbx
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_lit8x:
        movzx   eax, byte ptr [rbx]
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        mov     rbx, [r12]
        add     r12, 8
        NEXT
o_lit32:
        movsxd  rax, dword ptr [rbx]
        add     rbx, 4
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_branch:
        movsx   rax, word ptr [rbx]
        add     rbx, rax
        NEXT
o_qbranch:
        mov     rax, r14
        mov     r14, [rbp]
        add     rbp, 8
        test    rax, rax
        jnz     1f
        movsx   rax, word ptr [rbx]
        add     rbx, rax
        NEXT
1:      add     rbx, 2
        NEXT
o_dovar:                                /* [DOVAR][pad][PFA]            */
        lea     rax, [rbx + 7]
        and     rax, -8
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        mov     rbx, [r12]              /* return                       */
        add     r12, 8
        NEXT
o_dodoes:                               /* [DODOES][call][pad][PFA]     */
        movzx   eax, byte ptr [rbx]
        movzx   ecx, byte ptr [rbx + 1]
        and     eax, 0x7f
        shl     eax, 8
        or      eax, ecx
        lea     rdx, [rbx + 9]          /* PFA = align(ip + 2)          */
        and     rdx, -8
        sub     r12, 8
        mov     [r12], rdx
        lea     rbx, [r13 + rax*8]
        NEXT

/*  ---- specialised opcodes (VM-SURVEY.md) --------------------------- */
.macro  SLOT                            /* -> rax = cbase + (v << 3)    */
        movzx   eax, word ptr [rbx]
        add     rbx, 2
        lea     rax, [r13 + rax*8]
.endm
o_lit0: sub     rbp, 8
        mov     [rbp], r14
        xor     r14d, r14d
        NEXT
o_lit1: sub     rbp, 8
        mov     [rbp], r14
        mov     r14d, 1
        NEXT
o_litm1:
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, -1
        NEXT
o_vf:   SLOT
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, [rax]
        NEXT
o_vs:   SLOT
        mov     [rax], r14
        mov     r14, [rbp]
        add     rbp, 8
        NEXT
o_lstore:
        SLOT
        mov     [rax], r14
        mov     r14, [rbp]
        add     rbp, 8
        NEXT
o_lzero:
        SLOT
        mov     qword ptr [rax], 0
        NEXT
/*  LSAVE / LRESTORE: the fast path, deoptimising to the Forth word on
 *  the cases where it would ABORT" (see CV8.md). loc_hdr is at
 *  g_regs[6..10]: lsp, lstk, lmax, LSAVE body, LRESTORE body.  */
o_lsave:
        SLOT
        mov     r11, [rip + g_regs]
        mov     rcx, [r11 + 48]         /* loc_hdr[0]: LSAVE-SP offset  */
        add     rcx, r13
        mov     rdx, [rcx]              /* sp                           */
        mov     rsi, [r11 + 56]
        mov     rsi, [r13 + rsi]        /* stack buffer                 */
        test    rsi, rsi
        jz      9f
        cmp     rdx, [r11 + 64]         /* loc_hdr[2]: LSAVE-MAX        */
        jge     9f
        test    rdx, rdx
        js      9f
        mov     rdi, [rax]
        mov     [rsi + rdx*8], rdi
        inc     rdx
        mov     [rcx], rdx
        NEXT
9:      sub     rbp, 8                  /* deoptimise: push START offset */
        mov     [rbp], r14
        sub     rax, r13
        mov     r14, rax
        sub     r12, 8
        mov     [r12], rbx
        mov     rcx, [r11 + 72]         /* loc_hdr[3]: LSAVE body       */
        lea     rbx, [r13 + rcx]
        NEXT
o_lrest:
        SLOT
        mov     r11, [rip + g_regs]
        mov     rcx, [r11 + 48]
        add     rcx, r13
        mov     rdx, [rcx]
        mov     rsi, [r11 + 56]
        mov     rsi, [r13 + rsi]
        test    rsi, rsi
        jz      9f
        test    rdx, rdx
        jle     9f
        dec     rdx
        mov     [rcx], rdx
        mov     rdi, [rsi + rdx*8]
        mov     [rax], rdi
        NEXT
9:      sub     rbp, 8
        mov     [rbp], r14
        sub     rax, r13
        mov     r14, rax
        sub     r12, 8
        mov     [r12], rbx
        mov     rcx, [r11 + 80]         /* loc_hdr[4]: LRESTORE body    */
        lea     rbx, [r13 + rcx]
        NEXT
/*  tiny kernel words as opcodes  */
o_zeq:  xor     eax, eax
        test    r14, r14
        sete    al
        neg     rax
        mov     r14, rax
        NEXT
o_sub:  mov     rax, [rbp]
        sub     rax, r14
        add     rbp, 8
        mov     r14, rax
        NEXT
o_ne:   xor     eax, eax
        cmp     [rbp], r14
        setne   al
        add     rbp, 8
        neg     rax
        mov     r14, rax
        NEXT
o_zlt:  sar     r14, 63
        NEXT
o_sgt:  xor     eax, eax
        cmp     r14, [rbp]
        setl    al
        add     rbp, 8
        neg     rax
        mov     r14, rax
        NEXT
o_2dup: mov     rax, [rbp]
        sub     rbp, 16
        mov     [rbp + 8], r14
        mov     [rbp], rax
        NEXT
o_2drop:
        mov     r14, [rbp + 8]
        add     rbp, 16
        NEXT
o_1p:   inc     r14
        NEXT
o_cellp:
        add     r14, 8
        NEXT
o_cells:
        shl     r14, 3
        NEXT
o_1m:   dec     r14
        NEXT
o_invert:
        not     r14
        NEXT
o_count:
        movzx   eax, byte ptr [r14]
        inc     r14
        sub     rbp, 8
        mov     [rbp], r14
        mov     r14, rax
        NEXT
o_aligned:
        add     r14, 7
        and     r14, -8
        NEXT
o_addi: movsx   rax, byte ptr [rbx]
        inc     rbx
        add     r14, rax
        NEXT
o_addix:                                /* ADDI then EXIT               */
        movsx   rax, byte ptr [rbx]
        add     r14, rax
        mov     rbx, [r12]
        add     r12, 8
        NEXT
o_eqix: movsx   rax, byte ptr [rbx]
        xor     ecx, ecx
        cmp     r14, rax
        sete    cl
        neg     rcx
        mov     r14, rcx
        mov     rbx, [r12]
        add     r12, 8
        NEXT
o_eqi:  movsx   rax, byte ptr [rbx]
        inc     rbx
        xor     ecx, ecx
        cmp     r14, rax
        sete    cl
        neg     rcx
        mov     r14, rcx
        NEXT

/*  ---- everything needing libc or a syscall ------------------------- */
/*  vm_slow(opcode) spills the VM registers to g_regs, calls the C half,
 *  and reloads. One copy, so a cold word costs 12 bytes here, not a
 *  body. The C side is the same code the C engine runs.  */
o_slow:
        mov     r11, [rip + g_regs]
        mov     [r11 + 0], rbx
        mov     [r11 + 8], r12
        sub     rbp, 8                  /* spill tos: C half sees memory */
        mov     [rbp], r14
        mov     [r11 + 16], rbp
        mov     edi, eax                /* opcode                       */
        call    vm_slow
        test    eax, eax                /* nonzero: leave the VM        */
        jnz     vm_exit
        mov     r11, [rip + g_regs]
        mov     rbx, [r11 + 0]
        mov     r12, [r11 + 8]
        mov     rbp, [r11 + 16]
        mov     r14, [rbp]
        add     rbp, 8
        NEXT

/*  vm_slow returns nonzero to leave the interpreter (BYE, or the C half
 *  wanting to unwind). The real engine's BYE exits the process inside
 *  vm_slow and never comes back; core-bench.c uses the return path.  */
vm_exit:
        pop     r15
        pop     r14
        pop     r13
        pop     r12
        pop     rbp
        pop     rbx
        ret

        .size   vm_run, .-vm_run

        .section .data.rel.ro,"aw"
        .align  8
/*  Dispatch table, in kernel.4's PRIMITIVE order. Everything not
 *  implemented here goes to the shared slow path.  */
#define S o_slow
dtab:
        .quad o_noop, o_exit, o_lit, o_branch, o_qbranch
        .quad o_drop, o_dup, o_swap, o_rot, o_over
        .quad o_cfetch, o_fetch, o_cstore, o_store
        .quad o_and, o_or, o_xor
        .quad o_fromr, o_tor, o_rat
        .quad o_eq, o_ult, o_lt, o_plus, o_neg, o_lsh, o_rsh
        .quad S, S, S                   /* UM* UM/MOD D+                */
        .quad S, S, S                   /* EMIT KEY BYE                 */
        .quad o_spat, o_spstore, o_rpat, o_rpstore
        .quad S, S, S, S, S, S, S, S, S, S      /* file words           */
        .quad S, S, S, S, S, S, S, S, S, S      /* process, env         */
        .quad S, S, S, S, S, S, S, S, S, S, S    /* rest of the band    */
        .quad o_lit32, o_dovar, o_dodoes, o_lit8, o_lit8x
        .align 8
        .zero 8 * (0x60 - 73)           /* folded opcodes: filled by C  */
dtab_spec:
        .quad o_lit0, o_lit1, o_litm1, o_vf, o_vs
        .quad o_lsave, o_lrest, o_lstore, o_lzero
        .quad o_zeq, o_sub, o_ne, o_zlt, o_sgt, o_2dup, o_2drop
        .quad o_1p, o_1p, o_cellp, o_cells, o_1m, o_invert
        .quad o_count, o_aligned
        .quad o_addi, o_addix, o_eqi, o_eqix

        .bss
        .align 8
g_regs: .quad 0

        .section .note.GNU-stack,"",@progbits

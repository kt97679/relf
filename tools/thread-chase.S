/*
 *  tools/thread-chase.S - the call path of both threading models, by
 *  hand, so the comparison cannot be blamed on what a C compiler chose.
 *
 *  Iteration 187. tests/bench says a SOD16 image runs ~1.25x slower
 *  than the cell image on pure interpretation. The question this
 *  answers is whether that is inherent to the encoding or an artifact
 *  of how relf.c and sod16.c happen to compile.
 *
 *  Everything else about the two engines is identical - the same
 *  relf.c bar eight lines - so the only thing worth isolating is the
 *  step that differs, which is how a CALL finds its target:
 *
 *    cell    ip = ip + CELL_BYTES + *(long *)ip
 *            one load, then an ALU add. The offset is already in a
 *            register when it is needed.
 *
 *    token   ip = wordtab[*(unsigned short *)ip]
 *            one load, then a SECOND LOAD whose address depends on the
 *            first. Two cache accesses serialised, not one.
 *
 *  Threaded code is latency-bound on that chain: nothing else can
 *  start until the next ip is known. So this measures the chain and
 *  nothing else - no stack traffic, no primitive bodies, no dispatch
 *  table - because those are the same in both and would only dilute
 *  the ratio.
 *
 *  The caller arranges for both to visit the SAME sequence of slots,
 *  so cache behaviour is matched and the only difference left is the
 *  mechanism.
 */
    .text

/*  cell_chase(void *ip, long n) -> final ip
 *    rdi = ip, rsi = iterations  */
    .globl cell_chase
    .type  cell_chase, @function
cell_chase:
1:  movq    (%rdi), %rax            /* the relative offset            */
    leaq    8(%rdi,%rax), %rdi      /* ip += CELL_BYTES + offset      */
    decq    %rsi
    jnz     1b
    movq    %rdi, %rax
    ret
    .size  cell_chase, .-cell_chase

/*  tok_chase(void *ip, long n, void **wordtab) -> final ip
 *    rdi = ip, rsi = iterations, rdx = wordtab  */
    .globl tok_chase
    .type  tok_chase, @function
tok_chase:
1:  movzwl  (%rdi), %eax            /* the word number                */
    movq    (%rdx,%rax,8), %rdi     /* ip = wordtab[n] - DEPENDENT    */
    decq    %rsi
    jnz     1b
    movq    %rdi, %rax
    ret
    .size  tok_chase, .-tok_chase

    .section .note.GNU-stack,"",@progbits

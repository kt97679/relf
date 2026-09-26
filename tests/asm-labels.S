# tests/asm-labels.S - the reference for tests/asm-labels.4 (M1, Iteration 545)
    .intel_syntax noprefix
    .globl _start
_start:
    xor eax, eax
1:  inc eax
    cmp eax, 10
    jne 1b
    test eax, eax
    jz 2f
    mov edi, 42
    jmp done
2:  mov edi, 1
done:
    mov eax, 60
    jmp farther
    .rept 200
    nop
    .endr
farther:
    syscall

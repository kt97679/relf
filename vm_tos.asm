; This VM performs 3.3 slower than native C application.
; Benchmarked using fib test.

; esp - data stack pointer
; ebp - return stack pointer
; esi - instruction pointer
; edx - top of stack

;%macro donext 0
;    lodsd
;    bt ax, 0
;    jnc near vmdolist
;    jmp [eax + vmops]
;%endmacro
%macro donext 0
    lodsd
    test eax, 1
    jz near vmdolist
    jmp [eax + vmops]
%endmacro
;%macro donext 0
;    mov eax, [esi]
;    add esi, 4
;    bt ax, 0
;    jnc near vmdolist
;    jmp [eax + vmops]
;%endmacro
;%macro donext 0
;    mov eax, [esi]
;    add esi, 4
;    test eax, 1
;    jz near vmdolist
;    jmp [eax + vmops]
;%endmacro

extern rp
extern ip
extern dsp
extern exit
extern getchar
extern putchar

global virtual_machine

section .text

virtual_machine:
    cld
    mov esi, [ip]
    mov ebp, [rp]
    mov esp, [dsp]
    pop edx
    donext

;vmdolist:
;    xchg ebp, esp
;    push esi
;    add esi, eax
;    xchg ebp, esp
;    donext

vmdolist:
    sub ebp, 4
    mov [ebp], esi
    add esi, eax
    donext

vmnoop:
    donext

vmexit:
    mov esi, [ebp] 
    add ebp, 4
    donext

;vmexit:
;    xchg esp, ebp
;    pop esi
;    xchg esp, ebp
;    donext

vmlit:
    lodsd
    push edx
    mov edx, eax
    donext

;vmlit:
;    push edx
;    mov edx, [esi]
;    add esi, 4
;    donext

;vm0branch:
;    test edx, edx
;    pop edx
;    jz vmbranch
;    add esi, 4
;    donext
vm0branch:
    mov ecx, edx
    pop edx
    jecxz vmbranch
    add esi, 4
    donext
vmbranch:
    add esi, [esi]
    donext

vmdrop:
    pop edx
    donext

vmdup:
    push edx
    donext

vmswap:
    pop eax
    push edx
    mov edx, eax
    donext

vmrot:
    pop ebx
    pop eax
    push ebx
    push edx
    mov edx, eax    
    donext

vmover:
    pop ecx
    push ecx
    push edx
    mov edx, ecx
    donext

vmcfetch:
    xor edx, 3
    movzx edx, byte [edx]
    donext

vmfetch:
    mov edx, [edx]
    donext

vmcstore:
    pop ecx
    xor edx, 3
    mov [edx], cl
    pop edx
    donext

vmstore:
    pop ecx
    mov [edx], ecx
    pop edx
    donext

vmand:
    pop ecx
    and edx, ecx
    donext

vmor:
    pop ecx
    or edx, ecx
    donext

vmxor:
    pop ecx
    xor edx, ecx
    donext

vmfromr:
    push edx
    mov edx, [ebp]
    add ebp, 4
    donext

vmtor:
    sub ebp, 4
    mov [ebp], edx
    pop edx
    donext

vmrfetch:
    push edx
    mov edx, [ebp]
    donext

vmeq:
    pop ebx
    xor edx, ebx
    sub edx, 1
    sbb edx, edx
    donext

vmplus:
    pop eax
    add edx, eax
    donext

vmnegate:
    neg edx
    donext

vmrshift:
    mov ecx, edx
    pop edx
    shr edx, cl
    donext

vmlshift:
    mov ecx, edx
    pop edx
    shl edx, cl
    donext

vmspfetch:
    push edx
    mov edx, esp
    donext

vmspstore:
    mov esp, edx
    donext

vmrpfetch:
    push edx
    mov edx, ebp
    donext

vmrpstore:
    mov ebp, edx
    pop edx
    donext

vmgt:
    pop eax
    sub eax, edx
    cdq
    donext

vmugt:
     pop ecx
     cmp ecx, edx
     sbb edx, edx
     donext

vmummult:
    mov ecx, edx
    pop eax
    mul ecx
    push eax
    donext

vmumdiv:
    mov ecx, edx
    pop edx
    pop eax
    div ecx
    push edx
    mov edx, eax
    donext

vmdplus:
    pop eax
    pop ecx
    add [esp], eax
    adc edx, ecx
    donext

vmbye:
    push dword 0
    call exit
    donext

vmkey:
    push edx
    call getchar
    mov edx, eax
    donext

vmemit:
    push edx
    call putchar
    pop eax
    pop edx
    donext

vmopenfile:
vmclosefile:
vmreadline: 
vmwriteline:
vmreadfile: 
vmwritefile:
vmsystem:   
vmreposfile:
vmfilepos:  
vmdelfile:  
vmfilesize: 
    donext

section .data

_vmops dd vmnoop, vmexit, vmlit, vmbranch, vm0branch, vmdrop,
       dd vmdup, vmswap, vmrot, vmover, vmcfetch, vmfetch, vmcstore, vmstore,
       dd vmand, vmor, vmxor, vmfromr, vmtor, vmrfetch, vmeq, vmugt, vmgt,
       dd vmplus, vmnegate, vmlshift, vmrshift, vmummult, vmumdiv, vmdplus,
       dd vmemit, vmkey, vmbye, vmspfetch, vmspstore, vmrpfetch, vmrpstore,
       dd vmopenfile, vmclosefile, vmreadline, vmwriteline, vmreadfile,
       dd vmwritefile, vmsystem, vmreposfile, vmfilepos, vmdelfile, vmfilesize

vmops equ _vmops - 1

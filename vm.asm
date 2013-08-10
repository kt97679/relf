; This is VM without top of stack in separate register

; esp - data stack pointer
; ebp - return stacl pointer
; esi - instruction pointer

;%macro donext 0
;    lodsd
;    bt ax, 0
;    jnc near vmdolist
;    jmp [eax + vmops]
;%endmacro
;%macro donext 0
;    lodsd
;    test eax, 1
;    jz near vmdolist
;    jmp [eax + vmops]
;%endmacro
;%macro donext 0
;    mov eax, [esi]
;    add esi, 4
;    bt ax, 0
;    jnc near vmdolist
;    jmp [eax + vmops]
;%endmacro
%macro donext 0
    mov eax, [esi]
    add esi, 4
    test eax, 1
    jz near vmdolist
    jmp [eax + vmops]
%endmacro

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
    push eax
    donext

;vmlit:
;    push dword [esi]
;    add esi, 4
;    donext

;vm0branch:
;    pop eax
;    test eax, eax
;    jz vmbranch
;    add esi, 4
;    donext
vm0branch:
    pop ecx
    jecxz vmbranch
    add esi, 4
    donext
vmbranch:
    add esi, [esi]
    donext

;vmdrop:
;    pop eax
;    donext

vmdrop:
    add esp, 4
    donext

;vmdup:
;    pop eax
;    push eax
;    push eax
;    donext

vmdup:
    push dword [esp]
    donext

vmswap:
    pop eax
    pop ecx
    push eax
    push ecx
    donext

vmrot:
    pop ecx
    pop edx
    pop eax
    push edx
    push ecx
    push eax    
    donext

vmover:
    pop eax
    pop ecx
    push ecx
    push eax
    push ecx
    donext

vmcfetch:
    pop ecx
    xor ecx, 3
    movzx edx, byte [ecx]
    push edx
    donext

vmfetch:
    pop eax
    push dword [eax]
    donext

vmcstore:
    pop edx
    pop ecx
    xor edx, 3
    mov [edx], cl
    donext

vmstore:
    pop edx
    pop ecx
    mov [edx], ecx
    donext

vmand:
    pop eax
    pop ecx
    and eax, ecx
    push eax
    donext

vmor:
    pop eax
    pop ecx
    or eax, ecx
    push eax
    donext

vmxor:
    pop eax
    pop ecx
    xor eax, ecx
    push eax
    donext

vmfromr:
    push dword [ebp]
    add ebp, 4
    donext

vmtor:
    pop eax
    sub ebp, 4
    mov [ebp], eax
    donext

vmrfetch:
    push dword [ebp]
    donext

vmeq:
    pop eax
    pop ebx
    xor eax, ebx
    sub eax, 1
    sbb eax, eax
    push eax
    donext

vmplus:
    pop eax
    add [esp], eax
    donext

;vmplus:
;    pop eax
;    pop ecx
;    add eax, ecx
;    push eax
;    donext

;vmnegate:
;    pop eax
;    neg eax
;    push eax
;    donext

vmnegate:
    neg dword [esp]
    donext

;vmrshift:
;    pop ecx
;    pop eax
;    shr eax, cl
;    push eax
;    donext

vmrshift:
    pop ecx
    shr dword [esp], cl
    donext

;vmlshift:
;    pop ecx
;    pop eax
;    shl eax, cl
;    push eax
;    donext

vmlshift:
    pop ecx
    shl dword [esp], cl
    donext

vmspfetch:
    mov eax, esp
    push eax
    donext

vmspstore:
    pop esp
    donext

vmrpfetch:
    push ebp
    donext

vmrpstore:
    pop ebp
    donext

;vmgt:
;    pop ecx
;    pop eax
;    sub eax, ecx
;    sar eax, 31
;    push eax
;    donext

vmgt:
    pop ecx
    pop eax
    sub eax, ecx
    cdq
    push edx
    donext

vmugt:
     pop eax
     pop ecx
     cmp ecx, eax
     sbb eax, eax
     push eax
     donext

vmummult:
    pop ecx
    pop eax
    mul ecx
    push eax
    push edx
    donext

vmumdiv:
    pop ecx
    pop edx
    pop eax
    div ecx
    push edx
    push eax
    donext

vmdplus:
    pop ecx
    pop eax
    add [esp + 4], eax
    adc [esp], ecx
    donext

vmbye:
    push dword 0
    call exit
    donext

vmkey:
    call getchar
    push eax
    donext

vmemit:
    call putchar
    pop eax
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

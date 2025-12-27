[bits 32]

global asm_hello_world

asm_hello_world:
    push eax
    push ebx
    push esi
    push ecx    
    xor eax, eax
    xor ebx, ebx
    xor esi, esi
    xor ecx, ecx
    mov ecx, my_id_end - my_id
    mov ah, 0x3
    mov esi, my_id
    my_loop:
        mov al, [esi]
        mov word[gs:ebx], ax
        inc esi
        add ebx, 2
        loop my_loop
    pop ecx
    pop esi
    pop ebx
    pop eax
    ret
my_id db '22320021'
my_id_end:
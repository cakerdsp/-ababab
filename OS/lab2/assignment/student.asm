; If you meet compile error, try 'sudo apt install gcc-multilib g++-multilib' first

%include "head.include"
; you code here

your_if:
; put your implementation here
        cmp word[a1], 12
        jl first_if
        cmp word[a1], 24
        jl second_if
        jmp third_if
end_if:

your_while:
; put your implementation here
        pushad
	xor edx, edx
	mov edx, [while_flag]
	sub edx, 12
while:
        xor ebx, ebx
        mov ebx, [a2]
        cmp ebx, 12
        jl jump_out
	push edx
        call my_random
	pop edx
	add edx, ebx
        mov byte[edx], al
	sub edx, ebx
        sub ebx, 1
        mov [a2], ebx
        jmp while
jump_out:
        popad

%include "end.include"

your_function:
; put your implementation here
        pushad
        xor ebx, ebx
        mov ebx, 0
loop:
	xor eax, eax
	mov al, byte[your_string+ebx]
        cmp byte[your_string+ebx], 0
        je out_loop
        push eax
        pushad
        call print_a_char
        popad
        pop eax
        add ebx, 1
        jmp loop
out_loop:
        popad
        ret


first_if:
        pushad
        xor eax, eax
        xor edx, edx
        xor ecx, ecx
        mov eax, dword[a1]
        mov ecx, 2
        div ecx
        add eax, 1
        mov dword[if_flag], eax
        popad
        jmp end_if

second_if:
        pushad
        xor eax, eax
        xor ebx, ebx
        xor ecx, ecx
        mov eax, [a1]
	mov ebx, eax
        imul ebx, eax
        imul eax, 24
        sub eax, ebx
        mov dword[if_flag], eax
        popad
        jmp end_if

third_if:
        pushad
        xor eax, eax
        xor edx, edx
        xor ecx, ecx
        mov eax, [a1]
        shl eax, 4
        mov dword[if_flag], eax
        popad
        jmp end_if

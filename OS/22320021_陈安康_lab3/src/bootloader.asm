org 0x7e00
[bits 16]
mov ax, 0xb800
mov gs, ax


mov bx, 0
mov ah, 0x03
mov al, 'r'
mov word[gs:bx], ax
add bx, 2

mov al, 'u'
mov word[gs:bx], ax
add bx, 2

mov al, 'n'
mov word[gs:bx], ax
add bx, 2

mov al, ' '
mov word[gs:bx], ax
add bx, 2

mov al, 'b'
mov word[gs:bx], ax
add bx, 2

mov al, 'o'
mov word[gs:bx], ax
add bx, 2

mov al, 'o'
mov word[gs:bx], ax
add bx, 2

mov al, 't'
mov word[gs:bx], ax
add bx, 2

mov al, 'l'
mov word[gs:bx], ax
add bx, 2

mov al, 'o'
mov word[gs:bx], ax
add bx, 2

mov al, 'a'
mov word[gs:bx], ax
add bx, 2

mov al, 'd'
mov word[gs:bx], ax
add bx, 2

mov al, 'e'
mov word[gs:bx], ax
add bx, 2

mov al, 'r'
mov word[gs:bx], ax
add bx, 2

jmp $ 

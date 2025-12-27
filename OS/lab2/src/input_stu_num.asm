org 0x7c00
[bits 16]
xor ax, ax ; eax = 0
; 初始化段寄存器, 段地址全部设为0
mov ds, ax
mov ss, ax
mov es, ax
mov fs, ax
mov gs, ax

; 初始化栈指针
mov sp, 0x7c00
mov ax, 0xb800
mov gs, ax

mov ah, 09h
mov al, '2'
mov bh, 0
mov bl, 5
mov cx, 2

int 10h

mov ah, 03h
mov bx, 0

int 10h

mov ah, 02h
mov bx, 0
add dl, 2

int 10h

mov ah, 09h
mov al, '3'
mov bh, 0
mov bl, 5
mov cx, 1

int 10h

mov ah, 02h
mov bx, 0
add dl, 1

int 10h

mov ah, 09h
mov al, '2'
mov bh, 0
mov bl, 5
mov cx, 1

int 10h


mov ah, 02h
mov bx, 0
add dl, 1

int 10h

mov ah, 09h
mov al, '0'
mov bh, 0
mov bl, 5
mov cx, 2

int 10h

mov ah, 02h
mov bx, 0
add dl, 2

int 10h

mov ah, 09h
mov al, '1'
mov bh, 0
mov bl, 5
mov cx, 1

int 10h


jmp $ ; 死循环

times 510 - ($ - $$) db 0
db 0x55, 0xaa

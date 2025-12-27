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

mov ah, 02h
mov bh, 0
mov dh, 1
mov dl, 1
int 10h

jmp $ ; 死循环

times 510 - ($ - $$) db 0
db 0x55, 0xaa


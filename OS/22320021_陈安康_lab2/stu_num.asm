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


mov ah, 0x75 ; 背景是白色不闪烁，前景色为品红色
mov al, '2'
mov [gs:2 * (80 * 12 + 12)], ax

mov al, '2'
mov [gs:2 * (80 * 12 + 13)], ax

mov al, '3'
mov [gs:2 * (80 * 12 + 14)], ax

mov al, '2'
mov [gs:2 * (80 * 12 + 15)], ax

mov al, '0'
mov [gs:2 * (80 * 12 + 16)], ax

mov al, '0'
mov [gs:2 * (80 * 12 + 17)], ax

mov al, '2'
mov [gs:2 * (80 * 12 + 18)], ax

mov al, '1'
mov [gs:2 * (80 * 12 + 19)], ax


jmp $ ; 死循环

times 510 - ($ - $$) db 0
db 0x55, 0xaa

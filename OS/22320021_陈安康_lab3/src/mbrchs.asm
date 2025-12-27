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
mov bx, 0x7e00           ; bootloader的加载地址

mov ah, 0x02
mov al, 5
mov ch, 0
mov cl, 2
mov dh, 0
mov dl, 0x80 ; 驱动器号
int 0x13

jmp 0x0000:0x7e00
jmp $ 

times 510 - ($ - $$) db 0
db 0x55, 0xaa

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
mov dh, 19
mov dl, 21
int 10h


mov ah, 03h
mov bh, 0
int 10h



;在初始位置打印光标坐标，一个坐标用两个字符表示
shang db 0
yushu db 0
hang db 0
lie db 0
mov byte[hang], dh
mov byte[lie], dl
xor edx, edx
xor ecx, ecx
xor eax, eax
mov cx, 10
mov al, byte[hang]
div cx
mov byte[shang], al
mov byte[yushu], dl
mov ah, 0x01
add byte[shang], '0'
add byte[yushu], '0'
mov al, byte[shang]
mov [gs:2*(0)], ax
mov al, byte[yushu]
mov [gs:2*(1)], ax


xor edx, edx
xor ecx, ecx
xor eax, eax
mov cx, 10
mov al, [lie]
div cx
mov [shang], al
mov [yushu], dl
mov ah, 0x01
add byte[shang], '0'
add byte[yushu], '0'
mov al, byte[shang]
mov [gs:2*(2)], ax
mov al, byte[yushu]
mov [gs:2*(3)], ax


jmp $ ; 死循环

times 510 - ($ - $$) db 0
db 0x55, 0xaa
 

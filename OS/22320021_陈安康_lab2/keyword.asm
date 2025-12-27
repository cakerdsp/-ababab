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


input_key:
    ;获取键盘输入的字符，ASii放在al里
    mov ah, 00h
    int 16h

    cmp al, 1bh
    je close_key

    ;在当前光标处输出字符
    mov ah, 09h
    mov bh, 0
    mov bl, 1
    mov cx, 1
    int 10h

    ;获取光标的位置
    mov ah, 03h
    mov bx, 0
    int 10h

    ;移动光标的位置
    mov ah, 02h
    mov bh, 0
    add dl, 1
    cmp dl, 80
    je change_cursor
    change_cursor_back:
    int 10h

jmp input_key


change_cursor:
    mov dl, 0
    add dh, 1
    jmp change_cursor_back

close_key:
    mov ah, 04h
    mov al, 01h
    int 04h


jmp $ ; 死循环

times 510 - ($ - $$) db 0
db 0x55, 0xaa


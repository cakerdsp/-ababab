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

xor cx, cx
xor ax, ax
xor bx, bx
loop_pre:
	imul bx, cx, 2
	mov [gs:bx], ax
	add cx, 1
	cmp cx, 2000
	je out_loop_pre		
	jmp loop_pre

out_loop_pre:



i db 2
j db 0
offset_i db 1
offset_j db 1
xor dx, dx

loop:	
	mov ah, 0x01
	mov al, 'A'
	push ax
	xor ax, ax
	mov ax, [i]
	xor ah, ah
	xor bx, bx
	mov bx, [j]
	xor bh, bh
	imul bx, 80
	add bx, ax
	imul bx, 2
	pop ax
	mov [gs:bx], ax
	mov dl, [i]
        mov dh, [j]
	add dl, [offset_i]
        add dh, [offset_j]
	cmp dl, 80
	je change_i_a
	cmp dl, -1
	je change_i_b
return_i:
	cmp dh, 25
	je change_j_a
	cmp dh, -1
	je change_j_b
return_j:
	mov byte[i], dl
	mov byte[j], dh
	xor ecx, ecx
	mov ecx, 100000000
loop_time:
	nop;
	sub ecx, 1
	cmp ecx, 0
	je out_loop
	jmp loop_time
out_loop:
	jmp loop

change_i_a:
	mov byte[offset_i], -1
	mov dl, 78
	jmp return_i

change_i_b:
	mov byte[offset_i], 1
	mov dl, 1
	jmp return_i

change_j_a:
	mov byte[offset_j], -1
	mov dh, 23
	jmp return_j

change_j_b:
	mov byte[offset_j], 1
	mov dh, 1
	jmp return_j


jmp $;环

times 510 - ($ - $$) db 0
db 0x55, 0xaa

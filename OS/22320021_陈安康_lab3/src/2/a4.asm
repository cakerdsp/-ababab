%include "boot.inc"
org 0x7e00
[bits 16]

;空描述符
mov dword [GDT_START_ADDRESS+0x00],0x00
mov dword [GDT_START_ADDRESS+0x04],0x00  

;创建描述符，这是一个数据段，对应0~4GB的线性地址空间
mov dword [GDT_START_ADDRESS+0x08],0x0000ffff    ; 基地址为0，段界限为0xFFFFF
mov dword [GDT_START_ADDRESS+0x0c],0x00cf9200    ; 粒度为4KB，存储器段描述符 

;建立保护模式下的堆栈段描述符      
mov dword [GDT_START_ADDRESS+0x10],0x00000000    ; 基地址为0x00000000，界限0x0 
mov dword [GDT_START_ADDRESS+0x14],0x00409600    ; 粒度为1个字节

;建立保护模式下的显存描述符   
mov dword [GDT_START_ADDRESS+0x18],0x80007fff    ; 基地址为0x000B8000，界限0x07FFF 
mov dword [GDT_START_ADDRESS+0x1c],0x0040920b    ; 粒度为字节

;创建保护模式下平坦模式代码段描述符
mov dword [GDT_START_ADDRESS+0x20],0x0000ffff    ; 基地址为0，段界限为0xFFFFF
mov dword [GDT_START_ADDRESS+0x24],0x00cf9800    ; 粒度为4kb，代码段描述符 

;初始化描述符表寄存器GDTR
mov word [pgdt], 39      ;描述符表的界限   
lgdt [pgdt]
      
in al,0x92                         ;南桥芯片内的端口 
or al,0000_0010B
out 0x92,al                        ;打开A20

cli                                ;中断机制尚未工作
mov eax,cr0
or eax,1
mov cr0,eax                        ;设置PE位
      
;以下进入保护模式
jmp dword CODE_SELECTOR:protect_mode_begin

;16位的描述符选择子：32位偏移
;清流水线并串行化处理器
[bits 32]           
protect_mode_begin:                              

mov eax, DATA_SELECTOR                     ;加载数据段(0..4GB)选择子
mov ds, eax
mov es, eax
mov eax, STACK_SELECTOR
mov ss, eax
mov eax, VIDEO_SELECTOR
mov gs, eax



xor ecx, ecx
xor eax, eax
xor ebx, ebx
loop_pre:
	imul ebx, ecx, 2
	mov word[gs:ebx], ax
	add ecx, 1
	cmp ecx, 2000
	je out_loop_pre		
	jmp loop_pre

out_loop_pre:



i db 2
j db 0
offset_i db 1
offset_j db 1
xor edx, edx

loop:	
	call random
	;mov ah, 0x03
	;mov al, 'A'
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




random:
	push edx
	push ebx
	xor eax, eax
	xor ebx, ebx
	xor edx, edx
	mov eax, [randomval]
	imul eax, 17
	add eax, 12345
	mov ebx, 25
	idiv ebx
	mov eax, edx
	mov bl, 123
	imul dx, bx
	mov ah, dl
	add al, 'A'
	mov [randomval], al
	pop ebx
	pop edx
	ret



jmp $ ; 死循环

pgdt dw 0
     dd GDT_START_ADDRESS

bootloader_tag db 'run bootloader'
bootloader_tag_end:

protect_mode_tag db 'enter protect mode'
protect_mode_tag_end:

randomval db 0

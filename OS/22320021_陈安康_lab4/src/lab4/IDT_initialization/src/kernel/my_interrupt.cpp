#include "my_interrupt.h"
#include "asm_utils.h"
//最初想要尝试通过C语言调用汇编语言来实现的，结果没能实现，这个文件作废了
void my_interrupt() {
    asm_hello_world();
    char str[] = "Interrupt happend!";
    asm_my_interrupt(str);

    //asm_unhandled_interrupt();
    return;
}
#include "asm_utils.h"
#include "interrupt.h"
#include "stdio.h"
#include "program.h"
#include "thread.h"
#include "sync.h"
#include "memory.h"
#include "stdlib.h"
#include "os_constant.h"
// 屏幕IO处理器
STDIO stdio;
// 中断管理器
InterruptManager interruptManager;
// 程序管理器
ProgramManager programManager;
// 内存管理器
MemoryManager memoryManager;


void second_thread(void *arg) {
    char *p1 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 1);
    printf("%x\n", p1);
    printf("%x\n", memoryManager.vaddr2paddr((int)p1));
}


void first_thread(void *arg)
{
    // 第1个线程不可以返回
    // stdio.moveCursor(0);
    // for (int i = 0; i < 25 * 80; ++i)
    // {
    //     stdio.print(' ');
    // }
    // stdio.moveCursor(0);
    //对于物理页，从0号物理页开始，一个一个物理页去判断，直到找到足够大的可以容纳的物理页的空闲物理页的大小。




    // // 这些是测试best_fit物理页置换算法的用例
    // char *p1 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 10);
    // char *p2 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 20);
    // char *p3 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 30);
    // char *p4 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 10);
    // char *p5 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 30);
    // char *p6 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 30);
    // char *p7 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 30);
    // printf("%x %x %x %x %x %x %x\n", p1, p2, p3, p4, p5, p6, p7);
    // // memset(p1, 1, PAGE_SIZE * 10);
    // memoryManager.releasePages(AddressPoolType::KERNEL, (int)p2, 20);
    // memoryManager.releasePages(AddressPoolType::KERNEL, (int)p4, 10);
    // memoryManager.releasePages(AddressPoolType::KERNEL, (int)p6, 30);
    // p2 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 10);
    // printf("%x\n", p2);
    // p4 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 15);
    // printf("%x\n", p4);




    // //这些是页面置换算法的测试用例
    // char *p1 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 10);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1));
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 2 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 7 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 8 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 2 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 3 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();
    // programManager.running -> memory_queue.reference((int)(p1) + 10 * PAGE_SIZE);
    // programManager.running -> memory_queue.print();






    //下面是测试bug的用例，这里为了展示bug还将bitmap中set函数加了延迟，如果要正常运行需要注释掉延迟
    int pid = programManager.executeThread(second_thread, nullptr, "second thread", 10);
    if (pid == -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }
        char *p1 = (char *)memoryManager.allocatePages(AddressPoolType::KERNEL, 1);
        printf("%x\n", p1);
        printf("%x\n", memoryManager.vaddr2paddr((int)p1));

    asm_halt();
}



extern "C" void setup_kernel()
{

    // 中断管理器
    interruptManager.initialize();
    interruptManager.enableTimeInterrupt();
    interruptManager.setTimeInterrupt((void *)asm_time_interrupt_handler);

    // 输出管理器
    stdio.initialize();

    // 进程/线程管理器
    programManager.initialize();

    // 内存管理器
    memoryManager.openPageMechanism();
    memoryManager.initialize();

    // 创建第一个线程
    int pid = programManager.executeThread(first_thread, nullptr, "first thread", 1);
    if (pid == -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }

    ListItem *item = programManager.readyPrograms.front();
    PCB *firstThread = ListItem2PCB(item, tagInGeneralList);
    firstThread->status = RUNNING;
    programManager.readyPrograms.pop_front();
    programManager.running = firstThread;
    asm_switch_thread(0, firstThread);

    asm_halt();
}

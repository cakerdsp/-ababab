#include "asm_utils.h"
#include "interrupt.h"
#include "stdio.h"
#include "program.h"
#include "thread.h"

// 屏幕IO处理器
STDIO stdio;
// 中断管理器
InterruptManager interruptManager;
// 程序管理器
ProgramManager programManager;

void third_thread(void *arg) {
    printf("pid %d name \"%s\": Hello World!\n", programManager.running->pid, programManager.running->name);
    while(1) {

    }
}
void second_thread(void *arg) {
    printf("pid %d name \"%s\": Hello World!\n", programManager.running->pid, programManager.running->name);
}
void first_thread(void *arg)
{
    // 第1个线程不可以返回
    printf("pid %d name \"%s\": Hello World!\n", programManager.running->pid, programManager.running->name);
    if (!programManager.running->pid)
    {
        //programManager.executeThread(second_thread, nullptr, "second thread", 1);
        //programManager.executeThread(third_thread, nullptr, "third thread", 1);
    }
    asm_halt();
}

class param {
public:
    int a;
    int b;
    param() : a(0), b(0) {

    }
    param(int a, int b) : a(a),b(b) {

    }
};
void my_thread_schedule0(void* arg) {
    // int k = 3;
    // while(k--) {
    //     printf("the running thread is 0\n");
    // }
    // return ;
    long long count = 0;
    while(true) {
        count ++;
        if(count == 100000000) {
            printf("the running thread is 0\n");
            count = 0;
        }
    };
}
void child1(void* arg) {
    int k = 3;
    int count = 0;
    while(true) {
        count ++;
        if(count == 100000000) {
            printf("    the running thread is the child for thread1\n");           
            count = 0; 
        }
    }
}
void my_thread_schedule1(void* arg) {
    int k = 3;
    long long count = 0;
    while(k--) {
        // ++count;
        // if(count == 100000000) {
            printf("the running thread is 1\n");
            // count = 0;
        // }
    }
    int pid = programManager.executeThread(child1, nullptr, "child1", 6);
    if (pid == -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }  
    printf("thread1 is over!\n");
    return ;
}

void child2(void* arg) {
    int k = 3;
    int count = 0;
    while(true) {
        count ++;
        if(count == 100000000) {
            printf("    the running thread is the child for thread2\n");           
            count = 0; 
        }
    }
}
void my_thread_schedule2(void* arg) {
    int k = 3;
    long long count = 0;
    while(k--) {
        // ++count;
        // if(count == 100000000) {
            printf("the running thread is 2\n");
            // count = 0;
        // }
    }
    int pid = programManager.executeThread(child2, nullptr, "child2", 6);
    if (pid == -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }  
    printf("thread2 is over!\n");
    return ;
}

void my_thread(void *arg) {
    int ans = (*(param*)arg).a + (*(param*)arg).b;
    printf("pid %d name \"%s\": the param passed to thread is %d %d \nthe sum is %d\n",programManager.running->pid, programManager.running->name, (*(param*)arg).a, (*(param*)arg).b, ans);
    asm_halt();
}

//用与gdb调试的线程，有死循环
void thread1(void* arg) {
    int count = 0;
    while(true) {
        ++count;
        if(count == 10000000) {
        printf("this is thread for thread schedule debug,this is 1\n");            
        count = 0;
        }
    }
}
//用于gdb调试的线程，没有死循环
void thread2(void* arg) {
    printf("this is thread for thread schedule debug,this is 2\n");
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
    param p(2,2);
    // 创建第一个线程
    // int pid = programManager.executeThread(my_thread, &p, "my thread", 1);
    // if (pid == -1)
    // {
    //     printf("can not execute thread\n");
    //     asm_halt();
    // }  
    int pid = programManager.executeThread(my_thread_schedule0, nullptr, "my thread schedule0", 10);
    if (pid == -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }  
    int pid1 = programManager.executeThread(my_thread_schedule1, nullptr, "my thread schedule1", 5);
    if (pid1== -1)
    {
        printf("can not execute thread\n");
        asm_halt();
    }   
    int pid2 = programManager.executeThread(my_thread_schedule2, nullptr, "my thread schedule2", 3);
    if (pid2 == -1)
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

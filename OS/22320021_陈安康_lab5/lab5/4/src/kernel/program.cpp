#include "program.h"
#include "stdlib.h"
#include "interrupt.h"
#include "asm_utils.h"
#include "stdio.h"
#include "thread.h"
#include "os_modules.h"

const int PCB_SIZE = 4096;                   // PCB的大小，4KB。
char PCB_SET[PCB_SIZE * MAX_PROGRAM_AMOUNT]; // 存放PCB的数组，预留了MAX_PROGRAM_AMOUNT个PCB的大小空间。
bool PCB_SET_STATUS[MAX_PROGRAM_AMOUNT];     // PCB的分配状态，true表示已经分配，false表示未分配。

ProgramManager::ProgramManager()
{
    initialize();
}

void ProgramManager::initialize()
{
    allPrograms.initialize();
    readyPrograms.initialize();
    running = nullptr;

    for (int i = 0; i < MAX_PROGRAM_AMOUNT; ++i)
    {
        PCB_SET_STATUS[i] = false;
    }
}

int ProgramManager::executeThread(ThreadFunction function, void *parameter, const char *name, int priority)
{
    // 关中断，防止创建线程的过程被打断
    bool status = interruptManager.getInterruptStatus();
    interruptManager.disableInterrupt();

    // 分配一页作为PCB
    PCB *thread = allocatePCB();

    if (!thread)
        return -1;

    // 初始化分配的页
    memset(thread, 0, PCB_SIZE);

    for (int i = 0; i < MAX_PROGRAM_NAME && name[i]; ++i)
    {
        thread->name[i] = name[i];
    }

    thread->status = ProgramStatus::READY;
    thread->priority = priority;
    thread->ticks = priority * 10;
    thread->ticksPassedBy = 0;
    thread->pid = ((int)thread - (int)PCB_SET) / PCB_SIZE;

    // 线程栈
    thread->stack = (int *)((int)thread + PCB_SIZE);
    thread->stack -= 7;
    thread->stack[0] = 0;
    thread->stack[1] = 0;
    thread->stack[2] = 0;
    thread->stack[3] = 0;
    thread->stack[4] = (int)function;
    thread->stack[5] = (int)program_exit;
    thread->stack[6] = (int)parameter;

    allPrograms.push_back(&(thread->tagInAllList));
    readyPrograms.push_back(&(thread->tagInGeneralList));

    // 恢复中断
    interruptManager.setInterruptStatus(status);

    printf("call for create thread!\n");
    ProgramManager::PSA();

    return thread->pid;
}
// RR算法的调度函数
void ProgramManager::schedule()
{
    bool status = interruptManager.getInterruptStatus();
    interruptManager.disableInterrupt();

    if (readyPrograms.size() == 0)
    {
        interruptManager.setInterruptStatus(status);
        return;
    }

    if (running->status == ProgramStatus::RUNNING)
    {
        running->status = ProgramStatus::READY;
        running->ticks = running->priority * 10;
        readyPrograms.push_back(&(running->tagInGeneralList));
    }
    else if (running->status == ProgramStatus::DEAD)
    {
        releasePCB(running);
    }

    ListItem *item = readyPrograms.front();
    PCB *next = ListItem2PCB(item, tagInGeneralList);
    PCB *cur = running;
    next->status = ProgramStatus::RUNNING;
    running = next;
    readyPrograms.pop_front();

    asm_switch_thread(cur, next);

    interruptManager.setInterruptStatus(status);
}

void ProgramManager::FCFS() {
    bool status = interruptManager.getInterruptStatus();
    interruptManager.disableInterrupt();
    releasePCB(running);    
    if (readyPrograms.size() == 0)
    {
        interruptManager.setInterruptStatus(status);
        //等待直到队列不为空
        while(readyPrograms.size() == 0);
    }
    ListItem *item = readyPrograms.front();
    PCB *next = ListItem2PCB(item, tagInGeneralList);
    next->status = ProgramStatus::RUNNING;
    running = next;
    readyPrograms.pop_front();
    asm_switch_thread(0, next);
    interruptManager.setInterruptStatus(status);       
}


void ProgramManager::PSA()
{
    bool status = interruptManager.getInterruptStatus();
    interruptManager.disableInterrupt();

    if (readyPrograms.size() == 0)
    {
        interruptManager.setInterruptStatus(status);
        return;
    }


    // int min = running -> priority;
    PCB* next = nullptr;
    ListItem* minlist = nullptr;
    //这里想要让running初始为nullptr时也可以切换，只需要在判断时改成如下判断：
    // if(running && running->status != ProgramStatus::DEAD)
    if(running->status != ProgramStatus::DEAD) {
        next = running;
        minlist = &(running -> tagInGeneralList);
    } else {
        minlist = readyPrograms.front();
        next = ListItem2PCB(minlist, tagInGeneralList);
    }
    ListItem *item = readyPrograms.front();
    while(item) {
        PCB* it = ListItem2PCB(item, tagInGeneralList);
        if(it -> priority < next -> priority || ((next == running) && (it -> priority == next -> priority))) {
            next = it;
            // min = it -> priority;
            minlist = item;
        }    
        item = item -> next;
    }
    // PCB *next = ListItem2PCB(item, tagInGeneralList);

    PCB *cur = running;
    if (cur -> status == ProgramStatus::RUNNING)
    {

        cur->status = ProgramStatus::READY;
        readyPrograms.push_back(&(cur->tagInGeneralList));
        if(cur -> ticks == 0)
            cur->ticks = cur->priority * 10;
    } else if (running->status == ProgramStatus::DEAD) {
        releasePCB(cur);
    }



    next->status = ProgramStatus::RUNNING;
    running = next;
    readyPrograms.erase(minlist);

    asm_switch_thread(cur, next);

    interruptManager.setInterruptStatus(status);
}

void program_exit()
{
    PCB *thread = programManager.running;
    thread->status = ProgramStatus::DEAD;
    //开启这个要注释掉下面的内容
    // programManager.FCFS();



    if (thread->pid)
    {
        // programManager.schedule();
        programManager.PSA();
    }
    else
    {
        interruptManager.disableInterrupt();
        printf("halt\n");
        asm_halt();
    }

}

PCB *ProgramManager::allocatePCB()
{
    for (int i = 0; i < MAX_PROGRAM_AMOUNT; ++i)
    {
        if (!PCB_SET_STATUS[i])
        {
            PCB_SET_STATUS[i] = true;
            return (PCB *)((int)PCB_SET + PCB_SIZE * i);
        }
    }

    return nullptr;
}

void ProgramManager::releasePCB(PCB *program)
{
    int index = ((int)program - (int)PCB_SET) / PCB_SIZE;
    PCB_SET_STATUS[index] = false;
}
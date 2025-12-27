#include "sync.h"
#include "asm_utils.h"
#include "stdio.h"
#include "os_modules.h"
#include "program.h"
SpinLock::SpinLock()
{
    initialize();
}

void SpinLock::initialize()
{
    bolt = 0;
}

void SpinLock::lock()
{
    uint32 key = 1;

    do
    {
        asm_atomic_exchange(&key, &bolt);
        //printf("pid: %d\n", programManager.running->pid);
    } while (key);
}

void SpinLock::my_lock() {
    uint32 flag = 1;
    do {
        asm_atomic_lock(&bolt, &flag);
    } while(flag);
}

void SpinLock::unlock()
{
    bolt = 0;
}



Semaphore::Semaphore()
{
    initialize(10);
}

void Semaphore::initialize(uint32 size)
{
    this -> size = size;
    this -> counter = 0;
    semLock.initialize();
    waiting_p.initialize();
    waiting_c.initialize();
}

void Semaphore::producer_P()
{
    PCB *cur = nullptr;

    while (true)
    {
        semLock.lock();
        if (counter < size)
        {
            ++counter;
            // semLock.unlock();
            return;
        }

        cur = programManager.running;
        waiting_p.push_back(&(cur->tagInGeneralList));
        cur->status = ProgramStatus::BLOCKED;

        semLock.unlock();
        programManager.schedule();
    }
}

void Semaphore::consumer_P() {
    PCB *cur = nullptr;

    while (true)
    {
        semLock.lock();
        if (counter > 0)
        {
            --counter;
            // semLock.unlock();
            return;
        }

        cur = programManager.running;
        waiting_c.push_back(&(cur->tagInGeneralList));
        cur->status = ProgramStatus::BLOCKED;

        semLock.unlock();
        programManager.schedule();
    }
}

void Semaphore::producer_V()
{
    if (waiting_c.size())
    {
        PCB *program = ListItem2PCB(waiting_c.front(), tagInGeneralList);
        waiting_c.pop_front();
        semLock.unlock();
        programManager.MESA_WakeUp(program);
    }
    else
    {
        semLock.unlock();
    }
}
void Semaphore::consumer_V()
{
    if (waiting_p.size())
    {
        PCB *program = ListItem2PCB(waiting_p.front(), tagInGeneralList);
        waiting_p.pop_front();
        semLock.unlock();
        programManager.MESA_WakeUp(program);
    }
    else
    {
        semLock.unlock();
    }
}
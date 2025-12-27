#include "asm_utils.h"
#include "interrupt.h"
#include "stdio.h"
#include "program.h"
#include "thread.h"
#include "sync.h"


// 屏幕IO处理器
STDIO stdio;
// 中断管理器
InterruptManager interruptManager;
// 程序管理器
ProgramManager programManager;

Semaphore semaphore;

int cheese_burger;

#define PHILOSOPHER_NUM 5

class Fork : public Semaphore {
    public:
        Fork(int id) : Semaphore(1), id(id) {

        }
        void tryFork() {
            P();
            printf("have got the fork, the fork id is %d\n",id);
        } 
        void releaseFork() {
            printf("release the fork, the id is %d\n",id);
            V();
        }
        int getid() {
            return id;
        }
    private:
        int id;
};

class Philosopher {
    public:
        Philosopher(Fork* left, Fork* right, int id) : leftfork(left), rightfork(right), id(id) {

        }
        void think() {
            int count = 0;
            while(count) {
                count--;
            }           
        }
        void eat() {
            // if(id % 2 == 0) {
                printf("Philosopher id %d, try to get the fork whose id is %d\n",id, leftfork -> getid());
                leftfork -> tryFork();
                int delay = 0;
                while(delay) {
                    delay--;
                }
                printf("Philosopher id %d, try to get the fork whose id is %d\n",id, rightfork -> getid());
                rightfork -> tryFork();
                printf("Philosopher id %d, is eating!!!!\n",id);
                int count = 100000000;
                while(count) {
                    count--;
                }
                printf("Philosopher id %d, release fork:\n",id);
                rightfork -> releaseFork();
                leftfork -> releaseFork();
            // } else {
            //     printf("Philosopher id %d, try to get the fork whose id is %d\n",id, rightfork -> getid());
            //     rightfork -> tryFork();
            //     int delay = 0xfffffff;
            //     while(delay) {
            //         delay--;
            //     }
            //     printf("Philosopher id %d, try to get the fork whose id is %d\n",id, leftfork -> getid());
            //     leftfork -> tryFork();
            //     printf("Philosopher id %d, is eating!!!!\n",id);
            //     int count = 100000000;
            //     while(count) {
            //         count--;
            //     }
            //     printf("Philosopher id %d, release fork:\n",id);
            //     leftfork -> releaseFork();
            //     rightfork -> releaseFork();
            // }

        }
        int getid() {
            return id;
        }
    private:
        int id;
        Fork* leftfork;
        Fork* rightfork;
};

// 5支筷子
// Fork forks[PHILOSOPHER_NUM] = {Fork(0), Fork(1), Fork(2), Fork(3), Fork(4)};
// Philosopher philosophers[PHILOSOPHER_NUM] = {Philosopher(forks[0], forks[1], 0), Philosopher(forks[1], forks[2], 1), Philosopher(forks[2], forks[3], 2), Philosopher(forks[3], forks[4], 3), Philosopher(forks[4], forks[0], 4)};
// // Philosopher* philosophers[PHILOSOPHER_NUM];


void thread_philosopher(void* arg) {
    while(true) {
       ((Philosopher*)arg) -> think();
       ((Philosopher*)arg) -> eat();
        int count = 100000000;
        while(count) {
            count--;
        } 
    }
}

void first_thread_DPP(void *arg)
{
    // 5支筷子
    Fork forks[PHILOSOPHER_NUM] = {Fork(0), Fork(1), Fork(2), Fork(3), Fork(4)};
    Philosopher philosophers[PHILOSOPHER_NUM] = {Philosopher(&forks[0], &forks[1], 0), Philosopher(&forks[1], &forks[2], 1), Philosopher(&forks[2], &forks[3], 2), Philosopher(&forks[3], &forks[4], 3), Philosopher(&forks[4], &forks[0], 4)};
    // 第1个线程不可以返回
    stdio.moveCursor(0);
    for (int i = 0; i < 25 * 80; ++i)
    {
        stdio.print(' ');
    }
    stdio.moveCursor(0);
    // for(int i = 0; i < PHILOSOPHER_NUM; i++) {
    //     printf("forks[%d]\n", forks[i].getid());
    // }
    // for(int i = 0; i < PHILOSOPHER_NUM; i++) {
    //     printf("forks[%d]\n", philosophers[i].getid());
    // }
    for(int i = 0; i < PHILOSOPHER_NUM; i++) {
        // philosophers[i] = new Philosopher(forks[i], forks[(i + 1) % PHILOSOPHER_NUM], i);
        char str[13] = "philosopher";
        str[11] = i + '0';
        str[12] = '\0';
        programManager.executeThread(thread_philosopher, &philosophers[i], str, 1);
    }

    // programManager.executeThread(a_mother, nullptr, "second thread", 1);

    asm_halt();
}

void a_mother(void *arg)
{
    semaphore.P();
    int delay = 0;

    printf("mother: start to make cheese burger, there are %d cheese burger now\n", cheese_burger);
    // make 10 cheese_burger
    cheese_burger += 10;

    printf("mother: oh, I have to hang clothes out.\n");
    // hanging clothes out
    delay = 0xfffffff;
    while (delay)
        --delay;
    // done

    printf("mother: Oh, Jesus! There are %d cheese burgers\n", cheese_burger);
    semaphore.V();
}

void a_naughty_boy(void *arg)
{
    semaphore.P();
    printf("boy   : Look what I found!\n");
    // eat all cheese_burgers out secretly
    cheese_burger -= 10;
    // run away as fast as possible
    semaphore.V();
}

void first_thread(void *arg)
{
    // 第1个线程不可以返回
    stdio.moveCursor(0);
    for (int i = 0; i < 25 * 80; ++i)
    {
        stdio.print(' ');
    }
    stdio.moveCursor(0);

    cheese_burger = 0;
    semaphore.initialize(1);

    programManager.executeThread(a_mother, nullptr, "second thread", 1);
    programManager.executeThread(a_naughty_boy, nullptr, "third thread", 1);

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

    // 创建第一个线程
    int pid = programManager.executeThread(first_thread_DPP, nullptr, "first thread", 1);
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

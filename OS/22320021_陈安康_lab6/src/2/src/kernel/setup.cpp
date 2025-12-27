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
//信号量
Semaphore semaphore;


int shared_variable;
SpinLock aLock;

int cheese_burger;
#define BUFFER_SIZE 10
class Buffer {
    //缓冲区，大小定义为10个字节
    char buffer[BUFFER_SIZE];
    //head是指向队列的第一个数据，也是消费者开始拿数据的第一个位置
    //end指向队尾的下一个元素，也就是生产者需要放置数据的位置
    //当head == end，current_size = 0, 缓冲区为空，current_size = BUFFER_SIZE,缓冲区满
    int current_size;
    int head, end;
public:
    Buffer() : current_size(0), head(0), end(0) {

    }
    void put_data(char a) {
        buffer[end] = a;
        end = (end + 1) % BUFFER_SIZE;
        ++current_size;
        printf("producer has put a data %c in buffer, the current_size of buffer is %d\n", a, current_size);
        isvaild();
    }
    void get_data() {
        head = (head + 1) % BUFFER_SIZE;
        --current_size;
        printf("producer has get a data in buffer, the current_size of buffer is %d\n", current_size);
        isvaild();
    }
    void isvaild() {
        if(current_size > BUFFER_SIZE || current_size < 0) {
            printf("the buffer has go wrong!!!");
            // 触发除0错误来中断执行
            int interrupt = 1 / 0;
        }
    }

};
Buffer b;

void a_mother(void *arg)
{
    aLock.my_lock();
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
    aLock.unlock();
}

void a_naughty_boy(void *arg)
{
    aLock.my_lock();
    printf("boy   : Look what I found!\n");
    // eat all cheese_burgers out secretly
    cheese_burger -= 10;
    // run away as fast as possible
    aLock.unlock();
}


void producer1(void* arg) {
    while(true) {
        semaphore.producer_P();
        b.put_data('1'); 
        semaphore.producer_V();
        int c = 10000000;
        while(c--);
    }
}

void producer2(void* arg) {
    while(true) {
        semaphore.producer_P();
        b.put_data('2'); 
        semaphore.producer_V();
        int c = 1000000000;
        while(c--);
    }
}
// void producer3(void* arg) {
//     while(true) {
//         b.put_data('3'); 
//         int c = 1000000000;
//         while(c--);
//     }
// }
void consumer1(void* arg) {
    while(true) {
        semaphore.consumer_P();
        b.get_data(); 
        semaphore.consumer_V();
        int c = 1000000000;
        while(c--);
    }
}
void consumer2(void* arg) {
    while(true) {
        b.get_data(); 
        int c = 100000000;
        while(c--);
    }
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
    aLock.initialize();

    programManager.executeThread(a_mother, nullptr, "second thread", 1);
    programManager.executeThread(a_naughty_boy, nullptr, "third thread", 1);

    asm_halt();
}
void first_thread_PC_problem(void* arg) {
    stdio.moveCursor(0);
    semaphore.initialize(BUFFER_SIZE);
    for (int i = 0; i < 25 * 80; ++i)
    {
        stdio.print(' ');
    }
    stdio.moveCursor(0);
    programManager.executeThread(producer1, nullptr, "producer1", 1);
    programManager.executeThread(producer2, nullptr, "producer2", 1);
    programManager.executeThread(consumer1, nullptr, "consumer1", 1);
    // programManager.executeThread(producer3, nullptr, "producer3", 1);
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
    int pid = programManager.executeThread(first_thread_PC_problem, nullptr, "first thread", 1);
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

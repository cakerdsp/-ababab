#ifndef THREAD_H
#define THREAD_H

#include "list.h"
#include "os_constant.h"
#include "stdio.h"
#define MEMORY_QUEUE_SIZE 3
typedef void (*ThreadFunction)(void *);

enum ProgramStatus
{
    CREATED,
    RUNNING,
    READY,
    BLOCKED,
    DEAD
};



typedef struct Node {
    //虚拟页号
    int address;
    //LRU
    int lru;
} Node;
class VirtualPage_Queue {
    //该线程现有的内存队列
    Node queue[MEMORY_QUEUE_SIZE];
    //队列的大小
    int size;
    public:
    VirtualPage_Queue() {
        initialize();
    }
    void initialize() {
        size = MEMORY_QUEUE_SIZE;
        for(int i = 0; i < size; ++i) {
            queue[i].address = 0;
            queue[i].lru = 0;
        }
    }
    void swap(int index, int addr) {
        queue[index].address = addr;
        queue[index].lru = 0;
    }
    void reference(int addr) {
        //判断是否访问非法虚拟页
        int *pte = (int *)toPTE_thread(addr);
        if(!(*pte & 0x00000001)) {
            printf("reference error!!!\n");
            return;
        }
        //LRU算法
        int max = 0, index;
        for(int i = 0; i < size; ++i) {
            if(queue[i].address == addr) {
                queue[i].lru = 0;
                return;
            }
            ++queue[i].lru;
            if(queue[i].lru > max) {
                max = queue[i].lru;
                index = i;
            }
        }

        swap(index, addr);
    }
    void print() {
        printf("queue : ");
        for(int i = 0;i < size; ++i) {
            printf("%x ", queue[i].address);
        }
        printf("\n");
    }
    int getsize() {
        return size;
    }
    int toPTE_thread(const int virtualAddress)
    {
        return (0xffc00000 + ((virtualAddress & 0xffc00000) >> 10) + (((virtualAddress & 0x003ff000) >> 12) * 4));
    }
};
struct PCB
{
    int *stack;                      // 栈指针，用于调度时保存esp
    char name[MAX_PROGRAM_NAME + 1]; // 线程名
    enum ProgramStatus status;       // 线程的状态
    int priority;                    // 线程优先级
    int pid;                         // 线程pid
    int ticks;                       // 线程时间片总时间
    int ticksPassedBy;               // 线程已执行时间
    ListItem tagInGeneralList;       // 线程队列标识
    ListItem tagInAllList;           // 线程队列标识
    VirtualPage_Queue memory_queue;         // 页面置换队列
};

#endif
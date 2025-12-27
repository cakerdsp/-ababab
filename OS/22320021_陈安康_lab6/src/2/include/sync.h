#ifndef SYNC_H
#define SYNC_H

#include "os_type.h"
#include "list.h"
class SpinLock
{
private:
    uint32 bolt;
public:
    SpinLock();
    void initialize();
    void lock();
    void unlock();
    void my_lock();
};



class Semaphore
{
private:
    //计数信号量
    uint32 counter;
    uint32 size;
    //生产者和消费者的挂起队列
    List waiting_p, waiting_c;
    //自旋锁保互斥
    SpinLock semLock;

public:
    Semaphore();
    void initialize(uint32 counter);
    void producer_P();
    void consumer_P();
    void producer_V();
    void consumer_V();

};
#endif
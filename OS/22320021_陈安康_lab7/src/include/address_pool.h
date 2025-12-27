#ifndef ADDRESS_POOL_H
#define ADDRESS_POOL_H

#include "bitmap.h"
#include "os_type.h"
//startAddress是资源的起始地址
//分配释放只是释放位图里面的东西
//这个相当于把位图和资源的某些信息封装了一下
class AddressPool
{
public:
    BitMap resources;
    int startAddress;

public:
    AddressPool();
    // 初始化地址池
    void initialize(char *bitmap, const int length, const int startAddress);
    // 从地址池中分配count个连续页，成功则返回第一个页的地址，失败则返回-1
    int allocate(const int count);
    // 释放若干页的空间
    void release(const int address, const int amount);
};

#endif
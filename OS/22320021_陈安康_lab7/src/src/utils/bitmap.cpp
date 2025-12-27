#include "bitmap.h"
#include "stdlib.h"
#include "stdio.h"
//这个bitmap一定要和资源是一一对应的！不然就会出错！！！！
BitMap::BitMap()
{
}

//依据实现来看，这个length是位数，多大代表有多少个管理的资源，但我不知道管理的资源的大小，这里面是不可见的。
void BitMap::initialize(char *bitmap, const int length)
{
    this->bitmap = bitmap;
    this->length = length;
    //转换成涉及的字节数。
    int bytes = ceil(length, 8);
    //我们实现不了按位去赋值，只能按字节去赋值，所以我们不得已按照字节去赋值，这样严格来说会导致过多的0被设置，但对结果没有影响，因为所有操作都是以字节为单位的。
    for (int i = 0; i < bytes; ++i)
    {
        bitmap[i] = 0;
    }
}
//因为1位代表管理资源的状态，所以这里相当于分页找到页号，查页内偏移。，并且位在宏观上不是连续的，而是按字节去排序的
bool BitMap::get(const int index) const
{
    int pos = index / 8;
    int offset = index % 8;

    return (bitmap[pos] & (1 << offset));
}
//设置也是一样
void BitMap::set(const int index, const bool status)
{
    int pos = index / 8;
    int offset = index % 8;

    //测试bug加的延迟，如果不用请注释掉
    int c = 0xfffffff;
    while(c) {
        c--;
    }


    
    // 清0
    bitmap[pos] = bitmap[pos] & (~(1 << offset));

    // 置1
    if (status)
    {
        bitmap[pos] = bitmap[pos] | (1 << offset);
    }
}

// int BitMap::allocate(const int count)
// {
//     if (count == 0)
//         return -1;
//     int index, empty, start;
//     index = 0;
//     while (index < length)
//     {
//         // 越过已经分配的资源
//         while (index < length && get(index))
//             ++index;
//         // 不存在连续的count个资源
//         if (index == length)
//             return -1;
//         // 找到1个未分配的资源
//         // 检查是否存在从index开始的连续count个资源
//         empty = 0;
//         start = index;
//         while ((index < length) && (!get(index)) && (empty < count))
//         {
//             ++empty;
//             ++index;
//         }
//         // 存在连续的count个资源
//         if (empty == count)
//         {
//             for (int i = 0; i < count; ++i)
//             {
//                 set(start + i, true);
//             }

//             return start;
//         }
//     }
//     return -1;
// }



int BitMap::allocate(const int count)
{
    if (count == 0)
        return -1;
    int index, empty, start;
    int best_fit = -1, gap = length;
    index = 0;
    while (index < length)
    {
        // 越过已经分配的资源
        while (index < length && get(index))
            ++index;
        // 不存在连续的count个资源
        if (index == length)
            return -1;
        // 找到1个未分配的资源
        // 检查是否存在从index开始的连续count个资源
        empty = 0;
        start = index;
        while ((index < length) && (!get(index)))
        {
            ++empty;
            ++index;
        }
        if(empty - count >= 0 && empty - count < gap) {
            gap = empty - count;
            best_fit = start;
        }
    }
    if (best_fit != -1)
    {
        for (int i = 0; i < count; ++i)
        {
            set(best_fit + i, true);
        }
    }
    return best_fit;
}



void BitMap::release(const int index, const int count)
{
    for (int i = 0; i < count; ++i)
    {
        set(index + i, false);
    }
}

char *BitMap::getBitmap()
{
    return (char *)bitmap;
}

int BitMap::size() const
{
    return length;
}
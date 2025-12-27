// parallel_for.h
#ifndef PARALLEL_FOR_H
#define PARALLEL_FOR_H

#include <pthread.h>

// 调度类型定义
#define SCHEDULE_STATIC 0   // 静态调度
#define SCHEDULE_DYNAMIC 1  // 动态调度
#define SCHEDULE_GUIDED 2   // 引导调度

// 原始接口 - 默认使用静态调度
void parallel_for(int start, int end, int inc,
                  void (*func)(int, void *),
                  void *args, int num_threads);

// 扩展接口 - 支持选择调度类型和块大小
void parallel_for_schedule(int start, int end, int inc,
                         void (*func)(int, void *),
                         void *args, int num_threads,
                         int schedule_type, int chunk_size);

#endif
#include "parallel_for.h"
#include <stdlib.h>

// 调度类型枚举
#define SCHEDULE_STATIC 0   // 静态调度
#define SCHEDULE_DYNAMIC 1  // 动态调度
#define SCHEDULE_GUIDED 2   // 引导调度

typedef struct {
    int start, end, inc;
    void (*func)(int, void *);
    void *args;
    int schedule_type;      // 调度类型
    int chunk_size;         // 块大小
    int *next_index;        // 动态调度的下一个索引
    int num_threads;
    pthread_mutex_t *mutex; // 用于动态调度的互斥锁
} thread_data;

void *thread_worker(void *arg) {
    thread_data *data = (thread_data *)arg;
    
    // 静态调度 - 每个线程处理预分配的连续区域
    if (data->schedule_type == SCHEDULE_STATIC) {
        for (int i = data->start; i < data->end; i += data->inc) {
            data->func(i, data->args);
        }
    }
    // 动态调度 - 线程动态获取下一个可用的块
    else if (data->schedule_type == SCHEDULE_DYNAMIC) {
        int chunk_size = data->chunk_size > 0 ? data->chunk_size : 1;
        int next_i;
        
        while (1) {
            pthread_mutex_lock(data->mutex);
            next_i = *data->next_index;
            *data->next_index = next_i + chunk_size;
            pthread_mutex_unlock(data->mutex);
            
            if (next_i >= data->end) break;
            
            int end_i = next_i + chunk_size;
            if (end_i > data->end) end_i = data->end;
            
            for (int i = next_i; i < end_i; i += data->inc) {
                data->func(i, data->args);
            }
        }
    }
    // 引导调度 - 块大小随着执行逐渐减小
    else if (data->schedule_type == SCHEDULE_GUIDED) {
        int min_chunk = data->chunk_size > 0 ? data->chunk_size : 1;
        int next_i;
        
        while (1) {
            pthread_mutex_lock(data->mutex);
            next_i = *data->next_index;
            
            // 计算引导块大小 - 剩余工作量除以线程数
            int remaining = data->end - next_i;
            int chunk = (remaining + data->num_threads - 1) / data->num_threads; // 向上取整
            
            if (chunk < min_chunk) chunk = min_chunk;
            if (chunk > remaining) chunk = remaining;
            
            *data->next_index = next_i + chunk;
            pthread_mutex_unlock(data->mutex);
            
            if (next_i >= data->end) break;
            
            int end_i = next_i + chunk;
            if (end_i > data->end) end_i = data->end;
            
            for (int i = next_i; i < end_i; i += data->inc) {
                data->func(i, data->args);
            }
        }
    }
    
    return NULL;
}

void parallel_for_schedule(int start, int end, int inc,
                        void (*func)(int, void *),
                        void *args, int num_threads,
                        int schedule_type, int chunk_size) {
    pthread_t threads[num_threads];
    thread_data td[num_threads];
    
    // 动态和引导调度需要的共享变量
    int next_index = start;
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    
    // 静态调度
    if (schedule_type == SCHEDULE_STATIC) {
        int total = end - start;
        int chunk = total / num_threads;
        int remainder = total % num_threads;
        
        int current_start = start;
        for (int i = 0; i < num_threads; i++) {
            int current_end = current_start + chunk + (i < remainder ? 1 : 0);
            td[i].start = current_start;
            td[i].end = current_end;
            td[i].inc = inc;
            td[i].func = func;
            td[i].args = args;
            td[i].schedule_type = schedule_type;
            td[i].chunk_size = chunk_size;
            td[i].next_index = NULL;
            td[i].mutex = NULL;
            td[i].num_threads = num_threads;
            
            pthread_create(&threads[i], NULL, thread_worker, &td[i]);
            current_start = current_end;
        }
    }
    // 动态和引导调度
    else {
        for (int i = 0; i < num_threads; i++) {
            td[i].start = start;
            td[i].end = end;
            td[i].inc = inc;
            td[i].func = func;
            td[i].args = args;
            td[i].schedule_type = schedule_type;
            td[i].chunk_size = chunk_size;
            td[i].next_index = &next_index;
            td[i].mutex = &mutex;
            td[i].num_threads = num_threads;
            
            pthread_create(&threads[i], NULL, thread_worker, &td[i]);
        }
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // 清理资源
    if (schedule_type != SCHEDULE_STATIC) {
        pthread_mutex_destroy(&mutex);
    }
}

// 保持原有接口兼容性，默认使用静态调度
void parallel_for(int start, int end, int inc,
                  void (*func)(int, void *),
                  void *args, int num_threads) {
    parallel_for_schedule(start, end, inc, func, args, num_threads, SCHEDULE_STATIC, 0);
}
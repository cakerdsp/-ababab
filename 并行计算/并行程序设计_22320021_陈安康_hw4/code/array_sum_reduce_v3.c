#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <sys/time.h>
#include <math.h>



typedef struct {
    int thread_id;
    int num_threads;
    int* array;
    long long size;
    long long* partial_sums;
    int round;
    int max_rounds;
    pthread_mutex_t* mutex;
    pthread_cond_t* cond;
    int* round_completed;
} ThreadArgs;

double get_time_ms() {
   struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}


void* sum_array_reduce(void* arg) {
    ThreadArgs* args = (ThreadArgs*)arg;
    int thread_id = args->thread_id;
    int num_threads = args->num_threads;
    int* array = args->array;
    long long size = args->size;
    long long* partial_sums = args->partial_sums;
    int max_rounds = args->max_rounds;
    pthread_mutex_t* mutex = args->mutex;
    pthread_cond_t* cond = args->cond;
    int* round_completed = args->round_completed;
    long long elements_per_thread = size / num_threads;
    long long start = thread_id * elements_per_thread;
    long long end = (thread_id == num_threads - 1) ? size : start + elements_per_thread;

    long long local_sum = 0;
    for (long long i = start; i < end; i++) {
        local_sum += array[i];
    }
    partial_sums[thread_id] = local_sum;
    // 同步用的，使用了互斥锁+条件变量
    pthread_mutex_lock(mutex);
    (*round_completed)++;

    if (*round_completed == num_threads) {
        *round_completed = 0;
        pthread_cond_broadcast(cond);  
    } else {

        pthread_cond_wait(cond, mutex);
    }
    pthread_mutex_unlock(mutex);  

    for (int round = 0; round < max_rounds; round++) {

        int stride = 1 << round;
        if (thread_id % (stride * 2) == 0 && thread_id + stride < num_threads) {
            partial_sums[thread_id] += partial_sums[thread_id + stride];
            // printf("%lld ", partial_sums[thread_id]);
        }

        pthread_mutex_lock(mutex);
        (*round_completed)++;
        if (*round_completed == num_threads) {
            *round_completed = 0;
            pthread_cond_broadcast(cond);  
        } else {

            pthread_cond_wait(cond, mutex);
        }
        pthread_mutex_unlock(mutex);
    }
    
    return NULL;
}

int main(int argc, char* argv[]) {

    if (argc != 3) {
        printf("用法: %s <数组大小> <线程数>\n", argv[0]);
        return 1;
    }
    

    long long size = atoll(argv[1]) * 1000 * 1000;
    // long long size = atoll(argv[1]);
    int num_threads = atoi(argv[2]);
    

    int max_rounds = (int)ceil(log2(num_threads));
    

    int* array = (int*)malloc(size * sizeof(int));
    if (!array) {
        printf("内存分配失败\n");
        return 1;
    }
    

    srand(time(NULL));
    for (long long i = 0; i < size; i++) {
        array[i] = rand() % 100;  
    }
    

    long long* partial_sums = (long long*)malloc(num_threads * sizeof(long long));
    if (!partial_sums) {
        printf("内存分配失败\n");
        free(array);
        return 1;
    }
    

    ThreadArgs* thread_args = (ThreadArgs*)malloc(num_threads * sizeof(ThreadArgs));
    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    
    if (!thread_args || !threads) {
        printf("内存分配失败\n");
        free(array);
        free(partial_sums);
        if (thread_args) free(thread_args);
        if (threads) free(threads);
        return 1;
    }
    

    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
    int round_completed = 0;
    
    

    // for (int i = 0; i < size; i++) {
    //     printf("%d ", array[i]);
    // }
    // printf("\n");
    printf("开始计时\n");
    double start_time = get_time_ms();

    

    for (int i = 0; i < num_threads; i++) {
        thread_args[i].thread_id = i;
        thread_args[i].num_threads = num_threads;
        thread_args[i].array = array;
        thread_args[i].size = size;
        thread_args[i].partial_sums = partial_sums;
        thread_args[i].round = 0;
        thread_args[i].max_rounds = max_rounds;
        thread_args[i].mutex = &mutex;
        thread_args[i].cond = &cond;
        thread_args[i].round_completed = &round_completed;
        
        if (pthread_create(&threads[i], NULL, sum_array_reduce, &thread_args[i]) != 0) {
            printf("创建线程 %d 失败\n", i);
            free(array);
            free(partial_sums);
            free(thread_args);
            free(threads);
            return 1;
        }
    }
    
    

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    

    double end_time = get_time_ms();
    double elapsed_time = end_time - start_time;
    

    long long total_sum = partial_sums[0];
    

    printf("数组元素和: %lld\n", total_sum);
    printf("计算时间: %.3f 秒\n", elapsed_time);
    printf("线程数: %d\n", num_threads);
    printf("规约轮数: %d\n", max_rounds);
    

    free(array);
    free(partial_sums);
    free(thread_args);
    free(threads);
    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&cond);
    
    return 0;
}
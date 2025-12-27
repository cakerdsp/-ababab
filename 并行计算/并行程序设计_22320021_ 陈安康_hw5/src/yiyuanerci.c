#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <time.h>  // for clock_gettime()

typedef struct {
    double a, b, c;
    double b2, four_ac, discriminant, sqrt_discriminant, two_a;
    double x1, x2;

    // 状态标志
    int b2_ready, fourac_ready, discrim_ready, sqrt_ready, twoa_ready;

    // 锁与条件变量
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    
    // 计时统计
    double compute_time[7];  // 每个线程的计算时间
    double wait_time[7];     // 每个线程的等待时间
    int thread_ids[7];       // 线程ID映射
    
    // 线程创建开销统计
    double thread_create_time;  // 线程创建总时间
} SharedData;

void wait_for(int* flag, SharedData* data) {
    struct timespec wait_start, wait_end;
    int thread_id = -1;
    
    // 找出当前线程ID
    for (int i = 0; i < 7; i++) {
        if (pthread_equal(pthread_self(), data->thread_ids[i])) {
            thread_id = i;
            break;
        }
    }
    
    if (thread_id >= 0) {
        clock_gettime(CLOCK_MONOTONIC, &wait_start);
    }
    
    while (!(*flag)) {
        pthread_cond_wait(&data->cond, &data->mutex);
    }
    
    if (thread_id >= 0) {
        clock_gettime(CLOCK_MONOTONIC, &wait_end);
        data->wait_time[thread_id] += wait_end.tv_sec - wait_start.tv_sec + 
                                     (wait_end.tv_nsec - wait_start.tv_nsec) / 1e9;
    }
}

void* compute_b2(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    double b2 = data->b * data->b;
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    pthread_mutex_lock(&data->mutex);
    data->b2 = b2;
    data->b2_ready = 1;
    // 记录计算时间
    data->compute_time[0] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_cond_broadcast(&data->cond);
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_4ac(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    double fourac = 4 * data->a * data->c;
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    pthread_mutex_lock(&data->mutex);
    data->four_ac = fourac;
    data->fourac_ready = 1;
    // 记录计算时间
    data->compute_time[1] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_cond_broadcast(&data->cond);
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_discriminant(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    pthread_mutex_lock(&data->mutex);
    wait_for(&data->b2_ready, data);
    wait_for(&data->fourac_ready, data);
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    data->discriminant = data->b2 - data->four_ac;
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    data->discrim_ready = 1;
    // 记录计算时间
    data->compute_time[2] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_cond_broadcast(&data->cond);
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_sqrt(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    pthread_mutex_lock(&data->mutex);
    wait_for(&data->discrim_ready, data);
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    if (data->discriminant < 0) {
        data->sqrt_discriminant = -1; // 标记为无解
    } else {
        data->sqrt_discriminant = sqrt(data->discriminant);
    }
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    data->sqrt_ready = 1;
    // 记录计算时间
    data->compute_time[3] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_cond_broadcast(&data->cond);
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_2a(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    double twoa = 2 * data->a;
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    pthread_mutex_lock(&data->mutex);
    data->two_a = twoa;
    data->twoa_ready = 1;
    // 记录计算时间
    data->compute_time[4] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_cond_broadcast(&data->cond);
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_x1(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    pthread_mutex_lock(&data->mutex);
    wait_for(&data->sqrt_ready, data);
    wait_for(&data->twoa_ready, data);
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    if (data->sqrt_discriminant < 0) {
        data->x1 = NAN;
    } else {
        data->x1 = (-data->b + data->sqrt_discriminant) / data->two_a;
    }
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    // 记录计算时间
    data->compute_time[5] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

void* compute_x2(void* arg) {
    SharedData* data = (SharedData*) arg;
    struct timespec comp_start, comp_end;
    
    pthread_mutex_lock(&data->mutex);
    wait_for(&data->sqrt_ready, data);
    wait_for(&data->twoa_ready, data);
    
    // 开始计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_start);
    
    if (data->sqrt_discriminant < 0) {
        data->x2 = NAN;
    } else {
        data->x2 = (-data->b - data->sqrt_discriminant) / data->two_a;
    }
    
    // 结束计算时间统计
    clock_gettime(CLOCK_MONOTONIC, &comp_end);
    
    // 记录计算时间
    data->compute_time[6] += comp_end.tv_sec - comp_start.tv_sec + 
                           (comp_end.tv_nsec - comp_start.tv_nsec) / 1e9;
    pthread_mutex_unlock(&data->mutex);
    return NULL;
}

int main() {
    SharedData data = {0};
    pthread_mutex_init(&data.mutex, NULL);
    pthread_cond_init(&data.cond, NULL);
    
    // 初始化计时统计数组
    for (int i = 0; i < 7; i++) {
        data.compute_time[i] = 0.0;
        data.wait_time[i] = 0.0;
    }
    data.thread_create_time = 0.0;

    printf("请输入 a b c：\n");
    scanf("%lf %lf %lf", &data.a, &data.b, &data.c);

    if (data.a == 0) {
        printf("这不是一个二次方程。\n");
        return -1;
    }

    // 开始计时
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    // 创建线程
    pthread_t threads[7];
    struct timespec create_start, create_end;
    
    // 线程创建函数指针数组
    void* (*thread_funcs[7])(void*) = {
        compute_b2, compute_4ac, compute_discriminant, compute_sqrt,
        compute_2a, compute_x1, compute_x2
    };
    
    // 统计所有线程的创建时间
    clock_gettime(CLOCK_MONOTONIC, &create_start);
    for (int i = 0; i < 7; i++) {
        pthread_create(&threads[i], NULL, thread_funcs[i], &data);
    }
    clock_gettime(CLOCK_MONOTONIC, &create_end);
    data.thread_create_time = create_end.tv_sec - create_start.tv_sec + 
                             (create_end.tv_nsec - create_start.tv_nsec) / 1e9;
    
    // 保存线程ID用于统计
    for (int i = 0; i < 7; i++) {
        data.thread_ids[i] = threads[i];
    }

    // 等待所有线程完成
    for (int i = 0; i < 7; i++) {
        pthread_join(threads[i], NULL);
    }

    // 结束计时
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed_sec = end.tv_sec - start.tv_sec + (end.tv_nsec - start.tv_nsec) / 1e9;

    if (isnan(data.x1)) {
        printf("无实数根。\n");
    } else {
        printf("x1 = %.9f, x2 = %.9f\n", data.x1, data.x2);
    }

    printf("总耗时：%.9f 秒\n", elapsed_sec);
    
    // 输出各线程的计算和等待时间统计
    printf("\n线程计算和等待时间统计：\n");
    printf("%-20s %-20s %-20s %-20s\n", "线程", "计算时间(秒)", "等待时间(秒)", "总时间(秒)");
    
    const char* thread_names[] = {
        "计算b²", "计算4ac", "计算判别式", "计算平方根", 
        "计算2a", "计算x₁", "计算x₂"
    };
    
    double total_compute = 0.0, total_wait = 0.0;
    for (int i = 0; i < 7; i++) {
        printf("%-20s %-20.9f %-20.9f %-20.9f\n", 
               thread_names[i], 
               data.compute_time[i], 
               data.wait_time[i],
               data.compute_time[i] + data.wait_time[i]);
        total_compute += data.compute_time[i];
        total_wait += data.wait_time[i];
    }
    
    printf("\n总计算时间: %.9f 秒\n", total_compute);
    printf("总等待时间: %.9f 秒\n", total_wait);
    printf("计算/总时间比例: %.2f%%\n", (total_compute / elapsed_sec) * 100);
    printf("等待/总时间比例: %.2f%%\n", (total_wait / elapsed_sec) * 100);
    
    // 输出线程创建开销统计
    printf("\n线程创建开销统计：\n");
    printf("总线程创建时间: %.9f 秒\n", data.thread_create_time);
    printf("线程创建/总时间比例: %.2f%%\n", (data.thread_create_time / elapsed_sec) * 100);
    
    // 计算其他系统开销（总时间减去计算、等待和线程创建时间）
    double other_overhead = elapsed_sec - total_compute - total_wait - data.thread_create_time;
    printf("\n其他系统开销时间: %.9f 秒\n", other_overhead);
    printf("其他系统开销/总时间比例: %.2f%%\n", (other_overhead / elapsed_sec) * 100);

    pthread_mutex_destroy(&data.mutex);
    pthread_cond_destroy(&data.cond);
    return 0;
}

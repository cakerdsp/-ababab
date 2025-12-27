#include "parallel_for.h"
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <pthread.h>
#include <sys/time.h>

// 全局变量声明
int M, N;

// 获取当前时间（秒）
double get_wtime() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1e6;
}

typedef struct {
    double **w;        // 当前温度数组
    double **u;        // 上一次迭代的温度数组
    double mean;       // 平均值
    double diff;       // 最大差异
    pthread_mutex_t mutex; // 互斥锁
} HeatedPlateData;

// 边界初始化函数
void init_left(int i, void *args) { 
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->w[i][0] = 100.0;
}

void init_right(int i, void *args) { 
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->w[i][N-1] = 100.0;
}

void init_bottom(int j, void *args) { 
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->w[M-1][j] = 100.0;
}

void init_top(int j, void *args) { 
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->w[0][j] = 0.0;
}

// 计算左右边界温度和
void sum_left_right(int i, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->mean += data->w[i][0] + data->w[i][N-1];
}

// 计算上下边界温度和
void sum_top_bottom(int j, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    data->mean += data->w[M-1][j] + data->w[0][j];
}

// 初始化内部节点函数
void init_internal(int i, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    double mean = data->mean;
    for (int j = 1; j < N-1; j++) {
        data->w[i][j] = mean;
    }
}

// 复制数组函数
void copy_u(int i, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    for (int j = 0; j < N; j++) {
        data->u[i][j] = data->w[i][j];
    }
}

// 计算新温度函数 - 使用正确的热传导公式
void compute_w(int i, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    for (int j = 1; j < N-1; j++) {
        data->w[i][j] = (data->u[i-1][j] + data->u[i+1][j] + 
                       data->u[i][j-1] + data->u[i][j+1]) / 4.0;
    }
}

// 计算差异函数
void compute_diff(int i, void *args) {
    HeatedPlateData *data = (HeatedPlateData *)args;
    double my_diff = 0.0;
    
    for (int j = 1; j < N-1; j++) {
        double current_diff = fabs(data->w[i][j] - data->u[i][j]);
        if (my_diff < current_diff) {
            my_diff = current_diff;
        }
    }
    
    pthread_mutex_lock(&data->mutex);
    if (data->diff < my_diff) {
        data->diff = my_diff;
    }
    pthread_mutex_unlock(&data->mutex);
}

// 分配二维数组内存
double** allocate_matrix(int rows, int cols) {
    double **matrix = (double**)malloc(rows * sizeof(double*));
    for (int i = 0; i < rows; i++) {
        matrix[i] = (double*)malloc(cols * sizeof(double));
    }
    return matrix;
}

// 释放二维数组内存
void free_matrix(double **matrix, int rows) {
    for (int i = 0; i < rows; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

int main(int argc, char *argv[]) {
    double epsilon = 0.001;
    int num_threads = 4;
    int iterations = 0;
    int iterations_print = 1;
    int schedule_type = SCHEDULE_STATIC;
    int chunk_size = 0;

    // 从命令行获取参数
    if (argc >= 3) {
        M = atoi(argv[1]);
        N = atoi(argv[2]);
    } else {
        fprintf(stderr, "用法: %s M N [线程数 调度类型 块大小]\n", argv[0]);
        return 1;
    }
    if (argc > 3) {
        num_threads = atoi(argv[3]);
    }
    if (argc > 4) {
        schedule_type = atoi(argv[4]);
        if (schedule_type < 0 || schedule_type > 2) {
            printf("调度类型必须是0(静态), 1(动态), 或2(引导)\n");
            return 1;
        }
    }
    if (argc > 5) {
        chunk_size = atoi(argv[5]);
        if (chunk_size < 0) {
            printf("块大小必须大于等于0\n");
            return 1;
        }
    }

    printf("\n");
    printf("HEATED_PLATE_PTHREADS\n");
    printf("  使用parallel_for实现的Pthreads版本\n");
    printf("  求解平板稳态温度分布问题\n");
    printf("\n");
    printf("  空间网格: %d x %d 点\n", M, N);
    printf("  迭代将重复直到变化 <= %e\n", epsilon);
    printf("  线程数: %d\n", num_threads);
    printf("  调度类型: %d (%s)\n", schedule_type, 
           schedule_type == 0 ? "静态" : 
           schedule_type == 1 ? "动态" : "引导");
    printf("  块大小: %d\n", chunk_size);
    
    // 初始化数据结构
    HeatedPlateData data;
    data.w = allocate_matrix(M, N);
    data.u = allocate_matrix(M, N);
    data.mean = 0.0;
    data.diff = 0.0;
    pthread_mutex_init(&data.mutex, NULL);
    
    // 设置边界条件
    parallel_for_schedule(1, M-1, 1, init_left, &data, num_threads, schedule_type, chunk_size);
    parallel_for_schedule(1, M-1, 1, init_right, &data, num_threads, schedule_type, chunk_size);
    parallel_for_schedule(0, N, 1, init_bottom, &data, num_threads, schedule_type, chunk_size);
    parallel_for_schedule(0, N, 1, init_top, &data, num_threads, schedule_type, chunk_size);
    
    // 计算初始平均值
    parallel_for_schedule(1, M-1, 1, sum_left_right, &data, num_threads, schedule_type, chunk_size);
    parallel_for_schedule(0, N, 1, sum_top_bottom, &data, num_threads, schedule_type, chunk_size);
    data.mean = data.mean / (double)(2 * M + 2 * N - 4);
    
    printf("\n");
    printf("  边界平均温度 MEAN = %f\n", data.mean);
    
    // 初始化内部节点
    parallel_for_schedule(1, M-1, 1, init_internal, &data, num_threads, schedule_type, chunk_size);
    
    // 迭代计算
    printf("\n");
    printf(" 迭代次数  变化量\n");
    printf("\n");
    
    double wtime = get_wtime();
    data.diff = epsilon;
    
    while (epsilon <= data.diff) {
        // 重置差异值
        data.diff = 0.0;
        
        // 保存旧值
        parallel_for_schedule(0, M, 1, copy_u, &data, num_threads, schedule_type, chunk_size);
        
        // 计算新值
        parallel_for_schedule(1, M-1, 1, compute_w, &data, num_threads, schedule_type, chunk_size);
        
        // 计算差异
        parallel_for_schedule(1, M-1, 1, compute_diff, &data, num_threads, schedule_type, chunk_size);
        
        iterations++;
        if (iterations == iterations_print) {
            printf("  %8d  %f\n", iterations, data.diff);
            iterations_print *= 2;
        }
    }
    
    double elapsed = get_wtime() - wtime;
    
    printf("\n");
    printf("  %8d  %f\n", iterations, data.diff);
    printf("\n");
    printf("  误差容限已达到\n");
    printf("  耗时 = %f 秒\n", elapsed);
    
    // 性能对比
    printf("\n");
    printf("性能对比:\n");
    printf("  Pthreads版本 (线程数=%d, 调度类型=%d, 块大小=%d): %f 秒, 迭代次数: %d\n", 
           num_threads, schedule_type, chunk_size, elapsed, iterations);
    
    // 清理资源
    free_matrix(data.w, M);
    free_matrix(data.u, M);
    pthread_mutex_destroy(&data.mutex);
    
    printf("\n");
    printf("HEATED_PLATE_PTHREADS:\n");
    printf("  正常结束执行\n");
    
    return 0;
}
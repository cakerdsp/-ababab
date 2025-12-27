#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <sys/time.h>
#include <math.h>

#define MAX_THREADS 64

int num_threads;
long total_points;
long points_in_circle[MAX_THREADS]; // 每个线程的圆内点数

// 线程执行函数
void* monte_carlo_pi(void* arg) {
    int tid = *(int*)arg;
    unsigned int seed = tid + time(NULL); // 每个线程使用不同种子
    long local_count = 0;

    long points_per_thread = total_points / num_threads;
    for (long i = 0; i < points_per_thread; ++i) {
        double x = rand_r(&seed) / (double)RAND_MAX;
        double y = rand_r(&seed) / (double)RAND_MAX;
        if (x * x + y * y <= 1.0) {
            local_count++;
        }
    }

    points_in_circle[tid] = local_count;
    pthread_exit(NULL);
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        printf("用法: %s <线程数> <总点数>\n", argv[0]);
        return 1;
    }

    num_threads = atoi(argv[1]);
    total_points = atol(argv[2]);

    if (num_threads > MAX_THREADS || num_threads < 1) {
        printf("线程数需在 [1, %d] 范围内\n", MAX_THREADS);
        return 1;
    }

    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    int thread_ids[MAX_THREADS];

    struct timeval start, end;
    gettimeofday(&start, NULL);

    for (int i = 0; i < num_threads; ++i) {
        thread_ids[i] = i;
        pthread_create(&threads[i], NULL, monte_carlo_pi, &thread_ids[i]);
    }

    long total_in_circle = 0;
    for (int i = 0; i < num_threads; ++i) {
        pthread_join(threads[i], NULL);
        total_in_circle += points_in_circle[i];
    }

    gettimeofday(&end, NULL);
    double pi_estimate = 4.0 * total_in_circle / total_points;
    double elapsed_time = (end.tv_sec - start.tv_sec) +
                          (end.tv_usec - start.tv_usec) / 1e6;

    printf("总点数: %ld\n", total_points);
    printf("圆内点数: %ld\n", total_in_circle);
    printf("π 的估计值: %.6f\n", pi_estimate);
    printf("耗时: %.6f 秒\n", elapsed_time);

    return 0;
}

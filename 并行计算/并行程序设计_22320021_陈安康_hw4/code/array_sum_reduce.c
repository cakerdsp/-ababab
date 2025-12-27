#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <sys/time.h>

#define MAX_THREADS 16

int *A;
long long global_sum = 0;
pthread_mutex_t sum_lock;

typedef struct {
    int thread_id;
    long start, end;
} ThreadData;

void* partial_sum(void* arg) {
    ThreadData *data = (ThreadData*)arg;
    long long local_sum = 0;
    for (long i = data->start; i < data->end; ++i)
        local_sum += A[i];

    pthread_mutex_lock(&sum_lock);
    global_sum += local_sum;
    pthread_mutex_unlock(&sum_lock);
    return NULL;
}

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1e6;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage: %s <array_size_in_M> <thread_count>\n", argv[0]);
        return 1;
    }

    long N = atol(argv[1]) * 1000 * 1000;
    // long N = atol(argv[1]);
    int thread_count = atoi(argv[2]);
    pthread_t* threads = malloc(thread_count * sizeof(pthread_t));
    ThreadData thread_data[thread_count];


    A = malloc(sizeof(int) * N);
    srand((unsigned int)time(NULL));
    for (long i = 0; i < N; ++i) A[i] = rand() % 100;

    // for (int i = 0; i < N; i++) {
    //     printf("%d ", A[i]);
    // }

    pthread_mutex_init(&sum_lock, NULL);

    double start_time = get_time();

    long chunk = N / thread_count;
    for (int i = 0; i < thread_count; ++i) {
        thread_data[i].thread_id = i;
        thread_data[i].start = i * chunk;
        thread_data[i].end = (i == thread_count - 1) ? N : (i + 1) * chunk;
        pthread_create(&threads[i], NULL, partial_sum, &thread_data[i]);
    }

    for (int i = 0; i < thread_count; ++i)
        pthread_join(threads[i], NULL);

    double end_time = get_time();

    printf("Sum = %lld\n", global_sum);
    printf("Time elapsed: %.6f seconds\n", end_time - start_time);

    pthread_mutex_destroy(&sum_lock);
    free(A);
    return 0;
}

#include "parallel_for.h"

typedef struct {
    int start, end, inc;
    void (*func)(int, void *);
    void *args;
} thread_data;

void *thread_worker(void *arg) {
    thread_data *data = (thread_data *)arg;
    for (int i = data->start; i < data->end; i += data->inc) {
        data->func(i, data->args);
    }
    return NULL;
}

void parallel_for(int start, int end, int inc,
                  void (*func)(int, void *),
                  void *args, int num_threads) {
    pthread_t threads[num_threads];
    thread_data td[num_threads];

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

        pthread_create(&threads[i], NULL, thread_worker, &td[i]);
        current_start = current_end;
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
}
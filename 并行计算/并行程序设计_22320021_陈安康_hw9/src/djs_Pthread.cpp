// pthread_main.c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "djs_Comm.h"

double* results;

typedef struct {
    AdjList* graph;
    int* pairs;
    int pair_count;
    int node_count;
    int thread_id;
    int num_threads;
} ThreadArg;

void* worker(void* arg) {
    ThreadArg* ta = (ThreadArg*)arg;
    for (int i = ta->thread_id; i < ta->pair_count; i += ta->num_threads) {
        int s = ta->pairs[2 * i];
        int t = ta->pairs[2 * i + 1];
        results[i] = dijkstra(ta->graph, ta->node_count, s, t);
    }
    return NULL;
}

int main(int argc, char** argv) {
    AdjList* graph;
    int* test_pairs;
    int node_count, pair_count;
    read_graph("./updated_mouse.csv", &graph, &node_count);
    read_test_pairs("./test_2000.csv", &test_pairs, &pair_count);

    results = (double*)calloc(pair_count, sizeof(double));
    int num_threads = 1;
    pthread_t threads[num_threads];
    ThreadArg args[num_threads];

    double start = clock() / (double)CLOCKS_PER_SEC;

    for (int i = 0; i < num_threads; ++i) {
        args[i] = (ThreadArg){graph, test_pairs, pair_count, node_count, i, num_threads};
        pthread_create(&threads[i], NULL, worker, &args[i]);
    }
    for (int i = 0; i < num_threads; ++i) {
        pthread_join(threads[i], NULL);
    }

    printf("Results:\n");
    for (int i = 0; i < pair_count; ++i) {
        printf("Test case %d (%d -> %d): %.4f\n", i, test_pairs[2*i], test_pairs[2*i+1], results[i]);
    }

    double end = clock() / (double)CLOCKS_PER_SEC;
    printf("Total time: %.4f sec\n", end - start);

    free(results);
    return 0;
}

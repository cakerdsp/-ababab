// omp_main.c
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "djs_Comm.h"

int main(int argc, char** argv) {
    AdjList* graph;
    int* test_pairs;
    int node_count, pair_count;
    read_graph("./updated_mouse.csv", &graph, &node_count);
    read_test_pairs("./test_2000.csv", &test_pairs, &pair_count);

    double* results = (double*)calloc(pair_count, sizeof(double));
    double start = omp_get_wtime();

    #pragma omp parallel for schedule(dynamic)
    for (int i = 0; i < pair_count; ++i) {
        int s = test_pairs[2 * i];
        int t = test_pairs[2 * i + 1];
        results[i] = dijkstra(graph, node_count, s, t);
    }

    printf("Results:\n");
    for (int i = 0; i < pair_count; ++i) {
        printf("Test case %d (%d -> %d): %.4f\n", i, test_pairs[2*i], test_pairs[2*i+1], results[i]);
    }

    double end = omp_get_wtime();
    printf("Total time: %.4f sec\n", end - start);
    free(results);
    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include "parallel_for.h"

typedef struct {
    double *A;
    double *B;
    double *C;
    int m, n, k;
} functor_args;

typedef struct {
    void (*func)(int idx, void *args);
    functor_args *args_data;
} functor;

void matmul_row(int idx, void *args) {
    functor_args *fargs = (functor_args *)args;
    int n = fargs->n;
    int k = fargs->k;
    double *A = fargs->A;
    double *B = fargs->B;
    double *C = fargs->C;

    for (int j = 0; j < k; ++j) {
        C[idx * k + j] = 0.0;
        for (int l = 0; l < n; ++l) {
            C[idx * k + j] += A[idx * n + l] * B[l * k + j];
        }
    }
}

double* alloc_matrix(int rows, int cols) {
    return (double*)malloc(rows * cols * sizeof(double));
}

void random_initialize(double *mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i)
        mat[i] = (double)(rand() % 100) / 10.0;
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <m> <n> <k> <num_threads>\n", argv[0]);
        return 1;
    }

    int m = atoi(argv[1]); // A: m×n
    int n = atoi(argv[2]); // A: m×n, B: n×k
    int k = atoi(argv[3]); // B: n×k
    int num_threads = atoi(argv[4]);

    double *A = alloc_matrix(m, n);
    double *B = alloc_matrix(n, k);
    double *C = alloc_matrix(m, k);

    if (!A || !B || !C) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    srand((unsigned int)time(NULL));
    random_initialize(A, m, n);
    random_initialize(B, n, k);

    functor_args args = {A, B, C, m, n, k};
    functor f = {matmul_row, &args};

    struct timeval start, end;
    gettimeofday(&start, NULL);

    parallel_for(0, m, 1, f.func, f.args_data, num_threads);

    gettimeofday(&end, NULL);
    double elapsed = (end.tv_sec - start.tv_sec) * 1000.0 +
                     (end.tv_usec - start.tv_usec) / 1000.0;

    printf("Matrix multiplication (A: %dx%d, B: %dx%d) completed in %.6f s\n",
           m, n, n, k, elapsed / 1000);

    // // 可选输出
    // printf("A:\n");
    // for (int i = 0; i < m; i++) {
    //     for (int j = 0; j < n; j++)
    //         printf("%.2f ", A[i * k + j]);
    //     printf("\n");
    // }
    // printf("B:\n");
    // for (int i = 0; i < n; i++) {
    //     for (int j = 0; j < k; j++)
    //         printf("%.2f ", C[i * k + j]);
    //     printf("\n");
    // }
    // printf("C:\n");
    // for (int i = 0; i < m; i++) {
    //     for (int j = 0; j < k; j++)
    //         printf("%.2f ", C[i * k + j]);
    //     printf("\n");
    // }

    free(A);
    free(B);
    free(C);

    return 0;
}
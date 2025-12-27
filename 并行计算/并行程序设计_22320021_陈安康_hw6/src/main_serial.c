#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

double* alloc_matrix(int rows, int cols) {
    return (double*)malloc(rows * cols * sizeof(double));
}

void random_initialize(double *mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i)
        mat[i] = (double)(rand() % 100) / 10.0;
}

void serial_matmul(double *A, double *B, double *C, int m, int n, int k) {
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < k; ++j) {
            C[i * k + j] = 0.0;
            for (int l = 0; l < n; ++l) {
                C[i * k + j] += A[i * n + l] * B[l * k + j];
            }
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: %s <m> <n> <k>\n", argv[0]);
        return 1;
    }

    int m = atoi(argv[1]);
    int n = atoi(argv[2]);
    int k = atoi(argv[3]);

    double *A = alloc_matrix(m, n);
    double *B = alloc_matrix(n, k);
    double *C = alloc_matrix(m, k);

    if (!A || !B || !C) {
        printf("Memory allocation failed\n");
        return 1;
    }

    srand((unsigned int)time(NULL));
    random_initialize(A, m, n);
    random_initialize(B, n, k);

    struct timeval start, end;
    gettimeofday(&start, NULL);

    serial_matmul(A, B, C, m, n, k);

    gettimeofday(&end, NULL);
    double elapsed = (end.tv_sec - start.tv_sec) * 1000.0 +
                     (end.tv_usec - start.tv_usec) / 1000.0;

    printf("Serial matrix multiplication (A: %dx%d, B: %dx%d) completed in %.3f ms\n",
           m, n, n, k, elapsed);

    free(A);
    free(B);
    free(C);

    return 0;
}

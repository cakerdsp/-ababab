#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <sys/time.h>

typedef struct {
    int thread_id;
    int thread_count;
    int m, n, k;
    double *A, *B, *C;
} ThreadData;

void* matrixMultiplyThread(void *arg) {
    ThreadData *data = (ThreadData*)arg;
    int chunk_size = data->m / data->thread_count;
    int start_row = data->thread_id * chunk_size;
    int end_row = (data->thread_id == data->thread_count - 1) ? data->m : start_row + chunk_size;

    for (int i = start_row; i < end_row; ++i) {
        for (int j = 0; j < data->k; ++j) {
            double sum = 0.0;
            for (int p = 0; p < data->n; ++p) {
                sum += data->A[i * data->n + p] * data->B[p * data->k + j];
            }
            data->C[i * data->k + j] = sum;
        }
    }
    return NULL;
}

double getTimeInSeconds() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1e6;
}

void fillMatrix(double *mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i)
        mat[i] = (double)rand() / (double)RAND_MAX;
}

void printMatrix(const char *name, double *mat, int rows, int cols) {
    printf("%s = [\n", name);
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j)
            printf("%6.2f ", mat[i * cols + j]);
        printf("\n");
    }
    printf("]\n");
}

int main(int argc, char **argv) {
    if (argc != 5) {
        printf("Usage: %s m n k thread_count\n", argv[0]);
        return 1;
    }

    int m = atoi(argv[1]);
    int n = atoi(argv[2]);
    int k = atoi(argv[3]);
    long thread_count = atol(argv[4]);

    double *A = malloc(sizeof(double) * m * n);
    double *B = malloc(sizeof(double) * n * k);
    double *C = malloc(sizeof(double) * m * k);

    fillMatrix(A, m, n);
    fillMatrix(B, n, k);

    pthread_t* threads = malloc(thread_count * sizeof(pthread_t));
    ThreadData thread_data[thread_count];

    double start = getTimeInSeconds();

    for (int i = 0; i < thread_count; ++i) {
        thread_data[i] = (ThreadData){i, thread_count, m, n, k, A, B, C};
        pthread_create(&threads[i], NULL, matrixMultiplyThread, &thread_data[i]);
    }

    for (int i = 0; i < thread_count; ++i) {
        pthread_join(threads[i], NULL);
    }

    double end = getTimeInSeconds();
    double elapsed = end - start;

    // printMatrix("A", A, m, n);
    // printMatrix("B", B, n, k);
    // printMatrix("C", C, m, k);
    printf("Time elapsed: %.6f seconds\n", elapsed);

    free(A);
    free(B);
    free(C);

    return 0;
}

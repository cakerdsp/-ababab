#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <time.h>

void generate_matrix_unbalance(double* mat, int rows, int cols) {
    // for (int i = 0; i < rows * cols; i++) {
    //     mat[i] = (double)(rand() % 100) / 10.0;
    // }
    for (int i = 0; i < rows; i++) {
        int work = (i + 1);  // 行号越大，计算越多
        for (int j = 0; j < cols; j++) {
            if (j < work % cols) {
                mat[i * cols + j] = (double)(rand() % 100);
            } else {
                mat[i * cols + j] = 0.0; // 设为 0，减少乘法计算时间
            }
        }
    }
}
void generate_matrix(double* mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; i++) {
        mat[i] = (double)(rand() % 100) / 10.0;
    }
}

void print_matrix(const double* mat, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%.1f ", mat[i * cols + j]);
        }
        printf("\n");
    }
}

const char* get_sched_name(omp_sched_t kind) {
    switch (kind) {
        case omp_sched_static: return "static";
        case omp_sched_dynamic: return "dynamic";
        case omp_sched_guided: return "guided";
        case omp_sched_auto: return "auto";
        default: return "unknown";
    }
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        printf("Usage: %s <m> <n> <k> <threads_num> <schedule_type>\n", argv[0]);
        printf("schedule_type: 0=auto, 1=static, 2=dynamic\n");
        return -1;
    }

    int m = atoi(argv[1]);
    int n = atoi(argv[2]);
    int k = atoi(argv[3]);
    int num_threads = atoi(argv[4]);
    omp_set_num_threads(num_threads);
    int schedule_type = atoi(argv[5]);

    double *A = (double*)malloc(m * n * sizeof(double));
    double *B = (double*)malloc(n * k * sizeof(double));
    double *C = (double*)malloc(m * k * sizeof(double));

    if (!A || !B || !C) {
        printf("Memory allocation failed\n");
        return -1;
    }

    srand((unsigned int)time(NULL));
    // generate_matrix_unbalance(A, m, n);
    generate_matrix(A, m, n);
    generate_matrix(B, n, k);
    for (int i = 0; i < m * k; i++) C[i] = 0.0;

    // 设置调度策略
    if (schedule_type == 1)
        omp_set_schedule(omp_sched_static, 0);
    else if (schedule_type == 2)
        omp_set_schedule(omp_sched_dynamic, 0);
    else
        omp_set_schedule(omp_sched_auto, 0);

    double start_time = omp_get_wtime();

    #pragma omp parallel
    {
        // 仅线程 0 打印当前调度策略
        if (omp_get_thread_num() == 0) {
            omp_sched_t kind;
            int chunk_size;
            omp_get_schedule(&kind, &chunk_size);
            printf("Using schedule: %s", get_sched_name(kind));
        }

        #pragma omp for schedule(runtime)
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < k; j++) {
                double sum = 0.0;
                for (int l = 0; l < n; l++) {
                    sum += A[i * n + l] * B[l * k + j];
                }
                C[i * k + j] = sum;
            }
        }
    }

    double end_time = omp_get_wtime();
    // printf("Matrix A (%d x %d):\n", m, n);
    // print_matrix(A, m, n);

    // printf("\nMatrix B (%d x %d):\n", n, k);
    // print_matrix(B, n, k);

    // printf("\nMatrix C (%d x %d):\n", m, k);
    // print_matrix(C, m, k);
    printf("\nTime taken: %.6f seconds\n", end_time - start_time);

    free(A); free(B); free(C);
    return 0;
}


#include <stdio.h>
#include <mpi.h>
#include <stdlib.h>
#include <time.h>

// 生成随机矩阵
void generateRandomMatrix(double *matrix, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i) {
        matrix[i] = (double)rand() / (double)RAND_MAX;
    }
}

// 矩阵乘法
void matrixMultiply(const double *A, const double *B, double *C, int m, int n, int k) {
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < k; ++j) {
            C[i * k + j] = 0.0;
            for (int l = 0; l < n; ++l) {
                C[i * k + j] += A[i * n + l] * B[l * k + j];
            }
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(NULL, NULL);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // 输入矩阵规模
    int m = 0, n = 0, k = 0;
    double start_time = MPI_Wtime();
    if (rank == 0) {
        // 确保输入范围在 [128, 2048]
        m = 128, k = 128, n = 128;
        // 发送矩阵规模到其他进程
        for (int i = 1; i < size; ++i) {

            MPI_Send(&m, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
            MPI_Send(&n, 1, MPI_INT, i, 1, MPI_COMM_WORLD);
            MPI_Send(&k, 1, MPI_INT, i, 2, MPI_COMM_WORLD);
        }
    } else {
        // 接收矩阵规模
        MPI_Recv(&m, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&n, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(&k, 1, MPI_INT, 0, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("rank %d receive the matrix param\n",rank);
    }
    // 生成矩阵
    double *A = (double *)malloc(m * n * sizeof(double));
    double *B = (double *)malloc(n * k * sizeof(double));
    double *C = (double *)malloc(m * k * sizeof(double));

    if (rank == 0) {
        srand(time(NULL));
        generateRandomMatrix(A, m, n);
        generateRandomMatrix(B, n, k);
        printf("init matrix successfully!!\n");
        // 发送矩阵 B 到其他进程
        for (int i = 1; i < size; ++i) {
            MPI_Send(B, n * k, MPI_DOUBLE, i, 3, MPI_COMM_WORLD);
        }
    } else {
        // 接收矩阵 B
        MPI_Recv(B, n * k, MPI_DOUBLE, 0, 3, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("rank %d have receive the matrix B\n",rank);
    }

    // 分发矩阵 A 的部分到各个进程
    int local_m = m / size;
    double *local_A = (double *)malloc(local_m * n * sizeof(double));
    if (rank == 0) {
        for (int i = 0; i < size; ++i) {
            int start = i * local_m * n;
            if (i == 0) {
                for (int j = 0; j < local_m * n; ++j) {
                    local_A[j] = A[j];
                }
            } else {
                MPI_Send(A + start, local_m * n, MPI_DOUBLE, i, 4, MPI_COMM_WORLD);
            }
        }
    } else {
        MPI_Recv(local_A, local_m * n, MPI_DOUBLE, 0, 4, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("rank %d have receive the local_A\n",rank);
    }

    // 计算局部结果
    double *local_C = (double *)malloc(local_m * k * sizeof(double));
    matrixMultiply(local_A, B, local_C, local_m, n, k);

    // 收集局部结果到进程 0
    if (rank == 0) {
        for (int i = 0; i < size; ++i) {
            int start = i * local_m * k;
            if (i == 0) {
                for (int j = 0; j < local_m * k; ++j) {
                    C[j] = local_C[j];
                }
            } else {
                MPI_Recv(C + start, local_m * k, MPI_DOUBLE, i, 5, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            }
        }
    } else {
        MPI_Send(local_C, local_m * k, MPI_DOUBLE, 0, 5, MPI_COMM_WORLD);
    }
    double end_time = MPI_Wtime();
    double local_time = end_time - start_time;
    // 收集所有进程的时间
    double *all_times = (double *)malloc(size * sizeof(double));
    if (rank == 0) {
        all_times[0] = local_time;
        for (int i = 1; i < size; ++i) {
            MPI_Recv(all_times + i, 1, MPI_DOUBLE, i, 6, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    } else {
        MPI_Send(&local_time, 1, MPI_DOUBLE, 0, 6, MPI_COMM_WORLD);
    }

    if (rank == 0) {
        // 计算总时间
        double total_time = 0.0;
        for (int i = 0; i < size; ++i) {
            if (all_times[i] > total_time) {
                total_time = all_times[i];
            }
        }

        // 输出结果
        printf("矩阵 A:\n");
        for (int i = 0; i < m; ++i) {
            for (int j = 0; j < n; ++j) {
                printf("%f ", A[i * n + j]);
            }
            printf("\n");
        }
        printf("矩阵 B:\n");
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < k; ++j) {
                printf("%f ", B[i * k + j]);
            }
            printf("\n");
        }
        printf("矩阵 C:\n");
        for (int i = 0; i < m; ++i) {
            for (int j = 0; j < k; ++j) {
                printf("%f ", C[i * k + j]);
            }
            printf("\n");
        }
        printf("进程数：%d | 矩阵规模：%d | 矩阵计算所消耗的时间: %f 秒\n", size, k, total_time);
    }

    free(A);
    free(B);
    free(C);
    free(local_A);
    free(local_C);
    free(all_times);

    MPI_Finalize();
    return 0;
}

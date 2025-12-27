#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>


// 定义矩阵结构体
typedef struct {
    int rows;
    int cols;
    double* data;
} Matrix;

// 定义传输用的结构体（用于打包 m, n, k）
typedef struct {
    int m;
    int n;
    int k;
} MatrixDim;

void printMatrixInfo(const char* name, Matrix* mat) {
    printf("矩阵 %s: %d x %d\n", name, mat->rows, mat->cols);
    printf("数据：\n");
    for (int i = 0; i < mat->rows; i++) {
        for (int j = 0; j < mat->cols; j++) {
            printf("%.4f ", mat->data[i * mat->cols + j]);
        }
        printf("\n");
    }
}

void initMatrix(Matrix* mat, int rows, int cols) {
    mat->rows = rows;
    mat->cols = cols;
    mat->data = (double*)malloc(rows * cols * sizeof(double));

    for (int i = 0; i < rows * cols; i++) {
        mat->data[i] = (double)rand() / (double)RAND_MAX;
    }
}

void matrixMultiply(Matrix* A, Matrix* B, Matrix* C) {
    for (int i = 0; i < A->rows; i++) {
        for (int j = 0; j < B->cols; j++) {
            double sum = 0.0;
            for (int k = 0; k < A->cols; k++) {
                sum += A->data[i * A->cols + k] * B->data[k * B->cols + j];
            }
            C->data[i * C->cols + j] = sum;
        }
    }
}

int main(int argc, char** argv) {
    int rank, size;
    Matrix A, B, C;
    double start_time, end_time;
    MatrixDim dims;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    srand(time(NULL) + rank);

    // 定义 MPI 类型来广播 dims（m, n, k）
    MPI_Datatype MPI_MatrixDim;
    int block_lengths[3] = {1, 1, 1};
    MPI_Aint displacements[3];
    MPI_Aint base;
    MPI_Get_address(&dims, &base);
    MPI_Get_address(&dims.m, &displacements[0]);
    MPI_Get_address(&dims.n, &displacements[1]);
    MPI_Get_address(&dims.k, &displacements[2]);
    for (int i = 0; i < 3; i++) displacements[i] -= base;
    MPI_Datatype types[3] = {MPI_INT, MPI_INT, MPI_INT};
    MPI_Type_create_struct(3, block_lengths, displacements, types, &MPI_MatrixDim);
    MPI_Type_commit(&MPI_MatrixDim);

    // 根进程处理命令行参数并初始化矩阵
    if (rank == 0) {
        if (argc != 4) {
            fprintf(stderr, "用法: %s <m> <n> <k>\n", argv[0]);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        dims.m = atoi(argv[1]);
        dims.n = atoi(argv[2]);
        dims.k = atoi(argv[3]);

        initMatrix(&A, dims.m, dims.n);
        initMatrix(&B, dims.n, dims.k);
        C.rows = dims.m;
        C.cols = dims.k;
        C.data = (double*)malloc(dims.m * dims.k * sizeof(double));
    }

    // 广播结构体 dims（聚合 m, n, k）
    MPI_Bcast(&dims, 1, MPI_MatrixDim, 0, MPI_COMM_WORLD);

    // 非根进程分配空间
    if (rank != 0) {
        int rows_per_proc = dims.m / size;
        A.data = (double*)malloc(rows_per_proc * dims.n * sizeof(double));
        B.data = (double*)malloc(dims.n * dims.k * sizeof(double));
        C.data = (double*)malloc(rows_per_proc * dims.k * sizeof(double));
    }

    // 广播 B
    MPI_Bcast(B.data, dims.n * dims.k, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // 分发 A
    int rows_per_proc = dims.m / size;
    MPI_Scatter(A.data, rows_per_proc * dims.n, MPI_DOUBLE,
                A.data, rows_per_proc * dims.n, MPI_DOUBLE,
                0, MPI_COMM_WORLD);

    // 局部计算
    Matrix local_A = {rows_per_proc, dims.n, A.data};
    Matrix local_B = {dims.n, dims.k, B.data};
    Matrix local_C = {rows_per_proc, dims.k, C.data};
    start_time = MPI_Wtime();
    matrixMultiply(&local_A, &local_B, &local_C);
    end_time = MPI_Wtime();

    // 收集结果
    MPI_Gather(C.data, rows_per_proc * dims.k, MPI_DOUBLE,
               C.data, rows_per_proc * dims.k, MPI_DOUBLE,
               0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("进程数：%d, 规模：%d\n", size, A.rows);
        printf("矩阵乘法计算完成！\n");
        printf("计算时间: %f 秒\n", end_time - start_time);
        A.rows = dims.m; A.cols = dims.n;
        B.rows = dims.n; B.cols = dims.k;
        // printMatrixInfo("A", &A);
        // printMatrixInfo("B", &B);
        // printMatrixInfo("C", &C);
        free(A.data); free(B.data); free(C.data);
    } else {
        free(A.data); free(B.data); free(C.data);
    }

    MPI_Type_free(&MPI_MatrixDim);
    MPI_Finalize();
    return 0;
}

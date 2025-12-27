#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>


typedef struct {
    int rows;
    int cols;
    double* data;
} Matrix;

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

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    srand(time(NULL) + rank); 


    if (rank == 0) {
        if (argc != 4) {
                    fprintf(stderr, "用法: %s <m> <n> <k>\n", argv[0]);
                    MPI_Abort(MPI_COMM_WORLD, 1);
        }
        int m = atoi(argv[1]);
        int n = atoi(argv[2]);
        int k = atoi(argv[3]);

        initMatrix(&A, m, n);
        initMatrix(&B, n, k);
        C.rows = m;
        C.cols = k;
        C.data = (double*)malloc(m * k * sizeof(double));
    }


    start_time = MPI_Wtime();

    MPI_Bcast(&A.rows, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&A.cols, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&B.cols, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // 为非根进程分配内存,因为没有广播B.rows,图省事，使用A.cols也是一样的
    if (rank != 0) {
        int rows_per_proc = A.rows / size;
        A.data = (double*)malloc(rows_per_proc * A.cols * sizeof(double));
        B.data = (double*)malloc(A.cols * B.cols * sizeof(double));
        C.data = (double*)malloc(rows_per_proc * B.cols * sizeof(double));
    }

    // 广播矩阵B,因为没有广播B.rows,所以使用A.cols也是一样的
    MPI_Bcast(B.data, A.cols * B.cols, MPI_DOUBLE, 0, MPI_COMM_WORLD);


    int rows_per_proc = A.rows / size;
    MPI_Scatter(A.data, rows_per_proc * A.cols, MPI_DOUBLE,
                A.data, rows_per_proc * A.cols, MPI_DOUBLE,
                0, MPI_COMM_WORLD);


    Matrix local_A = {rows_per_proc, A.cols, A.data};
    Matrix local_C = {rows_per_proc, B.cols, C.data};
    matrixMultiply(&local_A, &B, &local_C);


    MPI_Gather(C.data, rows_per_proc * B.cols, MPI_DOUBLE,
               C.data, rows_per_proc * B.cols, MPI_DOUBLE,
               0, MPI_COMM_WORLD);


    end_time = MPI_Wtime();


    if (rank == 0) {
        printf("进程数：%d, 规模：%d\n", size, A.rows);
        printf("矩阵乘法计算完成！\n");
        printf("计算时间: %f 秒\n", end_time - start_time);
        // printMatrixInfo("A", &A);
        // printMatrixInfo("B", &B);
        // printMatrixInfo("C", &C);

        free(A.data);
        free(B.data);
        free(C.data);
    } else {
        free(A.data);
        free(B.data);
        free(C.data);
    }

    MPI_Finalize();
    return 0;
}
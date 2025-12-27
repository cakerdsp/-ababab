#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <math.h>


typedef struct {
    int rows, cols;
    double* data;
} Matrix;

void initMatrix(Matrix* mat, int rows, int cols) {
    mat->rows = rows;
    mat->cols = cols;
    mat->data = (double*)malloc(rows * cols * sizeof(double));
    for (int i = 0; i < rows * cols; ++i)
        mat->data[i] = (double)rand() / (double)RAND_MAX;
}

void matrixMultiply(Matrix* A, Matrix* B, Matrix* C) {
    for (int i = 0; i < A->rows; ++i) {
        for (int j = 0; j < B->cols; ++j) {
            double sum = 0.0;
            for (int k = 0; k < A->cols; ++k) {
                sum += A->data[i * A->cols + k] * B->data[k * B->cols + j];
            }
            C->data[i * C->cols + j] = sum;
        }
    }
}

void printMatrix(const char* name, Matrix* mat) {
    printf("矩阵 %s: %d x %d\n", name, mat->rows, mat->cols);
    for (int i = 0; i < mat->rows; i++) {
        for (int j = 0; j < mat->cols; j++) {
            printf("%.2f ", mat->data[i * mat->cols + j]);
        }
        printf("\n");
    }
}

int main(int argc, char* argv[]) {
    int rank, size;
    int m, n, k;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 6) {
        if (rank == 0) fprintf(stderr, "Usage: %s <m> <n> <k> <dims0> <dims1>\n", argv[0]);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    m = atoi(argv[1]);
    n = atoi(argv[2]);
    k = atoi(argv[3]);

    int dims[2];
    dims[0] = atoi(argv[4]);
    dims[1] = atoi(argv[5]);
    if (dims[0] * dims[1] != size) {
        if (rank == 0) printf("Error: Number of processes must be a perfect square.\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int coords[2], periods[2] = {0, 0};
    MPI_Comm grid_comm;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &grid_comm);
    MPI_Cart_coords(grid_comm, rank, 2, coords);

    int row_block = m / dims[0];
    int col_block = k / dims[1];
    int inner_dim = n;

    Matrix A_block = {row_block, inner_dim, malloc(row_block * inner_dim * sizeof(double))};
    Matrix B_block = {inner_dim, col_block, malloc(inner_dim * col_block * sizeof(double))};
    Matrix C_block = {row_block, col_block, malloc(row_block * col_block * sizeof(double))};
    double start = MPI_Wtime();
    // 根进程生成完整矩阵并分发

    if (rank == 0) {
        Matrix A = {m, n, malloc(m * n * sizeof(double))};
        Matrix B = {n, k, malloc(n * k * sizeof(double))};
        initMatrix(&A, m, n);
        initMatrix(&B, n, k);
        // 这里感觉会耗时，不过应该可以忽略
        // printMatrix("A", &A);
        // printMatrix("", &B);

        // 分发子块
        for (int proc = 0; proc < size; proc++) {
            int p_coords[2];
            MPI_Cart_coords(grid_comm, proc, 2, p_coords);
            int row_offset = p_coords[0] * row_block;
            int col_offset = p_coords[1] * col_block;

            if (proc == 0) {
                // 当前进程保留自己的子块
                for (int i = 0; i < row_block; i++)
                    for (int j = 0; j < inner_dim; j++)
                        A_block.data[i * inner_dim + j] = A.data[(row_offset + i) * n + j];
                for (int i = 0; i < inner_dim; i++)
                    for (int j = 0; j < col_block; j++)
                        B_block.data[i * col_block + j] = B.data[i * k + col_offset + j];
            } else {
                // 发送子块
                double* A_sub = malloc(row_block * inner_dim * sizeof(double));
                double* B_sub = malloc(inner_dim * col_block * sizeof(double));

                for (int i = 0; i < row_block; i++)
                    for (int j = 0; j < inner_dim; j++)
                        A_sub[i * inner_dim + j] = A.data[(row_offset + i) * n + j];
                for (int i = 0; i < inner_dim; i++)
                    for (int j = 0; j < col_block; j++)
                        B_sub[i * col_block + j] = B.data[i * k + col_offset + j];

                MPI_Send(A_sub, row_block * inner_dim, MPI_DOUBLE, proc, 0, MPI_COMM_WORLD);
                MPI_Send(B_sub, inner_dim * col_block, MPI_DOUBLE, proc, 1, MPI_COMM_WORLD);

                free(A_sub);
                free(B_sub);
            }
        }

        free(A.data);
        free(B.data);
    } else {
        MPI_Recv(A_block.data, row_block * inner_dim, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Recv(B_block.data, inner_dim * col_block, MPI_DOUBLE, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }

    matrixMultiply(&A_block, &B_block, &C_block);

    if (rank == 0) {
        Matrix C = {m, k, malloc(m * k * sizeof(double))};
        for (int i = 0; i < row_block; i++)
            for (int j = 0; j < col_block; j++)
                C.data[i * k + j] = C_block.data[i * col_block + j];

        for (int proc = 1; proc < size; proc++) {
            int coords[2];
            MPI_Cart_coords(grid_comm, proc, 2, coords);
            int row_offset = coords[0] * row_block;
            int col_offset = coords[1] * col_block;

            double* subblock = malloc(row_block * col_block * sizeof(double));
            MPI_Recv(subblock, row_block * col_block, MPI_DOUBLE, proc, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

            for (int i = 0; i < row_block; i++)
                for (int j = 0; j < col_block; j++)
                    C.data[(row_offset + i) * k + col_offset + j] = subblock[i * col_block + j];
            free(subblock);
        }
        double end = MPI_Wtime();
        printf("计算完成，耗时 %.6f 秒\n", end - start);
        // printMatrix("结果矩阵 C", &C);
        free(C.data);
    } else {
        MPI_Send(C_block.data, row_block * col_block, MPI_DOUBLE, 0, 2, MPI_COMM_WORLD);
    }

    free(A_block.data);
    free(B_block.data);
    free(C_block.data);
    MPI_Finalize();
    return 0;
}

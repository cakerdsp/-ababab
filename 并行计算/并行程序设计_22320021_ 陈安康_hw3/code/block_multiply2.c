#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

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

void printMatrix(const char* name, Matrix* mat) {
    printf("矩阵 %s: %d x %d\n", name, mat->rows, mat->cols);
    for (int i = 0; i < mat->rows; i++) {
        for (int j = 0; j < mat->cols; j++) {
            printf("%.2f ", mat->data[i * mat->cols + j]);
        }
        printf("\n");
    }
}

void matrixMultiply(Matrix* A, Matrix* B, Matrix* C) {
    for (int i = 0; i < A->rows; ++i) {
        for (int j = 0; j < B->cols; ++j) {
            double sum = 0.0;
            for (int k = 0; k < A->cols; ++k)
                sum += A->data[i * A->cols + k] * B->data[k * B->cols + j];
            C->data[i * C->cols + j] = sum;
        }
    }
}

int main(int argc, char* argv[]) {
    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 6) {
        if (rank == 0)
            fprintf(stderr, "Usage: %s <m> <n> <k> <dims0> <dims1>\n", argv[0]);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int m = atoi(argv[1]);
    int n = atoi(argv[2]);
    int k = atoi(argv[3]);
    int dims[2] = {atoi(argv[4]), atoi(argv[5])};

    if (dims[0] * dims[1] != size) {
        if (rank == 0)
            fprintf(stderr, "Error: dims[0]*dims[1] != number of processes\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    if (m % dims[0] != 0 || k % dims[1] != 0) {
        if (rank == 0)
            fprintf(stderr, "Matrix size must be divisible by dims\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    MPI_Comm grid_comm;
    int periods[2] = {0, 0};
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &grid_comm);

    int coords[2];
    MPI_Cart_coords(grid_comm, rank, 2, coords);

    int row_block = m / dims[0];
    int col_block = k / dims[1];

    Matrix A_block = {row_block, n, malloc(row_block * n * sizeof(double))};
    Matrix B_block = {n, col_block, malloc(n * col_block * sizeof(double))};
    Matrix C_block = {row_block, col_block, malloc(row_block * col_block * sizeof(double))};

    double start = MPI_Wtime();

    Matrix A_full, B_full, C_full;
    if (rank == 0) {
        initMatrix(&A_full, m, n);
        initMatrix(&B_full, n, k);
        // printMatrix("A", &A_full);
        // printMatrix("B", &B_full);
    }

    // Scatter A
    int* sendcounts_A = malloc(size * sizeof(int));
    int* displs_A = malloc(size * sizeof(int));
    for (int proc = 0; proc < size; ++proc) {
        int p_coords[2];
        MPI_Cart_coords(grid_comm, proc, 2, p_coords);
        int index = p_coords[0] * dims[1] + p_coords[1];
        sendcounts_A[index] = row_block * n;
        displs_A[index] = p_coords[0] * row_block * n;
    }

    MPI_Scatterv(rank == 0 ? A_full.data : NULL, sendcounts_A, displs_A, MPI_DOUBLE,
                 A_block.data, row_block * n, MPI_DOUBLE, 0, grid_comm);

    // Scatter B (column blocks)
    int* sendcounts_B = malloc(size * sizeof(int));
    int* displs_B = malloc(size * sizeof(int));
    double* B_reordered = NULL;

    if (rank == 0) {
        B_reordered = malloc(size * n * col_block * sizeof(double));
        for (int proc = 0; proc < size; ++proc) {
            int p_coords[2];
            MPI_Cart_coords(grid_comm, proc, 2, p_coords);
            int col_offset = p_coords[1] * col_block;
            int index = p_coords[0] * dims[1] + p_coords[1];

            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < col_block; ++j) {
                    B_reordered[index * n * col_block + i * col_block + j] =
                        B_full.data[i * k + col_offset + j];
                }
            }
            sendcounts_B[index] = n * col_block;
            displs_B[index] = index * n * col_block;
        }
    }

    MPI_Scatterv(B_reordered, sendcounts_B, displs_B, MPI_DOUBLE,
                 B_block.data, n * col_block, MPI_DOUBLE, 0, grid_comm);

    // Local computation
    matrixMultiply(&A_block, &B_block, &C_block);

    // Gather C
    int* recvcounts_C = malloc(size * sizeof(int));
    int* displs_C = malloc(size * sizeof(int));
    double* C_temp = NULL;

    if (rank == 0) {
        C_full.rows = m;
        C_full.cols = k;
        C_full.data = malloc(m * k * sizeof(double));
        C_temp = malloc(size * row_block * col_block * sizeof(double));
        for (int proc = 0; proc < size; ++proc) {
            int p_coords[2];
            MPI_Cart_coords(grid_comm, proc, 2, p_coords);
            int index = p_coords[0] * dims[1] + p_coords[1];
            recvcounts_C[index] = row_block * col_block;
            displs_C[index] = index * row_block * col_block;
        }
    }

    MPI_Gatherv(C_block.data, row_block * col_block, MPI_DOUBLE,
                C_temp, recvcounts_C, displs_C, MPI_DOUBLE,
                0, grid_comm);

    if (rank == 0) {
        for (int proc = 0; proc < size; ++proc) {
            int p_coords[2];
            MPI_Cart_coords(grid_comm, proc, 2, p_coords);
            int row_offset = p_coords[0] * row_block;
            int col_offset = p_coords[1] * col_block;
            int index = p_coords[0] * dims[1] + p_coords[1];
            for (int i = 0; i < row_block; ++i) {
                for (int j = 0; j < col_block; ++j) {
                    C_full.data[(row_offset + i) * k + col_offset + j] =
                        C_temp[index * row_block * col_block + i * col_block + j];
                }
            }
        }

        double end = MPI_Wtime();
        printf("计算完成，耗时 %.6f 秒\n", end - start);
        // printMatrix("C", &C_full);
        free(C_full.data);
        free(C_temp);
        free(B_reordered);
    }

    free(A_block.data);
    free(B_block.data);
    free(C_block.data);
    free(sendcounts_A);
    free(displs_A);
    free(sendcounts_B);
    free(displs_B);
    free(recvcounts_C);
    free(displs_C);

    MPI_Finalize();
    return 0;
}

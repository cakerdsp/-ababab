#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>
#include <time.h>

#define SPARSITY 0.8

typedef struct {
    int rows, cols, nnz;
    double* values;
    int* col_idx;
    int* row_ptr;
} SparseMatrixCSR;

void initSparseMatrix(SparseMatrixCSR* mat, int rows, int cols) {
    mat->rows = rows;
    mat->cols = cols;
    mat->row_ptr = malloc((rows + 1) * sizeof(int));
    int max_nnz = (int)((1.0 - SPARSITY) * rows * cols);
    mat->values = malloc(max_nnz * sizeof(double));
    mat->col_idx = malloc(max_nnz * sizeof(int));

    int nnz = 0;
    mat->row_ptr[0] = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (((double)rand() / RAND_MAX) > SPARSITY) {
                if (nnz < max_nnz) {
                    mat->values[nnz] = (double)rand() / RAND_MAX;
                    mat->col_idx[nnz] = j;
                    nnz++;
                }
            }
        }
        mat->row_ptr[i + 1] = nnz;
    }
    mat->nnz = nnz;
}

void sparseCSRMultiply(SparseMatrixCSR* A, SparseMatrixCSR* B, SparseMatrixCSR* C) {
    int m = A->rows, k = B->cols;
    int* row_ptr = malloc((m + 1) * sizeof(int));
    int* temp_col = calloc(k, sizeof(int));
    double* temp_val = calloc(k, sizeof(double));
    int capacity = 1000;
    double* values = malloc(capacity * sizeof(double));
    int* col_idx = malloc(capacity * sizeof(int));
    int nnz = 0;

    row_ptr[0] = 0;
    for (int i = 0; i < m; i++) {
        memset(temp_val, 0, k * sizeof(double));
        memset(temp_col, 0, k * sizeof(int));
        for (int idx = A->row_ptr[i]; idx < A->row_ptr[i + 1]; idx++) {
            int a_col = A->col_idx[idx];
            double a_val = A->values[idx];
            for (int j = B->row_ptr[a_col]; j < B->row_ptr[a_col + 1]; j++) {
                int b_col = B->col_idx[j];
                double b_val = B->values[j];
                if (temp_col[b_col] == 0) temp_col[b_col] = 1;
                temp_val[b_col] += a_val * b_val;
            }
        }
        for (int j = 0; j < k; j++) {
            if (temp_col[j]) {
                if (nnz == capacity) {
                    capacity *= 2;
                    values = realloc(values, capacity * sizeof(double));
                    col_idx = realloc(col_idx, capacity * sizeof(int));
                }
                values[nnz] = temp_val[j];
                col_idx[nnz] = j;
                nnz++;
            }
        }
        row_ptr[i + 1] = nnz;
    }

    C->rows = m;
    C->cols = k;
    C->nnz = nnz;
    C->values = values;
    C->col_idx = col_idx;
    C->row_ptr = row_ptr;

    free(temp_val);
    free(temp_col);
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc != 4) {
        if (rank == 0)
            printf("Usage: %s <m> <n> <k>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    int m = atoi(argv[1]), n = atoi(argv[2]), k = atoi(argv[3]);

    SparseMatrixCSR A, B, local_A, local_C;

    int* sendcounts = malloc(size * sizeof(int));
    int* displs = malloc(size * sizeof(int));
    int* rowcounts = malloc(size * sizeof(int));
    int* rowdispls = malloc(size * sizeof(int));
    int* start_row_ptr_vals = malloc(size * sizeof(int));

    if (rank == 0) {
        srand(time(NULL));
        initSparseMatrix(&A, m, n);
        initSparseMatrix(&B, n, k);

        for (int i = 0; i < size; ++i) {
            int rs = (m * i) / size;
            int re = (m * (i + 1)) / size;
            rowcounts[i] = re - rs;
            rowdispls[i] = rs;
            sendcounts[i] = A.row_ptr[re] - A.row_ptr[rs];
            displs[i] = A.row_ptr[rs];
            start_row_ptr_vals[i] = A.row_ptr[rs];
        }
    }

    // 广播 B 数据
    MPI_Bcast(&B.rows, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&B.cols, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&B.nnz, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank != 0) {
        B.row_ptr = malloc((B.rows + 1) * sizeof(int));
        B.values = malloc(B.nnz * sizeof(double));
        B.col_idx = malloc(B.nnz * sizeof(int));
    }

    MPI_Bcast(B.row_ptr, B.rows + 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(B.values, B.nnz, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(B.col_idx, B.nnz, MPI_INT, 0, MPI_COMM_WORLD);

    int local_rows;
    MPI_Scatter(rowcounts, 1, MPI_INT, &local_rows, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int local_row_ptr_offset = 0;
    if (rank == 0) {
        local_row_ptr_offset = 0;
    } else {
        MPI_Recv(&local_row_ptr_offset, 1, MPI_INT, 0, 100, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }

    if (rank == 0) {
        for (int i = 1; i < size; ++i)
            MPI_Send(&start_row_ptr_vals[i], 1, MPI_INT, i, 100, MPI_COMM_WORLD);
    }

    int* local_row_ptr = malloc((local_rows + 1) * sizeof(int));
    MPI_Scatterv(A.row_ptr + 1, rowcounts, rowdispls, MPI_INT,
                 local_row_ptr + 1, local_rows, MPI_INT, 0, MPI_COMM_WORLD);
    local_row_ptr[0] = 0;
    for (int i = 0; i < local_rows; ++i)
        local_row_ptr[i + 1] -= local_row_ptr_offset;

    int local_nnz = local_row_ptr[local_rows];

    double* local_values = malloc(local_nnz * sizeof(double));
    int* local_col_idx = malloc(local_nnz * sizeof(int));

    MPI_Scatterv(A.values, sendcounts, displs, MPI_DOUBLE,
                 local_values, local_nnz, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Scatterv(A.col_idx, sendcounts, displs, MPI_INT,
                 local_col_idx, local_nnz, MPI_INT, 0, MPI_COMM_WORLD);

    local_A.rows = local_rows;
    local_A.cols = n;
    local_A.nnz = local_nnz;
    local_A.values = local_values;
    local_A.col_idx = local_col_idx;
    local_A.row_ptr = local_row_ptr;

    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();

    sparseCSRMultiply(&local_A, &B, &local_C);

    double end = MPI_Wtime();

    int* all_nnz = NULL;
    int* recvdispls = NULL;
    if (rank == 0) {
        all_nnz = malloc(size * sizeof(int));
    }

    MPI_Gather(&local_C.nnz, 1, MPI_INT, all_nnz, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        recvdispls = malloc(size * sizeof(int));
        recvdispls[0] = 0;
        for (int i = 1; i < size; ++i)
            recvdispls[i] = recvdispls[i - 1] + all_nnz[i - 1];

        int total_nnz = recvdispls[size - 1] + all_nnz[size - 1];
        double* final_values = malloc(total_nnz * sizeof(double));
        int* final_col_idx = malloc(total_nnz * sizeof(int));

        MPI_Gatherv(local_C.values, local_C.nnz, MPI_DOUBLE,
                    final_values, all_nnz, recvdispls, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        MPI_Gatherv(local_C.col_idx, local_C.nnz, MPI_INT,
                    final_col_idx, all_nnz, recvdispls, MPI_INT, 0, MPI_COMM_WORLD);

        printf("总乘法耗时: %.6f 秒\n", end - start);

        free(final_values);
        free(final_col_idx);
        free(recvdispls);
        free(all_nnz);
    } else {
        MPI_Gatherv(local_C.values, local_C.nnz, MPI_DOUBLE,
                    NULL, NULL, NULL, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        MPI_Gatherv(local_C.col_idx, local_C.nnz, MPI_INT,
                    NULL, NULL, NULL, MPI_INT, 0, MPI_COMM_WORLD);
    }

    free(local_A.values); free(local_A.col_idx); free(local_A.row_ptr);
    free(local_C.values); free(local_C.col_idx); free(local_C.row_ptr);
    free(B.values); free(B.col_idx); free(B.row_ptr);
    free(sendcounts); free(displs); free(rowcounts); free(rowdispls); free(start_row_ptr_vals);

    MPI_Finalize();
    return 0;
}

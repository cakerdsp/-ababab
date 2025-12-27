#include <stdio.h>
#include <cuda_runtime.h>
#include <stdlib.h>
#include <time.h>

#define IDX(i, j, n) ((i) * (n) + (j))

#define TILE_DIM 32
#define BLOCK_ROWS 8

__global__ void transposeSharedFlexibleKernel(float* A, float* AT, int n) {
    __shared__ float tile[TILE_DIM][TILE_DIM + 1];  // 避免 bank conflict

    int x = blockIdx.x * TILE_DIM + threadIdx.x;
    int y = blockIdx.y * TILE_DIM + threadIdx.y;

    // 以 BLOCK_ROWS 为单位分多次加载tile的内容
    for (int i = 0; i < TILE_DIM; i += BLOCK_ROWS) {
        if (x < n && (y + i) < n) {
            tile[threadIdx.y + i][threadIdx.x] = A[IDX(y + i, x, n)];
        }
    }

    __syncthreads();

    // 交换 blockIdx 的 x 和 y，实现转置效果
    x = blockIdx.y * TILE_DIM + threadIdx.x;
    y = blockIdx.x * TILE_DIM + threadIdx.y;

    for (int i = 0; i < TILE_DIM; i += BLOCK_ROWS) {
        if (x < n && (y + i) < n) {
            AT[IDX(y + i, x, n)] = tile[threadIdx.x][threadIdx.y + i];
        }
    }
}

void fillMatrix(float* A, int n) {
    for (int i = 0; i < n * n; i++) {
        A[i] = static_cast<float>(rand()) / RAND_MAX;
    }
}

void printMatrix(float* A, int n, const char* name) {
    printf("%s:\n", name);
    for (int i = 0; i < n && i < 8; i++) {
        for (int j = 0; j < n && j < 8; j++) {
            printf("%6.2f ", A[IDX(i, j, n)]);
        }
        printf("\n");
    }
    printf("...\n");
}

int main(int argc, char** argv) {
    if (argc != 2) {
        printf("Usage: %s <n>\n", argv[0]);
        return 1;
    }
    int n = atoi(argv[1]);
    size_t size = n * n * sizeof(float);

    float* h_A = (float*)malloc(size);
    float* h_AT = (float*)malloc(size);
    fillMatrix(h_A, n);

    float *d_A, *d_AT;
    cudaMalloc(&d_A, size);
    cudaMalloc(&d_AT, size);
    cudaMemcpy(d_A, h_A, size, cudaMemcpyHostToDevice);

    dim3 blockDim(TILE_DIM, BLOCK_ROWS);  // 每个 block 线程数
    dim3 gridDim((n + TILE_DIM - 1) / TILE_DIM, (n + TILE_DIM - 1) / TILE_DIM);  // grid 维度

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    transposeSharedFlexibleKernel<<<gridDim, blockDim>>>(d_A, d_AT, n);
    cudaEventRecord(stop);

    cudaMemcpy(h_AT, d_AT, size, cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();

    float milliseconds;
    cudaEventElapsedTime(&milliseconds, start, stop);

    printMatrix(h_A, n, "Matrix A");
    printMatrix(h_AT, n, "Matrix A^T");
    printf("Transpose time: %.4f ms\n", milliseconds);

    cudaFree(d_A);
    cudaFree(d_AT);
    free(h_A);
    free(h_AT);

    return 0;
}
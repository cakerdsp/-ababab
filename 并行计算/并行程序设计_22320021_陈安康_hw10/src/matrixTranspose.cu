#include <stdio.h>
#include <cuda_runtime.h>
#include <stdlib.h>
#include <time.h>

#define IDX(i, j, n) ((i) * (n) + (j))

__global__ void transposeKernel(float* A, float* AT, int n) {
    int i = blockIdx.y * blockDim.y + threadIdx.y;  // 行
    int j = blockIdx.x * blockDim.x + threadIdx.x;  // 列
    if (i < n && j < n) {
        AT[IDX(j, i, n)] = A[IDX(i, j, n)];
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

    int blockDimx = 16;
    int blockDimy = 16;
    dim3 blockDim(blockDimx, blockDimy);
    dim3 gridDim((n + blockDimx - 1) / blockDimx, (n + blockDimy - 1) / blockDimy);

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    cudaEventRecord(start);
    transposeKernel<<<gridDim, blockDim>>>(d_A, d_AT, n);
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

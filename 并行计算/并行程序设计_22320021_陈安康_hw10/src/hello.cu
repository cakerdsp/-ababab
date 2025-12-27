#include <stdio.h>

__global__ void helloFromGPU() {
    int block = blockIdx.x;
    int x = threadIdx.x;
    int y = threadIdx.y;

    printf("Hello World from Thread (%d,%d) in block %d!\n", x, y, block);
}

int main() {
    int n, m, k;
    printf("Enter n m k:");
    scanf("%d %d %d", &n, &m, &k);
    printf("Hello World from the host!\n");
    dim3 threadsPerBlock(m,k);
    dim3 numBlocks(n);
    helloFromGPU<<<numBlocks, threadsPerBlock>>>();
    cudaDeviceSynchronize();
    return 0;
}
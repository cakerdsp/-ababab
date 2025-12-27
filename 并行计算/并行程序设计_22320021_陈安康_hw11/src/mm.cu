#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <stdexcept>

#include "cuda_runtime.h"


#define TILE_SIZE 16

inline void checkCudaErr(cudaError_t err, const char* file, int line) {
    if (err != cudaSuccess) {
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) 
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}
#define CHECK_CUDA_ERR(err) (checkCudaErr(err, __FILE__, __LINE__))



__global__ void gemm_naive(const float* A, const float* B, float* C, int m, int n, int k) {
    // 计算当前线程负责的 C 矩阵元素的全局行和列
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    // 边界检查，防止线程访问越界内存
    if (row < m && col < k) {
        float sum = 0.0f;
        // 计算点积: A的第row行 * B的第col列
        // 这里的每一次 A[...] 和 B[...] 都是一次全局内存读取
        for (int i = 0; i < n; ++i) {
            sum += A[row * n + i] * B[i * k + col];
        }
        C[row * k + col] = sum;
    }
}


__global__ void gemm_shared(const float* A, const float* B, float* C, int m, int n, int k) {
    // 声明共享内存来存放 A 和 B 的子矩阵 (Tile)
    // 每个线程块(Block)都拥有自己的一份共享内存
    __shared__ float tile_A[TILE_SIZE][TILE_SIZE];
    __shared__ float tile_B[TILE_SIZE][TILE_SIZE];

    // 计算当前线程在线程块内的局部索引 (0 到 TILE_SIZE-1)
    int tx = threadIdx.x;
    int ty = threadIdx.y;

    // 计算当前线程负责的 C 矩阵元素的全局行和列
    int row = blockIdx.y * TILE_SIZE + ty;
    int col = blockIdx.x * TILE_SIZE + tx;

    float sum = 0.0f;

    // 循环遍历所有需要的子矩阵块来计算最终的点积
    for (int t = 0; t < (n + TILE_SIZE - 1) / TILE_SIZE; ++t) {
        
        // 每个线程负责从全局内存加载一个元素到共享内存
        const int A_row = row;
        const int A_col = t * TILE_SIZE + tx;
        if (A_row < m && A_col < n) {
            tile_A[ty][tx] = A[A_row * n + A_col];
        } else {
            tile_A[ty][tx] = 0.0f;
        }

        const int B_row = t * TILE_SIZE + ty;
        const int B_col = col;
        if (B_row < n && B_col < k) {
            tile_B[ty][tx] = B[B_row * k + B_col];
        } else {
            tile_B[ty][tx] = 0.0f;
        }

        // 保证所有线程都完成了从全局内存到共享内存的加载后，再进行下一步计算
        __syncthreads();

        // 每个线程计算 TILE_SIZE 次乘加操作
        for (int i = 0; i < TILE_SIZE; ++i) {
            sum += tile_A[ty][i] * tile_B[i][tx];
        }

        // 保证所有线程都完成了本次子块的计算后，再进入下一次循环去加载新的子块
        __syncthreads();
    }

    // 将最终结果写回全局内存
    if (row < m && col < k) {
        C[row * k + col] = sum;
    }
}



// 矩阵初始化函数
void initialize_matrix(float* mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i) {
        mat[i] = static_cast<float>(rand()) / static_cast<float>(RAND_MAX);
    }
}

// 矩阵打印函数 (用于验证结果，数据量大时建议只打印一部分)
void print_matrix(const char* name, const float* mat, int rows, int cols) {
    std::cout << "Matrix " << name << ":" << std::endl;
    for (int r = 0; r < std::min(rows, 10); ++r) {
        for (int c = 0; c < std::min(cols, 10); ++c) {
            std::cout << mat[r * cols + c] << " ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}


int main(int argc, char** argv) {
    if (argc != 4) {
        std::cerr << "用法: " << argv[0] << " m n k" << std::endl;
        std::cerr << "例如: " << argv[0] << " 1024 1024 1024" << std::endl;
        return 1;
    }

    // 从命令行参数获取矩阵维度
    int m = std::atoi(argv[1]);
    int n = std::atoi(argv[2]);
    int k = std::atoi(argv[3]);

    if (m < 128 || m > 2048 || n < 128 || n > 2048 || k < 128 || k > 2048) {
        std::cerr << "错误: 矩阵维度 m, n, k 必须在 [128, 2048] 范围内。" << std::endl;
        return 1;
    }

    std::cout << "正在计算矩阵乘法 C(" << m << "x" << k << ") = A(" 
              << m << "x" << n << ") * B(" << n << "x" << k << ")" << std::endl;
    
    // 初始化随机数种子
    srand(static_cast<unsigned int>(time(0)));

    // 1. 在主机端 (CPU) 分配内存
    float *h_A = new float[m * n];
    float *h_B = new float[n * k];
    float *h_C_naive = new float[m * k];
    float *h_C_shared = new float[m * k];

    // 2. 初始化主机端的矩阵 A 和 B
    initialize_matrix(h_A, m, n);
    initialize_matrix(h_B, n, k);

    // 3. 在设备端 (GPU) 分配内存
    float *d_A, *d_B, *d_C;
    CHECK_CUDA_ERR(cudaMalloc(&d_A, m * n * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_B, n * k * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_C, m * k * sizeof(float)));

    // 4. 将输入矩阵从主机复制到设备
    CHECK_CUDA_ERR(cudaMemcpy(d_A, h_A, m * n * sizeof(float), cudaMemcpyHostToDevice));
    CHECK_CUDA_ERR(cudaMemcpy(d_B, h_B, n * k * sizeof(float), cudaMemcpyHostToDevice));


    cudaEvent_t start, stop;
    CHECK_CUDA_ERR(cudaEventCreate(&start));
    CHECK_CUDA_ERR(cudaEventCreate(&stop));
    

    dim3 blockDimNaive(16, 16); // 可尝试不同大小
    dim3 gridDimNaive((k + blockDimNaive.x - 1) / blockDimNaive.x, (m + blockDimNaive.y - 1) / blockDimNaive.y);

    CHECK_CUDA_ERR(cudaEventRecord(start));
    gemm_naive<<<gridDimNaive, blockDimNaive>>>(d_A, d_B, d_C, m, n, k);
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize()); // 确保 kernel 执行完毕
    
    float time_naive;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&time_naive, start, stop));
    CHECK_CUDA_ERR(cudaMemcpy(h_C_naive, d_C, m * k * sizeof(float), cudaMemcpyDeviceToHost));

    double gflops_naive = (2.0 * m * n * k) / (time_naive * 1e6);
    std::cout << "Naive Kernel 执行时间: " << time_naive << " ms" << std::endl;
    std::cout << "Naive Kernel 性能: " << gflops_naive << " GFLOPS" << std::endl << std::endl;
    

    dim3 blockDimShared(TILE_SIZE, TILE_SIZE);
    dim3 gridDimShared((k + blockDimShared.x - 1) / blockDimShared.x, (m + blockDimShared.y - 1) / blockDimShared.y);

    CHECK_CUDA_ERR(cudaEventRecord(start));
    gemm_shared<<<gridDimShared, blockDimShared>>>(d_A, d_B, d_C, m, n, k);
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize());

    float time_shared;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&time_shared, start, stop));
    CHECK_CUDA_ERR(cudaMemcpy(h_C_shared, d_C, m * k * sizeof(float), cudaMemcpyDeviceToHost));

    double gflops_shared = (2.0 * m * n * k) / (time_shared * 1e6);
    std::cout << "Shared Memory Kernel 执行时间: " << time_shared << " ms" << std::endl;
    std::cout << "Shared Memory Kernel 性能: " << gflops_shared << " GFLOPS" << std::endl << std::endl;

    // --- 输出矩阵 ---
    print_matrix("A", h_A, m, n);
    print_matrix("B", h_B, n, k);
    // 选择一个结果进行打印
    print_matrix("C (Shared Memory)", h_C_shared, m, k);

    // 8. 释放所有内存和事件
    delete[] h_A;
    delete[] h_B;
    delete[] h_C_naive;
    delete[] h_C_shared;
    CHECK_CUDA_ERR(cudaFree(d_A));
    CHECK_CUDA_ERR(cudaFree(d_B));
    CHECK_CUDA_ERR(cudaFree(d_C));
    CHECK_CUDA_ERR(cudaEventDestroy(start));
    CHECK_CUDA_ERR(cudaEventDestroy(stop));

    return 0;
}
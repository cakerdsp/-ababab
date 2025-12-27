#include <iostream>
#include <cmath>
#include <stdexcept>
#include <cstdlib> 

#include "cuda_runtime.h"

// --- CUDA 错误检查宏 ---
inline void checkCudaErr(cudaError_t err, const char* file, int line) {
    if (err != cudaSuccess) {
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) 
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}
#define CHECK_CUDA_ERR(err) (checkCudaErr(err, __FILE__, __LINE__))


__global__ void im2col_kernel(float* col_matrix, const float* input, 
                              int input_h, int input_w, int channels,
                              int kernel_h, int kernel_w, int stride, int pad,
                              int output_h, int output_w) {

    const int kernel_flat_size = kernel_h * kernel_w * channels;
    const int output_pixels = output_h * output_w;

    int row_idx = blockIdx.y * blockDim.y + threadIdx.y;
    int col_idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (row_idx >= kernel_flat_size || col_idx >= output_pixels) {
        return;
    }

    int oh = col_idx / output_w;
    int ow = col_idx % output_w;
    int c = row_idx / (kernel_h * kernel_w);
    int kh_rem = row_idx % (kernel_h * kernel_w);
    int kh = kh_rem / kernel_w;
    int kw = kh_rem % kernel_w;
    int in_y = oh * stride - pad + kh;
    int in_x = ow * stride - pad + kw;

    float val = 0.0f;
    if (in_y >= 0 && in_y < input_h && in_x >= 0 && in_x < input_w) {
        val = input[c * (input_h * input_w) + in_y * input_w + in_x];
    }
    
    col_matrix[row_idx * output_pixels + col_idx] = val;
}


#define TILE_SIZE 16
__global__ void gemm_shared(const float* A, const float* B, float* C, int m, int n, int k) {
    __shared__ float tile_A[TILE_SIZE][TILE_SIZE];
    __shared__ float tile_B[TILE_SIZE][TILE_SIZE];

    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int row = blockIdx.y * TILE_SIZE + ty;
    int col = blockIdx.x * TILE_SIZE + tx;

    float sum = 0.0f;
    for (int t = 0; t < (n + TILE_SIZE - 1) / TILE_SIZE; ++t) {
        if (row < m && (t * TILE_SIZE + tx) < n) {
            tile_A[ty][tx] = A[row * n + (t * TILE_SIZE + tx)];
        } else {
            tile_A[ty][tx] = 0.0f;
        }

        if ((t * TILE_SIZE + ty) < n && col < k) {
            tile_B[ty][tx] = B[(t * TILE_SIZE + ty) * k + col];
        } else {
            tile_B[ty][tx] = 0.0f;
        }
        __syncthreads();

        for (int i = 0; i < TILE_SIZE; ++i) {
            sum += tile_A[ty][i] * tile_B[i][tx];
        }
        __syncthreads();
    }

    if (row < m && col < k) {
        C[row * k + col] = sum;
    }
}


int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "用法: " << argv[0] << " <input_size> <kernel_size>" << std::endl;
        return 1;
    }


    const int input_size = std::atoi(argv[1]);
    const int kernel_dim = std::atoi(argv[2]);
    const int stride = 1; // 步幅
    
    const int num_kernels = 3; 
    const int input_h = input_size;
    const int input_w = input_size;
    const int channels = 3; 
    const int kernel_h = kernel_dim;
    const int kernel_w = kernel_dim;
    
    const int pad = kernel_h / 2;
    const int output_h = (input_h - kernel_h + 2 * pad) / stride + 1;
    const int output_w = (input_w - kernel_w + 2 * pad) / stride + 1;

    std::cout << "输入尺寸: " << input_h << "x" << input_w << "x" << channels << std::endl;
    std::cout << "卷积核尺寸: " << kernel_h << "x" << kernel_w << "x" << channels << std::endl;
    std::cout << "步幅: " << stride << ", 填充: " << pad << ", 输出通道数: " << num_kernels << std::endl;
    std::cout << "输出尺寸: " << output_h << "x" << output_w << "x" << num_kernels << std::endl;

    const size_t kernel_flat_size = (size_t)kernel_h * kernel_w * channels;
    const size_t input_data_size = (size_t)input_h * input_w * channels;
    const size_t kernel_total_size = (size_t)num_kernels * kernel_flat_size;
    
    float *h_input, *h_kernel, *h_output_gemm;

    h_input = (float*)malloc(input_data_size * sizeof(float));
    h_kernel = (float*)malloc(kernel_total_size * sizeof(float));

    if (!h_input || !h_kernel) {
        std::cerr << "主机内存分配失败 (malloc failed)!" << std::endl;
        free(h_input);
        free(h_kernel);
        return 1;
    }

    for(size_t i = 0; i < input_data_size; ++i) h_input[i] = static_cast<float>(i % 256);
    for(size_t i = 0; i < kernel_total_size; ++i) h_kernel[i] = static_cast<float>(i % 10);


    const int output_pixels = output_h * output_w;
    const int m = num_kernels;       
    const int n = kernel_flat_size;
    const int k = output_pixels;     


    float *d_input, *d_kernel, *d_col_matrix, *d_output_gemm;
    CHECK_CUDA_ERR(cudaMalloc(&d_input, input_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_kernel, kernel_total_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_col_matrix, (size_t)n * k * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_output_gemm, (size_t)m * k * sizeof(float)));
    

    CHECK_CUDA_ERR(cudaMemcpy(d_input, h_input, input_data_size * sizeof(float), cudaMemcpyHostToDevice));
    CHECK_CUDA_ERR(cudaMemcpy(d_kernel, h_kernel, kernel_total_size * sizeof(float), cudaMemcpyHostToDevice));
    

    cudaEvent_t start, stop;
    CHECK_CUDA_ERR(cudaEventCreate(&start));
    CHECK_CUDA_ERR(cudaEventCreate(&stop));
    
    CHECK_CUDA_ERR(cudaEventRecord(start));


    dim3 block_dim_im2col(16, 16);
    dim3 grid_dim_im2col((output_pixels + block_dim_im2col.x - 1) / block_dim_im2col.x,
                         (kernel_flat_size + block_dim_im2col.y - 1) / block_dim_im2col.y);
    
    im2col_kernel<<<grid_dim_im2col, block_dim_im2col>>>(d_col_matrix, d_input, 
        input_h, input_w, channels, kernel_h, kernel_w, stride, pad, output_h, output_w);


    dim3 block_dim_gemm(TILE_SIZE, TILE_SIZE);
    dim3 grid_dim_gemm((k + block_dim_gemm.x - 1) / block_dim_gemm.x, 
                       (m + block_dim_gemm.y - 1) / block_dim_gemm.y);
    
    gemm_shared<<<grid_dim_gemm, block_dim_gemm>>>(d_kernel, d_col_matrix, d_output_gemm, m, n, k);
    
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize());

    float milliseconds = 0;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&milliseconds, start, stop));
    
    std::cout << "\nGPU 端总计算时间 (im2col+GEMM): " << milliseconds << " ms" << std::endl;


    const size_t output_data_size = (size_t)m * k;

    h_output_gemm = (float*)malloc(output_data_size * sizeof(float));
    if (!h_output_gemm) {
        std::cerr << "主机输出内存分配失败 (malloc failed)!" << std::endl;
        return 1;
    }
    
    CHECK_CUDA_ERR(cudaMemcpy(h_output_gemm, d_output_gemm, output_data_size * sizeof(float), cudaMemcpyDeviceToHost));
    
    // std::cout << "计算结果 (抽样前10个值): ";
    // for (size_t i = 0; i < 10 && i < output_data_size; ++i) {
    //     std::cout << h_output_gemm[i] << " ";
    // }
    // std::cout << std::endl;


    free(h_input);
    free(h_kernel);
    free(h_output_gemm);

    CHECK_CUDA_ERR(cudaFree(d_input));
    CHECK_CUDA_ERR(cudaFree(d_kernel));
    CHECK_CUDA_ERR(cudaFree(d_col_matrix));
    CHECK_CUDA_ERR(cudaFree(d_output_gemm));
    CHECK_CUDA_ERR(cudaEventDestroy(start));
    CHECK_CUDA_ERR(cudaEventDestroy(stop));

    return 0;
}
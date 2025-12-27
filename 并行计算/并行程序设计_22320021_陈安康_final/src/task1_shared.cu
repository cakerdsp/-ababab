#include <iostream>
#include <cmath>
#include <cstdlib>
#include <stdexcept>
#include <iomanip> 

#include "cuda_runtime.h"

//  这个版本效果并不好
inline void checkCudaErr(cudaError_t err, const char* file, int line) {
    if (err != cudaSuccess) {
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) 
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}
#define CHECK_CUDA_ERR(err) (checkCudaErr(err, __FILE__, __LINE__))

// --- 常量定义 ---
constexpr int BLOCK_DIM = 16;

__global__ void final_shared_mem_conv(const float* input, const float* kernel, float* output,
                                      int input_h, int input_w, int channels,
                                      int kernel_h, int kernel_w, int stride, int pad,
                                      int output_h, int output_w, int num_output_channels) {
    

    extern __shared__ float tile[];

    const int tile_dim = BLOCK_DIM + kernel_h - 1;
    int tx = threadIdx.x;
    int ty = threadIdx.y;
    

    int out_x = blockIdx.x * BLOCK_DIM + tx;
    int out_y = blockIdx.y * BLOCK_DIM + ty;
    int oc = blockIdx.z; // 输出通道由 grid.z 决定


    if (out_x >= output_w || out_y >= output_h || oc >= num_output_channels) {
        return;
    }


    float sum = 0.0f;
    const int input_plane_size = input_h * input_w;
    const int kernel_plane_size = kernel_h * kernel_w;
    const int single_kernel_size = channels * kernel_plane_size;


    for (int c = 0; c < channels; ++c) {

        int block_start_x = blockIdx.x * BLOCK_DIM * stride;
        int block_start_y = blockIdx.y * BLOCK_DIM * stride;
        
        const float* current_channel_input = input + c * input_plane_size;

        for (int j = 0; j < tile_dim; j += BLOCK_DIM) {
            for (int i = 0; i < tile_dim; i += BLOCK_DIM) {
                int current_load_ty = ty + j;
                int current_load_tx = tx + i;

                if (current_load_ty < tile_dim && current_load_tx < tile_dim) {
                    int load_y = block_start_y + current_load_ty - pad;
                    int load_x = block_start_x + current_load_tx - pad;
                    int tile_idx = current_load_ty * tile_dim + current_load_tx;

                    if (load_y >= 0 && load_y < input_h && load_x >= 0 && load_x < input_w) {
                        tile[tile_idx] = current_channel_input[load_y * input_w + load_x];
                    } else {
                        tile[tile_idx] = 0.0f;
                    }
                }
            }
        }
        

        __syncthreads();


        for (int kh = 0; kh < kernel_h; ++kh) {
            for (int kw = 0; kw < kernel_w; ++kw) {
                int tile_idx = (ty + kh) * tile_dim + (tx + kw);
                int kernel_idx = oc * single_kernel_size + c * kernel_plane_size + kh * kernel_w + kw;
                sum += tile[tile_idx] * kernel[kernel_idx];
            }
        }

        __syncthreads();
    }


    int output_idx = oc * (output_h * output_w) + out_y * output_w + out_x;
    output[output_idx] = sum;
}


int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "用法: " << argv[0] << " <input_size> <kernel_size>" << std::endl;
        return 1;
    }


    const int input_size = std::atoi(argv[1]);
    const int kernel_size = std::atoi(argv[2]);


    const int channels = 3;            // 输入通道数
    const int num_output_channels = 64;  // 输出通道数
    const int stride = 1;              // 步幅


    const int input_h = input_size;
    const int input_w = input_size;
    const int kernel_h = kernel_size;
    const int kernel_w = kernel_size;
    const int pad = kernel_size / 2;

    const int output_h = (input_h - kernel_h + 2 * pad) / stride + 1;
    const int output_w = (input_w - kernel_w + 2 * pad) / stride + 1;

    std::cout << "输入尺寸: " << input_h << "x" << input_w << "x" << channels << std::endl;
    std::cout << "卷积核尺寸: " << kernel_h << "x" << kernel_w << "x" << channels << std::endl;
    std::cout << "步幅: " << stride << ", 填充: " << pad << ", 输出通道数: " << num_output_channels << std::endl;
    std::cout << "输出尺寸: " << output_h << "x" << output_w << "x" << num_output_channels << std::endl;

    const size_t input_data_size = (size_t)input_h * input_w * channels;
    const size_t kernel_data_size = (size_t)kernel_h * kernel_w * channels * num_output_channels;
    const size_t output_data_size = (size_t)output_h * output_w * num_output_channels;

    float* h_input = (float*)malloc(input_data_size * sizeof(float));
    float* h_kernel = (float*)malloc(kernel_data_size * sizeof(float));
    float* h_output = (float*)malloc(output_data_size * sizeof(float));

    if (!h_input || !h_kernel || !h_output) {
        std::cerr << "内存分配失败!" << std::endl;
        free(h_input); free(h_kernel); free(h_output);
        return 1;
    }

    for(size_t i = 0; i < input_data_size; ++i) h_input[i] = static_cast<float>(i % 256);
    for(size_t i = 0; i < kernel_data_size; ++i) h_kernel[i] = static_cast<float>(rand()) / RAND_MAX;

    float *d_input, *d_kernel, *d_output;
    CHECK_CUDA_ERR(cudaMalloc(&d_input, input_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_kernel, kernel_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_output, output_data_size * sizeof(float)));

    CHECK_CUDA_ERR(cudaMemcpy(d_input, h_input, input_data_size * sizeof(float), cudaMemcpyHostToDevice));
    CHECK_CUDA_ERR(cudaMemcpy(d_kernel, h_kernel, kernel_data_size * sizeof(float), cudaMemcpyHostToDevice));

    const int tile_dim = BLOCK_DIM + kernel_size - 1;
    const size_t shared_mem_size = (size_t)tile_dim * tile_dim * sizeof(float);
    std::cout << "每个线程块分配的动态共享内存大小: " << shared_mem_size << " bytes" << std::endl;
    
    cudaEvent_t start, stop;
    CHECK_CUDA_ERR(cudaEventCreate(&start));
    CHECK_CUDA_ERR(cudaEventCreate(&stop));

    dim3 block_dim(BLOCK_DIM, BLOCK_DIM, 1);
    dim3 grid_dim((output_w + block_dim.x - 1) / block_dim.x, 
                  (output_h + block_dim.y - 1) / block_dim.y,
                  num_output_channels);
    
    CHECK_CUDA_ERR(cudaEventRecord(start));
    final_shared_mem_conv<<<grid_dim, block_dim, shared_mem_size>>>(
        d_input, d_kernel, d_output,
        input_h, input_w, channels,
        kernel_h, kernel_w, stride, pad,
        output_h, output_w, num_output_channels);
    CHECK_CUDA_ERR(cudaGetLastError());
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize());

    float milliseconds = 0;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&milliseconds, start, stop));

    std::cout << "\nGPU (最终优化版) 计算时间: " << milliseconds << " ms" << std::endl;

    CHECK_CUDA_ERR(cudaMemcpy(h_output, d_output, output_data_size * sizeof(float), cudaMemcpyDeviceToHost));
    
    std::cout << "\n抽样检查输出结果 (第一个通道左上角 5x5):" << std::endl;
    for (int y = 0; y < 5 && y < output_h; ++y) {
        for (int x = 0; x < 5 && x < output_w; ++x) {
            std::cout << std::fixed << std::setprecision(4) 
                      << h_output[y * output_w + x] << "\t";
        }
        std::cout << "\n";
    }

    free(h_input);
    free(h_kernel);
    free(h_output);

    CHECK_CUDA_ERR(cudaFree(d_input));
    CHECK_CUDA_ERR(cudaFree(d_kernel));
    CHECK_CUDA_ERR(cudaFree(d_output));
    CHECK_CUDA_ERR(cudaEventDestroy(start));
    CHECK_CUDA_ERR(cudaEventDestroy(stop));

    return 0;
}
#include <iostream>
#include <cmath>
#include <cstdlib>
#include <stdexcept>

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

__global__ void direct_convolution_kernel(const float* input, const float* kernel, float* output,
                                          int input_h, int input_w, int channels,
                                          int kernel_h, int kernel_w, int stride, int pad,
                                          int output_h, int output_w, int num_output_channels) {
    int out_x = blockIdx.x * blockDim.x + threadIdx.x;
    int out_y = blockIdx.y * blockDim.y + threadIdx.y;

    if (out_x < output_w && out_y < output_h) {
        for (int oc = 0; oc < num_output_channels; ++oc) { // 遍历输出通道
            float sum = 0.0f;
            
            for (int c = 0; c < channels; ++c) {         // 遍历通道
                for (int kh = 0; kh < kernel_h; ++kh) {    // 遍历卷积核高度
                    for (int kw = 0; kw < kernel_w; ++kw) { // 遍历卷积核宽度
                        
                        int in_y = out_y * stride + kh - pad;
                        int in_x = out_x * stride + kw - pad;

                        if (in_y >= 0 && in_y < input_h && in_x >= 0 && in_x < input_w) {
                            int input_idx = c * (input_h * input_w) + in_y * input_w + in_x;
                            int kernel_idx = oc * channels * kernel_h * kernel_w + c * kernel_h * kernel_w + kh * kernel_w + kw;
                            sum += input[input_idx] * kernel[kernel_idx];
                        }
                    }
                }
            }
            int output_idx = oc * (output_h * output_w) + out_y * output_w + out_x;
            output[output_idx] = sum;
        }
    }
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "用法: " << argv[0] << " <input_size> <kernel_size>" << std::endl;
        return 1;
    }

    const int input_size = std::atoi(argv[1]);
    const int kernel_size = std::atoi(argv[2]);

    const int input_h = input_size;
    const int input_w = input_size;
    const int channels = 3;
    const int num_output_channels = 3; // 假设有3个输出通道
    const int kernel_h = kernel_size;
    const int kernel_w = kernel_size;
    const int stride = 1;  // 固定步幅为1

    const int pad = kernel_h / 2;
    const int output_h = (input_h - kernel_h + 2 * pad) / stride + 1;
    const int output_w = (input_w - kernel_w + 2 * pad) / stride + 1;

    std::cout << "输入尺寸: " << input_h << "x" << input_w << "x" << channels << std::endl;
    std::cout << "卷积核尺寸: " << kernel_h << "x" << kernel_w << "x" << channels << std::endl;
    std::cout << "步幅: " << stride << ", 填充: " << pad << std::endl;
    std::cout << "输出尺寸: " << output_h << "x" << output_w << "x" << num_output_channels << std::endl;

    const int input_data_size = input_h * input_w * channels;
    const int kernel_data_size = kernel_h * kernel_w * channels * num_output_channels;
    const int output_data_size = output_h * output_w * num_output_channels;

    float* h_input = static_cast<float*>(malloc(input_data_size * sizeof(float)));
    float* h_kernel = static_cast<float*>(malloc(kernel_data_size * sizeof(float)));
    float* h_output = static_cast<float*>(malloc(output_data_size * sizeof(float)));

    if (!h_input || !h_kernel || !h_output) {
        std::cerr << "内存分配失败!" << std::endl;
        free(h_input);
        free(h_kernel);
        free(h_output);
        return 1;
    }

    for(size_t i = 0; i < input_data_size; ++i) h_input[i] = static_cast<float>(rand()) / RAND_MAX;
    for(size_t i = 0; i < kernel_data_size; ++i) h_kernel[i] = static_cast<float>(rand()) / RAND_MAX;

    float *d_input, *d_kernel, *d_output;
    CHECK_CUDA_ERR(cudaMalloc(&d_input, input_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_kernel, kernel_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_output, output_data_size * sizeof(float)));

    CHECK_CUDA_ERR(cudaMemcpy(d_input, h_input, input_data_size * sizeof(float), cudaMemcpyHostToDevice));
    CHECK_CUDA_ERR(cudaMemcpy(d_kernel, h_kernel, kernel_data_size * sizeof(float), cudaMemcpyHostToDevice));

    cudaEvent_t start, stop;
    CHECK_CUDA_ERR(cudaEventCreate(&start));
    CHECK_CUDA_ERR(cudaEventCreate(&stop));

    dim3 block_dim(16, 16);
    dim3 grid_dim((output_w + block_dim.x - 1) / block_dim.x, (output_h + block_dim.y - 1) / block_dim.y);
    
    CHECK_CUDA_ERR(cudaEventRecord(start));
    direct_convolution_kernel<<<grid_dim, block_dim>>>(d_input, d_kernel, d_output,
                                                        input_h, input_w, channels,
                                                        kernel_h, kernel_w, stride, pad,
                                                        output_h, output_w, num_output_channels);
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize());

    float milliseconds = 0;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&milliseconds, start, stop));

    std::cout << "直接卷积计算时间: " << milliseconds << " ms" << std::endl;

    CHECK_CUDA_ERR(cudaMemcpy(h_output, d_output, output_data_size * sizeof(float), cudaMemcpyDeviceToHost));

    // --- 输出卷积结果 ---
    // for (int oc = 0; oc < num_output_channels; ++oc) {
    //     std::cout << "Output Channel " << oc + 1 << ":\n";
    //     for (int y = 0; y < output_h; ++y) {
    //         for (int x = 0; x < output_w; ++x) {
    //             std::cout << h_output[oc * (output_h * output_w) + y * output_w + x] << " ";
    //         }
    //         std::cout << "\n";
    //     }
    //     std::cout << "\n";
    // }

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




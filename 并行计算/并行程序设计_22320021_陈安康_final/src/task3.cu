#include <iostream>

#include <cmath>
#include <stdexcept>
#include <cstdlib> 

#include "cuda_runtime.h"
#include "cudnn.h" 


#define CHECK_CUDA_ERR(err) (checkCudaErr(err, __FILE__, __LINE__))
inline void checkCudaErr(cudaError_t err, const char* file, int line) {
    if (err != cudaSuccess) {
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) 
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}
#define CHECK_CUDNN_ERR(err) (checkCudnnErr(err, __FILE__, __LINE__))
inline void checkCudnnErr(cudnnStatus_t err, const char* file, int line) {
    if (err != CUDNN_STATUS_SUCCESS) {
        std::cerr << "cuDNN Error: " << cudnnGetErrorString(err) 
                  << " at " << file << ":" << line << std::endl;
        exit(EXIT_FAILURE);
    }
}


int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "用法: " << argv[0] << " <input_size> <kernel_size>" << std::endl;
        return 1;
    }

    const int n_images = 1; // Batch size
    const int input_size = std::atoi(argv[1]);
    const int kernel_size = std::atoi(argv[2]); // 【改动】从命令行获取 kernel_size

    const int stride = 1;

    const int input_c = 3;
    const int input_h = input_size;
    const int input_w = input_size;
    
    const int kernel_c_out = 3; // 您可以根据需要修改输出通道数
    const int kernel_c_in = 3;
    const int kernel_h = kernel_size; 
    const int kernel_w = kernel_size; 
    const int pad = kernel_h / 2;

    const size_t input_data_size = (size_t)n_images * input_c * input_h * input_w;
    const size_t kernel_data_size = (size_t)kernel_c_out * kernel_c_in * kernel_h * kernel_w;
    
    float *h_input, *h_kernel;
    h_input = (float*)malloc(input_data_size * sizeof(float));
    h_kernel = (float*)malloc(kernel_data_size * sizeof(float));

    if (!h_input || !h_kernel) {
        std::cerr << "主机内存分配失败 (malloc failed)!" << std::endl;
        free(h_input);
        free(h_kernel);
        return 1;
    }
    
    for(size_t i = 0; i < input_data_size; ++i) h_input[i] = static_cast<float>(rand()) / RAND_MAX;
    for(size_t i = 0; i < kernel_data_size; ++i) h_kernel[i] = static_cast<float>(rand()) / RAND_MAX;


    float *d_input, *d_kernel, *d_output;
    CHECK_CUDA_ERR(cudaMalloc(&d_input, input_data_size * sizeof(float)));
    CHECK_CUDA_ERR(cudaMalloc(&d_kernel, kernel_data_size * sizeof(float)));
    

    cudnnHandle_t cudnn_handle;
    CHECK_CUDNN_ERR(cudnnCreate(&cudnn_handle));
    
    cudnnTensorDescriptor_t input_desc, output_desc;
    cudnnFilterDescriptor_t kernel_desc; 
    CHECK_CUDNN_ERR(cudnnCreateTensorDescriptor(&input_desc));
    CHECK_CUDNN_ERR(cudnnCreateTensorDescriptor(&output_desc));
    CHECK_CUDNN_ERR(cudnnCreateFilterDescriptor(&kernel_desc));
    
    CHECK_CUDNN_ERR(cudnnSetTensor4dDescriptor(input_desc, CUDNN_TENSOR_NCHW, CUDNN_DATA_FLOAT, n_images, input_c, input_h, input_w));
    CHECK_CUDNN_ERR(cudnnSetFilter4dDescriptor(kernel_desc, CUDNN_DATA_FLOAT, CUDNN_TENSOR_NCHW, kernel_c_out, kernel_c_in, kernel_h, kernel_w));
    

    cudnnConvolutionDescriptor_t conv_desc;
    CHECK_CUDNN_ERR(cudnnCreateConvolutionDescriptor(&conv_desc));
    CHECK_CUDNN_ERR(cudnnSetConvolution2dDescriptor(conv_desc, pad, pad, stride, stride, 1, 1, CUDNN_CROSS_CORRELATION, CUDNN_DATA_FLOAT));

    int out_n, out_c, out_h, out_w;
    CHECK_CUDNN_ERR(cudnnGetConvolution2dForwardOutputDim(conv_desc, input_desc, kernel_desc, &out_n, &out_c, &out_h, &out_w));
    
    std::cout << "cuDNN 输出尺寸: " << out_h << "x" << out_w << "x" << out_c << std::endl;
    const size_t output_data_size = (size_t)out_n * out_c * out_h * out_w;
    CHECK_CUDA_ERR(cudaMalloc(&d_output, output_data_size * sizeof(float)));
    CHECK_CUDNN_ERR(cudnnSetTensor4dDescriptor(output_desc, CUDNN_TENSOR_NCHW, CUDNN_DATA_FLOAT, out_n, out_c, out_h, out_w));
    
    cudnnConvolutionFwdAlgoPerf_t perf_results[1];
    int returned_algo_count;
    CHECK_CUDNN_ERR(cudnnGetConvolutionForwardAlgorithm_v7(cudnn_handle, input_desc, kernel_desc, conv_desc, output_desc, 1, &returned_algo_count, perf_results));
    cudnnConvolutionFwdAlgo_t algo = perf_results[0].algo;
    std::cout << "cuDNN 选择了算法: " << algo << std::endl;

    size_t workspace_size = 0;
    CHECK_CUDNN_ERR(cudnnGetConvolutionForwardWorkspaceSize(cudnn_handle, input_desc, kernel_desc, conv_desc, output_desc, algo, &workspace_size));
    void* d_workspace = nullptr;
    if (workspace_size > 0) {
        CHECK_CUDA_ERR(cudaMalloc(&d_workspace, workspace_size));
    }
    std::cout << "cuDNN 工作空间大小: " << workspace_size / (1024.0 * 1024.0) << " MB" << std::endl;

    CHECK_CUDA_ERR(cudaMemcpy(d_input, h_input, input_data_size * sizeof(float), cudaMemcpyHostToDevice));
    CHECK_CUDA_ERR(cudaMemcpy(d_kernel, h_kernel, kernel_data_size * sizeof(float), cudaMemcpyHostToDevice));
    
    cudaEvent_t start, stop;
    CHECK_CUDA_ERR(cudaEventCreate(&start));
    CHECK_CUDA_ERR(cudaEventCreate(&stop));

    float alpha = 1.0f, beta = 0.0f;
    CHECK_CUDA_ERR(cudaEventRecord(start));
    CHECK_CUDNN_ERR(cudnnConvolutionForward(cudnn_handle, &alpha, input_desc, d_input, kernel_desc, d_kernel, conv_desc, algo, d_workspace, workspace_size, &beta, output_desc, d_output));
    CHECK_CUDA_ERR(cudaEventRecord(stop));
    CHECK_CUDA_ERR(cudaDeviceSynchronize());

    float milliseconds = 0;
    CHECK_CUDA_ERR(cudaEventElapsedTime(&milliseconds, start, stop));
    std::cout << "cuDNN 卷积计算时间: " << milliseconds << " ms" << std::endl;

    free(h_input);
    free(h_kernel);
    
    if (d_workspace) cudaFree(d_workspace);
    cudaFree(d_input);
    cudaFree(d_kernel);
    cudaFree(d_output);
    cudnnDestroyConvolutionDescriptor(conv_desc);
    cudnnDestroyTensorDescriptor(input_desc);
    cudnnDestroyTensorDescriptor(output_desc);
    cudnnDestroyFilterDescriptor(kernel_desc); 
    cudnnDestroy(cudnn_handle);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return 0;
}
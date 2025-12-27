#include <iostream>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include "mkl.h"  // 引入 Intel MKL 头文件

using namespace std;
using namespace chrono;

const int n = 1024, m = 4096, p = 1024;

// 生成随机矩阵
void initializeMatrix(double* matrix, int rows, int cols) {
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = static_cast<double>(rand()) / RAND_MAX;
    }
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr)));  // 设置随机数种子

    // 采用 MKL 提供的 mkl_malloc 进行对齐分配
    double *A = (double*)mkl_malloc(n * m * sizeof(double), 64);
    double *B = (double*)mkl_malloc(m * p * sizeof(double), 64);
    double *C = (double*)mkl_malloc(n * p * sizeof(double), 64);

    if (A == nullptr || B == nullptr || C == nullptr) {
        cout << "Memory allocation failed!" << endl;
        return -1;
    }

    initializeMatrix(A, n, m);
    initializeMatrix(B, m, p);
    fill_n(C, n * p, 0.0);  // 初始化 C 为 0

    auto start = high_resolution_clock::now();

    // 采用 Intel MKL 进行矩阵乘法计算
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, 
                n, p, m, 1.0, A, m, B, p, 0.0, C, p);

    auto end = high_resolution_clock::now();
    duration<double> elapsed = end - start;

    cout << "Execution Time with Intel MKL: " << elapsed.count() << " sec" << endl;

    // 释放内存
    mkl_free(A);
    mkl_free(B);
    mkl_free(C);

    return 0;
}

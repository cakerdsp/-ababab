#include <iostream>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <ctime>

using namespace std;
using namespace chrono;

const int n = 1024, m = 4096, p = 1024;

// 采用 `__restrict__` 提示编译器进行优化
void matrixMultiply(const double* __restrict__ A, 
                    const double* __restrict__ B, 
                    double* __restrict__ C, int n, int m, int p) 
{
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < m; k++) {
            for (int j = 0; j < p; j++) {
                C[i * p + j] += A[i * m + k] * B[k * p + j];
            }
        }
    }
}

// 生成随机矩阵
void initializeMatrix(double* matrix, int rows, int cols) {
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = static_cast<double>(rand()) / RAND_MAX;
    }
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr)));  // 设置随机数种子

    // 采用一维数组存储矩阵，提高缓存局部性
    double *A = new double[n * m];
    double *B = new double[m * p];
    double *C = new double[n * p];

    initializeMatrix(A, n, m);
    initializeMatrix(B, m, p);

    auto start = high_resolution_clock::now();
    matrixMultiply(A, B, C, n, m, p);
    auto end = high_resolution_clock::now();

    duration<double> elapsed = end - start;
    cout << "Execution Time: " << elapsed.count() << " sec" << endl;

    // 释放内存
    delete[] A;
    delete[] B;
    delete[] C;

    return 0;
}

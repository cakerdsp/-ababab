#include <iostream>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <ctime>

using namespace std;
using namespace chrono;

const int n = 1024, m = 4096, p = 1024;

// 采用 `__restrict__` + 循环展开（Unrolling）
void matrixMultiply(const double* __restrict__ A, 
                    const double* __restrict__ B, 
                    double* __restrict__ C, int n, int m, int p) 
{
    // 初始化 C 矩阵，避免使用未定义值
    // for (int i = 0; i < n * p; i++) {
    //     C[i] = 0.0;
    // }

    // 进行矩阵乘法计算，并使用 4×展开加速
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < m; k++) {
            double Aik = A[i * m + k];  // 预取 A[i][k]，减少内存访问

            for (int j = 0; j < p; j += 2) {  // 2 次展开,展開次數越多，效果反而越不好
                C[i * p + j]     += Aik * B[k * p + j];
                C[i * p + j + 1] += Aik * B[k * p + j + 1];
                // C[i * p + j + 2] += Aik * B[k * p + j + 2];
                // C[i * p + j + 3] += Aik * B[k * p + j + 3];
            }
        }
    }
}


// void matrixMultiply(const double* A, 
//                     const double*  B, 
//                     double*  C, int n, int m, int p) 
// {
//     // 初始化 C 矩阵，避免使用未定义值
//     // for (int i = 0; i < n * p; i++) {
//     //     C[i] = 0.0;
//     // }

//     // 进行矩阵乘法计算，并使用 4×展开加速
//     for (int i = 0; i < n; i++) {
//         for (int k = 0; k < m; k++) {
//             double Aik = A[i * m + k];  // 预取 A[i][k]，减少内存访问

//             for (int j = 0; j < p; j += 8) {  // 8 次展开
//                 C[i * p + j]     += Aik * B[k * p + j];
//                 C[i * p + j + 1] += Aik * B[k * p + j + 1];
//                 C[i * p + j + 2] += Aik * B[k * p + j + 2];
//                 C[i * p + j + 3] += Aik * B[k * p + j + 3];
//                 C[i * p + j + 4] += Aik * B[k * p + j + 4];
//                 C[i * p + j + 5] += Aik * B[k * p + j + 5];
//                 C[i * p + j + 6] += Aik * B[k * p + j + 6];
//                 C[i * p + j + 7] += Aik * B[k * p + j + 7];
//             }
//         }
//     }
// }

// 生成随机矩阵
void initializeMatrix(double* matrix, int rows, int cols) {
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = static_cast<double>(rand()) / RAND_MAX;
    }
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr)));  // 设置随机数种子

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

    delete[] A;
    delete[] B;
    delete[] C;

    return 0;
}

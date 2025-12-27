#include <iostream>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <ctime>

using namespace std;
using namespace chrono;

const int n = 1024, m = 4096, p = 1024;

// 动态分配内存并返回二维数组
void matrixMultiply(double** A, double** B, double** C) {
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < m; k++) {
            for (int j = 0; j < p; j++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

// 初始化二维数组
void initializeMatrix(double** matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = (double)rand() / (double)RAND_MAX;
        }
    }
}

int main() {
    srand(static_cast<unsigned int>(time(nullptr))); // 设置随机数种子
    double** A = new double*[n];
    for (int i = 0; i < n; i++) {
        A[i] = new double[m];
    }
    double** B = new double*[m];
    for (int i = 0; i < m; i++) {
        B[i] = new double[p];
    }
    double** C = new double*[n];
    for (int i = 0; i < n; i++) {
        C[i] = new double[p];
        for (int j = 0; j < p; j++) {
            C[i][j] = 0.0;
        }
    }
    initializeMatrix(A, n, m);
    initializeMatrix(B, m, p);

    auto start = high_resolution_clock::now();
    matrixMultiply(A, B, C);
    auto end = high_resolution_clock::now();

    duration<double> elapsed = end - start;
    cout << "Execution Time: " << elapsed.count() << " sec" << endl;

    // 释放内存
    for (int i = 0; i < n; i++) {
        delete[] C[i];
    }
    delete[] C;
    for (int i = 0; i < n; i++) {
        delete[] A[i];
    }
    delete[] A;
    for (int i = 0; i < m; i++) {
        delete[] B[i];
    }
    delete[] B;

    return 0;
}
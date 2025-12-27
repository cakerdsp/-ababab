#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <chrono>

using namespace std;
using namespace chrono;

long long flop_count = 0; // 全局变量，记录浮点运算次数
// 初始化二维数组
void initializeMatrix(double** matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = (double)rand() / (double)RAND_MAX;
        }
    }
}

// 矩阵加法
void addMatrix(double** A, double** B, double** C, int n, int m) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            C[i][j] = A[i][j] + B[i][j];
            flop_count++;
}

// 矩阵减法
void subMatrix(double** A, double** B, double** C, int n, int m) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            C[i][j] = A[i][j] - B[i][j];
            flop_count++;
}

// 申请矩阵
double** allocateMatrix(int rows, int cols) {
    double** matrix = new double*[rows];
    for (int i = 0; i < rows; i++) {
        matrix[i] = new double[cols];
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = 0.0;
        }
    }
    return matrix;
}

// 释放矩阵
void freeMatrix(double** matrix, int rows) {
    for (int i = 0; i < rows; i++)
        delete[] matrix[i];
    delete[] matrix;
}

// Strassen 递归算法
void strassen(double** A, double** B, double** C, int n, int m, int p) {
    if (n <= 64 || m <= 64 || p <= 64) {
        for (int i = 0; i < n; i++)
            for (int k = 0; k < m; k++) 
                for (int j = 0; j < p; j++) {
                    C[i][j] += A[i][k] * B[k][j];
                    flop_count += 2;
                }
        return;
    }

    int new_n = n / 2, new_m = m / 2, new_p = p / 2;

    double** A11 = allocateMatrix(new_n, new_m);
    double** A12 = allocateMatrix(new_n, new_m);
    double** A21 = allocateMatrix(new_n, new_m);
    double** A22 = allocateMatrix(new_n, new_m);

    double** B11 = allocateMatrix(new_m, new_p);
    double** B12 = allocateMatrix(new_m, new_p);
    double** B21 = allocateMatrix(new_m, new_p);
    double** B22 = allocateMatrix(new_m, new_p);

    double** C11 = allocateMatrix(new_n, new_p);
    double** C12 = allocateMatrix(new_n, new_p);
    double** C21 = allocateMatrix(new_n, new_p);
    double** C22 = allocateMatrix(new_n, new_p);

    double** M1 = allocateMatrix(new_n, new_p);
    double** M2 = allocateMatrix(new_n, new_p);
    double** M3 = allocateMatrix(new_n, new_p);
    double** M4 = allocateMatrix(new_n, new_p);
    double** M5 = allocateMatrix(new_n, new_p);
    double** M6 = allocateMatrix(new_n, new_p);
    double** M7 = allocateMatrix(new_n, new_p);

    double** tempA = allocateMatrix(new_n, new_m);
    double** tempB = allocateMatrix(new_m, new_p);

    for (int i = 0; i < new_n; i++) {
        for (int j = 0; j < new_p; j++) {
            A11[i][j] = A[i][j];
            A12[i][j] = A[i][j + new_m];
            A21[i][j] = A[i + new_n][j];
            A22[i][j] = A[i + new_n][j + new_m];

            B11[i][j] = B[i][j];
            B12[i][j] = B[i][j + new_p];
            B21[i][j] = B[i + new_m][j];
            B22[i][j] = B[i + new_m][j + new_p];
        }
    }

    addMatrix(A11, A22, tempA, new_n, new_m);
    addMatrix(B11, B22, tempB, new_m, new_p);
    strassen(tempA, tempB, M1, new_n, new_m, new_p);

    addMatrix(A21, A22, tempA, new_n, new_m);
    strassen(tempA, B11, M2, new_n, new_m, new_p);

    subMatrix(B12, B22, tempB, new_m, new_p);
    strassen(A11, tempB, M3, new_n, new_m, new_p);

    subMatrix(B21, B11, tempB, new_m, new_p);
    strassen(A22, tempB, M4, new_n, new_m, new_p);

    addMatrix(A11, A12, tempA, new_n, new_m);
    strassen(tempA, B22, M5, new_n, new_m, new_p);

    subMatrix(A21, A11, tempA, new_n, new_m);
    addMatrix(B11, B12, tempB, new_m, new_p);
    strassen(tempA, tempB, M6, new_n, new_m, new_p);

    subMatrix(A12, A22, tempA, new_n, new_m);
    addMatrix(B21, B22, tempB, new_m, new_p);
    strassen(tempA, tempB, M7, new_n, new_m, new_p);

    addMatrix(M1, M4, tempA, new_n, new_p);
    subMatrix(tempA, M5, tempB, new_n, new_p);
    addMatrix(tempB, M7, C11, new_n, new_p);

    addMatrix(M3, M5, C12, new_n, new_p);
    addMatrix(M2, M4, C21, new_n, new_p);

    addMatrix(M1, M3, tempA, new_n, new_p);
    subMatrix(tempA, M2, tempB, new_n, new_p);
    addMatrix(tempB, M6, C22, new_n, new_p);

    // **合并结果**
    for (int i = 0; i < new_n; i++) {
        for (int j = 0; j < new_p; j++) {
            C[i][j] = C11[i][j];
            C[i][j + new_p] = C12[i][j];
            C[i + new_n][j] = C21[i][j];
            C[i + new_n][j + new_p] = C22[i][j];
        }
    }

    freeMatrix(A11, new_n); freeMatrix(A12, new_n);
    freeMatrix(A21, new_n); freeMatrix(A22, new_n);
    freeMatrix(B11, new_m); freeMatrix(B12, new_m);
    freeMatrix(B21, new_m); freeMatrix(B22, new_m);
    freeMatrix(C11, new_n); freeMatrix(C12, new_n);
    freeMatrix(C21, new_n); freeMatrix(C22, new_n);
    freeMatrix(M1, new_n); freeMatrix(M2, new_n);
    freeMatrix(M3, new_n); freeMatrix(M4, new_n);
    freeMatrix(M5, new_n); freeMatrix(M6, new_n);
    freeMatrix(M7, new_n);
    freeMatrix(tempA, new_n); freeMatrix(tempB, new_m);
}


int main() {
    srand(time(nullptr));
    int n = 1024, m = 4096, p = 1024;

    double** A = allocateMatrix(n, m);
    double** B = allocateMatrix(m, p);
    double** C = allocateMatrix(n, p);
    initializeMatrix(A,n,m);
    initializeMatrix(B,m,p);
    auto start = high_resolution_clock::now();
    strassen(A, B, C, n, m, p);
    auto end = high_resolution_clock::now();

    cout << "Computation finished!" << endl;
    cout << "Execution Time: " << duration<double>(end - start).count() << " sec" << endl;
    cout << "Total Floating Point Operations: " << flop_count << endl;
    freeMatrix(A, n);
    freeMatrix(B, m);
    freeMatrix(C, n);

    return 0;
}

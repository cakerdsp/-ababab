import numpy as np
import time

def matrix_multiply(A, B):
    n, m = len(A), len(A[0])
    p = len(B[0])
    C = [[0] * p for _ in range(n)]
    
    for i in range(n):
        for j in range(p):
            for k in range(m):
                C[i][j] += A[i][k] * B[k][j]
    
    return C

n = 1024
m = 4096
p = 1024
# 生成 500x500 矩阵
A = [[1] * n for _ in range(m)]
B = [[1] * m for _ in range(p)]

start_time = time.time()
C = matrix_multiply(A, B)
end_time = time.time()

print(f"Execution Time: {end_time - start_time} sec")
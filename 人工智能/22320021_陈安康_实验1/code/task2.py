import time
def MatrixAdd(A,B):
    n=len(A)
    ans=[]
    for i in range(n):
        row=[]
        for j in range(n):
            row.append(A[i][j]+B[i][j])
        ans.append(row)
    return ans

def MatrixMul(A,B):
    n=len(A)
    ans=[]
    for i in range(n):
        row=[]
        for j in range(n):
            tmp=0
            for k in range(n):
                tmp+=A[i][k]*B[k][j]
            row.append(tmp)
        ans.append(row)
    return ans


matrix1 = [[1, 2, 3],
           [4, 5, 6],
           [7, 8, 9]]

matrix2 = [[9, 8, 7],
           [6, 5, 4],
           [3, 2, 1]]
start_time=time.time()
ans1=MatrixAdd(matrix1,matrix2)
ans2=MatrixMul(matrix1,matrix2)
end_time=time.time()
run_time=start_time-end_time
for cell in ans1:
    print(cell)
print()
for cell in ans2:
    print(cell)
print(run_time)
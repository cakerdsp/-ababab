#include <mpi.h>
#include <complex>
#include <cmath>
#include <iostream>
#include <cstring>
using namespace std;

typedef complex<double> Complex;

// 随机数生成函数
double ggl(double *seed) {
    const double d2 = 2147483647.0; // 2^31 -1
    *seed = fmod(16807.0 * (*seed), d2);
    return (*seed - 1.0) / (d2 - 1.0);
}

// 位逆序置换函数
void bit_reverse(double* data, int n) {
    int bits = 0;
    int temp = n - 1;
    while (temp > 0) {
        bits++;
        temp >>= 1;
    }
    for (int i = 0; i < n; ++i) {
        int j = 0, tmp = i;
        for (int k = 0; k < bits; ++k) {
            j = (j << 1) | (tmp & 1);
            tmp >>= 1;
        }
        if (i < j) {
            std::swap(data[2 * i], data[2 * j]);
            std::swap(data[2 * i + 1], data[2 * j + 1]);
        }
    }
}

// 预计算旋转因子
double* precompute_twiddles(int n) {
    double* W = new double[2 * n];
    for (int i = 0; i < n; ++i) {
        double angle = 2.0 * M_PI * i / n;  // 旋转因子 e^{2πi/N}
        W[2 * i] = cos(angle);
        W[2 * i + 1] = sin(angle);
    }
    return W;
}


void fft_parallel(double* local_data, int N, int local_N, int stages, double* W_N, int rank) {
    
    for (int stage = 0; stage < stages; ++stage) {
        int stride = 1 << stage;
        int group_size = 2 * stride;
        

        if (stride >= local_N) {

            int partner = rank ^ (stride / local_N);
            double* recv_buf = new double[2 * local_N];
   
            MPI_Sendrecv(local_data, 2 * local_N, MPI_DOUBLE, partner, 0,
                         recv_buf, 2 * local_N, MPI_DOUBLE, partner, 0,
                         MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            int flag = (partner < rank) ? -1 : 1;
            // 蝶形运算
            for (int k = 0; k < local_N; ++k) {
                // 计算使用的旋转因子
                int L = stage + 1; 
                int group_idx = rank % (stride / local_N); 
                int j = group_idx * local_N + k;
                int index = j * (1<<(stages-L));
                double wr = W_N[2 * (index % N)];
                double wi = W_N[2 * (index % N) + 1];
                
                // 保存本地数据
                double local_real = local_data[2 * k];
                double local_imag = local_data[2 * k + 1];
                // 保存接收数据
                double recv_real = recv_buf[2 * k];
                double recv_imag = recv_buf[2 * k + 1];
                
                // 计算旋转因子与接收数据的乘积
                double tr = wr * recv_real - wi * recv_imag;
                double ti = wr * recv_imag + wi * recv_real;
                
                // 根据flag选择正确的更新方式
                if (flag == 1) {
                    local_data[2 * k] = local_real + tr;
                    local_data[2 * k + 1] = local_imag + ti;
                } else {
                    local_data[2 * k] = local_real - tr;
                    local_data[2 * k + 1] = local_imag - ti;
                }
            }
            delete[] recv_buf;
        } else {
            // 进程内蝶形运算
            for (int k = 0; k < local_N; k += group_size) { //遍历蝶形运算组，local_N/2^(stage+1)
                for (int j = 0; j < stride; ++j) { //每个蝶形运算组内蝶形运算
                    int idx = k + j;

                
                    double wr = W_N[2 * j * (N/group_size)];
                    double wi = W_N[2 * j * (N/group_size) + 1];
                    // 两个计算数的下标
                    int even_idx = 2 * (idx);
                    int odd_idx = 2 * (idx + stride);

                    double tr = wr * local_data[odd_idx] - wi * local_data[odd_idx + 1];
                    double ti = wr * local_data[odd_idx + 1] + wi * local_data[odd_idx];

                    local_data[odd_idx]     = local_data[even_idx] - tr;
                    local_data[odd_idx + 1] = local_data[even_idx + 1] - ti;
                    local_data[even_idx]   += tr;
                    local_data[even_idx + 1] += ti;
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    int N = 0;
    int nits = 0;
    double* original_data = nullptr;
    double* global_data = nullptr;
    double* W_N = nullptr;
    
    if (rank == 0) { 
        //
        // cout << "please input N and nits, slipt using space" << endl;
        N = atoi(argv[1]);
        nits = atoi(argv[2]);
        
        if ((N & (N - 1)) != 0 || N < 1) {
            cerr << "N is not 2^n.\n";
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        if (N % size != 0) {
            cerr << "N %p != 0\n";
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        
        // 1.生成原始数据并备份
        original_data = new double[2 * N];
        double seed = 331.0;
        for (int i = 0; i < N; ++i) {
            original_data[2 * i] = ggl(&seed);
            original_data[2 * i + 1] = ggl(&seed);
        }
        
        // 2.准备位逆序数据用于正向FFT
        global_data = new double[2 * N];
        memcpy(global_data, original_data, 2 * N * sizeof(double));
        bit_reverse(global_data, N);
    }
    
    // 3.广播N和nits
    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&nits, 1, MPI_INT, 0, MPI_COMM_WORLD);
    
    int stages = log2(N);
    int local_N = N / size;
    double* local_data = new double[2 * local_N];
    

    if (rank == 0) W_N = precompute_twiddles(N);
    else W_N = new double[2 * N];
    MPI_Bcast(W_N, 2 * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    

    // if (rank == 0) cout << "\nrun one time FFT for Checking" << endl;
 
    MPI_Scatter(global_data, 2 * local_N, MPI_DOUBLE, 
               local_data, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    fft_parallel(local_data, N, local_N, stages, W_N, rank);

    double* global_forward = nullptr;
    if (rank == 0) global_forward = new double[2 * N];
    MPI_Gather(local_data, 2 * local_N, MPI_DOUBLE, 
              global_forward, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    

    if (rank == 0) {
        for (int i = 0; i < N; ++i) {
            global_forward[i*2 + 1] = -global_forward[i*2 + 1];
        }
        bit_reverse(global_forward, N);
    }
    
    // 逆向FFT
    MPI_Scatter(global_forward, 2 * local_N, MPI_DOUBLE, 
               local_data, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    fft_parallel(local_data, N, local_N, stages, W_N, rank);
    
    // 本地归一化
    for (int i = 0; i < local_N; ++i) {
        local_data[i*2 + 1] = -local_data[i*2 + 1];
        local_data[i*2] /= N;
        local_data[i*2 + 1] /= N;
    }
    
    // 收集逆向结果并验证
    double* global_inverse = nullptr;
    if (rank == 0) global_inverse = new double[2 * N];
    MPI_Gather(local_data, 2 * local_N, MPI_DOUBLE, 
              global_inverse, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    
    if (rank == 0) {
        double error = 0.0;
        for (int i = 0; i < N; ++i) {
            double dr = global_inverse[2 * i] - original_data[2 * i];
            double di = global_inverse[2 * i + 1] - original_data[2 * i + 1];
            error += dr*dr + di*di;
        }
        error = sqrt(error / N);
        // cout << "Validation Error: " << error << endl;
        
        delete[] global_forward;
        delete[] global_inverse;
    }
    
    // 准备计时迭代的数据
    if (rank == 0) {
        bit_reverse(global_data, N);  // 重新准备初始位逆序数据
    }
    
    // 同步所有进程
    MPI_Barrier(MPI_COMM_WORLD);
    
    // 开始计时
    double start_time = MPI_Wtime();
    
    // 执行nits次计时迭代
    if (rank == 0) cout << "\nrun " << nits << " times FFT " << endl;
    
    for (int iter = 0; iter < nits; ++iter) {

        MPI_Scatter(global_data, 2 * local_N, MPI_DOUBLE, 
                   local_data, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        fft_parallel(local_data, N, local_N, stages, W_N, rank);
        

        double* global_forward = nullptr;
        if (rank == 0) global_forward = new double[2 * N];
        MPI_Gather(local_data, 2 * local_N, MPI_DOUBLE, 
                  global_forward, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        

        if (rank == 0) {
            for (int i = 0; i < N; ++i) {
                global_forward[i*2 + 1] = -global_forward[i*2 + 1]; // 取负虚部
            }
            bit_reverse(global_forward, N);
        }
        //逆向FFT
        MPI_Scatter(global_forward, 2 * local_N, MPI_DOUBLE, 
                   local_data, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        fft_parallel(local_data, N, local_N, stages, W_N, rank);
        //本地归一化
        for (int i = 0; i < local_N; ++i) {
            local_data[i*2 + 1] = -local_data[i*2 + 1]; // 取负虚部
            local_data[i*2] /= N;     // 实部归一化
            local_data[i*2 + 1] /= N; // 虚部归一化
        }
        //收集逆向结果
        double* global_inverse = nullptr;
        if (rank == 0) global_inverse = new double[2 * N];
        MPI_Gather(local_data, 2 * local_N, MPI_DOUBLE, 
                  global_inverse, 2 * local_N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
        //清理内存
        if (rank == 0) {
            delete[] global_forward;
            delete[] global_inverse;
        }
    }
    
    // 结束计时
    double end_time = MPI_Wtime();
    double total_time = end_time - start_time;
    
    // 主进程输出计时结果
    if (rank == 0) {
        cout << "Total time for " << nits << " FFT+IFFT iterations: " 
             << total_time << " seconds" << endl;
        cout << "Average time per FFT+IFFT: " << total_time / nits << " seconds" << endl;
        
        delete[] original_data;
        delete[] global_data;
    }
    
    delete[] local_data;
    delete[] W_N;
    MPI_Finalize();
    return 0;
}
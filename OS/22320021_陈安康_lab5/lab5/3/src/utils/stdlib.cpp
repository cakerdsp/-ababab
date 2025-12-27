#include "os_type.h"

template<typename T>
void swap(T &x, T &y) {
    T z = x;
    x = y;
    y = z;
}


void itos(char *numStr, uint32 num, uint32 mod) {
    // 只能转换2~26进制的整数
    if (mod < 2 || mod > 26 || num < 0) {
        return;
    }

    uint32 length, temp;

    // 进制转换
    length = 0;
    while(num) {
        temp = num % mod;
        num /= mod;
        numStr[length] = temp > 9 ? temp - 10 + 'A' : temp + '0';
        ++length;
    }

    // 特别处理num=0的情况
    if(!length) {
        numStr[0] = '0';
        ++length;
    }

    // 将字符串倒转，使得numStr[0]保存的是num的高位数字
    for(int i = 0, j = length - 1; i < j; ++i, --j) {
        swap(numStr[i], numStr[j]);
    }
    
    numStr[length] = '\0';
}

void ftos(char *numStr, double num, uint32 k) {
    uint32 length = 0,num_int = (int)num;
    // unsigned long long ieee754 = (*(unsigned long long*)(&num) & (0x000fffffffffffff));
    // double num_float = *(double*)&ieee754;
    double num_float = num - (int)num;
    while(num_int) {
        uint32 tmp = num_int % 10;
        num_int /= 10;
        numStr[length] = tmp + '0';
        ++length;
    }
    if(!length) {
        numStr[length] = '0';
        ++length;
    }  
    // 将字符串倒转，使得numStr[0]保存的是num的高位数字
    for(int i = 0, j = length - 1; i < j; ++i, --j) {
        swap(numStr[i], numStr[j]);
    }
    //小数部分不为零，输出小数部分，只输出6位,这部分不用反转
    // if(num_float) {
    // if(num_int == num) {
        numStr[length] = '.';
        ++length;
        num_float *= 10;
        // uint32 k = 3;
        while(k--) {
            numStr[length] = (int)num_float + '0';
            ++length;
            num_float = num_float - (int)num_float;
            num_float *= 10;
        }
    // }
    numStr[length] = '\0';
}
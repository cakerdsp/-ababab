#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

int main() {
    double a, b, c;
    printf("请输入 a b c（范围 [-100, 100]）：\n");
    scanf("%lf %lf %lf", &a, &b, &c);

    if (a == 0) {
        printf("这不是一个二次方程。\n");
        return -1;
    }

    // 开始计时
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    double b2 = b * b;
    double four_ac = 4 * a * c;
    double discriminant = b2 - four_ac;

    double sqrt_discriminant;
    if (discriminant < 0) {
        sqrt_discriminant = -1; // 无实数根
    } else {
        sqrt_discriminant = sqrt(discriminant);
    }

    double two_a = 2 * a;
    double x1, x2;
    if (sqrt_discriminant < 0) {
        x1 = x2 = NAN;
    } else {
        x1 = (-b + sqrt_discriminant) / two_a;
        x2 = (-b - sqrt_discriminant) / two_a;
    }

    // 结束计时
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed_sec = end.tv_sec - start.tv_sec + (end.tv_nsec - start.tv_nsec) / 1e9;

    if (isnan(x1)) {
        printf("无实数根。\n");
    } else {
        printf("x1 = %.9f, x2 = %.9f\n", x1, x2);
    }

    printf("总耗时：%.9f 秒\n", elapsed_sec);

    return 0;
}

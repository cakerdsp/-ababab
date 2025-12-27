#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <math.h>
#include <time.h>

int main(int argc, char* argv[]) {
    if (argc != 2) {
        printf("用法: %s <总点数>\n", argv[0]);
        return 1;
    }

    long total_points = atol(argv[1]);
    long points_in_circle = 0;
    unsigned int seed = time(NULL);

    struct timeval start, end;
    gettimeofday(&start, NULL);

    for (long i = 0; i < total_points; ++i) {
        double x = rand_r(&seed) / (double)RAND_MAX;
        double y = rand_r(&seed) / (double)RAND_MAX;
        if (x * x + y * y <= 1.0) {
            points_in_circle++;
        }
    }

    gettimeofday(&end, NULL);

    double pi_estimate = 4.0 * points_in_circle / total_points;
    double elapsed_time = (end.tv_sec - start.tv_sec) +
                          (end.tv_usec - start.tv_usec) / 1e6;

    printf("总点数: %ld\n", total_points);
    printf("圆内点数: %ld\n", points_in_circle);
    printf("π 的估计值: %.6f\n", pi_estimate);
    printf("耗时: %.6f 秒\n", elapsed_time);

    return 0;
}

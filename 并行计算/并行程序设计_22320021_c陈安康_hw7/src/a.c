#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

int main()
{
#define M 500
#define N 500

  double diff;
  double epsilon = 0.001;
  int i, j;
  int iterations = 0;
  int iterations_print = 1;
  double mean = 0.0;
  double u[M][N];
  double w[M][N];
  double my_diff;
  double start, end;

  printf("\n");
  printf("HEATED_PLATE_SERIAL\n");
  printf("  Solving the steady state heat equation on a 2D plate.\n");
  printf("  Grid size: %d x %d\n", M, N);
  printf("  Iteration continues until the max change <= %e\n", epsilon);

  // Set fixed boundary values
  for (i = 1; i < M - 1; i++) {
    w[i][0] = 100.0;
    w[i][N - 1] = 100.0;
  }
  for (j = 0; j < N; j++) {
    w[0][j] = 0.0;
    w[M - 1][j] = 100.0;
  }

  // Compute mean of boundary values
  for (i = 1; i < M - 1; i++) {
    mean += w[i][0] + w[i][N - 1];
  }
  for (j = 0; j < N; j++) {
    mean += w[0][j] + w[M - 1][j];
  }
  mean /= (double)(2 * M + 2 * N - 4);
  printf("  Initial mean value = %f\n", mean);

  // Initialize interior values to the mean
  for (i = 1; i < M - 1; i++) {
    for (j = 1; j < N - 1; j++) {
      w[i][j] = mean;
    }
  }

  printf("\n");
  printf(" Iteration  Change\n");
  printf("\n");

  start = clock();

  diff = epsilon;

  while (epsilon <= diff) {
    // Save current solution
    for (i = 0; i < M; i++) {
      for (j = 0; j < N; j++) {
        u[i][j] = w[i][j];
      }
    }

    // Update values using average of neighbors
    for (i = 1; i < M - 1; i++) {
      for (j = 1; j < N - 1; j++) {
        w[i][j] = 0.25 * (u[i - 1][j] + u[i + 1][j] + u[i][j - 1] + u[i][j + 1]);
      }
    }

    // Compute maximum change
    diff = 0.0;
    for (i = 1; i < M - 1; i++) {
      for (j = 1; j < N - 1; j++) {
        my_diff = fabs(w[i][j] - u[i][j]);
        if (diff < my_diff) {
          diff = my_diff;
        }
      }
    }

    iterations++;
    if (iterations == iterations_print) {
      printf("  %8d  %f\n", iterations, diff);
      iterations_print *= 2;
    }
  }

  end = clock();
  double wall_time = (double)(end - start) / CLOCKS_PER_SEC;

  printf("\n");
  printf("  %8d  %f\n", iterations, diff);
  printf("\n");
  printf("  Tolerance achieved.\n");
  printf("  Elapsed time = %f seconds\n", wall_time);
  printf("\nHEATED_PLATE_SERIAL:\n  Normal end of execution.\n");

  return 0;

#undef M
#undef N
}

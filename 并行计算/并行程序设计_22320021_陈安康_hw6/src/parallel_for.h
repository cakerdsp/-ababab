// parallel_for.h
#ifndef PARALLEL_FOR_H
#define PARALLEL_FOR_H

#include <pthread.h>

void parallel_for(int start, int end, int inc,
                  void (*func)(int, void *),
                  void *args, int num_threads);

#endif
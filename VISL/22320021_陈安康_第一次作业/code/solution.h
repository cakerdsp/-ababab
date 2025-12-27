#ifndef SOLUTION_H
#define SOLUTION_H

#include <string>
#include "Graph.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <set>

using namespace std;

#define ACC_RATE 0.5

#define BIPARTITION_RATIO 0.02
class Solution{
    public:
        set<int> boundary_X;
        set<int> boundary_Y;

        void read_benchmark(Graph &graph, string benchmark_name);
        void my_partition_algorithm(Graph graph, set<int> &X, set<int> &Y, string benchmark_name);
        
        // 模拟退火算法相关函数
        void simulated_annealing_partition(Graph &graph, set<int> &X, set<int> &Y);
        int calculate_cost(Graph &graph, set<int> &X, set<int> &Y);
        void generate_initial_solution(Graph graph, set<int> &X, set<int> &Y);
        void generate_new_solution(Graph &graph,set<int> &X, set<int> &Y);
        double cooling_schedule(double t, double acc_rate);
        set<int> find_boundary_nodes(Graph &graph, set<int> &X, set<int> &Y, bool from_X);
        void update_boundary_set(Graph &graph, set<int> &X, int index, bool from_X, bool is_in);
};

#endif
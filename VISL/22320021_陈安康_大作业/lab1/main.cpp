#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <string>
#include <set>
#include "Net.h"
#include "Node.h"
#include "Graph.h"
#include "evaluate.h"
#include "solution.h"

using namespace std;

int main(int argc, char **argv) {

    Solution solution;

    if(argc != 2) {
        cout << "Usage: ./main benchmark_file" << endl;
        exit(-1);
    }
    string benchmark_name = argv[1];
    Graph graph;

    solution.read_benchmark(graph, benchmark_name);    

    cout << "Num nodes: " << graph.get_node_num() << endl;
    cout << "Num nets: " << graph.get_net_num() << endl;

    // 执行图划分算法
    set<int> X, Y;
    solution.my_partition_algorithm(graph, X, Y, benchmark_name);
    
    // 从benchmark_name中提取基本文件名（去除路径和扩展名）
    string base_name = benchmark_name;
    size_t last_slash = base_name.find_last_of("\\/");
    if (last_slash != string::npos) {
        base_name = base_name.substr(last_slash + 1);
    }
    size_t last_dot = base_name.find_last_of(".");
    if (last_dot != string::npos) {
        base_name = base_name.substr(0, last_dot);
    }
    
    // 构造输出文件名：benchmark_name_partition.txt
    string output_filename = base_name + "_partition.txt";
    
    // 评估划分结果
    cout << "割边数: " << calculate_cut(graph, X, Y) << endl;
    cout << "评估结果: " << evaluate(graph, output_filename) << endl;

    return 0;
}
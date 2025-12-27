#include "solution.h"
#include "evaluate.h"
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <algorithm>
#include <random>


void Solution::read_benchmark(Graph &graph, string benchmark_name) {
    ifstream file(benchmark_name);

    if(!file.is_open()) {
        cerr << "Failed to open the file!" << endl;
        exit(-1);
    }

    int edge_num, node_num;
    string line;
    getline(file >> ws, line);
    istringstream iss(line);
    iss >> edge_num;
    iss >> node_num;

    
    for(int i = 0; i < edge_num; i++) {
        getline(file, line);
        istringstream iss(line);
        int node_id;
        
        Net *net = graph.add_net(i);

        while(iss >> node_id) {
            Node *node = graph.get_or_create_node(node_id);
            node->add_net(net);
            net->add_node(node);
        }
        
    }

    file.close();
}


set<int> Solution::find_boundary_nodes(Graph &graph, set<int> &X, set<int> &Y, bool from_X) {
    set<int> boundary_nodes;
    const set<int> &group = from_X ? X : Y;
    const set<int> &other_group = from_X ? Y : X;

    for (int node_id : group) {
        Node *node = graph.get_node(node_id); 
        if (!node) continue;

        // 如果它连接了至少一个来自对方集合的节点，则是边界节点
        vector<Net *> nets = node->get_nets();
        for (const auto &net : nets) {
            for (const auto &adj : net->get_nodes()) {
                if (adj->get_index() != node_id && other_group.count(adj->get_index())) {
                    boundary_nodes.insert(node_id);
                }
            }
        }
    }

    return boundary_nodes;
}

// 注意：假设index在S中操作已经完成
void Solution::update_boundary_set(Graph &graph, set<int> &S, int index, bool from_X, bool is_in) {
    set<int>& boundary = from_X ? boundary_X : boundary_Y;
    Node *node = graph.get_node(index);
    // 如果是移出操作
    if(!is_in) {
        // 先删除源节点
        if(boundary.find(index) != boundary.end()) boundary.erase(index);
        // 添加在S中的邻接点
        for (const auto &net : node->get_nets()) {
            for (const auto &adj : net->get_nodes()) {
                if (adj->get_index() != index && S.count(adj->get_index())) {
                    boundary.insert(adj->get_index());
                }
            }
        }
    } else {
        bool is_acc = false;
        for (const auto &net : node->get_nets()) {
            for (const auto &adj : net->get_nodes()) {
                if (adj->get_index() != index && !S.count(adj->get_index())) {
                    is_acc = true;
                    break;
                }
            }
            if(is_acc) {
                boundary.insert(index);
                break;
            }
        }
    }


}

// 主分区算法，调用模拟退火算法
void Solution::my_partition_algorithm(Graph graph, set<int> &X, set<int> &Y, string benchmark_name) {
    // 调用模拟退火算法进行图划分
    simulated_annealing_partition(graph, X, Y);
    cout << boundary_X.size() << " " << boundary_Y.size() << endl;
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
    
    // 输出划分结果到文件
    ofstream outfile(output_filename);
    if (outfile.is_open()) {
        // 获取节点的最大索引
        int max_index = 0;
        vector<Node *> nodes = graph.get_nodes();
        for (auto node : nodes) {
            max_index = max(max_index, node->get_index());
        }
        
        // 按照索引顺序（从1到max_index）输出划分结果
        for (int i = 1; i <= max_index; i++) {
            // 检查索引i的节点是否存在
            Node* node = graph.get_node(i);
            if (node) {
                // 如果节点在X集合中，输出0，否则输出1
                if (X.find(i) != X.end()) {
                    outfile << "0" << endl;
                } else {
                    outfile << "1" << endl;
                }
            }
        }
        outfile.close();
        cout << "划分结果已保存到: " << output_filename << endl;
    } else {
        cerr << "无法创建输出文件！" << endl;
    }
}

// 计算当前划分的代价（割边数）
int Solution::calculate_cost(Graph &graph, set<int> &X, set<int> &Y) {
    return calculate_cut(graph, X, Y);
}

// // 生成初始解
// void Solution::generate_initial_solution(Graph graph, set<int> &X, set<int> &Y) {
//     // 清空当前解
//     X.clear();
//     Y.clear();
    
//     // 获取所有节点
//     vector<Node *> nodes = graph.get_nodes();
//     int total_nodes = nodes.size();
    
//     // 随机打乱节点顺序
//     std::random_device rd;
//     std::mt19937 g(rd());
//     std::shuffle(nodes.begin(), nodes.end(), g);
    
//     // 将节点平均分配到X和Y中，确保满足平衡约束
//     int half_size = total_nodes / 2;
//     for (int i = 0; i < total_nodes; i++) {
//         if (i < half_size) {
//             X.insert(nodes[i]->get_index());
//         } else {
//             Y.insert(nodes[i]->get_index());
//         }
//     }
// }

void Solution::generate_initial_solution(Graph graph, set<int> &X, set<int> &Y) {
    // 清空当前解
    X.clear();
    Y.clear();
    
    // 获取所有节点
    vector<Node *> nodes = graph.get_nodes();
    int total_nodes = nodes.size();
    
    // 随机选择一个起始节点
    std::random_device rd;
    std::mt19937 g(rd());
    std::uniform_int_distribution<> dist(0, total_nodes - 1);
    int start_node_index = dist(g);
    Node *start_node = nodes[start_node_index];
    
    // 将起始节点的所有相邻节点添加到集合 X 中
    vector<Net *> nets = start_node->get_nets();
    for (const auto &net : nets) {
        for (const auto &adj : net->get_nodes()) {
            if (adj->get_index() != start_node->get_index()) {
                X.insert(adj->get_index());
            }
        }
    }
    
    // 检查集合 X 的大小是否已经达到了总节点数的一半
    int half_size = total_nodes / 2;
    while (X.size() < half_size) {
        // 从集合 X 中随机选择一个节点，将它的相邻节点添加到集合 X 中
        std::uniform_int_distribution<> dist_X(0, X.size() - 1);
        auto it = X.begin();
        std::advance(it, dist_X(g));
        int node_index = *it;
        Node *node = graph.get_node(node_index);
        vector<Net *> nets = node->get_nets();
        for (const auto &net : nets) {
            for (const auto &adj : net->get_nodes()) {
                if (adj->get_index() != node_index && !X.count(adj->get_index()) && X.size() < half_size) {
                    X.insert(adj->get_index());
                }
            }
        }
    }
    
    // 将剩余的节点添加到集合 Y 中
    for (int i = 0; i < total_nodes; i++) {
        if (!X.count(nodes[i]->get_index())) {
            Y.insert(nodes[i]->get_index());
        }
    }
}

// 生成新解，通过随机交换X和Y中的一个节点
void Solution::generate_new_solution(Graph &graph,set<int> &X, set<int> &Y) {
    // 随机选择X中的一个节点和Y中的一个节点进行交换
    if (X.empty() || Y.empty()) return;
    
    // 如果边界节点集合为空，重新计算
    if (boundary_X.empty()) {
        boundary_X = find_boundary_nodes(graph, X, Y, true);
    }
    if (boundary_Y.empty()) {
        boundary_Y = find_boundary_nodes(graph, X, Y, false);
    }
        
    std::random_device rd;
    std::mt19937 gen(rd());
    
    std::uniform_real_distribution<> rand_prob(0.0, 1.0);
    double prob = rand_prob(gen);
    if (prob < 0.2) {
        // 检查移动一个节点是否会破坏平衡性
        if ((X.size() - 1) * 1.0 / (X.size() + Y.size()) >= 0.5-BIPARTITION_RATIO && (X.size() - 1) * 1.0 / (X.size() + Y.size()) <= 0.5+BIPARTITION_RATIO && !boundary_X.empty()) {
            // 从X移动到Y
            std::uniform_int_distribution<> distX(0, boundary_X.size() - 1);
            auto itX = boundary_X.begin();
            std::advance(itX, distX(gen));
            int nodeX = *itX;
            X.erase(nodeX);
            Y.insert(nodeX);
            update_boundary_set(graph,X, nodeX, 1, 0);
            update_boundary_set(graph,Y, nodeX, 0, 1);
        } else if ((Y.size() - 1) * 1.0 / (X.size() + Y.size()) >= 0.5-BIPARTITION_RATIO && (Y.size() - 1) * 1.0 / (X.size() + Y.size()) <= 0.5+BIPARTITION_RATIO && !boundary_Y.empty()) {
            // 从Y移动到X
            std::uniform_int_distribution<> distY(0, boundary_Y.size() - 1);
            auto itY = boundary_Y.begin();
            std::advance(itY, distY(gen));
            int nodeY = *itY;
            Y.erase(nodeY);
            X.insert(nodeY);
            update_boundary_set(graph,X, nodeY, 1, 1);
            update_boundary_set(graph,Y, nodeY, 0, 0);
        } else {
            // 交换节点以保持平衡
            // 从X中随机选择一个节点
            std::uniform_int_distribution<> distX(0, boundary_X.size() - 1);
            auto itX = boundary_X.begin();
            std::advance(itX, distX(gen));
            int nodeX = *itX;
            
            // 从Y中随机选择一个节点
            std::uniform_int_distribution<> distY(0, boundary_Y.size() - 1);
            auto itY = boundary_Y.begin();
            std::advance(itY, distY(gen));
            int nodeY = *itY;
            
            // 交换节点
            X.erase(nodeX);
            Y.erase(nodeY);
            X.insert(nodeY);
            Y.insert(nodeX);

            update_boundary_set(graph,X, nodeX, 1, 0);
            update_boundary_set(graph,Y, nodeX, 0, 1);
            update_boundary_set(graph,X, nodeY, 1, 1);
            update_boundary_set(graph,Y, nodeY, 0, 0);
        }
    } else {
        // 交换节点以保持平衡
        // 从X中随机选择一个节点
        std::uniform_int_distribution<> distX(0, boundary_X.size() - 1);
        auto itX = boundary_X.begin();
        std::advance(itX, distX(gen));
        int nodeX = *itX;
        
        // 从Y中随机选择一个节点
        std::uniform_int_distribution<> distY(0, boundary_Y.size() - 1);
        auto itY = boundary_Y.begin();
        std::advance(itY, distY(gen));
        int nodeY = *itY;
        
        // 交换节点
        X.erase(nodeX);
        Y.erase(nodeY);
        X.insert(nodeY);
        Y.insert(nodeX);

        update_boundary_set(graph,X, nodeX, 1, 0);
        update_boundary_set(graph,Y, nodeX, 0, 1);
        update_boundary_set(graph,X, nodeY, 1, 1);
        update_boundary_set(graph,Y, nodeY, 0, 0);
    }
    
}

// 温度下降函数
double Solution::cooling_schedule(double t, double acc_rate) {
    if (acc_rate > ACC_RATE) {
        t = t * 0.98;
    } else {
        t = t * 0.95;
    }
    return t; 
}

// 模拟退火算法实现图划分
void Solution::simulated_annealing_partition(Graph &graph, set<int> &X, set<int> &Y) {
    // 初始化随机数生成器
    srand(time(nullptr));
    // 设置初始温度和终止温度
    double T = 100.0;  // 初始温度
    double T0 = 0.1;   // 终止温度
    int n = 500;       // 内循环迭代次数
    // 生成初始解
    generate_initial_solution(graph, X, Y);
    boundary_X = find_boundary_nodes(graph, X, Y, true);
    boundary_Y = find_boundary_nodes(graph, X, Y, false);
    // 计算初始解的代价
    int cost = calculate_cost(graph, X, Y);
    
    // 保存最佳解
    set<int> X_best = X;
    set<int> Y_best = Y;
    set<int> boundary_X_best = boundary_X;
    set<int> boundary_Y_best = boundary_Y;
    int best_cost = cost;
    
    // 模拟退火主循环
    while (T > T0) {
        int accept = 0;
        for (int i = 1; i <= n; i++) {
            // 保存当前解
            set<int> X_current = X;
            set<int> Y_current = Y;
            set<int> boundary_X_current = boundary_X;
            set<int> boundary_Y_current = boundary_Y;
            int current_cost = cost;
            
            // 生成新解
            generate_new_solution(graph, X, Y);
            
            // 计算新解的代价
            int new_cost = calculate_cost(graph, X, Y);
            
            // 如果新解更好，直接接受
            if (new_cost < current_cost) {
                cost = new_cost;
                accept++;
                // 更新最佳解
                if (cost < best_cost) {
                    X_best = X;
                    Y_best = Y;
                    boundary_X_best = boundary_X;
                    boundary_Y_best = boundary_Y;
                    best_cost = cost;
                }
            } 
            // 否则，根据概率接受较差的解
            else {
                double delta = new_cost - current_cost;
                double p = exp(-delta / T);
                double r = (double)rand() / RAND_MAX;
                
                if (r < p) {
                    // 接受新解
                    cost = new_cost;
                    accept++;
                } else {
                    // 拒绝新解，恢复之前的解
                    X = X_current;
                    Y = Y_current;
                    boundary_X = boundary_X_current;
                    boundary_Y = boundary_Y_current;
                }
            }

        }
        double acc_rate = accept * 1.0 / n;
        cout << acc_rate << endl;
        // 降低温度
        T = cooling_schedule(T, acc_rate);
    }
    
    // 返回最佳解
    X = X_best;
    Y = Y_best;
    boundary_X = boundary_X_best;
    boundary_Y = boundary_Y_best;
    
    cout << "最佳割边数: " << best_cost << endl;
}
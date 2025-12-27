#include "Solution.h"
#include "FPGA.h"
#include "Design.h"
#include "Net.h"
#include "RRNode.h"
#include "FpgaTile.h"
#include <queue>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include <limits>
#include <iostream>
#include <random>

using namespace std;

// 辅助函数：计算Net的包围盒面积，用于排序和“恶霸 vs. 受害者”逻辑
double getNetBBoxArea(Net* net) {
    if (!net || net->getSinks().empty()) return 0.0;
    
    int min_x = net->getSource().getX();
    int max_x = net->getSource().getX();
    int min_y = net->getSource().getY();
    int max_y = net->getSource().getY();

    for (auto* sink : net->getSinks()) {
        min_x = std::min(min_x, sink->getX());
        max_x = std::max(max_x, sink->getX());
        min_y = std::min(min_y, sink->getY());
        max_y = std::max(max_y, sink->getY());
    }
    return static_cast<double>((max_x - min_x) + (max_y - min_y)); // 使用半周长
}

// 辅助函数：拆除指定线网的布线路径 (Rip-up a net)
void MyRouter::ripUpNet(Net& net) {
    for (RRNode* node : net.getPath()) {
        // Source节点是路径的根，不应该被完全释放
        if (node == &net.getSource()) continue;

        if (occupancy.count(node)) {
            occupancy[node]--;
            if (occupancy[node] == 0) {
                occupancy.erase(node);
            }
        }
        node->clearNet();
    }
    net.clearPath();

    // 清空后，必须将Source节点重新加回路经的起点
    net.addRRToPath(net.getSource());
}


/**
 * @brief 主布线函数，实现了混合选择标准和最困难优先重布策略
 */
void MyRouter::routeDesign(FPGA &fpga, Design &design) {
    cout << "Starting PathFinder Routing with Hybrid Selection and Hardest-First Rerouting..." << endl;
    auto& nets = design.getNets();

    // --- 可调参数 ---
    const double HIGH_COST_NET_PERCENTAGE = 0.05; // 额外拆除成本最高的Top 5%的线网

    // 1. 初始化历史成本和占用图
    history_cost.clear();
    for (auto* tile : fpga.getTiles()) {
        for (auto* node : tile->getRRNodes()) {
            history_cost[node] = 1.0;
        }
    }
    occupancy.clear();
    for (auto* net : nets) {
        net->clearPath();
        RRNode& source_node = net->getSource();
        source_node.setNet(*net);
        net->addRRToPath(source_node);
        occupancy[&source_node] = 1;
    }

    // 2. 初始布线 (Iteration 0)
    cout << "\n=============== Initial Routing (Iteration 0) =============== " << endl;
    cout << "  [PHASE] Sorting " << nets.size() << " nets by BBox (hardest first)..." << endl;
    std::sort(nets.begin(), nets.end(), [](Net* a, Net* b) {
        return getNetBBoxArea(a) > getNetBBoxArea(b);
    });
    
    cout << "  [PHASE] Routing all nets for the first time..." << endl;
    for (auto* net : nets) {
        this->current_net = net;
        routeNet(fpga, *net);
    }

    // 3. 迭代优化循环 (从第1次迭代开始)
    for (int iter = 1; iter < 100; iter++) {
        cout << "\n=============== Routing iteration " << iter << " =============== " << endl;

        // A. 检查拥塞并更新历史成本
        bool congested = false;
        vector<RRNode*> congested_nodes; // 保存所有拥塞节点
        for (auto const& [node, occ] : occupancy) {
            if (occ > 1) {
                congested = true;
                congested_nodes.push_back(node);
                history_cost[node] += (occ - 1) * H_FAC; 
            }
        }
        cout << "  [SUMMARY] Previous Iteration: " << congested_nodes.size() << " congested nodes found." << endl;
        
        // B. 检查是否收敛
        if (!congested) {
            cout << "\n✅ Routing successful in " << iter << " iterations." << endl;
            finalizeAllRouting(design);
            return;
        }

        // C. 应用“混合选择标准”，识别需要拆除的线网
        set<Net*> nets_to_reroute;
        
        // C.1: 基于“恶霸 vs. 受害者”逻辑，选择拥塞点上的受害者
        cout << "  [PHASE] Identifying 'victim' nets..." << endl;
        for (RRNode* congested_node : congested_nodes) {
            vector<Net*> competing_nets;
            for (Net* net : nets) {
                if (net->getPath().count(congested_node)) {
                    competing_nets.push_back(net);
                }
            }
            if (competing_nets.empty()) continue;
            Net* victim_net = *std::min_element(competing_nets.begin(), competing_nets.end(), 
                [](Net* a, Net* b) { return getNetBBoxArea(a) < getNetBBoxArea(b); });
            nets_to_reroute.insert(victim_net);
        }
        
        // C.2: (新增) 基于路径成本，额外选择成本最高的线网进行拆除
        cout << "  [PHASE] Identifying high-cost nets..." << endl;
        vector<pair<double, Net*>> net_costs;
        for(auto* net : nets) {
            if (nets_to_reroute.find(net) == nets_to_reroute.end()) {
               // 【已修正】先将std::set转换为std::vector，再调用calculatePathCost
               const auto& path_set = net->getPath();
               vector<RRNode*> path_vec(path_set.begin(), path_set.end());
               net_costs.push_back({calculatePathCost(path_vec), net});
            }
        }
        std::sort(net_costs.rbegin(), net_costs.rend()); // 按成本降序排序

        int num_high_cost_nets_to_rip = static_cast<int>(nets.size() * HIGH_COST_NET_PERCENTAGE);
        // 【已修正】将循环变量i的类型从int改为size_t，以避免有符号/无符号比较的警告
        for(size_t i = 0; i < (size_t)num_high_cost_nets_to_rip && i < net_costs.size(); ++i) {
            nets_to_reroute.insert(net_costs[i].second);
        }

        // D. 拆除所有被选中的线网
        for (Net* net : nets_to_reroute) {
            ripUpNet(*net);
        }
        cout << "  [INFO] Ripped up " << nets_to_reroute.size() << " nets for re-routing." << endl;

        // E. 应用“最困难优先”策略，对重布线网进行排序
        cout << "  [PHASE] Rerouting ripped up nets (hardest first)..." << endl;
        vector<Net*> reroute_vec(nets_to_reroute.begin(), nets_to_reroute.end());
        
        // (新增) 不再随机打乱，而是按难度（BBox）降序排序
        std::sort(reroute_vec.begin(), reroute_vec.end(), [](Net* a, Net* b){
            return getNetBBoxArea(a) > getNetBBoxArea(b);
        });

        for (auto* net : reroute_vec) {
            this->current_net = net;
            if (!routeNet(fpga, *net)) {
                 cout << "      [WARNING] Re-routing failed for net " << net->getIdx() << " in iter " << iter << endl;
            }
        }
    }

    cout << "\n❌ Routing failed to converge after max iterations." << endl;
    finalizeAllRouting(design);
}


// =================================================================
// 以下函数保持不变，因为它们的实现已经是健壮和正确的
// =================================================================

bool MyRouter::routeNet(FPGA &fpga, Net &net) {
    auto &sinks = net.getSinks();
    if (sinks.empty()) return true; 
    
    vector<RRNode*> connected(net.getPath().begin(), net.getPath().end());
    set<RRNode*> sinksToConnect = sinks;

    while(!sinksToConnect.empty()){
        RRNode* bestSinkNode = nullptr;
        vector<RRNode*> bestPath;
        double bestCost = std::numeric_limits<double>::max();

        for (auto* startNode : connected) {
            for (auto* sinkNode : sinksToConnect) {
                vector<RRNode*> path = mazeRoute(fpga, *startNode, *sinkNode, net);
                if (!path.empty()) {
                    double cost = calculatePathCost(path);
                    if (cost < bestCost) {
                        bestCost = cost;
                        bestPath = path;
                        bestSinkNode = sinkNode;
                    }
                }
            }
        }
        
        if (bestPath.empty()) {
            cout << "      [FAILED] Net " << net.getIdx() << ": Could not find any path to " << sinksToConnect.size() << " remaining sinks." << endl;
            return false;
        }
        
        applyPath(net, bestPath);
        sinksToConnect.erase(bestSinkNode);

        for (auto* node : bestPath) {
             if (std::find(connected.begin(), connected.end(), node) == connected.end()) {
                connected.push_back(node);
            }
        }
    }
    
    return true;
}

vector<RRNode*> MyRouter::mazeRoute(FPGA &fpga, RRNode &source, RRNode &sink, Net &net) {
    map<RRNode*, double> distance;
    map<RRNode*, RRNode*> predecessor;
    priority_queue<pair<double, RRNode*>, vector<pair<double, RRNode*>>, greater<pair<double, RRNode*>>> pq;
    set<RRNode*> visited;
    
    distance[&source] = 0.0;
    pq.push({0.0 + getManhattanDistance(source, sink), &source});
    
    while (!pq.empty()) {
        auto [f_cost_priority, current] = pq.top(); 
        pq.pop();
        
        if (visited.count(current)) continue;
        visited.insert(current);
        
        if (current == &sink) return constructPath(predecessor, &source, &sink);
        
        double g_cost_current = distance[current];

        for (auto* neighbor : current->getConnections()) {
            if(visited.count(neighbor)) continue;

            double g_cost_neighbor = g_cost_current + getNodeCost(neighbor);
            
            if (!distance.count(neighbor) || g_cost_neighbor < distance[neighbor]) {
                predecessor[neighbor] = current;
                distance[neighbor] = g_cost_neighbor;
                double h_cost_neighbor = getManhattanDistance(*neighbor, sink);
                pq.push({g_cost_neighbor + h_cost_neighbor, neighbor});
            }
        }
    }
    
    return {};
}

double MyRouter::getNodeCost(RRNode* node) {
    if (!node) return std::numeric_limits<double>::max();
    
    double cost = 1.0; 

    if (history_cost.count(node)) {
        cost *= history_cost[node]; 
    }

    if (occupancy.count(node) && occupancy[node] > 0 && node->getNet() != this->current_net) {
        cost *= (1.0 + occupancy[node] * P_FAC);
    }

    return cost;
}

vector<RRNode*> MyRouter::constructPath(map<RRNode*, RRNode*> &predecessor, RRNode* source, RRNode* sink) {
    vector<RRNode*> path;
    RRNode* current = sink;
    while (current != source) {
        path.push_back(current);
        if (predecessor.find(current) == predecessor.end()) return {};
        current = predecessor[current];
    }
    reverse(path.begin(), path.end());
    return path;
}

double MyRouter::getManhattanDistance(RRNode &node1, RRNode &node2) {
    return abs(node1.getX() - node2.getX()) + abs(node1.getY() - node2.getY());
}

double MyRouter::calculatePathCost(const vector<RRNode*>& path) {
    double total_cost = 0.0;
    for (auto* node : path) {
        total_cost += getNodeCost(node);
    }
    return total_cost;
}

void MyRouter::applyPath(Net &net, const vector<RRNode*> &path) {
    for (auto* node : path) {
        node->setNet(net);
        net.addRRToPath(*node);
        occupancy[node]++;
    }
}

void MyRouter::finalizeAllRouting(Design &design) {
    for (int i = 0; i < design.getNumNets(); i++) {
        Net &net = design.getNet(i);
        net.finalizeRouting();
    }
}

#include <iostream>
#include <queue>
#include <map>
#include <set>
#include <algorithm>
#include "FPGA.h"
#include "FpgaTile.h"
#include "RRNode.h"
#include "Net.h"

using namespace std;

bool canUseNode(RRNode &node) {
    return !node.isUsed();
}

vector<RRNode*> simpleRoute(RRNode &source, RRNode &sink) {
    map<RRNode*, RRNode*> predecessor;
    queue<RRNode*> q;
    set<RRNode*> visited;
    
    q.push(&source);
    visited.insert(&source);
    
    while (!q.empty()) {
        RRNode* current = q.front();
        q.pop();
        
        if (current == &sink) {
            // 构建路径
            vector<RRNode*> path;
            RRNode* node = &sink;
            while (node != &source) {
                path.push_back(node);
                node = predecessor[node];
            }
            reverse(path.begin(), path.end());
            return path;
        }
        
        for (auto* neighbor : current->getConnections()) {
            if (visited.find(neighbor) == visited.end() && canUseNode(*neighbor)) {
                visited.insert(neighbor);
                predecessor[neighbor] = current;
                q.push(neighbor);
            }
        }
    }
    
    return {}; // 无路径
}

int main() {
    FPGA fpga(5, 12);
    
    // 测试第一个net: (2,1).4 -> (1,1).2
    RRNode &source = fpga.getTile(2, 1).getLogicPin(4);
    RRNode &sink = fpga.getTile(1, 1).getLogicPin(2);
    
    cout << "Testing route from " << source << " to " << sink << endl;
    cout << "Source connections: " << source.getConnections().size() << endl;
    cout << "Sink connections: " << sink.getConnections().size() << endl;
    
    // 检查源和目标的连接
    cout << "\nSource connections:" << endl;
    for (int i = 0; i < min(5, (int)source.getConnections().size()); i++) {
        auto* conn = source.getConnections()[i];
        cout << "  " << *conn << endl;
    }
    
    cout << "\nSink connections:" << endl;
    for (int i = 0; i < min(5, (int)sink.getConnections().size()); i++) {
        auto* conn = sink.getConnections()[i];
        cout << "  " << *conn << endl;
    }
    
    vector<RRNode*> path = simpleRoute(source, sink);
    
    if (path.empty()) {
        cout << "\nNo path found!" << endl;
    } else {
        cout << "\nPath found with " << path.size() << " nodes:" << endl;
        for (auto* node : path) {
            cout << "  " << *node << endl;
        }
    }
    
    return 0;
} 
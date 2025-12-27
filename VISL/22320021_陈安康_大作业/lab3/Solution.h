#ifndef SOLUTION_H
#define SOLUTION_H

#include <vector>
#include <map>

using namespace std;

class FPGA;
class Design;
class Net;
class RRNode;

class Router {
public:
    Router(){}
    virtual ~Router(){}
    virtual void routeDesign(FPGA &fpga, Design &design) = 0;
};

class MyRouter:public Router{
public:
    MyRouter(){}
    virtual ~MyRouter(){}
    void routeDesign(FPGA &fpga, Design &design);
    
private:
    // 核心布线方法
    bool routeNet(FPGA &fpga, Net &net);
    vector<RRNode*> mazeRoute(FPGA &fpga, RRNode &source, RRNode &sink, Net &net);
    vector<RRNode*> constructPath(map<RRNode*, RRNode*> &predecessor, RRNode* source, RRNode* sink);
    
    // 辅助方法
    bool canUseNode(RRNode &node, Net &net);
    double getNodeCost(RRNode* node);
    double getManhattanDistance(RRNode &node1, RRNode &node2);
    double calculatePathCost(const vector<RRNode*> &path);
    
    // 路径管理
    void applyPath(Net &net, const vector<RRNode*> &path);


    void ripUpNet(Net& net);


    void clearNetRouting(Net &net);
    
    // 高级策略
    void finalizeAllRouting(Design &design);

    // 新增的数据成员
    map<RRNode*, double> history_cost; // 存储每个节点的历史拥塞成本
    map<RRNode*, int> occupancy;       // 存储每个节点当前被多少个net占用

    // 成本因子（用于调优，可以先用固定的值）
    const double P_FAC = 0.5; // 当前拥塞的惩罚因子 (Present penalty factor)
    const double H_FAC = 2.0; // 历史拥塞的惩罚因子 (History penalty factor)

    Net* current_net; // 方便在成本函数中知道当前正在为哪个net布线
};

#endif
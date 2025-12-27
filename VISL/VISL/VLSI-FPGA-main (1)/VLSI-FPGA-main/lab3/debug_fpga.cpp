#include <iostream>
#include "FPGA.h"
#include "FpgaTile.h"
#include "RRNode.h"

using namespace std;

int main() {
    FPGA fpga(5, 12); // 模拟tiny数据集的设置
    
    cout << "Checking FPGA structure:" << endl;
    cout << "Grid size: " << fpga.getN() << "x" << fpga.getN() << endl;
    cout << "Channel width: " << fpga.getW() << endl;
    
    // 检查关键位置的逻辑块
    vector<pair<int,int>> testPositions = {{2,1}, {1,1}, {3,1}, {1,3}, {3,0}, {2,0}, {1,2}};
    
    for (auto pos : testPositions) {
        int x = pos.first, y = pos.second;
        cout << "\nPosition (" << x << "," << y << "):" << endl;
        
        FpgaTile &tile = fpga.getTile(x, y);
        cout << "  Has neighbors: ";
        cout << "left=" << (tile.getLeft() != nullptr);
        cout << " right=" << (tile.getRight() != nullptr);  
        cout << " up=" << (tile.getUp() != nullptr);
        cout << " down=" << (tile.getDown() != nullptr) << endl;
        
        try {
            RRNode &pin1 = tile.getLogicPin(1);
            cout << "  Logic pin 1: " << pin1 << endl;
            cout << "  Pin 1 connections: " << pin1.getConnections().size() << endl;
        } catch (...) {
            cout << "  No logic pins available" << endl;
        }
    }
    
    return 0;
} 
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <cmath>
#include <random>
#include <algorithm>
#include <chrono>
#include <vector>

#include "Solution.h"
#include "Object.h"

// 模拟退火算法的参数
class SimulatedAnnealing {
private:
    // 随机数生成器
    std::mt19937 rng;
    // 温度参数
    double initial_temperature;
    double final_temperature;
    double cooling_rate;
    // 当前温度
    double current_temperature;
    // 当前线网长度
    int current_wirelength;
    // 最佳线网长度
    int best_wirelength;
    // 最佳布局方案
    std::map<int, std::pair<int, int>> best_placement;
    std::map<int, std::pair<int, int>> tmp_placement;
    // 移动和交换的概率
    double move_probability;
    double swap_probability;
    // 内循环迭代次数
    int inner_iterations;
    // 缓存可移动的实例列表，避免重复计算
    std::vector<Instance*> movable_instances;

public:
    SimulatedAnnealing() {
        // 使用当前时间作为随机数种子
        unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
        rng = std::mt19937(seed);
        
        // 设置模拟退火参数
        initial_temperature = 1000.0;
        final_temperature = 0.1;
        cooling_rate = 0.95;
        current_temperature = initial_temperature;
        
        // 移动和交换的概率
        move_probability = 0.7;
        swap_probability = 0.3;
        
        // 内循环迭代次数，与问题规模相关
        inner_iterations = 100 * glb_inst_map.size();
        
        // 初始化可移动实例列表
        initMovableInstances();
        
        // 初始化线网长度
        current_wirelength = reportWireLength();
        best_wirelength = current_wirelength;
    }
    
    // 初始化可移动实例列表
    void initMovableInstances() {
        movable_instances.clear();
        for (auto& inst_pair : glb_inst_map) {
            Instance* inst = inst_pair.second;
            if (!inst->isFixed()) {
                movable_instances.push_back(inst);
            }
        }
    }
    
    // 保存当前最佳布局
    void saveBestPlacement() {
        best_placement.clear();
        for (auto& inst_pair : glb_inst_map) {
            Instance* inst = inst_pair.second;
            if (!inst->isFixed()) {
                best_placement[inst->getInstId()] = inst->getPosition();
            }
        }
    }

    // 保存当前布局
    void saveTmpPlacement() {
        tmp_placement.clear();
        for (auto& inst_pair : glb_inst_map) {
            Instance* inst = inst_pair.second;
            if (!inst->isFixed()) {
                tmp_placement[inst->getInstId()] = inst->getPosition();
            }
        }
    }
    
    // 恢复最佳布局
    void restoreBestPlacement() {
        for (auto& placement : best_placement) {
            int inst_id = placement.first;
            int x = placement.second.first;
            int y = placement.second.second;
            
            Instance* inst = glb_inst_map[inst_id];
            std::pair<int, int> current_pos = inst->getPosition();
            
            // 如果位置不同，则移动
            if (current_pos.first != x || current_pos.second != y) {
                // 从当前位置删除
                Block* current_block = glb_fpga.getBlock(current_pos.first, current_pos.second);
                if (current_block) {
                    glb_fpga.deleteInst(current_pos.first, current_pos.second, inst);
                }
                
                // 检查目标位置是否已有实例
                Block* target_block = glb_fpga.getBlock(x, y);
                if (target_block && target_block->getInstsCount() > 0) {
                    // 如果目标位置已有实例，先将其移出
                    Instance* existing_inst = target_block->getInsts()[0];
                    glb_fpga.deleteInst(x, y, existing_inst);
                    
                    // 将当前实例放入目标位置
                    glb_fpga.addInst(x, y, inst);
                    
                    // 将原位置的实例放回原位置
                    glb_fpga.addInst(current_pos.first, current_pos.second, existing_inst);
                } else {
                    // 如果目标位置为空，直接添加
                    glb_fpga.addInst(x, y, inst);
                }
            }
        }
    }

     // 恢复当前布局
    void restoreTmpPlacement() {
        for (auto& placement : tmp_placement) {
            int inst_id = placement.first;
            int x = placement.second.first;
            int y = placement.second.second;
            
            Instance* inst = glb_inst_map[inst_id];
            std::pair<int, int> current_pos = inst->getPosition();
            
            // 如果位置不同，则移动
            if (current_pos.first != x || current_pos.second != y) {
                // 从当前位置删除
                Block* current_block = glb_fpga.getBlock(current_pos.first, current_pos.second);
                if (current_block) {
                    glb_fpga.deleteInst(current_pos.first, current_pos.second, inst);
                }
                
                // 检查目标位置是否已有实例
                Block* target_block = glb_fpga.getBlock(x, y);
                if (target_block && target_block->getInstsCount() > 0) {
                    // 如果目标位置已有实例，先将其移出
                    Instance* existing_inst = target_block->getInsts()[0];
                    glb_fpga.deleteInst(x, y, existing_inst);
                    
                    // 将当前实例放入目标位置
                    glb_fpga.addInst(x, y, inst);
                    
                    // 将原位置的实例放回原位置
                    glb_fpga.addInst(current_pos.first, current_pos.second, existing_inst);
                } else {
                    // 如果目标位置为空，直接添加
                    glb_fpga.addInst(x, y, inst);
                }
            }
        }
    }
    
    // 随机选择一个可移动的Instance
    Instance* selectRandomInstance() {
        if (movable_instances.empty()) {
            return nullptr;
        }
        
        std::uniform_int_distribution<int> dist(0, movable_instances.size() - 1);
        return movable_instances[dist(rng)];
    }
    
    // 随机选择一个空闲的位置
    std::pair<int, int> selectRandomEmptyPosition() {
        int fpga_size_x = glb_fpga.getSizeX();
        int fpga_size_y = glb_fpga.getSizeY();
        
        std::vector<std::pair<int, int>> empty_positions;
        
        for (int x = 0; x < fpga_size_x; x++) {
            for (int y = 0; y < fpga_size_y; y++) {
                Block* block = glb_fpga.getBlock(x, y);
                if (block && block->getInstsCount() == 0) {
                    empty_positions.push_back(std::make_pair(x, y));
                }
            }
        }
        
        if (empty_positions.empty()) {
            // 如果没有空闲位置，返回一个无效位置
            return std::make_pair(-1, -1);
        }
        
        std::uniform_int_distribution<int> dist(0, empty_positions.size() - 1);
        return empty_positions[dist(rng)];
    }
    
    // 移动操作：将一个Instance移动到一个空闲位置
    bool moveOperation() {
        Instance* inst = selectRandomInstance();
        if (!inst) {
            return false;
        }
        
        std::pair<int, int> current_pos = inst->getPosition();
        std::pair<int, int> new_pos = selectRandomEmptyPosition();
        
        // 如果没有找到空闲位置或者位置无效
        if (new_pos.first == -1 || new_pos.second == -1) {
            return false;
        }
        
        // 从当前位置删除
        Block* current_block = glb_fpga.getBlock(current_pos.first, current_pos.second);
        if (!current_block) {
            return false;
        }
        
        if (!glb_fpga.deleteInst(current_pos.first, current_pos.second, inst)) {
            return false;
        }
        
        // 添加到新位置
        if (!glb_fpga.addInst(new_pos.first, new_pos.second, inst)) {
            // 如果添加失败，恢复到原位置
            glb_fpga.addInst(current_pos.first, current_pos.second, inst);
            return false;
        }
        
        return true;
    }
    
    // 交换操作：交换两个Instance的位置
    bool swapOperation() {
        Instance* inst1 = selectRandomInstance();
        Instance* inst2 = selectRandomInstance();
        
        if (!inst1 || !inst2 || inst1 == inst2) {
            return false;
        }
        
        std::pair<int, int> pos1 = inst1->getPosition();
        std::pair<int, int> pos2 = inst2->getPosition();
        
        // 从当前位置删除
        if (!glb_fpga.deleteInst(pos1.first, pos1.second, inst1)) {
            return false;
        }
        
        if (!glb_fpga.deleteInst(pos2.first, pos2.second, inst2)) {
            // 恢复inst1
            glb_fpga.addInst(pos1.first, pos1.second, inst1);
            return false;
        }
        
        // 添加到新位置
        if (!glb_fpga.addInst(pos2.first, pos2.second, inst1)) {
            // 恢复原位置
            glb_fpga.addInst(pos1.first, pos1.second, inst1);
            glb_fpga.addInst(pos2.first, pos2.second, inst2);
            return false;
        }
        
        if (!glb_fpga.addInst(pos1.first, pos1.second, inst2)) {
            // 恢复原位置
            glb_fpga.deleteInst(pos2.first, pos2.second, inst1);
            glb_fpga.addInst(pos1.first, pos1.second, inst1);
            glb_fpga.addInst(pos2.first, pos2.second, inst2);
            return false;
        }
        
        return true;
    }
    
    // 计算接受概率
    double acceptanceProbability(int new_wirelength, int current_wirelength, double temperature) {
        if (new_wirelength < current_wirelength) {
            return 1.0; // 如果新解更好，总是接受
        }
        
        // 如果新解更差，根据温度和差值计算接受概率
        return exp((current_wirelength - new_wirelength) / temperature);
    }
    
    // 执行模拟退火算法
    void run() {
        // 保存初始布局作为最佳布局
        saveBestPlacement();
        
        // 外循环：降温过程
        while (current_temperature > final_temperature) {
            // 内循环：在当前温度下进行多次扰动
            for (int i = 0; i < inner_iterations; i++) {

                // 保存当前布局
                // saveTmpPlacement();
                bool operation_success = false;
                
                // 随机选择移动或交换操作
                std::uniform_real_distribution<double> dist(0.0, 1.0);
                double random_value = dist(rng);
                
                if (random_value < move_probability) {
                    operation_success = moveOperation();
                } else {
                    operation_success = swapOperation();
                }
                
                if (operation_success) {
                    // 计算新的线网长度
                    int new_wirelength = reportWireLength();
                    
                    // 计算接受概率
                    double p = acceptanceProbability(new_wirelength, current_wirelength, current_temperature);
                    
                    // 决定是否接受新解
                    random_value = dist(rng);
                    if (random_value < p) {
                        // 接受新解
                        current_wirelength = new_wirelength;
                        
                        // 如果是最佳解，保存它
                        if (new_wirelength < best_wirelength) {
                            best_wirelength = new_wirelength;
                            saveBestPlacement();
                        }
                    } else {
                        // 不接受新解，恢复上一个布局
                        // 这里需要撤销之前的操作，但由于我们没有保存具体的操作，
                        // 所以直接恢复最佳布局（这是一个简化处理，实际上应该只恢复上一步）
                        // restoreTmpPlacement();
                        restoreBestPlacement();
                        current_wirelength = best_wirelength;
                    }
                }
            }
            
            // 降温
            current_temperature *= cooling_rate;
            std::cout << "Temperature: " << current_temperature << ", Best Wirelength: " << best_wirelength << std::endl;
        }
        
        // 最终恢复最佳布局
        restoreBestPlacement();
    }
};

int readBenchMarkFile(std::string i_file_name){

    std::fstream f;
    f.open(i_file_name, std::ios::in);

    if (!f.is_open()){
        std::printf("file %s open failed", i_file_name.c_str());
        return -1;
    }

    std::string line;
    while (std::getline(f, line)){
        // 换行符/r会影响这个判断
        if (line.empty() || line.size() == 1)
            break;
        
        std::istringstream iss(line);
        std::string temp;
        std::vector<std::string> row;
        while (iss >> temp){
            row.push_back(temp);
        }
        if (row.size() == 2){
            int l_size_x = std::stoi(row[0]);
            int l_size_y = std::stoi(row[1]);
            glb_fpga.setSize(l_size_x, l_size_y);
            glb_fpga.initialize();
        }else if (row.size() == 3){
            int l_inst_id, l_x, l_y;
            l_inst_id = std::stoi(row[0]);
            l_x = std::stoi(row[1]);
            l_y = std::stoi(row[2]);
            Instance* inst = new Instance(l_x, l_y, l_inst_id, true);
            glb_inst_map[l_inst_id] = inst;
            glb_fpga.addInst(l_x, l_y, inst);
        }else{
            std::printf("something wrong when try to parser: %s", line.c_str());
            return -1;
        }
    }
    while (std::getline(f, line)){
        if (line.empty() || line.size() == 1)
            continue;
        
        std::istringstream iss(line);
        std::string temp;
        std::vector<std::string> row;
        while (iss >> temp){
            row.push_back(temp);
        }
        int l_inst_id, l_net_id;
        l_inst_id = std::stoi(row[0]);
        Instance* l_inst_point = nullptr;
        if (glb_inst_map.find(l_inst_id) == glb_inst_map.end()){
            l_inst_point = new Instance();
            l_inst_point->setInstId(l_inst_id);
            glb_inst_map[l_inst_id] = l_inst_point;
        }else{
            l_inst_point = glb_inst_map[l_inst_id];
        }
        
        for (size_t i = 1; i < row.size(); i++){
            l_net_id = std::stoi(row[i]);
            Net* lo_net_point = nullptr;
            if (glb_net_map.find(l_net_id) == glb_net_map.end()){
                lo_net_point = new Net;
                lo_net_point->setNetId(l_net_id);
                glb_net_map[l_net_id] = lo_net_point;
            }else{
                lo_net_point = glb_net_map[l_net_id];
            }
            l_inst_point->addNet(lo_net_point);
            lo_net_point->addInst(l_inst_point);
        }
    }
    f.close();
    return 0;
}

int outputSolution(std::string i_file_name){
    std::fstream f;
    f.open(i_file_name, std::ios::out);
    if (!f.is_open()){
        std::printf("unable to open file %s\n", i_file_name.c_str());
        return -1;
    }
    for (size_t i = 0; i < glb_inst_map.size(); i++){
        Instance* lo_inst_p = glb_inst_map[i];
        std::pair<int, int> lo_pos = lo_inst_p->getPosition();
        f << std::setw(5) << std::left << lo_inst_p->getInstId() \
            << std::setw(5) << std::left << lo_pos.first \
            << std::setw(5) << std::left << lo_pos.second << std::endl;
    }
    f.close();
    return 0;
}

int reportWireLength(){
    int l_wirelength = 0;
    for (auto lo_net : glb_net_map){
        l_wirelength += lo_net.second->evalHPWL();
    }
    std::cout << "Wirelength: " << std::setw(5) << std::right << l_wirelength << std::endl;
    return l_wirelength;
}

int reportValid(){
    // 检查布局是否合法
    // 1. 检查每个inst的布局位置是否和Block包含的inst一致
    // 2. 检查每个Block是否存在inst重复出现的情况

    int l_error_count = 0;
    // 先检查每个inst的布局位置是否和Block包含的inst一致
    for (auto lo_inst : glb_inst_map){
        Instance* lo_inst_p = lo_inst.second;
        std::pair<int, int> lo_inst_pos = lo_inst_p->getPosition();
        Block* lo_block_p = glb_fpga.getBlock(lo_inst_pos.first, lo_inst_pos.second);
        if (lo_block_p == nullptr){
            std::printf("[ERROR] inst %d is not placed (%d, %d)\n", lo_inst_p->getInstId(), lo_inst_pos.first, lo_inst_pos.second);
            l_error_count++;
            continue;
        }
        if (lo_block_p->getInsts()[0] != lo_inst_p){
            std::printf("[ERROR] inst %d is not in block (%d, %d)\n", lo_inst_p->getInstId(), lo_inst_pos.first, lo_inst_pos.second);
            l_error_count++;
        }
    }
    // 再从block一侧检查是否存在inst重复出现的情况
    std::set<Instance*> lo_inst_attend;
    for (int i = 0; i < glb_fpga.getSizeX(); i++){
        for (int j = 0; j < glb_fpga.getSizeY(); j++){
            Block* lo_block_p = glb_fpga.getBlock(i, j);
            if (lo_block_p == nullptr)
                continue;
            for (auto lo_inst : lo_block_p->getInsts()){
                if (lo_inst_attend.find(lo_inst) != lo_inst_attend.end()){
                    std::printf("[ERROR] inst %d is repeated in block (%d, %d)\n", lo_inst->getInstId(), i, j);
                    l_error_count++; 
                } 
                lo_inst_attend.insert(lo_inst);
            }
        } 
    }
    return l_error_count;
}

// 初始化布局函数 - 使用Timberwolf贪心策略
void initializePlacement() {
    int fpga_size_x = glb_fpga.getSizeX();
    int fpga_size_y = glb_fpga.getSizeY();
    
    // 收集所有非固定的Instance
    std::vector<Instance*> unplaced_instances;
    std::set<Instance*> placed_instances;
    
    for (auto& inst_pair : glb_inst_map) {
        Instance* inst = inst_pair.second;
        if (!inst->isFixed() && inst->getPosition().first == -1 && inst->getPosition().second == -1) {
            unplaced_instances.push_back(inst);
        } else if (inst->getPosition().first != -1 && inst->getPosition().second != -1) {
            placed_instances.insert(inst);
        }
    }
    
    // 如果没有已放置的实例，随机选择一个作为起点
    if (placed_instances.empty() && !unplaced_instances.empty()) {
        std::random_device rd;
        std::mt19937 rng(rd());
        std::uniform_int_distribution<int> dist(0, unplaced_instances.size() - 1);
        
        int idx = dist(rng);
        Instance* first_inst = unplaced_instances[idx];
        
        // 放置在FPGA中心位置附近
        int center_x = fpga_size_x / 2;
        int center_y = fpga_size_y / 2;
        
        // 查找中心附近的空位
        bool placed = false;
        for (int radius = 0; radius < std::max(fpga_size_x, fpga_size_y) && !placed; radius++) {
            for (int dx = -radius; dx <= radius && !placed; dx++) {
                for (int dy = -radius; dy <= radius && !placed; dy++) {
                    if (abs(dx) + abs(dy) == radius) { // 曼哈顿距离等于radius
                        int x = center_x + dx;
                        int y = center_y + dy;
                        
                        if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                            Block* block = glb_fpga.getBlock(x, y);
                            if (block && block->getInstsCount() == 0) {
                                glb_fpga.addInst(x, y, first_inst);
                                placed = true;
                                placed_instances.insert(first_inst);
                                unplaced_instances.erase(unplaced_instances.begin() + idx);
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Timberwolf贪心策略：依次选择与已放置模块连接最多的未放置模块
    while (!unplaced_instances.empty()) {
        // 找出与已放置模块连接最多的未放置模块
        int max_connections = -1;
        int best_idx = -1;
        
        for (size_t i = 0; i < unplaced_instances.size(); i++) {
            Instance* inst = unplaced_instances[i];
            int connections = 0;
            
            // 计算与已放置模块的连接数
            for (Net* net : inst->getNets()) {
                for (Instance* connected_inst : net->getInsts()) {
                    if (placed_instances.find(connected_inst) != placed_instances.end()) {
                        connections++;
                    }
                }
            }
            
            if (connections > max_connections) {
                max_connections = connections;
                best_idx = i;
            }
        }
        
        // 如果没有找到连接的模块，随机选择一个
        if (best_idx == -1) {
            std::random_device rd;
            std::mt19937 rng(rd());
            std::uniform_int_distribution<int> dist(0, unplaced_instances.size() - 1);
            best_idx = dist(rng);
        }
        
        Instance* inst_to_place = unplaced_instances[best_idx];
        
        // 为选中的模块找到最优位置（线网长度最小的位置）
        int best_x = -1;
        int best_y = -1;
        int min_wirelength = MAX_INT;
        
        for (int x = 0; x < fpga_size_x; x++) {
            for (int y = 0; y < fpga_size_y; y++) {
                Block* block = glb_fpga.getBlock(x, y);
                if (block && block->getInstsCount() == 0) {
                    // 临时放置并计算线网长度
                    inst_to_place->setPosition(x, y);
                    
                    // 计算与该模块相关的线网长度
                    int local_wirelength = 0;
                    for (Net* net : inst_to_place->getNets()) {
                        local_wirelength += net->evalHPWL();
                    }
                    
                    if (local_wirelength < min_wirelength) {
                        min_wirelength = local_wirelength;
                        best_x = x;
                        best_y = y;
                    }
                    
                    // 重置位置
                    inst_to_place->setPosition(-1, -1);
                }
            }
        }
        
        // 放置模块到最优位置
        if (best_x != -1 && best_y != -1) {
            glb_fpga.addInst(best_x, best_y, inst_to_place);
            placed_instances.insert(inst_to_place);
        } else {
            // 如果找不到空位，尝试顺序查找
            bool placed = false;
            for (int x = 0; x < fpga_size_x && !placed; x++) {
                for (int y = 0; y < fpga_size_y && !placed; y++) {
                    Block* block = glb_fpga.getBlock(x, y);
                    if (block && block->getInstsCount() == 0) {
                        glb_fpga.addInst(x, y, inst_to_place);
                        placed = true;
                    }
                }
            }
            
            if (!placed) {
                std::cout << "[WARNING] Cannot place instance " << inst_to_place->getInstId() << ", FPGA may be full." << std::endl;
            } else {
                placed_instances.insert(inst_to_place);
            }
        }
        
        // 从未放置列表中移除
        unplaced_instances.erase(unplaced_instances.begin() + best_idx);
    }
    
    std::cout << "Timberwolf greedy initialization completed. Placed " << placed_instances.size() << " instances." << std::endl;
}

// 主布局函数
void runPlacement() {
    std::cout << "Starting placement with Simulated Annealing..." << std::endl;
    
    // 初始化布局
    initializePlacement();
    
    // 报告初始线网长度
    std::cout << "Initial ";
    int initial_wirelength = reportWireLength();
    
    // 执行模拟退火算法
    SimulatedAnnealing sa;
    sa.run();
    
    // 报告最终线网长度
    std::cout << "Final ";
    int final_wirelength = reportWireLength();
    std::cout << "Initial Wirelength:   " << initial_wirelength << std::endl;;
    std::cout << "Placement completed. Improvement: " 
              << (initial_wirelength - final_wirelength) * 100.0 / initial_wirelength 
              << "% reduction in wirelength." << std::endl;
}
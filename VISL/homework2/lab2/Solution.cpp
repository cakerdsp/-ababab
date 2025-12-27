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

// 模拟退火算法的参数 - 参考TimberWolf算法优化
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
    // 全局最佳线网长度（多起点搜索）
    int global_best_wirelength;
    // 最佳布局方案
    std::map<int, std::pair<int, int>> best_placement;
    // 全局最佳布局方案（多起点搜索）
    std::map<int, std::pair<int, int>> global_best_placement;
    // 移动和交换的概率
    double move_probability;
    double swap_probability;
    // 内循环迭代次数
    int inner_iterations;
    // 缓存可移动的实例列表，避免重复计算
    std::vector<Instance*> movable_instances;
    // TimberWolf优化参数
    double move_range_factor;      // 移动范围因子，控制扰动范围
    double accept_rate;            // 当前接受率
    double target_accept_rate;     // 目标接受率
    int accepted_moves;            // 接受的移动次数
    int total_moves;               // 总移动次数
    int no_improvement_count;      // 无改进计数
    int max_no_improvement;        // 最大无改进次数
    bool use_adaptive_cooling;     // 是否使用自适应降温
    // 连接度缓存
    std::map<Instance*, int> connectivity_cache; // 缓存每个实例的连接度
    
    // 增强型优化参数
    bool use_reheating;            // 是否使用重加热机制
    int reheat_interval;           // 重加热间隔
    double reheat_factor;          // 重加热因子
    int multi_start_count;         // 多起点搜索次数
    bool use_tabu_search;          // 是否使用禁忌搜索
    int tabu_tenure;               // 禁忌期限
    std::map<std::pair<int, int>, int> tabu_list; // 禁忌列表，记录移动的禁忌期限
    
    // 关键路径和拥塞因素
    std::map<Net*, double> net_criticality;  // 网络关键性
    std::map<std::pair<int, int>, int> congestion_map; // 拥塞图，记录每个位置的拥塞程度
    double congestion_weight;      // 拥塞权重
    double timing_weight;          // 时序权重

public:
    SimulatedAnnealing() {
        // 使用当前时间作为随机数种子
        unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
        rng = std::mt19937(seed);
        
        // 设置模拟退火参数 - 增强型优化参数
        initial_temperature = 1500.0;  // 提高初始温度，增加搜索空间
        final_temperature = 0.1;       // 降低最终温度，提高最终解的质量
        cooling_rate = 0.95;           // 减缓降温速度，更充分地搜索解空间
        current_temperature = initial_temperature;
        
        // 移动和交换的概率 - 增加交换操作的比例以提高布局质量
        move_probability = 0.5;
        swap_probability = 0.5;
        
        // 内循环迭代次数，与问题规模相关
        // 增加迭代次数，确保充分搜索
        inner_iterations = 100 * glb_inst_map.size();
        
        // TimberWolf优化参数初始化
        move_range_factor = 1.0;       // 初始移动范围因子
        accept_rate = 0.0;             // 初始接受率
        target_accept_rate = 0.44;     // TimberWolf推荐的目标接受率
        accepted_moves = 0;            // 接受的移动次数
        total_moves = 0;               // 总移动次数
        no_improvement_count = 0;      // 无改进计数
        max_no_improvement = 10;       // 增加最大无改进次数，更耐心地等待改进
        use_adaptive_cooling = true;   // 默认使用自适应降温
        
        // 增强型优化参数初始化
        use_reheating = true;          // 启用重加热机制
        reheat_interval = 5;           // 每5次无改进后重加热
        reheat_factor = 1.5;           // 重加热因子
        multi_start_count = 3;         // 多起点搜索次数
        use_tabu_search = true;        // 启用禁忌搜索
        tabu_tenure = 10;              // 禁忌期限
        
        // 关键路径和拥塞因素初始化
        congestion_weight = 0.3;       // 拥塞权重
        timing_weight = 0.7;           // 时序权重
        
        // 初始化可移动实例列表
        initMovableInstances();
        
        // 初始化连接度缓存和关键性评估
        initConnectivityAndCriticality();
        
        // 初始化拥塞图
        initCongestionMap();
        
        // 初始化线网长度
        current_wirelength = reportWireLength();
        best_wirelength = current_wirelength;
        global_best_wirelength = current_wirelength;
    }
    
    // 增强型连接度和关键性初始化 - 考虑网络权重、关键性和时序信息
    void initConnectivityAndCriticality() {
        connectivity_cache.clear();
        net_criticality.clear();
        
        // 计算每个网络的关键性 - 考虑线长、扇出数和位置
        for (auto& net_pair : glb_net_map) {
            Net* net = net_pair.second;
            int hpwl = net->evalHPWL();
            int inst_count = net->getInsts().size();
            
            // 基础关键性：线长与实例数的比值
            double base_criticality = (inst_count > 1) ? static_cast<double>(hpwl) / inst_count : 0;
            
            // 增强关键性评估：考虑扇出数的影响
            // 扇出数越大的网络越关键
            double fanout_factor = 1.0 + 0.2 * log(std::max(1, inst_count));
            
            // 计算网络的最大曼哈顿距离，作为时序关键性的指标
            double max_manhattan_dist = 0.0;
            if (inst_count > 1) {
                std::vector<Instance*> net_insts(net->getInsts().begin(), net->getInsts().end());
                for (size_t i = 0; i < net_insts.size(); i++) {
                    for (size_t j = i + 1; j < net_insts.size(); j++) {
                        std::pair<int, int> pos_i = net_insts[i]->getPosition();
                        std::pair<int, int> pos_j = net_insts[j]->getPosition();
                        double manhattan_dist = std::abs(pos_i.first - pos_j.first) + std::abs(pos_i.second - pos_j.second);
                        max_manhattan_dist = std::max(max_manhattan_dist, manhattan_dist);
                    }
                }
            }
            
            // 时序关键性：最大曼哈顿距离的影响
            double timing_factor = 1.0 + 0.5 * (max_manhattan_dist / 100.0); // 归一化
            
            // 综合关键性评估
            double net_crit = base_criticality * fanout_factor * timing_factor;
            net_criticality[net] = net_crit;
        }
        
        // 归一化网络关键性
        double max_criticality = 0.0001; // 避免除以零
        for (auto& crit_pair : net_criticality) {
            max_criticality = std::max(max_criticality, crit_pair.second);
        }
        for (auto& crit_pair : net_criticality) {
            crit_pair.second /= max_criticality; // 归一化到[0,1]范围
        }
        
        // 为每个可移动实例计算加权连接度
        for (auto& inst_pair : glb_inst_map) {
            Instance* inst = inst_pair.second;
            if (!inst->isFixed()) {
                double weighted_connectivity = 0.0;
                
                for (Net* net : inst->getNets()) {
                    // 基础连接度：连接到该网络的其他实例数
                    int basic_connectivity = net->getInsts().size() - 1;
                    
                    // 网络关键性权重：使用归一化后的关键性
                    double criticality_weight = 1.0 + 2.0 * net_criticality[net]; // 放大关键性影响
                    
                    // 计算加权连接度
                    weighted_connectivity += basic_connectivity * criticality_weight;
                }
                
                // 存储为整数，四舍五入
                connectivity_cache[inst] = static_cast<int>(weighted_connectivity + 0.5);
            }
        }
    }
    
    // 初始化拥塞图
    void initCongestionMap() {
        congestion_map.clear();
        int fpga_size_x = glb_fpga.getSizeX();
        int fpga_size_y = glb_fpga.getSizeY();
        
        // 初始化拥塞图
        for (int x = 0; x < fpga_size_x; x++) {
            for (int y = 0; y < fpga_size_y; y++) {
                congestion_map[std::make_pair(x, y)] = 0;
            }
        }
        
        // 计算每个网络对拥塞的贡献
        for (auto& net_pair : glb_net_map) {
            Net* net = net_pair.second;
            std::vector<Instance*> net_insts(net->getInsts().begin(), net->getInsts().end());
            
            if (net_insts.size() <= 1) continue;
            
            // 计算网络的边界框
            int min_x = std::numeric_limits<int>::max();
            int min_y = std::numeric_limits<int>::max();
            int max_x = std::numeric_limits<int>::min();
            int max_y = std::numeric_limits<int>::min();
            
            for (Instance* inst : net_insts) {
                std::pair<int, int> pos = inst->getPosition();
                min_x = std::min(min_x, pos.first);
                min_y = std::min(min_y, pos.second);
                max_x = std::max(max_x, pos.first);
                max_y = std::max(max_y, pos.second);
            }
            
            // 更新边界框内的拥塞值
            for (int x = min_x; x <= max_x; x++) {
                for (int y = min_y; y <= max_y; y++) {
                    congestion_map[std::make_pair(x, y)]++;
                }
            }
        }
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
    
    // 随机选择一个可移动的Instance
    Instance* selectRandomInstance() {
        if (movable_instances.empty()) {
            return nullptr;
        }
        
        std::uniform_int_distribution<int> dist(0, movable_instances.size() - 1);
        return movable_instances[dist(rng)];
    }
    
    // 随机选择一个空闲的位置，考虑当前温度和移动范围
    std::pair<int, int> selectRandomEmptyPosition(const std::pair<int, int>& current_pos = std::make_pair(-1, -1)) {
        int fpga_size_x = glb_fpga.getSizeX();
        int fpga_size_y = glb_fpga.getSizeY();
        
        // 如果提供了当前位置，则在其周围范围内寻找空位
        if (current_pos.first != -1 && current_pos.second != -1) {
            // 根据当前温度计算移动范围
            int range = static_cast<int>(move_range_factor * fpga_size_x * current_temperature / initial_temperature);
            // 确保范围至少为1
            range = std::max(1, range);
            
            std::vector<std::pair<int, int>> empty_positions;
            
            // 在当前位置周围的范围内寻找空位
            for (int dx = -range; dx <= range; dx++) {
                for (int dy = -range; dy <= range; dy++) {
                    int x = current_pos.first + dx;
                    int y = current_pos.second + dy;
                    
                    // 检查位置是否在FPGA范围内
                    if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                        Block* block = glb_fpga.getBlock(x, y);
                        if (block && block->getInstsCount() == 0) {
                            empty_positions.push_back(std::make_pair(x, y));
                        }
                    }
                }
            }
            
            if (!empty_positions.empty()) {
                std::uniform_int_distribution<int> dist(0, empty_positions.size() - 1);
                return empty_positions[dist(rng)];
            }
        }
        
        // 如果没有找到合适的位置或没有提供当前位置，则在整个FPGA中寻找
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
    
    // 增强型移动操作：将一个Instance移动到一个空闲位置，考虑连接度、温度和禁忌列表
    bool moveOperation() {
        // 根据连接度选择实例，连接度高的实例有更高概率被选中
        Instance* inst = selectInstanceByConnectivity();
        if (!inst) {
            return false;
        }
        
        std::pair<int, int> current_pos = inst->getPosition();
        
        // 获取多个候选位置，而不是只获取一个
        std::vector<std::pair<int, int>> candidate_positions = selectMultipleEmptyPositions(current_pos, 5); // 获取5个候选位置
        
        if (candidate_positions.empty()) {
            return false;
        }
        
        // 评估每个候选位置的质量
        std::vector<std::pair<std::pair<int, int>, double>> position_scores;
        for (const auto& new_pos : candidate_positions) {
            // 检查是否在禁忌列表中
            bool is_tabu = false;
            if (use_tabu_search) {
                // 检查移动是否在禁忌列表中
                int inst_id = inst->getInstId();
                auto move_key = std::make_pair(inst_id, new_pos.first * 10000 + new_pos.second); // 编码移动
                is_tabu = (tabu_list.find(move_key) != tabu_list.end() && 
                          tabu_list[move_key] > 0);
            }
            
            // 如果在禁忌列表中，跳过该位置，除非它能带来显著改进（特赦规则）
            if (is_tabu) {
                // 临时评估移动到该位置的效果
                double score = evaluateMoveScore(inst, current_pos, new_pos);
                // 只有当移动带来显著改进时才考虑特赦
                if (score > 0.2) { // 特赦阈值
                    position_scores.push_back(std::make_pair(new_pos, score));
                }
            } else {
                // 不在禁忌列表中，正常评估
                double score = evaluateMoveScore(inst, current_pos, new_pos);
                position_scores.push_back(std::make_pair(new_pos, score));
            }
        }
        
        // 如果没有有效的候选位置，返回失败
        if (position_scores.empty()) {
            return false;
        }
        
        // 根据分数选择最佳位置
        std::sort(position_scores.begin(), position_scores.end(), 
            [](const std::pair<std::pair<int, int>, double>& a, const std::pair<std::pair<int, int>, double>& b) {
                return a.second > b.second; // 降序排列，分数高的在前
            });
        
        // 选择最佳位置，但在高温时引入随机性
        std::pair<int, int> new_pos;
        if (current_temperature > initial_temperature * 0.5) {
            // 在高温下，有一定概率不选择最佳位置，而是随机选择一个较好的位置
            std::uniform_real_distribution<double> dist(0.0, 1.0);
            if (dist(rng) < 0.3) { // 30%的概率选择非最佳位置
                std::uniform_int_distribution<int> idx_dist(0, std::min(2, (int)position_scores.size() - 1));
                new_pos = position_scores[idx_dist(rng)].first;
            } else {
                new_pos = position_scores[0].first; // 70%的概率选择最佳位置
            }
        } else {
            // 在低温下，总是选择最佳位置
            new_pos = position_scores[0].first;
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
        
        // 更新总移动次数
        total_moves++;
        
        // 如果使用禁忌搜索，将此移动添加到禁忌列表
        if (use_tabu_search) {
            int inst_id = inst->getInstId();
            // 禁止该实例移回原位置
            auto move_key = std::make_pair(inst_id, current_pos.first * 10000 + current_pos.second);
            tabu_list[move_key] = tabu_tenure;
        }
        
        return true;
    }
    
    // 评估移动的分数 - 考虑线网长度、关键性和拥塞
    double evaluateMoveScore(Instance* inst, const std::pair<int, int>& current_pos, const std::pair<int, int>& new_pos) {
        // 临时移动并计算线网长度变化
        if (!glb_fpga.deleteInst(current_pos.first, current_pos.second, inst)) {
            return -1.0; // 移动失败
        }
        
        if (!glb_fpga.addInst(new_pos.first, new_pos.second, inst)) {
            // 恢复原位置
            glb_fpga.addInst(current_pos.first, current_pos.second, inst);
            return -1.0; // 移动失败
        }
        
        // 计算移动后的线网长度
        double wirelength_score = 0.0;
        double timing_score = 0.0;
        double congestion_score = 0.0;
        
        // 计算与该实例相关的网络的线网长度和时序得分
        for (Net* net : inst->getNets()) {
            int new_hpwl = net->evalHPWL();
            
            // 线网长度得分：新线网长度越短越好
            wirelength_score -= new_hpwl;
            
            // 时序得分：考虑网络关键性
            timing_score -= new_hpwl * net_criticality[net];
        }
        
        // 拥塞得分：新位置的拥塞程度越低越好
        congestion_score = -congestion_map[new_pos];
        
        // 恢复原位置
        glb_fpga.deleteInst(new_pos.first, new_pos.second, inst);
        glb_fpga.addInst(current_pos.first, current_pos.second, inst);
        
        // 综合得分：加权组合各项得分
        double total_score = (1.0 - congestion_weight - timing_weight) * wirelength_score + 
                             timing_weight * timing_score + 
                             congestion_weight * congestion_score;
        
        // 归一化得分
        return total_score / (std::abs(wirelength_score) + 0.0001); // 避免除以零
    }
    
    // 选择多个空闲位置
    std::vector<std::pair<int, int>> selectMultipleEmptyPositions(const std::pair<int, int>& current_pos, int count = 5) {
        std::vector<std::pair<int, int>> result;
        int fpga_size_x = glb_fpga.getSizeX();
        int fpga_size_y = glb_fpga.getSizeY();
        
        // 如果提供了当前位置，则在其周围范围内寻找空位
        if (current_pos.first != -1 && current_pos.second != -1) {
            // 根据当前温度计算移动范围
            int range = static_cast<int>(move_range_factor * fpga_size_x * current_temperature / initial_temperature);
            // 确保范围至少为1
            range = std::max(1, range);
            
            std::vector<std::pair<int, int>> empty_positions;
            
            // 在当前位置周围的范围内寻找空位
            for (int dx = -range; dx <= range; dx++) {
                for (int dy = -range; dy <= range; dy++) {
                    int x = current_pos.first + dx;
                    int y = current_pos.second + dy;
                    
                    // 检查位置是否在FPGA范围内
                    if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                        Block* block = glb_fpga.getBlock(x, y);
                        if (block && block->getInstsCount() == 0) {
                            empty_positions.push_back(std::make_pair(x, y));
                        }
                    }
                }
            }
            
            // 如果找到的空位足够多，随机选择count个
            if (empty_positions.size() > count) {
                std::shuffle(empty_positions.begin(), empty_positions.end(), rng);
                result.insert(result.end(), empty_positions.begin(), empty_positions.begin() + count);
            } else {
                result = empty_positions;
            }
        }
        
        // 如果没有找到足够的位置，在整个FPGA中寻找补充
        if (result.size() < count) {
            std::vector<std::pair<int, int>> global_empty_positions;
            
            for (int x = 0; x < fpga_size_x; x++) {
                for (int y = 0; y < fpga_size_y; y++) {
                    Block* block = glb_fpga.getBlock(x, y);
                    if (block && block->getInstsCount() == 0) {
                        // 检查是否已经在结果中
                        bool already_in_result = false;
                        for (const auto& pos : result) {
                            if (pos.first == x && pos.second == y) {
                                already_in_result = true;
                                break;
                            }
                        }
                        
                        if (!already_in_result) {
                            global_empty_positions.push_back(std::make_pair(x, y));
                        }
                    }
                }
            }
            
            // 随机选择剩余需要的位置
            if (!global_empty_positions.empty()) {
                std::shuffle(global_empty_positions.begin(), global_empty_positions.end(), rng);
                int remaining = count - result.size();
                remaining = std::min(remaining, (int)global_empty_positions.size());
                result.insert(result.end(), global_empty_positions.begin(), global_empty_positions.begin() + remaining);
            }
        }
        
        return result;
    }
    
    // 根据连接度选择实例，连接度高的实例有更高概率被选中
    Instance* selectInstanceByConnectivity() {
        if (movable_instances.empty()) {
            return nullptr;
        }
        
        // 使用轮盘赌选择法，连接度高的实例有更高概率被选中
        double total_connectivity = 0.0;
        for (Instance* inst : movable_instances) {
            total_connectivity += connectivity_cache[inst];
        }
        
        // 如果总连接度为0，则随机选择
        if (total_connectivity <= 0.0) {
            std::uniform_int_distribution<int> dist(0, movable_instances.size() - 1);
            return movable_instances[dist(rng)];
        }
        
        // 根据连接度进行加权选择
        std::uniform_real_distribution<double> dist(0.0, total_connectivity);
        double random_value = dist(rng);
        
        double cumulative = 0.0;
        for (Instance* inst : movable_instances) {
            cumulative += connectivity_cache[inst];
            if (cumulative >= random_value) {
                return inst;
            }
        }
        
        // 如果出现意外情况，返回最后一个实例
        return movable_instances.back();
    }
    
    // 交换操作：交换两个Instance的位置，优先考虑高连接度的块和相邻块
    bool swapOperation() {
        // 选择第一个实例，优先选择高连接度的实例
        Instance* inst1 = selectInstanceByConnectivity();
        if (!inst1) {
            return false;
        }
        
        std::pair<int, int> pos1 = inst1->getPosition();
        
        // 选择第二个实例，优先选择与第一个实例相邻且连接度高的实例
        Instance* inst2 = selectNeighborInstance(inst1);
        
        // 如果没有找到合适的相邻实例，则随机选择一个
        if (!inst2) {
            inst2 = selectInstanceByConnectivity();
            // 确保不是同一个实例
            while (inst2 == inst1) {
                inst2 = selectInstanceByConnectivity();
                if (!inst2) {
                    return false;
                }
            }
        }
        
        if (!inst2 || inst1 == inst2) {
            return false;
        }
        
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
        
        // 更新总移动次数
        total_moves++;
        
        return true;
    }
    
    // 选择与给定实例相邻且连接度高的实例
    Instance* selectNeighborInstance(Instance* inst) {
        if (!inst) {
            return nullptr;
        }
        
        std::pair<int, int> pos = inst->getPosition();
        int fpga_size_x = glb_fpga.getSizeX();
        int fpga_size_y = glb_fpga.getSizeY();
        
        // 收集相邻位置的实例
        std::vector<Instance*> neighbor_instances;
        
        // 检查四个方向的相邻位置
        const int dx[4] = {-1, 0, 1, 0};
        const int dy[4] = {0, -1, 0, 1};
        
        for (int i = 0; i < 4; i++) {
            int x = pos.first + dx[i];
            int y = pos.second + dy[i];
            
            if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                Block* block = glb_fpga.getBlock(x, y);
                if (block && block->getInstsCount() > 0) {
                    Instance* neighbor = block->getInsts()[0];
                    if (!neighbor->isFixed() && neighbor != inst) {
                        neighbor_instances.push_back(neighbor);
                    }
                }
            }
        }
        
        if (neighbor_instances.empty()) {
            return nullptr;
        }
        
        // 根据连接度选择相邻实例
        double total_connectivity = 0.0;
        for (Instance* neighbor : neighbor_instances) {
            total_connectivity += connectivity_cache[neighbor];
        }
        
        // 如果总连接度为0，则随机选择
        if (total_connectivity <= 0.0) {
            std::uniform_int_distribution<int> dist(0, neighbor_instances.size() - 1);
            return neighbor_instances[dist(rng)];
        }
        
        // 根据连接度进行加权选择
        std::uniform_real_distribution<double> dist(0.0, total_connectivity);
        double random_value = dist(rng);
        
        double cumulative = 0.0;
        for (Instance* neighbor : neighbor_instances) {
            cumulative += connectivity_cache[neighbor];
            if (cumulative >= random_value) {
                return neighbor;
            }
        }
        
        // 如果出现意外情况，返回最后一个实例
        return neighbor_instances.back();
    }
    
    // 计算接受概率 - 高级优化版本
    double acceptanceProbability(int new_wirelength, int current_wirelength, double temperature) {
        if (new_wirelength < current_wirelength) {
            // 如果新解更好，几乎总是接受，但在温度非常低时略微降低接受概率
            // 这有助于在低温时避免接受微小改进但可能导致局部最优的解
            if (temperature < final_temperature * 2 && (current_wirelength - new_wirelength) < 5) {
                return 0.95; // 在低温下对微小改进略微降低接受概率
            }
            return 1.0; // 否则总是接受更好的解
        }
        
        // 如果新解更差，根据温度和差值计算接受概率
        double delta = new_wirelength - current_wirelength;
        
        // 自适应能量函数：考虑当前温度和线网长度的比例
        // 在高温时更容易接受较差的解，在低温时更难接受较差的解
        double normalized_delta = delta / (current_wirelength * 0.01 + 1.0); // 归一化差值
        double acceptance_rate = exp(-normalized_delta / temperature);
        
        // 在温度非常低时，进一步降低接受概率，加速收敛
        if (temperature < final_temperature * 3) {
            acceptance_rate *= 0.8;
        }
        
        return acceptance_rate;
    }
    
    // 更新接受率和自适应调整温度
    void updateAcceptanceRate() {
        if (total_moves > 0) {
            accept_rate = static_cast<double>(accepted_moves) / total_moves;
        }
        
        // 重置计数器
        accepted_moves = 0;
        total_moves = 0;
        
        // 自适应调整温度
        if (use_adaptive_cooling) {
            if (accept_rate > target_accept_rate + 0.1) {
                // 接受率过高，加速降温
                cooling_rate = 0.8;
            } else if (accept_rate < target_accept_rate - 0.1) {
                // 接受率过低，减缓降温
                cooling_rate = 0.95;
            } else {
                // 接受率在目标范围内，使用标准降温率
                cooling_rate = 0.9;
            }
        }
    }
    
    // 优化的局部搜索算法 - 基于连接度和贪心策略
    void localSearch() {
        bool improved = true;
        int iterations = 0;
        int max_iterations = 50; // 减少最大迭代次数，提高效率
        
        // 按连接度排序实例，优先处理高连接度的实例
        std::vector<Instance*> sorted_instances = movable_instances;
        std::sort(sorted_instances.begin(), sorted_instances.end(), 
            [this](Instance* a, Instance* b) {
                return connectivity_cache[a] > connectivity_cache[b];
            });
        
        while (improved && iterations < max_iterations) {
            improved = false;
            iterations++;
            
            // 只处理前70%的高连接度实例，减少计算量
            int instances_to_process = static_cast<int>(sorted_instances.size() * 0.7);
            instances_to_process = std::max(1, instances_to_process);
            
            for (int idx = 0; idx < instances_to_process; idx++) {
                Instance* inst = sorted_instances[idx];
                std::pair<int, int> current_pos = inst->getPosition();
                
                // 计算当前位置的线网长度 - 只计算与该实例相关的线网
                int current_local_wirelength = 0;
                for (Net* net : inst->getNets()) {
                    current_local_wirelength += net->evalHPWL();
                }
                
                // 尝试移动到相邻位置 - 扩展到8个方向以增加搜索空间
                const int dx[8] = {-1, 0, 1, 0, -1, -1, 1, 1};
                const int dy[8] = {0, -1, 0, 1, -1, 1, -1, 1};
                
                int best_x = current_pos.first;
                int best_y = current_pos.second;
                int best_wirelength = current_local_wirelength;
                bool found_better = false;
                
                int fpga_size_x = glb_fpga.getSizeX();
                int fpga_size_y = glb_fpga.getSizeY();
                
                // 先检查所有可能的位置，找出最佳位置
                for (int i = 0; i < 8; i++) {
                    int x = current_pos.first + dx[i];
                    int y = current_pos.second + dy[i];
                    
                    if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                        Block* block = glb_fpga.getBlock(x, y);
                        if (block && block->getInstsCount() == 0) {
                            // 临时移动并计算线网长度
                            if (glb_fpga.deleteInst(current_pos.first, current_pos.second, inst)) {
                                if (glb_fpga.addInst(x, y, inst)) {
                                    int new_local_wirelength = 0;
                                    for (Net* net : inst->getNets()) {
                                        new_local_wirelength += net->evalHPWL();
                                    }
                                    
                                    // 恢复原位置以继续评估其他位置
                                    glb_fpga.deleteInst(x, y, inst);
                                    glb_fpga.addInst(current_pos.first, current_pos.second, inst);
                                    
                                    // 更新最佳位置
                                    if (new_local_wirelength < best_wirelength) {
                                        best_wirelength = new_local_wirelength;
                                        best_x = x;
                                        best_y = y;
                                        found_better = true;
                                    }
                                } else {
                                    // 恢复原位置
                                    glb_fpga.addInst(current_pos.first, current_pos.second, inst);
                                }
                            }
                        }
                    }
                }
                
                // 如果找到更好的位置，移动到该位置
                if (found_better && (best_x != current_pos.first || best_y != current_pos.second)) {
                    glb_fpga.deleteInst(current_pos.first, current_pos.second, inst);
                    glb_fpga.addInst(best_x, best_y, inst);
                    improved = true;
                }
            }
        }
    }
    
    // 执行模拟退火算法 - 高级优化版本（多起点搜索、自适应温度调度、混合策略）
    void run() {
        // 多起点搜索策略
        std::cout << "Starting multi-start simulated annealing with " << multi_start_count << " starting points..." << std::endl;
        
        // 记录开始时间，设置最大运行时间（分钟）
        auto start_time = std::chrono::high_resolution_clock::now();
        const int max_runtime_minutes = 30; // 最大运行时间30分钟
        
        // 保存初始布局作为第一个起点
        saveBestPlacement();
        global_best_wirelength = best_wirelength;
        global_best_placement = best_placement;
        
        // 执行多起点搜索
        for (int start_idx = 0; start_idx < multi_start_count; start_idx++) {
            // 检查是否超时
            auto current_time = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = current_time - start_time;
            if (elapsed.count() > max_runtime_minutes * 60) {
                std::cout << "Maximum runtime reached (" << max_runtime_minutes << " minutes). Stopping search." << std::endl;
                break;
            }
            
            std::cout << "\nStarting point " << (start_idx + 1) << " of " << multi_start_count << std::endl;
            std::cout << "Elapsed time: " << elapsed.count() << " seconds" << std::endl;
            
            // 如果不是第一个起点，则生成新的随机起点
            if (start_idx > 0) {
                // 随机扰动当前布局作为新起点
                std::cout << "Generating new starting point..." << std::endl;
                generateNewStartingPoint(start_idx);
                current_wirelength = reportWireLength();
                best_wirelength = current_wirelength;
                saveBestPlacement();
            }
            
            // 重置温度和相关参数
            current_temperature = initial_temperature;
            no_improvement_count = 0;
            accepted_moves = 0;
            total_moves = 0;
            
            // 单起点搜索过程
            std::cout << "Starting single-point search with initial temperature: " << current_temperature << std::endl;
            runSingleSearch();
            
            // 更新全局最佳解
            if (best_wirelength < global_best_wirelength) {
                std::cout << "Found better global solution: " << best_wirelength 
                          << " (improved from " << global_best_wirelength << ")" << std::endl;
                global_best_wirelength = best_wirelength;
                global_best_placement = best_placement;
            }
        }
        
        // 恢复全局最佳布局
        std::cout << "\nRestoring global best placement with wirelength: " << global_best_wirelength << std::endl;
        best_placement = global_best_placement;
        restoreBestPlacement();
        
        // 最终阶段：进行更彻底的局部搜索
        std::cout << "Performing final intensive local search optimization..." << std::endl;
        for (int i = 0; i < 10; i++) { // 增加最终局部搜索次数
            // 交替使用不同的局部搜索策略
            if (i % 2 == 0) {
                localSearch();
            } else {
                advancedLocalSearch();
            }
            
            int final_local_wirelength = reportWireLength();
            if (final_local_wirelength < global_best_wirelength) {
                global_best_wirelength = final_local_wirelength;
                saveBestPlacement();
                global_best_placement = best_placement;
            }
        }
        
        // 最终恢复全局最佳布局
        best_placement = global_best_placement;
        restoreBestPlacement();
    }
    
    // 生成新的起点 - 基于当前最佳解的扰动或基于连接度的构造
    void generateNewStartingPoint(int start_idx) {
        // 恢复全局最佳布局作为基础
        best_placement = global_best_placement;
        restoreBestPlacement();
        
        // 根据起点索引选择不同的策略
        if (start_idx % 3 == 1) {
            // 策略1: 大幅度随机扰动 - 随机交换30%的实例
            int swap_count = movable_instances.size() * 0.3;
            swap_count = std::max(10, swap_count);
            
            std::uniform_int_distribution<int> dist(0, movable_instances.size() - 1);
            for (int i = 0; i < swap_count; i++) {
                int idx1 = dist(rng);
                int idx2 = dist(rng);
                while (idx2 == idx1) idx2 = dist(rng);
                
                Instance* inst1 = movable_instances[idx1];
                Instance* inst2 = movable_instances[idx2];
                
                std::pair<int, int> pos1 = inst1->getPosition();
                std::pair<int, int> pos2 = inst2->getPosition();
                
                // 交换位置
                if (glb_fpga.deleteInst(pos1.first, pos1.second, inst1) &&
                    glb_fpga.deleteInst(pos2.first, pos2.second, inst2)) {
                    glb_fpga.addInst(pos2.first, pos2.second, inst1);
                    glb_fpga.addInst(pos1.first, pos1.second, inst2);
                }
            }
        } else if (start_idx % 3 == 2) {
            // 策略2: 基于连接度的聚类 - 将高连接度的实例聚集在一起
            // 按连接度排序实例
            std::vector<Instance*> sorted_instances = movable_instances;
            std::sort(sorted_instances.begin(), sorted_instances.end(), 
                [this](Instance* a, Instance* b) {
                    return connectivity_cache[a] > connectivity_cache[b];
                });
            
            // 清除当前布局
            for (Instance* inst : sorted_instances) {
                std::pair<int, int> pos = inst->getPosition();
                glb_fpga.deleteInst(pos.first, pos.second, inst);
            }
            
            // 从FPGA中心开始，螺旋状放置高连接度的实例
            int fpga_size_x = glb_fpga.getSizeX();
            int fpga_size_y = glb_fpga.getSizeY();
            int center_x = fpga_size_x / 2;
            int center_y = fpga_size_y / 2;
            
            int placed_count = 0;
            for (int radius = 0; radius < std::max(fpga_size_x, fpga_size_y) && placed_count < sorted_instances.size(); radius++) {
                // 螺旋状遍历
                for (int dx = -radius; dx <= radius && placed_count < sorted_instances.size(); dx++) {
                    for (int dy = -radius; dy <= radius && placed_count < sorted_instances.size(); dy++) {
                        if (abs(dx) + abs(dy) == radius) { // 曼哈顿距离等于radius
                            int x = center_x + dx;
                            int y = center_y + dy;
                            
                            if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                                Block* block = glb_fpga.getBlock(x, y);
                                if (block && block->getInstsCount() == 0 && placed_count < sorted_instances.size()) {
                                    glb_fpga.addInst(x, y, sorted_instances[placed_count]);
                                    placed_count++;
                                }
                            }
                        }
                    }
                }
            }
            
            // 如果还有未放置的实例，随机放置
            if (placed_count < sorted_instances.size()) {
                for (int x = 0; x < fpga_size_x && placed_count < sorted_instances.size(); x++) {
                    for (int y = 0; y < fpga_size_y && placed_count < sorted_instances.size(); y++) {
                        Block* block = glb_fpga.getBlock(x, y);
                        if (block && block->getInstsCount() == 0) {
                            glb_fpga.addInst(x, y, sorted_instances[placed_count]);
                            placed_count++;
                        }
                    }
                }
            }
        } else {
            // 策略3: 基于关键网络的优化 - 优先考虑关键网络的实例
            // 更新网络关键性
            initConnectivityAndCriticality();
            
            // 找出最关键的网络
            std::vector<std::pair<Net*, double>> critical_nets;
            for (auto& crit_pair : net_criticality) {
                critical_nets.push_back(crit_pair);
            }
            
            // 按关键性排序
            std::sort(critical_nets.begin(), critical_nets.end(), 
                [](const std::pair<Net*, double>& a, const std::pair<Net*, double>& b) {
                    return a.second > b.second;
                });
            
            // 选择前20%的关键网络
            int critical_net_count = std::max(1, static_cast<int>(critical_nets.size() * 0.2));
            
            // 收集这些网络连接的实例
            std::set<Instance*> critical_instances;
            for (int i = 0; i < critical_net_count && i < critical_nets.size(); i++) {
                Net* net = critical_nets[i].first;
                for (Instance* inst : net->getInsts()) {
                    if (!inst->isFixed()) {
                        critical_instances.insert(inst);
                    }
                }
            }
            
            // 随机交换这些关键实例的位置
            std::vector<Instance*> critical_inst_vec(critical_instances.begin(), critical_instances.end());
            std::shuffle(critical_inst_vec.begin(), critical_inst_vec.end(), rng);
            
            for (size_t i = 0; i < critical_inst_vec.size(); i++) {
                for (size_t j = i + 1; j < critical_inst_vec.size(); j++) {
                    Instance* inst1 = critical_inst_vec[i];
                    Instance* inst2 = critical_inst_vec[j];
                    
                    std::pair<int, int> pos1 = inst1->getPosition();
                    std::pair<int, int> pos2 = inst2->getPosition();
                    
                    // 交换位置
                    if (glb_fpga.deleteInst(pos1.first, pos1.second, inst1) &&
                        glb_fpga.deleteInst(pos2.first, pos2.second, inst2)) {
                        glb_fpga.addInst(pos2.first, pos2.second, inst1);
                        glb_fpga.addInst(pos1.first, pos1.second, inst2);
                    }
                }
            }
        }
        
        // 更新拥塞图
        initCongestionMap();
    }
    
    // 单起点搜索过程 - 优化的模拟退火核心算法
    void runSingleSearch() {
        int last_improvement_temp_step = 0;
        int temp_step = 0;
        int stagnation_count = 0; // 停滞计数，用于检测算法是否陷入局部最优
        int last_best_wirelength = best_wirelength;
        
        // 添加最大迭代次数限制，防止无限循环
        const int max_temp_steps = 200;
        
        // 外循环：降温过程
        while (current_temperature > final_temperature && temp_step < max_temp_steps) {
            temp_step++;
            accepted_moves = 0;
            total_moves = 0;
            
            // 每10步输出一次进度信息
            if (temp_step % 10 == 0) {
                std::cout << "Progress: " << temp_step << " temperature steps completed. Current temp: " 
                          << current_temperature << ", Target: " << final_temperature << std::endl;
            }
            
            // 根据当前温度调整移动范围因子 - 更加自适应的调整
            move_range_factor = 0.3 + 0.7 * std::pow(current_temperature / initial_temperature, 0.8);
            
            // 动态调整内循环迭代次数 - 温度越低，迭代次数越少
            int current_iterations = static_cast<int>(inner_iterations * (0.4 + 0.6 * current_temperature / initial_temperature));
            current_iterations = std::max(inner_iterations / 5, current_iterations); // 确保最小迭代次数
            
            // 内循环：在当前温度下进行多次扰动
            for (int i = 0; i < current_iterations; i++) {
                bool operation_success = false;
                
                // 随机选择移动或交换操作，温度越低越倾向于交换操作
                std::uniform_real_distribution<double> dist(0.0, 1.0);
                double random_value = dist(rng);
                
                // 动态调整移动和交换的概率 - 更加倾向于交换操作以提高布局质量
                double current_move_prob = move_probability * std::pow(current_temperature / initial_temperature, 0.7) + 0.15;
                current_move_prob = std::min(0.7, std::max(0.2, current_move_prob));
                
                if (random_value < current_move_prob) {
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
                        accepted_moves++;
                        current_wirelength = new_wirelength;
                        
                        // 如果是最佳解，保存它
                        if (new_wirelength < best_wirelength) {
                            best_wirelength = new_wirelength;
                            saveBestPlacement();
                            last_improvement_temp_step = temp_step;
                            no_improvement_count = 0;
                            stagnation_count = 0; // 重置停滞计数
                        }
                    } else {
                        // 不接受新解，恢复上一个布局
                        restoreBestPlacement();
                        current_wirelength = best_wirelength;
                    }
                }
                
                // 每隔一定次数检查是否需要提前终止内循环
                if (i > 0 && i % (current_iterations / 4) == 0) {
                    // 如果接受率过低，提前终止内循环
                    if (total_moves > 0 && static_cast<double>(accepted_moves) / total_moves < 0.03) {
                        break;
                    }
                }
            }
            
            // 更新接受率并自适应调整温度
            updateAcceptanceRate();
            
            // 在温度较低或接受率较低时执行局部搜索
            if (current_temperature < initial_temperature * 0.4 || accept_rate < 0.12) {
                // 交替使用不同的局部搜索策略
                if (temp_step % 2 == 0) {
                    localSearch();
                } else {
                    advancedLocalSearch();
                }
                
                // 更新当前线网长度
                current_wirelength = reportWireLength();
                // 如果找到更好的解，更新最佳解
                if (current_wirelength < best_wirelength) {
                    best_wirelength = current_wirelength;
                    saveBestPlacement();
                    last_improvement_temp_step = temp_step;
                    no_improvement_count = 0;
                    stagnation_count = 0; // 重置停滞计数
                }
            }
            
            // 检查是否长时间没有改进
            if (temp_step - last_improvement_temp_step > 6) { // 减少等待时间
                no_improvement_count++;
                
                // 使用重加热机制
                if (use_reheating && no_improvement_count >= reheat_interval) {
                    std::cout << "No improvement for " << reheat_interval << " temperature steps, reheating..." << std::endl;
                    // 重加热 - 提高温度
                    current_temperature *= reheat_factor;
                    // 限制最高温度
                    current_temperature = std::min(current_temperature, initial_temperature * 0.8);
                    no_improvement_count = 0;
                }
                // 如果重加热后仍无改进，则加速降温
                else if (no_improvement_count >= max_no_improvement) {
                    std::cout << "No improvement for " << max_no_improvement << " temperature steps, accelerating cooling." << std::endl;
                    // 加速降温
                    cooling_rate = 0.65;
                    no_improvement_count = 0;
                }
            }
            
            // 检查是否陷入停滞状态
            if (best_wirelength == last_best_wirelength) {
                stagnation_count++;
                if (stagnation_count >= 3) { // 如果连续3次温度步骤没有改进
                    // 执行扰动操作，尝试跳出局部最优
                    std::cout << "Stagnation detected, performing perturbation..." << std::endl;
                    performPerturbation();
                    current_wirelength = reportWireLength();
                    if (current_wirelength < best_wirelength) {
                        best_wirelength = current_wirelength;
                        saveBestPlacement();
                    }
                    stagnation_count = 0;
                }
            } else {
                stagnation_count = 0;
            }
            last_best_wirelength = best_wirelength;
            
            // 降温
            current_temperature *= cooling_rate;
            
            // 自适应调整降温速率
            if (use_adaptive_cooling) {
                // 如果接受率过高，加速降温
                if (accept_rate > 0.6) {
                    cooling_rate = 0.85;
                }
                // 如果接受率适中，使用标准降温率
                else if (accept_rate > 0.3) {
                    cooling_rate = 0.9;
                }
                // 如果接受率过低，减缓降温
                else {
                    cooling_rate = 0.95;
                }
            }
            
            std::cout << "Temperature: " << current_temperature 
                      << ", Accept Rate: " << accept_rate 
                      << ", Move Range: " << move_range_factor
                      << ", Best Wirelength: " << best_wirelength << std::endl;
        }
    }
    
    // 高级局部搜索 - 基于关键路径和拥塞的优化
    void advancedLocalSearch() {
        bool improved = true;
        int iterations = 0;
        int max_iterations = 30; // 适当的迭代次数
        
        // 更新网络关键性和拥塞图
        initConnectivityAndCriticality();
        initCongestionMap();
        
        // 按关键性排序网络
        std::vector<std::pair<Net*, double>> critical_nets;
        for (auto& crit_pair : net_criticality) {
            critical_nets.push_back(crit_pair);
        }
        
        std::sort(critical_nets.begin(), critical_nets.end(), 
            [](const std::pair<Net*, double>& a, const std::pair<Net*, double>& b) {
                return a.second > b.second;
            });
        
        // 选择前30%的关键网络
        int critical_net_count = std::max(1, static_cast<int>(critical_nets.size() * 0.3));
        
        while (improved && iterations < max_iterations) {
            improved = false;
            iterations++;
            
            // 处理关键网络
            for (int i = 0; i < critical_net_count && i < critical_nets.size(); i++) {
                Net* net = critical_nets[i].first;
                
                // 收集该网络连接的可移动实例
                std::vector<Instance*> net_instances;
                for (Instance* inst : net->getInsts()) {
                    if (!inst->isFixed()) {
                        net_instances.push_back(inst);
                    }
                }
                
                // 尝试优化这些实例的位置
                for (Instance* inst : net_instances) {
                    std::pair<int, int> current_pos = inst->getPosition();
                    
                    // 计算当前位置的线网长度和拥塞度
                    int current_local_wirelength = 0;
                    for (Net* connected_net : inst->getNets()) {
                        current_local_wirelength += connected_net->evalHPWL();
                    }
                    
                    int current_congestion = congestion_map[current_pos];
                    
                    // 尝试移动到周围位置
                    const int dx[8] = {-1, 0, 1, 0, -1, -1, 1, 1};
                    const int dy[8] = {0, -1, 0, 1, -1, 1, -1, 1};
                    
                    int best_x = current_pos.first;
                    int best_y = current_pos.second;
                    double best_score = 0;
                    bool found_better = false;
                    
                    int fpga_size_x = glb_fpga.getSizeX();
                    int fpga_size_y = glb_fpga.getSizeY();
                    
                    // 检查所有可能的位置
                    for (int d = 0; d < 8; d++) {
                        int x = current_pos.first + dx[d];
                        int y = current_pos.second + dy[d];
                        
                        if (x >= 0 && x < fpga_size_x && y >= 0 && y < fpga_size_y) {
                            Block* block = glb_fpga.getBlock(x, y);
                            if (block && block->getInstsCount() == 0) {
                                // 临时移动并计算综合得分
                                if (glb_fpga.deleteInst(current_pos.first, current_pos.second, inst)) {
                                    if (glb_fpga.addInst(x, y, inst)) {
                                        // 计算新的线网长度
                                        int new_local_wirelength = 0;
                                        for (Net* connected_net : inst->getNets()) {
                                            new_local_wirelength += connected_net->evalHPWL();
                                        }
                                        
                                        // 计算拥塞改善
                                        int new_congestion = congestion_map[std::make_pair(x, y)];
                                        int congestion_improvement = current_congestion - new_congestion;
                                        
                                        // 计算线网长度改善
                                        int wirelength_improvement = current_local_wirelength - new_local_wirelength;
                                        
                                        // 综合得分 - 加权组合
                                        double score = (1.0 - congestion_weight) * wirelength_improvement + 
                                                      congestion_weight * congestion_improvement;
                                        
                                        // 恢复原位置以继续评估其他位置
                                        glb_fpga.deleteInst(x, y, inst);
                                        glb_fpga.addInst(current_pos.first, current_pos.second, inst);
                                        
                                        // 更新最佳位置
                                        if (score > best_score) {
                                            best_score = score;
                                            best_x = x;
                                            best_y = y;
                                            found_better = true;
                                        }
                                    } else {
                                        // 恢复原位置
                                        glb_fpga.addInst(current_pos.first, current_pos.second, inst);
                                    }
                                }
                            }
                        }
                    }
                    
                    // 如果找到更好的位置，移动到该位置
                    if (found_better && (best_x != current_pos.first || best_y != current_pos.second)) {
                        glb_fpga.deleteInst(current_pos.first, current_pos.second, inst);
                        glb_fpga.addInst(best_x, best_y, inst);
                        improved = true;
                    }
                }
            }
            
            // 更新拥塞图
            if (improved) {
                initCongestionMap();
            }
        }
    }
    
    // 执行扰动操作，帮助算法跳出局部最优
    void performPerturbation() {
        // 随机交换一定比例的实例
        int perturbation_count = movable_instances.size() * 0.1; // 扰动10%的实例
        perturbation_count = std::max(5, perturbation_count); // 至少扰动5个实例
        
        std::uniform_int_distribution<int> dist(0, movable_instances.size() - 1);
        
        for (int i = 0; i < perturbation_count; i++) {
            // 随机选择两个实例进行交换
            int idx1 = dist(rng);
            int idx2 = dist(rng);
            
            // 确保选择不同的实例
            while (idx2 == idx1) {
                idx2 = dist(rng);
            }
            
            Instance* inst1 = movable_instances[idx1];
            Instance* inst2 = movable_instances[idx2];
            
            std::pair<int, int> pos1 = inst1->getPosition();
            std::pair<int, int> pos2 = inst2->getPosition();
            
            // 交换位置
            if (glb_fpga.deleteInst(pos1.first, pos1.second, inst1) &&
                glb_fpga.deleteInst(pos2.first, pos2.second, inst2)) {
                
                if (glb_fpga.addInst(pos2.first, pos2.second, inst1) &&
                    glb_fpga.addInst(pos1.first, pos1.second, inst2)) {
                    // 交换成功
                } else {
                    // 恢复原位置
                    glb_fpga.addInst(pos1.first, pos1.second, inst1);
                    glb_fpga.addInst(pos2.first, pos2.second, inst2);
                }
            }
        }
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

// 主布局函数 - 使用优化的TimberWolf模拟退火算法
void runPlacement() {
    std::cout << "Starting placement with Optimized TimberWolf Simulated Annealing..." << std::endl;
    
    // 初始化布局
    initializePlacement();
    
    // 报告初始线网长度
    std::cout << "Initial ";
    int initial_wirelength = reportWireLength();
    
    // 执行优化的模拟退火算法
    std::cout << "Running optimized simulated annealing algorithm..." << std::endl;
    std::cout << "Features: dynamic temperature adjustment, adaptive cooling, local search optimization" << std::endl;
    
    SimulatedAnnealing sa;
    
    // 记录开始时间
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // 运行算法
    sa.run();
    
    // 记录结束时间
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    
    // 报告最终线网长度
    std::cout << "Final ";
    int final_wirelength = reportWireLength();
    
    // 计算改进百分比
    double improvement = (initial_wirelength - final_wirelength) * 100.0 / initial_wirelength;
    
    std::cout << "Placement completed in " << elapsed.count() << " seconds." << std::endl;
    std::cout << "Improvement: " << improvement << "% reduction in wirelength." << std::endl;
    
    // 验证布局合法性
    int errors = reportValid();
    if (errors == 0) {
        std::cout << "Final placement is valid." << std::endl;
    } else {
        std::cout << "Warning: Final placement has " << errors << " errors." << std::endl;
    }
}
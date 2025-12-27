#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feedthrough分析模块 - 基于FTAFP论文模型实现
Implements the feedthrough estimation model from the FTAFP paper.
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

try:
    from ..data.structures import FloorplanDesign, Net, Module, ModuleType
except ImportError:
    # 适用于独立测试
    from data.structures import FloorplanDesign, Net, Module, ModuleType

# --- 新的数据结构 ---

@dataclass
class SubNet:
    """子网定义"""
    id: int
    modules: List[Module]
    center: Tuple[float, float] = (0.0, 0.0)
    width: float = 0.0
    height: float = 0.0
    bounding_box_area: float = 0.0
    module_area_sum: float = 0.0
    bbox_min_x: float = 0.0  # 包围盒左边界
    bbox_min_y: float = 0.0  # 包围盒下边界
    bbox_max_x: float = 0.0  # 包围盒右边界
    bbox_max_y: float = 0.0  # 包围盒上边界

@dataclass
class FTAFPResult:
    """FTAFP模型分析结果"""
    total_feedthrough_wirelength: float
    total_feedthrough_number: int
    net_details: Dict[str, Dict[str, float]] # 每个net的fthwl和fthnum

# --- 主实现类 ---

class FTAFPEstimator:
    """
    基于FTAFP论文模型的Feedthrough预测器
    """
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def analyze(self, design: FloorplanDesign) -> FTAFPResult:
        """执行完整的FTAFP Feedthrough分析"""
        total_fthwl = 0.0
        total_fthnum = 0
        net_details = {}

        for net in design.nets.values():
            if len(net.pins) < 2:
                continue

            # --- 阶段一：网络简化 ---
            sub_nets = self._simplify_net(design, net)
            
            # --- 阶段二：Feedthrough估算 ---
            fthwl, fthnum = self._estimate_feedthrough_for_net(sub_nets, design, net)
            
            total_fthwl += fthwl
            total_fthnum += fthnum
            net_details[net.name] = {'fthwl': fthwl, 'fthnum': fthnum}
            
        return FTAFPResult(
            total_feedthrough_wirelength=total_fthwl,
            total_feedthrough_number=total_fthnum,
            net_details=net_details
        )

    # --- 阶段一：网络简化实现 ---

    def _simplify_net(self, design: FloorplanDesign, net: Net) -> List[SubNet]:
        """使用并查集将网络简化为子网"""
        net_modules = [design.get_module(pin[0]) for pin in net.pins if design.get_module(pin[0])]
        net_modules = [m for m in net_modules if m.module_type != ModuleType.TERMINAL] # 只考虑宏模块

        if len(net_modules) < 2:
            return []

        # 初始化并查集
        parent = {m.name: m.name for m in net_modules}
        def find(module_name: str) -> str:
            if parent[module_name] == module_name:
                return module_name
            parent[module_name] = find(parent[module_name])
            return parent[module_name]

        def union(m1_name: str, m2_name: str):
            root1 = find(m1_name)
            root2 = find(m2_name)
            if root1 != root2:
                parent[root2] = root1

        # 根据邻接关系合并模块
        for i in range(len(net_modules)):
            for j in range(i + 1, len(net_modules)):
                m1 = net_modules[i]
                m2 = net_modules[j]
                if self._are_modules_adjacent(m1, m2):
                    union(m1.name, m2.name)
        
        # 将集合分组为子网
        sub_net_groups: Dict[str, List[Module]] = {}
        for module in net_modules:
            root = find(module.name)
            if root not in sub_net_groups:
                sub_net_groups[root] = []
            sub_net_groups[root].append(module)

        # 创建并计算SubNet对象
        sub_nets = []
        for i, modules in enumerate(sub_net_groups.values()):
            sub_net = self._create_subnet_from_modules(i, modules)
            sub_nets.append(sub_net)
            
        return sub_nets

    def _are_modules_adjacent(self, m1: Module, m2: Module) -> bool:
        """检查两个模块是否邻接（边界接触或非常近）"""
        m1_bbox = m1.get_bounding_box()
        m2_bbox = m2.get_bounding_box()
        
        # 检查x方向邻接
        x_adjacent = (abs(m1_bbox[0] - m2_bbox[2]) < 1e-6 or abs(m2_bbox[0] - m1_bbox[2]) < 1e-6) and \
                     (m1_bbox[1] < m2_bbox[3] and m1_bbox[3] > m2_bbox[1])
        # 检查y方向邻接
        y_adjacent = (abs(m1_bbox[1] - m2_bbox[3]) < 1e-6 or abs(m2_bbox[1] - m1_bbox[3]) < 1e-6) and \
                     (m1_bbox[0] < m2_bbox[2] and m1_bbox[2] > m2_bbox[0])

        return x_adjacent or y_adjacent

    def _create_subnet_from_modules(self, id: int, modules: List[Module]) -> SubNet:
        """从模块列表创建SubNet对象并计算其属性"""
        center_x = sum(m.get_center()[0] for m in modules) / len(modules)
        center_y = sum(m.get_center()[1] for m in modules) / len(modules)
        
        min_x = min(m.x for m in modules)
        min_y = min(m.y for m in modules)
        max_x = max(m.x + m.width for m in modules)
        max_y = max(m.y + m.height for m in modules)
        
        width = max_x - min_x
        height = max_y - min_y
        
        return SubNet(
            id=id,
            modules=modules,
            center=(center_x, center_y),
            width=width,
            height=height,
            bounding_box_area=width * height,
            module_area_sum=sum(m.area for m in modules),
            bbox_min_x=min_x,
            bbox_min_y=min_y,
            bbox_max_x=max_x,
            bbox_max_y=max_y
        )

    # --- 阶段二：Feedthrough估算实现 ---

    def _estimate_feedthrough_for_net(self, sub_nets: List[SubNet], design: FloorplanDesign, current_net: Net) -> Tuple[float, int]:
        """在简化的子网图上使用MST估算Feedthrough"""
        if len(sub_nets) < 2:
            return 0.0, 0

        # 构建MST
        mst_edges = self._build_mst(sub_nets)

        # 🔧 **修复逻辑错误**: 收集设计中所有不属于当前网络的模块作为障碍物
        obstacle_modules = []
        current_net_modules = set()
        
        # 收集当前网络涉及的所有模块
        for module_name, _ in current_net.pins:
            current_net_modules.add(module_name)
        
        # 收集所有不属于当前网络的宏模块作为障碍物
        for module in design.modules.values():
            if (module.module_type != ModuleType.TERMINAL and 
                module.name not in current_net_modules):
                obstacle_modules.append(module)

        # 累加MST各边的Feedthrough
        net_fthwl = 0.0
        net_fthnum = 0
        for u_idx, v_idx in mst_edges:
            sub_net_u = sub_nets[u_idx]
            sub_net_v = sub_nets[v_idx]
            
            # 计算模块数量权重
            omega = (len(sub_net_u.modules) + len(sub_net_v.modules)) / 2
            
            # 计算线长
            fthwl_edge = self._calculate_fthwl_edge(sub_net_u, sub_net_v)
            net_fthwl += fthwl_edge * omega
            
            # 🔧 **修复逻辑错误**: 传递正确的障碍物模块列表
            fthnum_edge = self._estimate_fthnum_edge(sub_net_u, sub_net_v, obstacle_modules)
            net_fthnum += fthnum_edge

        return max(0, net_fthwl), net_fthnum

    def _build_mst(self, sub_nets: List[SubNet]) -> List[Tuple[int, int]]:
        """使用Prim算法构建子网图的MST"""
        n = len(sub_nets)
        visited = [False] * n
        min_weight = [float('inf')] * n
        parent = [-1] * n
        min_weight[0] = 0

        for _ in range(n):
            # 找到未访问的最小权重节点
            u = -1
            min_w = float('inf')
            for i in range(n):
                if not visited[i] and min_weight[i] < min_w:
                    min_w = min_weight[i]
                    u = i
            
            if u == -1: break
            visited[u] = True

            # 更新邻居的权重
            for v in range(n):
                if not visited[v]:
                    # 计算加权距离作为边权
                    omega = (len(sub_nets[u].modules) + len(sub_nets[v].modules)) / 2
                    dist = abs(sub_nets[u].center[0] - sub_nets[v].center[0]) + \
                           abs(sub_nets[u].center[1] - sub_nets[v].center[1])
                    weight = dist * omega

                    if weight < min_weight[v]:
                        min_weight[v] = weight
                        parent[v] = u
        
        mst_edges = []
        for i in range(1, n):
            if parent[i] != -1:
                mst_edges.append((parent[i], i))
        return mst_edges

    def _calculate_fthwl_edge(self, u: SubNet, v: SubNet) -> float:
        """计算MST边上的Feedthrough线长"""
        wl_manh = abs(u.center[0] - v.center[0]) + abs(u.center[1] - v.center[1])
        
        def wl_o(sub_net: SubNet) -> float:
            hpwl_bbox = (sub_net.width + sub_net.height) / 2
            util_ratio = sub_net.module_area_sum / sub_net.bounding_box_area if sub_net.bounding_box_area > 0 else 0
            return hpwl_bbox * util_ratio

        return wl_manh - wl_o(u) - wl_o(v)

    def _estimate_fthnum_edge(self, u: SubNet, v: SubNet, obstacle_modules: List[Module]) -> int:
        """使用改进的路径分析估算Feedthrough数量"""
        feedthrough_count = 0
        
        # 🔧 **修复核心问题**: 使用真实的包围盒坐标，而不是错误地重建
        u_min_x, u_min_y, u_max_x, u_max_y = u.bbox_min_x, u.bbox_min_y, u.bbox_max_x, u.bbox_max_y
        v_min_x, v_min_y, v_max_x, v_max_y = v.bbox_min_x, v.bbox_min_y, v.bbox_max_x, v.bbox_max_y
        
        # 计算连接u和v的路径包围盒
        path_min_x = min(u_min_x, v_min_x)
        path_max_x = max(u_max_x, v_max_x)
        path_min_y = min(u_min_y, v_min_y)
        path_max_y = max(u_max_y, v_max_y)
        
        # 🔧 添加包围盒扩展以处理退化情况
        min_expansion = 10.0  # 最小扩展尺寸
        if path_max_x - path_min_x < min_expansion:
            center_x = (path_min_x + path_max_x) / 2
            path_min_x = center_x - min_expansion / 2
            path_max_x = center_x + min_expansion / 2
            
        if path_max_y - path_min_y < min_expansion:
            center_y = (path_min_y + path_max_y) / 2
            path_min_y = center_y - min_expansion / 2
            path_max_y = center_y + min_expansion / 2

        # 如果相交面积足够大，计入feedthrough
        # module_area = obstacle_module.width * obstacle_module.height
        module_area = (path_max_x - path_min_x) * (path_max_y - path_min_y)
        # threshold_area = module_area * 0.5
        overlap_area = 0.0
        overlap_num = 0
        # 🔧 **修复逻辑错误**: 检查路径是否穿越了其他网络的模块
        for obstacle_module in obstacle_modules:
            # 获取障碍模块的边界
            obstacle_min_x = obstacle_module.x
            obstacle_max_x = obstacle_module.x + obstacle_module.width
            obstacle_min_y = obstacle_module.y
            obstacle_max_y = obstacle_module.y + obstacle_module.height
            
            # 🔧 修复相交判断 - 使用矩形相交算法
            x_overlap = (obstacle_min_x < path_max_x) and (obstacle_max_x > path_min_x)
            y_overlap = (obstacle_min_y < path_max_y) and (obstacle_max_y > path_min_y)
            
            if x_overlap and y_overlap:
                # 🔧 改进计数策略 - 根据相交面积确定feedthrough强度
                overlap_x = min(obstacle_max_x, path_max_x) - max(obstacle_min_x, path_min_x)
                overlap_y = min(obstacle_max_y, path_max_y) - max(obstacle_min_y, path_min_y)
                overlap_area = overlap_area + overlap_x * overlap_y
                overlap_num = overlap_num + 1

        threshold = 0.4
        r = float(overlap_area) / module_area
        # beta = math.log(overlap_num + 1) / (1 - r)
        # if r > threshold:
        #     feedthrough_count = int((math.exp(beta *(r - threshold)) - 1) * overlap_num )   # 每个障碍模块计为1个feedthrough

        # beta = overlap_num / math.log(2 - threshold)
        # if r > threshold:
        #     feedthrough_count = int(beta * math.log(r - threshold + 1))   

        # alpha = (len(obstacle_modules) - overlap_num) * 0.05
        beta = overlap_num / (1 - threshold)
        if r > threshold:
            feedthrough_count = beta * (r - threshold)
        
        
        return feedthrough_count

# --- 方便调用的顶层函数 ---

def calculate_ftafp_feedthrough(design: FloorplanDesign) -> FTAFPResult:
    """
    使用FTAFP模型计算Feedthrough
    """
    estimator = FTAFPEstimator()
    return estimator.analyze(design)

# 导出
__all__ = ['FTAFPEstimator', 'FTAFPResult', 'SubNet', 'calculate_ftafp_feedthrough']
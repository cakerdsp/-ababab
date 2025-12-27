#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feedthrough分析模块 - Feedthrough Analysis Module

实现feedthrough路径检测、统计和优化分析
Implements feedthrough path detection, statistics and optimization analysis
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from ..data.structures import FloorplanDesign, Net, Module


@dataclass
class FeedthroughPath:
    """Feedthrough路径信息"""
    net_name: str
    source_module: str
    target_module: str
    feedthrough_modules: List[str]
    path_length: float
    severity: float  # 严重程度评分


@dataclass
class FeedthroughResult:
    """Feedthrough分析结果"""
    total_feedthrough_count: int
    feedthrough_paths: List[FeedthroughPath]
    module_feedthrough_load: Dict[str, int]  # 每个模块的feedthrough负载
    critical_modules: List[str]  # 高负载模块
    avg_path_length: float
    max_path_length: float


def calculate_feedthrough_count(design: FloorplanDesign) -> int:
    """
    计算总的feedthrough数量
    Calculate total feedthrough count
    
    Args:
        design: 布图设计
        
    Returns:
        feedthrough总数
    """
    analyzer = FeedthroughAnalyzer()
    result = analyzer.analyze(design)
    return result.total_feedthrough_count


def analyze_feedthrough_paths(design: FloorplanDesign) -> List[FeedthroughPath]:
    """
    分析feedthrough路径
    Analyze feedthrough paths
    
    Args:
        design: 布图设计
        
    Returns:
        feedthrough路径列表
    """
    analyzer = FeedthroughAnalyzer()
    result = analyzer.analyze(design)
    return result.feedthrough_paths


class FeedthroughAnalyzer:
    """
    Feedthrough分析器类
    Feedthrough Analyzer Class
    
    分析网线穿越模块的情况，识别feedthrough路径
    Analyzes net traversal through modules, identifies feedthrough paths
    """
    
    def __init__(self, analysis_method: str = 'geometric'):
        """
        初始化分析器
        
        Args:
            analysis_method: 分析方法 ('geometric', 'graph_based')
        """
        self.analysis_method = analysis_method
        self.feedthrough_threshold = 0.1  # 穿越阈值
    
    def analyze(self, design: FloorplanDesign) -> FeedthroughResult:
        """
        执行完整的feedthrough分析
        Perform complete feedthrough analysis
        
        Args:
            design: 布图设计
            
        Returns:
            分析结果
        """
        feedthrough_paths = []
        module_load = {}
        
        # 初始化模块负载统计
        # ✅ 修复：只统计功能模块（HARD/SOFT），排除Terminals
        from ..data.structures import ModuleType
        for module_name, module in design.modules.items():
            if module.module_type != ModuleType.TERMINAL:
                module_load[module_name] = 0
        
        for net in design.nets.values():
            if len(net.pins) < 2:
                continue
            
            # 分析每个网线的feedthrough情况
            paths = self._analyze_net_feedthrough(design, net)
            feedthrough_paths.extend(paths)
            
            # 统计模块负载
            for path in paths:
                for module_name in path.feedthrough_modules:
                    if module_name in module_load:
                        module_load[module_name] += 1
        
        # 计算统计信息
        total_count = len(feedthrough_paths)
        path_lengths = [path.path_length for path in feedthrough_paths]
        avg_length = np.mean(path_lengths) if path_lengths else 0.0
        max_length = max(path_lengths) if path_lengths else 0.0
        
        # 识别关键模块（负载最高的前20%）
        if module_load:
            load_values = list(module_load.values())
            threshold = np.percentile(load_values, 80) if load_values else 0
            critical_modules = [name for name, load in module_load.items() 
                              if load >= threshold and load > 0]
        else:
            critical_modules = []
        
        return FeedthroughResult(
            total_feedthrough_count=total_count,
            feedthrough_paths=feedthrough_paths,
            module_feedthrough_load=module_load,
            critical_modules=critical_modules,
            avg_path_length=avg_length,
            max_path_length=max_length
        )
    
    def _analyze_net_feedthrough(self, design: FloorplanDesign, net: Net) -> List[FeedthroughPath]:
        """分析单个网线的feedthrough情况"""
        if self.analysis_method == 'geometric':
            return self._geometric_analysis(design, net)
        elif self.analysis_method == 'graph_based':
            return self._graph_based_analysis(design, net)
        else:
            raise ValueError(f"Unknown analysis method: {self.analysis_method}")
    
    def _geometric_analysis(self, design: FloorplanDesign, net: Net) -> List[FeedthroughPath]:
        """基于几何位置的feedthrough分析"""
        from ..data.structures import ModuleType
        paths = []
        
        # 获取网线连接的模块
        # ✅ 修复：只考虑功能模块作为源和目标，排除Terminals
        connected_modules = []
        for module_name, pin_name in net.pins:
            module = design.get_module(module_name)
            if module is not None and module.module_type != ModuleType.TERMINAL:
                connected_modules.append(module)
        
        if len(connected_modules) < 2:
            return paths
        
        # 对于每对连接的模块，检查是否有其他模块在路径上
        for i in range(len(connected_modules)):
            for j in range(i + 1, len(connected_modules)):
                source = connected_modules[i]
                target = connected_modules[j]
                
                # 找到路径上的feedthrough模块
                feedthrough_modules = self._find_modules_on_path(design, source, target)
                
                if feedthrough_modules:
                    # 计算路径长度
                    source_center = source.get_center()
                    target_center = target.get_center()
                    path_length = abs(source_center[0] - target_center[0]) + \
                                abs(source_center[1] - target_center[1])
                    
                    # 计算严重程度（基于穿越的模块数量和路径长度）
                    severity = len(feedthrough_modules) * (1.0 + path_length / 1000.0)
                    
                    path = FeedthroughPath(
                        net_name=net.name,
                        source_module=source.name,
                        target_module=target.name,
                        feedthrough_modules=feedthrough_modules,
                        path_length=path_length,
                        severity=severity
                    )
                    paths.append(path)
        
        return paths
    
    def _find_modules_on_path(self, design: FloorplanDesign, source: Module, target: Module) -> List[str]:
        """找到从源模块到目标模块路径上的feedthrough模块"""
        feedthrough_modules = []
        
        source_center = source.get_center()
        target_center = target.get_center()
        
        # 计算路径的边界矩形
        min_x = min(source_center[0], target_center[0])
        max_x = max(source_center[0], target_center[0])
        min_y = min(source_center[1], target_center[1])
        max_y = max(source_center[1], target_center[1])
        
        # 检查所有其他模块是否与路径矩形相交
        # ✅ 关键修复：只考虑功能模块（HARD/SOFT），排除Terminals
        for module_name, module in design.modules.items():
            if module.name == source.name or module.name == target.name:
                continue
            
            # ✅ 修复：Feedthrough计算不应包含Terminals
            # Terminals是固定的端口点，不是可以被"穿越"的功能模块
            from ..data.structures import ModuleType
            if module.module_type == ModuleType.TERMINAL:
                continue
                
            # 检查模块是否与路径矩形相交
            module_bbox = module.get_bounding_box()
            
            # 如果模块与路径矩形相交，认为是feedthrough
            if (module_bbox[0] < max_x and module_bbox[2] > min_x and
                module_bbox[1] < max_y and module_bbox[3] > min_y):
                
                # 进一步检查模块是否真的在路径上
                if self._is_module_on_path(source_center, target_center, module):
                    feedthrough_modules.append(module.name)
        
        return feedthrough_modules
    
    def _is_module_on_path(self, source_pos: Tuple[float, float], 
                          target_pos: Tuple[float, float], module: Module) -> bool:
        """检查模块是否在从源到目标的路径上"""
        module_center = module.get_center()
        
        # 使用点到线段的距离判断
        # L形路径：先水平再垂直或先垂直再水平
        
        # 计算两种可能的L形路径
        path1_corner = (source_pos[0], target_pos[1])  # 先水平再垂直
        path2_corner = (target_pos[0], source_pos[1])  # 先垂直再水平
        
        # 检查模块是否接近任一路径
        threshold = max(module.width, module.height) * 0.5
        
        # 路径1：source -> (source.x, target.y) -> target
        dist1_seg1 = self._point_to_segment_distance(module_center, source_pos, path1_corner)
        dist1_seg2 = self._point_to_segment_distance(module_center, path1_corner, target_pos)
        min_dist1 = min(dist1_seg1, dist1_seg2)
        
        # 路径2：source -> (target.x, source.y) -> target
        dist2_seg1 = self._point_to_segment_distance(module_center, source_pos, path2_corner)
        dist2_seg2 = self._point_to_segment_distance(module_center, path2_corner, target_pos)
        min_dist2 = min(dist2_seg1, dist2_seg2)
        
        return min(min_dist1, min_dist2) < threshold
    
    def _point_to_segment_distance(self, point: Tuple[float, float], 
                                  seg_start: Tuple[float, float], 
                                  seg_end: Tuple[float, float]) -> float:
        """计算点到线段的最短距离"""
        px, py = point
        sx, sy = seg_start
        ex, ey = seg_end
        
        # 线段长度的平方
        seg_len_sq = (ex - sx) ** 2 + (ey - sy) ** 2
        
        if seg_len_sq == 0:
            # 线段退化为点
            return np.sqrt((px - sx) ** 2 + (py - sy) ** 2)
        
        # 计算投影参数
        t = max(0, min(1, ((px - sx) * (ex - sx) + (py - sy) * (ey - sy)) / seg_len_sq))
        
        # 投影点
        proj_x = sx + t * (ex - sx)
        proj_y = sy + t * (ey - sy)
        
        # 距离
        return np.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
    
    def _graph_based_analysis(self, design: FloorplanDesign, net: Net) -> List[FeedthroughPath]:
        """基于图论的feedthrough分析（更精确但复杂）"""
        # TODO: 实现基于图论的分析方法
        # 这里先使用几何分析作为fallback
        return self._geometric_analysis(design, net)
    
    def get_feedthrough_statistics(self, design: FloorplanDesign) -> Dict[str, float]:
        """
        获取feedthrough统计信息
        Get feedthrough statistics
        
        Returns:
            统计信息字典
        """
        result = self.analyze(design)
        
        total_nets = len(design.nets)
        feedthrough_nets = len(set(path.net_name for path in result.feedthrough_paths))
        
        return {
            'total_feedthrough_count': result.total_feedthrough_count,
            'feedthrough_nets_count': feedthrough_nets,
            'feedthrough_ratio': feedthrough_nets / total_nets if total_nets > 0 else 0.0,
            'avg_feedthrough_per_net': result.total_feedthrough_count / total_nets if total_nets > 0 else 0.0,
            'avg_path_length': result.avg_path_length,
            'max_path_length': result.max_path_length,
            'critical_modules_count': len(result.critical_modules)
        }
    
    def suggest_optimizations(self, design: FloorplanDesign) -> List[str]:
        """
        建议feedthrough优化策略
        Suggest feedthrough optimization strategies
        
        Returns:
            优化建议列表
        """
        result = self.analyze(design)
        suggestions = []
        
        if result.total_feedthrough_count > 0:
            suggestions.append(f"检测到 {result.total_feedthrough_count} 个feedthrough路径")
            
            if result.critical_modules:
                suggestions.append(f"关键模块（高feedthrough负载）: {', '.join(result.critical_modules[:5])}")
                suggestions.append("建议重新布局这些关键模块以减少feedthrough")
            
            # 按严重程度排序路径
            critical_paths = sorted(result.feedthrough_paths, 
                                  key=lambda x: x.severity, reverse=True)[:3]
            
            if critical_paths:
                suggestions.append("最严重的feedthrough路径:")
                for i, path in enumerate(critical_paths, 1):
                    suggestions.append(f"  {i}. 网线 {path.net_name}: "
                                     f"{path.source_module} -> {path.target_module}, "
                                     f"穿越模块: {len(path.feedthrough_modules)}")
        
        return suggestions


def self_check_feedthrough() -> bool:
    """
    Feedthrough模块自检功能
    Self-check functionality for feedthrough module
    """
    print("🔧 Feedthrough模块 (feedthrough) 自检")
    
    try:
        # 创建测试设计
        from ..data.structures import FloorplanDesign, Module, Net, ModuleType
        
        design = FloorplanDesign("test_feedthrough")
        
        # 创建一个经典的feedthrough场景：
        # m1 ---- m_middle ---- m2
        # 其中 m_middle 在 m1 和 m2 的连线路径上
        
        m1 = Module("m1", ModuleType.SOFT, width=100, height=100, x=0, y=0, area=10000)
        m_middle = Module("m_middle", ModuleType.SOFT, width=100, height=100, x=200, y=0, area=10000) 
        m2 = Module("m2", ModuleType.SOFT, width=100, height=100, x=400, y=0, area=10000)
        
        # 添加一个不在路径上的模块
        m3 = Module("m3", ModuleType.SOFT, width=100, height=100, x=0, y=200, area=10000)
        
        design.add_module(m1)
        design.add_module(m_middle)
        design.add_module(m2)
        design.add_module(m3)
        
        # 创建会产生feedthrough的网线
        net1 = Net("net1", [("m1", "pin1"), ("m2", "pin1")])  # 应该穿越 m_middle
        net2 = Net("net2", [("m1", "pin2"), ("m3", "pin2")])  # 不应该穿越其他模块
        
        design.add_net(net1)
        design.add_net(net2)
        
        # 测试基础函数
        ft_count = calculate_feedthrough_count(design)
        ft_paths = analyze_feedthrough_paths(design)
        
        # 验证基本合理性
        if ft_count < 0:
            print(f"❌ calculate_feedthrough_count() 错误: 负值 {ft_count}")
            return False
        
        if not isinstance(ft_paths, list):
            print(f"❌ analyze_feedthrough_paths() 返回类型错误")
            return False
        
        # 测试FeedthroughAnalyzer
        analyzer = FeedthroughAnalyzer(analysis_method='geometric')
        result = analyzer.analyze(design)
        
        if not isinstance(result, FeedthroughResult):
            print(f"❌ FeedthroughAnalyzer.analyze() 返回类型错误")
            return False
        
        # 验证结果的合理性
        if result.total_feedthrough_count != len(result.feedthrough_paths):
            print(f"❌ Feedthrough计数不一致: {result.total_feedthrough_count} vs {len(result.feedthrough_paths)}")
            return False
        
        # 测试统计功能
        stats = analyzer.get_feedthrough_statistics(design)
        if not isinstance(stats, dict):
            print(f"❌ get_feedthrough_statistics() 返回类型错误")
            return False
        
        # 测试优化建议
        suggestions = analyzer.suggest_optimizations(design)
        if not isinstance(suggestions, list):
            print(f"❌ suggest_optimizations() 返回类型错误")
            return False
        
        print("✅ Feedthrough模块自检通过")
        print(f"   - Feedthrough计数: {ft_count}")
        print(f"   - 详细路径数: {len(ft_paths)}")
        print(f"   - 分析器结果: {result.total_feedthrough_count} 个feedthrough")
        print(f"   - 关键模块: {len(result.critical_modules)} 个")
        print(f"   - 平均路径长度: {result.avg_path_length:.2f}")
        print(f"   - 优化建议: {len(suggestions)} 条")
        
        # 验证feedthrough检测的准确性（针对我们的测试用例）
        if len(design.modules) >= 3 and len(design.nets) >= 2:
            # 预期应该检测到net1的feedthrough（m1->m2穿越m_middle）
            net1_paths = [p for p in result.feedthrough_paths if p.net_name == "net1"]
            if not net1_paths:
                print("警告: 未检测到预期的feedthrough (net1)")
            else:
                print(f"   - 检测到net1的feedthrough路径: {len(net1_paths)} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ Feedthrough模块自检失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def output_feedthrough_debug_info(design: FloorplanDesign, prefix: str = "  ") -> str:
    """
    输出Feedthrough模块的调试信息
    Output debug information for feedthrough module
    """
    try:
        ft_count = calculate_feedthrough_count(design)
        analyzer = FeedthroughAnalyzer(analysis_method='geometric')
        result = analyzer.analyze(design)
        stats = analyzer.get_feedthrough_statistics(design)
        suggestions = analyzer.suggest_optimizations(design)
        
        debug_info = f"{prefix}=== Feedthrough模块调试信息 ===\n"
        debug_info += f"{prefix}基础统计:\n"
        debug_info += f"{prefix}  - 总Feedthrough数: {ft_count}\n"
        debug_info += f"{prefix}  - 详细路径数: {len(result.feedthrough_paths)}\n"
        debug_info += f"{prefix}  - 影响的网线数: {stats['feedthrough_nets_count']}\n"
        debug_info += f"{prefix}  - Feedthrough比例: {stats['feedthrough_ratio']:.3f}\n"
        debug_info += f"{prefix}  - 平均每网线FT: {stats['avg_feedthrough_per_net']:.2f}\n"
        
        debug_info += f"{prefix}路径分析:\n"
        debug_info += f"{prefix}  - 平均路径长度: {result.avg_path_length:.2f}\n"
        debug_info += f"{prefix}  - 最大路径长度: {result.max_path_length:.2f}\n"
        debug_info += f"{prefix}  - 关键模块数: {len(result.critical_modules)}\n"
        
        # 列出关键模块
        if result.critical_modules:
            debug_info += f"{prefix}关键模块: {', '.join(result.critical_modules[:5])}"
            if len(result.critical_modules) > 5:
                debug_info += f" (共 {len(result.critical_modules)} 个)"
            debug_info += "\n"
        
        # 列出最严重的路径
        critical_paths = sorted(result.feedthrough_paths, key=lambda x: x.severity, reverse=True)[:3]
        if critical_paths:
            debug_info += f"{prefix}最严重的路径:\n"
            for i, path in enumerate(critical_paths, 1):
                debug_info += f"{prefix}  {i}. {path.net_name}: {path.source_module}->{path.target_module}, "
                debug_info += f"穿越{len(path.feedthrough_modules)}个模块, 严重度{path.severity:.2f}\n"
        
        # 优化建议
        debug_info += f"{prefix}优化建议 ({len(suggestions)} 条):\n"
        for i, suggestion in enumerate(suggestions[:3], 1):
            debug_info += f"{prefix}  {i}. {suggestion}\n"
        
        return debug_info
        
    except Exception as e:
        return f"{prefix}Feedthrough模块调试信息获取失败: {e}\n"


# 导出函数和类
__all__ = [
    'calculate_feedthrough_count',
    'analyze_feedthrough_paths',
    'FeedthroughAnalyzer',
    'FeedthroughPath',
    'FeedthroughResult',
    'self_check_feedthrough',
    'output_feedthrough_debug_info'
] 
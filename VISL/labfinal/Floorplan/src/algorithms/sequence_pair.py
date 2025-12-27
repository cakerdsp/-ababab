#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
序列对表示法 - Sequence Pair Representation

经典的布图拓扑表示方法，使用两个序列来表示模块的相对位置关系
Classic floorplan topology representation using two sequences to represent relative positions of modules
"""

import numpy as np
import random
import math
from typing import List, Tuple, Dict, Any
import copy
from dataclasses import dataclass

try:
    from .base import RepresentationMethod
    from ..data.structures import FloorplanDesign, Module, ModuleType
    from ..evaluation.legality import ComprehensiveLegalityChecker, LegalityConstraints
except ImportError:
    from algorithms.base import RepresentationMethod
    from data.structures import FloorplanDesign, Module, ModuleType
    from evaluation.legality import ComprehensiveLegalityChecker, LegalityConstraints


@dataclass
class SequencePairSolution:
    """序列对解结构"""
    positive_sequence: List[int]    # 正序列
    negative_sequence: List[int]    # 负序列
    module_list: List[Module]       # 模块列表


class SequencePair(RepresentationMethod):
    """
    序列对表示法 - Sequence Pair Representation
    
    使用两个模块序列(Γ+, Γ-)来表示布图的拓扑结构
    Uses two module sequences (Γ+, Γ-) to represent floorplan topology
    
    参考文献:
    Murata, H., et al. "Rectangle-packing-based module placement." 
    ICCAD 1995.
    """
    
    def __init__(self, zero_tolerance: bool = True, verbose: bool = True):
        super().__init__("SequencePair")
        self.modules = []        # 可移动模块列表
        self.module_map = {}     # 模块名到索引的映射
        self.fixed_modules = {}  # 固定模块
        self.zero_tolerance = zero_tolerance
        self.verbose = verbose
        
        # 🔧 **统一合法性检查**: 使用专业的legality.py系统
        legality_constraints = LegalityConstraints(
            enable_overlap_check=True,
            enable_boundary_check=True,
            enable_spacing_check=False,
            enable_alignment_check=False,
            enable_keepout_check=False,
            overlap_penalty_weight=10000.0,
            boundary_penalty_weight=1000.0
        )
        self.legality_checker = ComprehensiveLegalityChecker(legality_constraints)
        
        # 解码统计
        self.decode_attempts = 0
        self.legal_decodes = 0
        
    def initialize(self, design: FloorplanDesign) -> Tuple[List[int], List[int]]:
        """
        初始化序列对表示
        
        Args:
            design: 布图设计
            
        Returns:
            初始序列对 (Γ+, Γ-)
        """
        # 🔧 **CRITICAL FIX**: 保存原始设计引用，以便在decode时复制网络信息
        self.original_design = design
        
        # 提取可移动模块
        movable_modules = design.get_movable_modules()
        self.modules = list(movable_modules.values())
        self.module_map = {module.name: i for i, module in enumerate(self.modules)}
        
        # 保存固定模块信息
        self.fixed_modules = design.get_fixed_modules()
        
        # 初始化随机序列对
        n = len(self.modules)
        gamma_plus = list(range(n))
        gamma_minus = list(range(n))
        
        random.shuffle(gamma_plus)
        random.shuffle(gamma_minus)
        
        return (gamma_plus, gamma_minus)
    
    def random_solution(self) -> Tuple[List[int], List[int]]:
        """
        生成随机序列对解
        
        Returns:
            随机序列对 (Γ+, Γ-)
        """
        n = len(self.modules)
        gamma_plus = list(range(n))
        gamma_minus = list(range(n))
        
        random.shuffle(gamma_plus)
        random.shuffle(gamma_minus)
        
        return (gamma_plus, gamma_minus)
    
    def decode(self, representation: Tuple[List[int], List[int]]) -> FloorplanDesign:
        """解码序列对为布图设计 - 支持软模块迭代优化"""
        self.decode_attempts += 1
        
        gamma_plus, gamma_minus = representation
        
        # 使用迭代优化处理软模块
        design = self._iterative_soft_module_optimization(gamma_plus, gamma_minus)
        
        # 统一零容忍检查
        if design.chip_width > 0 and design.chip_height > 0:
            self.legality_checker.constraints.chip_boundary = (0, 0, design.chip_width, design.chip_height)
        
        legality_result = self.legality_checker.check_legality(design)
        
        if not legality_result.is_legal:
            return design  # 返回原始设计，让算法决定如何处理
        else:
            self.legal_decodes += 1
        
        return design
    
    def _iterative_soft_module_optimization(self, gamma_plus: List[int], gamma_minus: List[int]) -> FloorplanDesign:
        """
        迭代软模块优化算法
        Iterative soft module optimization algorithm
        
        解决序列对中"形状依赖位置，位置依赖形状"的循环依赖问题
        Solves the circular dependency problem in sequence pair soft module optimization
        
        Args:
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            优化后的布图设计
        """
        n = len(self.modules)
        max_iterations = 10  # 最大迭代次数
        convergence_threshold = 0.01  # 收敛阈值
        
        # 第1步：给所有软模块合理的初始形状
        original_sizes = {}  # 保存原始尺寸
        for i, module in enumerate(self.modules):
            original_sizes[i] = (module.width, module.height)
            
            if module.module_type == ModuleType.SOFT:
                # 🔧 修复：给软模块设置合理的初始形状，而不是强制正方形
                min_ratio = getattr(module, 'min_aspect_ratio', 0.5)
                max_ratio = getattr(module, 'max_aspect_ratio', 2.0)
                area = getattr(module, 'area', module.width * module.height)
                
                # 选择在允许范围内的初始长宽比（接近1.0但在范围内）
                target_ratio = max(min_ratio, min(max_ratio, 1.0))
                
                # 计算对应尺寸
                initial_width = math.sqrt(area * target_ratio)
                initial_height = area / initial_width
                
                # 确保在约束范围内
                if min_ratio <= initial_width / initial_height <= max_ratio:
                    module.set_size(initial_width, initial_height)
                else:
                    # 如果计算有误，使用边界值
                    if target_ratio == min_ratio:
                        width = math.sqrt(area * min_ratio)
                        height = area / width
                    else:  # target_ratio == max_ratio
                        width = math.sqrt(area * max_ratio)
                        height = area / width
                    module.set_size(width, height)
        
        best_design = None
        best_area = float('inf')
        prev_area = float('inf')
        
        # 第2步：迭代优化循环
        for iteration in range(max_iterations):
            # 2a. 基于当前形状进行完整解码
            current_design = self._decode_with_current_shapes(gamma_plus, gamma_minus)
            
            # 🔧 **统一零容忍检查**: 使用ComprehensiveLegalityChecker
            if self.zero_tolerance:
                # 设置芯片边界
                if current_design.chip_width > 0 and current_design.chip_height > 0:
                    self.legality_checker.constraints.chip_boundary = (0, 0, current_design.chip_width, current_design.chip_height)
                
                legality_result = self.legality_checker.check_legality(current_design)
                if not legality_result.is_legal:
                    if self.verbose:
                        print(f"警告：序列对解码发现 {legality_result.total_violations} 个违规")
                        print(f"重叠违规: {legality_result.overlap_violations}, 边界违规: {legality_result.boundary_violations}")
                # 注意：不再执行修复，让算法层面处理不合法的解
            
            # 2b. 分析布局特性
            layout_stats = self._analyze_layout_characteristics(current_design, gamma_plus, gamma_minus)
            
            # 2c. 记录最优解（只有无重叠的解才被考虑）
            current_area = layout_stats['total_area']
            # 计算重叠数量
            legality_result = self.legality_checker.check_legality(current_design)
            overlap_count = legality_result.overlap_violations
            
            if overlap_count == 0 and current_area < best_area:  # 零容忍：只接受无重叠解
                best_area = current_area
                best_design = current_design
            
            # 2d. 检查收敛
            if abs(prev_area - current_area) / max(prev_area, 1.0) < convergence_threshold:
                break
            
            prev_area = current_area
            
            # 2e. 智能调整软模块形状
            if iteration < max_iterations - 1:  # 不在最后一次迭代时调整
                self._adjust_soft_module_shapes(layout_stats, iteration, max_iterations)
        
        # 恢复硬模块的原始尺寸（如果有误改）
        for i, module in enumerate(self.modules):
            if module.module_type != ModuleType.SOFT:
                orig_w, orig_h = original_sizes[i]
                module.set_size(orig_w, orig_h)
        
        # 🔧 **FINAL ZERO TOLERANCE CHECK**: 确保最终解绝对无重叠
        final_design = best_design if best_design else self._decode_with_current_shapes(gamma_plus, gamma_minus)
        final_design = self._enforce_no_overlap(final_design, gamma_plus, gamma_minus)
        
                # 验证最终结果
        # 计算最终重叠数量
        final_legality_result = self.legality_checker.check_legality(final_design)
        final_overlap_count = final_legality_result.overlap_violations
        if final_overlap_count > 0:
            print(f"警告：最终解仍有 {final_overlap_count} 个重叠违规，执行强制修复...")
            final_design = self._force_remove_all_overlaps(final_design)
        
        return final_design
    
    def _decode_with_current_shapes(self, gamma_plus: List[int], gamma_minus: List[int]) -> FloorplanDesign:
        """
        基于当前模块形状进行标准解码
        Standard decoding based on current module shapes
        """
        n = len(self.modules)
        
        # 构建约束关系（基于当前模块尺寸）
        h_constraints = self._build_horizontal_constraints(gamma_plus, gamma_minus)
        v_constraints = self._build_vertical_constraints(gamma_plus, gamma_minus)
        
        # 计算模块坐标
        x_coords = self._longest_path_algorithm(h_constraints, n, 'x')
        y_coords = self._longest_path_algorithm(v_constraints, n, 'y')
        
        # 创建设计对象
        design = FloorplanDesign(name="decoded")
        
        # 🔧 **CRITICAL FIX**: 复制原始设计的网络信息和其他重要属性
        if hasattr(self, 'original_design') and self.original_design:
            # 复制芯片尺寸
            design.chip_width = self.original_design.chip_width
            design.chip_height = self.original_design.chip_height
            
            # 🔧 **KEY FIX**: 复制所有网络信息
            for net_name, net in self.original_design.nets.items():
                design.nets[net_name] = net
        
        # 添加模块
        for i, module in enumerate(self.modules):
            new_module = module.clone()
            new_module.set_position(x_coords[i], y_coords[i])
            
            # 🔧 修复：确保软模块的面积约束和长宽比约束被正确维护
            if new_module.module_type == ModuleType.SOFT:
                current_area = new_module.width * new_module.height
                expected_area = getattr(new_module, 'area', current_area)
                
                # 如果面积不匹配，调整尺寸
                if abs(current_area - expected_area) > 1.0:
                    min_ratio = getattr(new_module, 'min_aspect_ratio', 0.5)
                    max_ratio = getattr(new_module, 'max_aspect_ratio', 2.0)
                    
                    # 保持当前长宽比（如果在允许范围内），否则调整到边界
                    current_ratio = new_module.width / new_module.height if new_module.height > 0 else 1.0
                    
                    if min_ratio <= current_ratio <= max_ratio:
                        # 当前比例合法，按面积缩放
                        scale_factor = math.sqrt(expected_area / current_area)
                        new_width = new_module.width * scale_factor
                        new_height = new_module.height * scale_factor
                    else:
                        # 当前比例不合法，使用目标比例
                        target_ratio = max(min_ratio, min(max_ratio, 1.0))
                        new_width = math.sqrt(expected_area * target_ratio)
                        new_height = expected_area / new_width
                    
                    new_module.set_size(new_width, new_height)
            
            design.add_module(new_module)
        
        # 添加固定模块
        for fixed_module in self.fixed_modules.values():
            design.add_module(fixed_module)
        
        # 🔧 **CRITICAL FIX**: 保持宏模块在原来的位置，不移动到原点
        if design.modules:
            # 只计算宏模块的边界框
            macro_modules = [m for m in design.modules.values() if m.module_type.name != 'TERMINAL']
            
            if macro_modules:
                # 计算宏模块的实际边界框
                min_x = min(module.x for module in macro_modules)
                min_y = min(module.y for module in macro_modules)
                max_x = max(module.x + module.width for module in macro_modules)
                max_y = max(module.y + module.height for module in macro_modules)
            
                # 设置芯片尺寸为实际布局的边界框尺寸
                design.chip_width = max_x
                design.chip_height = max_y
            else:
                # 没有宏模块时设置默认尺寸
                design.chip_width = 100.0
                design.chip_height = 100.0
        
        return design
    
    def _analyze_layout_characteristics(self, design: FloorplanDesign, 
                                      gamma_plus: List[int], gamma_minus: List[int]) -> Dict[str, Any]:
        """
        分析布局特性
        Analyze layout characteristics
        
        Args:
            design: 当前布局设计
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            布局特性统计
        """
        # 计算总边界框
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        soft_modules_info = []
        
        for module in design.modules.values():
            min_x = min(min_x, module.x)
            min_y = min(min_y, module.y)
            max_x = max(max_x, module.x + module.width)
            max_y = max(max_y, module.y + module.height)
            
            if module.module_type == ModuleType.SOFT:
                soft_modules_info.append({
                    'module': module,
                    'current_ratio': module.width / module.height if module.height > 0 else 1.0,
                    'min_ratio': getattr(module, 'min_aspect_ratio', 0.5),
                    'max_ratio': getattr(module, 'max_aspect_ratio', 2.0),
                    'area': getattr(module, 'area', module.width * module.height)
                })
        
        total_width = max_x - min_x
        total_height = max_y - min_y
        total_area = total_width * total_height
        layout_ratio = total_width / total_height if total_height > 0 else 1.0
        
        return {
            'total_width': total_width,
            'total_height': total_height,
            'total_area': total_area,
            'layout_ratio': layout_ratio,
            'soft_modules': soft_modules_info,
            'bbox': (min_x, min_y, max_x, max_y)
        }
    
    def _adjust_soft_module_shapes(self, layout_stats: Dict[str, Any], 
                                 iteration: int, max_iterations: int):
        """
        智能调整软模块形状
        Intelligently adjust soft module shapes
        
        根据布局分析结果，智能地调整软模块形状以改善总体布局
        
        Args:
            layout_stats: 布局特性统计
            iteration: 当前迭代次数
            max_iterations: 最大迭代次数
        """
        layout_ratio = layout_stats['layout_ratio']
        soft_modules = layout_stats['soft_modules']
        
        if not soft_modules:
            return
        
        # 策略：根据布局的长宽比来调整软模块
        target_layout_ratio = 1.0  # 目标：尽量接近正方形布局
        
        # 计算调整力度（随迭代递减）
        adjustment_factor = 0.3 * (1.0 - iteration / max_iterations)
        
        if layout_ratio > 1.2:  # 布局太宽，需要变高
            # 让一些软模块变得更"瘦高"
            for soft_info in soft_modules:
                module = soft_info['module']
                current_ratio = soft_info['current_ratio']
                min_ratio = soft_info['min_ratio']
                max_ratio = soft_info['max_ratio']
                area = soft_info['area']
                
                # 倾向于减小长宽比（变瘦高）
                new_ratio = max(min_ratio, current_ratio * (1.0 - adjustment_factor))
                
                # 计算新尺寸
                new_width = math.sqrt(area * new_ratio)
                new_height = area / new_width
                
                module.set_size(new_width, new_height)
        
        elif layout_ratio < 0.8:  # 布局太高，需要变宽
            # 让一些软模块变得更"扁平"
            for soft_info in soft_modules:
                module = soft_info['module']
                current_ratio = soft_info['current_ratio']
                min_ratio = soft_info['min_ratio']
                max_ratio = soft_info['max_ratio']
                area = soft_info['area']
                
                # 倾向于增大长宽比（变扁平）
                new_ratio = min(max_ratio, current_ratio * (1.0 + adjustment_factor))
                
                # 计算新尺寸
                new_width = math.sqrt(area * new_ratio)
                new_height = area / new_width
                
                module.set_size(new_width, new_height)
        
        else:
            # 布局比例较好，进行细微优化
            # 随机选择一些软模块进行小幅调整，探索更好的解
            import random
            num_to_adjust = max(1, len(soft_modules) // 3)
            modules_to_adjust = random.sample(soft_modules, num_to_adjust)
            
            for soft_info in modules_to_adjust:
                module = soft_info['module']
                current_ratio = soft_info['current_ratio']
                min_ratio = soft_info['min_ratio']
                max_ratio = soft_info['max_ratio']
                area = soft_info['area']
                
                # 小幅随机调整
                ratio_range = max_ratio - min_ratio
                random_adjustment = (random.random() - 0.5) * adjustment_factor * ratio_range
                new_ratio = max(min_ratio, min(max_ratio, current_ratio + random_adjustment))
                
                # 计算新尺寸
                new_width = math.sqrt(area * new_ratio)
                new_height = area / new_width
                
                module.set_size(new_width, new_height)
    
    def _optimize_soft_module_shape(self, module: Module, h_constraints: List[List[Tuple[int, float]]], 
                                   v_constraints: List[List[Tuple[int, float]]], module_index: int):
        """
        优化软模块的形状
        Optimize soft module shape
        
        Args:
            module: 软模块
            h_constraints: 水平约束
            v_constraints: 垂直约束
            module_index: 模块在列表中的索引
        """
        try:
            from ..data.structures import ModuleType
        except ImportError:
            from data.structures import ModuleType
        
        if module.module_type != ModuleType.SOFT:
            return
        
        # 计算可用空间约束（基于约束图分析）
        available_width, available_height = self._calculate_available_space_from_constraints(
            module_index, h_constraints, v_constraints
        )
        
        # 如果没有有效约束，使用模块面积的合理估算
        if available_width <= 0:
            available_width = float('inf')
        if available_height <= 0:
            available_height = float('inf')
        
        # 寻找在约束范围内的最优长宽比
        optimal_width, optimal_height = self._find_optimal_dimensions(
            module.area, 
            module.min_aspect_ratio, 
            module.max_aspect_ratio,
            available_width,
            available_height
        )
        
        # 更新模块尺寸
        module.set_size(optimal_width, optimal_height)
    
    def _calculate_available_space_from_constraints(self, module_index: int, 
                                                  h_constraints: List[List[Tuple[int, float]]], 
                                                  v_constraints: List[List[Tuple[int, float]]]) -> Tuple[float, float]:
        """
        基于约束图计算模块的可用空间
        Calculate available space for module based on constraint graph
        
        Args:
            module_index: 模块索引
            h_constraints: 水平约束图
            v_constraints: 垂直约束图
            
        Returns:
            (available_width, available_height)
        """
        # 计算水平方向的约束
        available_width = self._calculate_horizontal_space(module_index, h_constraints)
        
        # 计算垂直方向的约束
        available_height = self._calculate_vertical_space(module_index, v_constraints)
        
        return available_width, available_height
    
    def _calculate_horizontal_space(self, module_index: int, 
                                  h_constraints: List[List[Tuple[int, float]]]) -> float:
        """
        计算水平方向的可用空间
        Calculate available horizontal space
        
        在序列对中，水平约束表示：如果模块i约束模块j，则模块i在模块j的左侧
        约束图中的边权重是模块i的宽度，表示模块j必须至少在模块i右侧width距离处
        """
        # 查找所有被当前模块约束的模块（即当前模块左侧的所有模块）
        min_right_boundary = 0.0
        
        # 遍历所有模块，找出约束当前模块的模块
        for i, constraints_from_i in enumerate(h_constraints):
            for constrained_module, width in constraints_from_i:
                if constrained_module == module_index:
                    # 模块i约束当前模块，当前模块必须在模块i右侧
                    # 这里width是模块i的宽度
                    min_right_boundary = max(min_right_boundary, width)
        
        # 查找当前模块约束的其他模块，估算右侧空间
        max_right_boundary = float('inf')
        
        # 如果当前模块约束了其他模块，这些模块给出了右边界的线索
        for constrained_module, current_width in h_constraints[module_index]:
            # 当前模块约束了constrained_module
            # 这意味着constrained_module在当前模块右侧
            # 我们可以基于布图的总体尺寸来估算可用空间
            # 这里进行保守估算
            if max_right_boundary == float('inf'):
                max_right_boundary = 300.0  # 保守的右边界估算
        
        # 计算可用宽度
        if max_right_boundary == float('inf'):
            return float('inf')  # 没有右侧约束
        else:
            available = max_right_boundary - min_right_boundary
            return max(0.0, available)
    
    def _calculate_vertical_space(self, module_index: int, 
                                v_constraints: List[List[Tuple[int, float]]]) -> float:
        """
        计算垂直方向的可用空间
        Calculate available vertical space
        
        在序列对中，垂直约束表示：如果模块i约束模块j，则模块i在模块j的下方
        """
        # 查找所有约束当前模块的模块（即当前模块下方的所有模块）
        min_top_boundary = 0.0
        
        # 遍历所有模块，找出约束当前模块的模块
        for i, constraints_from_i in enumerate(v_constraints):
            for constrained_module, height in constraints_from_i:
                if constrained_module == module_index:
                    # 模块i约束当前模块，当前模块必须在模块i上方
                    min_top_boundary = max(min_top_boundary, height)
        
        # 查找当前模块约束的其他模块，估算上方空间
        max_top_boundary = float('inf')
        
        # 如果当前模块约束了其他模块，这些模块给出了上边界的线索
        for constrained_module, current_height in v_constraints[module_index]:
            # 当前模块约束了constrained_module
            # 进行保守估算
            if max_top_boundary == float('inf'):
                max_top_boundary = 300.0  # 保守的上边界估算
        
        # 计算可用高度
        if max_top_boundary == float('inf'):
            return float('inf')  # 没有上方约束
        else:
            available = max_top_boundary - min_top_boundary
            return max(0.0, available)
    
    def _find_optimal_dimensions(self, area: float, min_ratio: float, max_ratio: float,
                               max_width: float, max_height: float) -> Tuple[float, float]:
        """
        在约束范围内寻找最优尺寸
        Find optimal dimensions within constraints
        
        Args:
            area: 模块面积
            min_ratio: 最小长宽比
            max_ratio: 最大长宽比
            max_width: 最大宽度约束
            max_height: 最大高度约束
            
        Returns:
            (optimal_width, optimal_height)
        """
        # 目标长宽比（在允许范围内尽量接近1:1）
        target_ratio = max(min_ratio, min(max_ratio, 1.0))
        
        # 计算理想尺寸
        ideal_width = math.sqrt(area * target_ratio)
        ideal_height = area / ideal_width
        
        # 检查约束并调整
        if ideal_width <= max_width and ideal_height <= max_height:
            return ideal_width, ideal_height
        
        # 如果理想尺寸超出约束，寻找最佳可行解
        candidates = []
        
        # 策略1：固定宽度为最大允许值
        if max_width < float('inf'):
            width = max_width
            height = area / width
            ratio = width / height
            if min_ratio <= ratio <= max_ratio and height <= max_height:
                candidates.append((width, height, abs(ratio - target_ratio)))
        
        # 策略2：固定高度为最大允许值
        if max_height < float('inf'):
            height = max_height
            width = area / height
            ratio = width / height
            if min_ratio <= ratio <= max_ratio and width <= max_width:
                candidates.append((width, height, abs(ratio - target_ratio)))
        
        # 策略3：使用长宽比边界值
        for ratio in [min_ratio, max_ratio]:
            width = math.sqrt(area * ratio)
            height = area / width
            if width <= max_width and height <= max_height:
                candidates.append((width, height, abs(ratio - target_ratio)))
        
        # 选择最接近目标长宽比的候选解
        if candidates:
            best_candidate = min(candidates, key=lambda x: x[2])
            return best_candidate[0], best_candidate[1]
        
        # 如果没有可行解，返回当前尺寸（保持原状）
        current_width = math.sqrt(area * target_ratio)
        current_height = area / current_width
        return current_width, current_height
    
    def _build_horizontal_constraints(self, gamma_plus: List[int], gamma_minus: List[int]) -> List[List[Tuple[int, float]]]:
        """
        构建水平约束图
        
        如果模块i在Γ+中出现在模块j之前，且在Γ-中也出现在模块j之前，
        则模块i在模块j的左边
        
        Args:
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            邻接表表示的约束图，每个边包含权重（模块宽度）
        """
        n = len(self.modules)
        constraints = [[] for _ in range(n)]
        
        # 计算在每个序列中的位置
        pos_plus = {module_id: pos for pos, module_id in enumerate(gamma_plus)}
        pos_minus = {module_id: pos for pos, module_id in enumerate(gamma_minus)}
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # 检查水平约束条件
                    if (pos_plus[i] < pos_plus[j] and pos_minus[i] < pos_minus[j]):
                        # 模块i在模块j的左边
                        width_i = self.modules[i].width
                        constraints[i].append((j, width_i))
        
        return constraints
    
    def _build_vertical_constraints(self, gamma_plus: List[int], gamma_minus: List[int]) -> List[List[Tuple[int, float]]]:
        """
        构建垂直约束图
        
        如果模块i在Γ+中出现在模块j之前，但在Γ-中出现在模块j之后，
        则模块i在模块j的下面
        
        Args:
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            邻接表表示的约束图，每个边包含权重（模块高度）  
        """
        n = len(self.modules)
        constraints = [[] for _ in range(n)]
        
        # 计算在每个序列中的位置
        pos_plus = {module_id: pos for pos, module_id in enumerate(gamma_plus)}
        pos_minus = {module_id: pos for pos, module_id in enumerate(gamma_minus)}
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # 检查垂直约束条件
                    if (pos_plus[i] < pos_plus[j] and pos_minus[i] > pos_minus[j]):
                        # 模块i在模块j的下面
                        height_i = self.modules[i].height
                        constraints[i].append((j, height_i))
        
        return constraints
    
    def _longest_path_algorithm(self, constraints: List[List[Tuple[int, float]]], n: int, coord_type: str) -> List[float]:
        """
        使用正确的最长路径算法计算坐标
        
        🔧 修复：使用拓扑排序 + 动态规划实现正确的最长路径算法
        
        Args:
            constraints: 约束图 (邻接表)
            n: 模块数量
            coord_type: 坐标类型 ('x' 或 'y')
            
        Returns:
            各模块的坐标值
        """
        # 初始化距离数组
        distances = [0.0] * n
        
        # 计算入度
        in_degree = [0] * n
        for u in range(n):
            for v, weight in constraints[u]:
                in_degree[v] += 1
        
        # Kahn算法进行拓扑排序
        queue = []
        for i in range(n):
            if in_degree[i] == 0:
                queue.append(i)
        
        topo_order = []
        
        while queue:
            # 从队列中取出入度为0的节点
            u = queue.pop(0)
            topo_order.append(u)
            
            # 更新邻接节点的入度
            for v, weight in constraints[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        # 检查是否有环路（拓扑排序失败）
        if len(topo_order) != n:
            # 如果有环路，使用简化方法（按索引顺序处理）
            print(f"警告: 检测到约束图中有环路，使用备用方法 ({coord_type}坐标)")
            return self._fallback_coordinate_calculation(constraints, n)
        
        # 按拓扑顺序计算最长路径
        for u in topo_order:
            for v, weight in constraints[u]:
                # 松弛操作：更新最长路径
                distances[v] = max(distances[v], distances[u] + weight)
        
        return distances
    
    def _fallback_coordinate_calculation(self, constraints: List[List[Tuple[int, float]]], n: int) -> List[float]:
        """
        备用坐标计算方法（当约束图有环时使用）
        Fallback coordinate calculation method (used when constraint graph has cycles)
        
        Args:
            constraints: 约束图
            n: 模块数量
            
        Returns:
            各模块的坐标值
        """
        distances = [0.0] * n
        
        # 使用固定次数的松弛操作
        max_iterations = n * 2  # 最多迭代2n次
        
        for iteration in range(max_iterations):
            updated = False
            
            for u in range(n):
                for v, weight in constraints[u]:
                    new_distance = distances[u] + weight
                    if new_distance > distances[v]:
                        distances[v] = new_distance
                        updated = True
            
            # 如果没有更新，提前退出
            if not updated:
                break
        
        return distances
    
    def neighborhood_operations(self, representation: Tuple[List[int], List[int]]) -> List[Tuple[List[int], List[int]]]:
        """
        生成邻域操作
        
        包含以下邻域操作：
        1. 在Γ+中交换两个相邻模块
        2. 在Γ-中交换两个相邻模块  
        3. 在Γ+中交换两个随机模块
        4. 在Γ-中交换两个随机模块
        
        Args:
            representation: 当前序列对
            
        Returns:
            邻域解列表
        """
        gamma_plus, gamma_minus = representation
        n = len(gamma_plus)
        neighbors = []
        
        if n < 2:
            return neighbors
        
        # 操作1: Γ+中相邻交换
        for i in range(n - 1):
            new_gamma_plus = gamma_plus.copy()
            new_gamma_plus[i], new_gamma_plus[i + 1] = new_gamma_plus[i + 1], new_gamma_plus[i]
            neighbors.append((new_gamma_plus, gamma_minus.copy()))
        
        # 操作2: Γ-中相邻交换
        for i in range(n - 1):
            new_gamma_minus = gamma_minus.copy()
            new_gamma_minus[i], new_gamma_minus[i + 1] = new_gamma_minus[i + 1], new_gamma_minus[i]
            neighbors.append((gamma_plus.copy(), new_gamma_minus))
        
        # 操作3: Γ+中随机交换
        if n >= 2:
            i, j = random.sample(range(n), 2)
            new_gamma_plus = gamma_plus.copy()
            new_gamma_plus[i], new_gamma_plus[j] = new_gamma_plus[j], new_gamma_plus[i]
            neighbors.append((new_gamma_plus, gamma_minus.copy()))
        
        # 操作4: Γ-中随机交换
        if n >= 2:
            i, j = random.sample(range(n), 2)
            new_gamma_minus = gamma_minus.copy()
            new_gamma_minus[i], new_gamma_minus[j] = new_gamma_minus[j], new_gamma_minus[i]
            neighbors.append((gamma_plus.copy(), new_gamma_minus))
        
        return neighbors
    
    def single_move(self, representation: Tuple[List[int], List[int]]) -> Tuple[List[int], List[int]]:
        """
        执行单次移动操作（用于模拟退火等算法）
        
        Args:
            representation: 当前序列对
            
        Returns:
            移动后的序列对
        """
        gamma_plus, gamma_minus = representation
        n = len(gamma_plus)
        
        if n < 2:
            return representation
        
        # 随机选择操作类型
        operation = random.randint(0, 3)
        
        new_gamma_plus = gamma_plus.copy()
        new_gamma_minus = gamma_minus.copy()
        
        if operation == 0:
            # Γ+中相邻交换
            i = random.randint(0, n - 2)
            new_gamma_plus[i], new_gamma_plus[i + 1] = new_gamma_plus[i + 1], new_gamma_plus[i]
        
        elif operation == 1:
            # Γ-中相邻交换
            i = random.randint(0, n - 2)
            new_gamma_minus[i], new_gamma_minus[i + 1] = new_gamma_minus[i + 1], new_gamma_minus[i]
        
        elif operation == 2:
            # Γ+中随机交换
            i, j = random.sample(range(n), 2)
            new_gamma_plus[i], new_gamma_plus[j] = new_gamma_plus[j], new_gamma_plus[i]
        
        else:
            # Γ-中随机交换
            i, j = random.sample(range(n), 2)
            new_gamma_minus[i], new_gamma_minus[j] = new_gamma_minus[j], new_gamma_minus[i]
        
        return (new_gamma_plus, new_gamma_minus)
    
    def get_representation_info(self, representation: Tuple[List[int], List[int]]) -> Dict[str, Any]:
        """获取表示信息"""
        gamma_plus, gamma_minus = representation
        
        return {
            'type': self.name,
            'size': len(gamma_plus),
            'gamma_plus': gamma_plus,
            'gamma_minus': gamma_minus,
            'modules': [self.modules[i].name for i in gamma_plus] if self.modules else []
        }
    
    def copy_representation(self, representation: Tuple[List[int], List[int]]) -> Tuple[List[int], List[int]]:
        """复制序列对表示"""
        gamma_plus, gamma_minus = representation
        return (gamma_plus.copy(), gamma_minus.copy())
    
    def is_valid_representation(self, representation: Tuple[List[int], List[int]]) -> bool:
        """
        检查序列对是否有效
        
        Args:
            representation: 序列对
            
        Returns:
            是否有效
        """
        gamma_plus, gamma_minus = representation
        
        # 检查长度是否一致
        if len(gamma_plus) != len(gamma_minus):
            return False
        
        # 检查是否包含所有模块且无重复
        n = len(self.modules)
        if set(gamma_plus) != set(range(n)) or set(gamma_minus) != set(range(n)):
            return False
        
        return True
    
    def calculate_area(self, representation: Tuple[List[int], List[int]]) -> Tuple[float, float]:
        """
        计算序列对对应布图的面积
        
        Args:
            representation: 序列对
            
        Returns:
            (宽度, 高度)
        """
        if not self.modules:
            return (0.0, 0.0)
        
        # 解码获取坐标
        gamma_plus, gamma_minus = representation
        n = len(self.modules)
        
        h_constraints = self._build_horizontal_constraints(gamma_plus, gamma_minus)
        v_constraints = self._build_vertical_constraints(gamma_plus, gamma_minus)
        
        x_coords = self._longest_path_algorithm(h_constraints, n, 'x')
        y_coords = self._longest_path_algorithm(v_constraints, n, 'y')
        
        # 计算总宽度和高度
        max_x = max(x_coords[i] + self.modules[i].width for i in range(n))
        max_y = max(y_coords[i] + self.modules[i].height for i in range(n))
        
        return (max_x, max_y)
    
    def _count_overlaps(self, design: FloorplanDesign) -> int:
        """
        计算重叠模块对的数量
        Count the number of overlapping module pairs
        
        Args:
            design: 布图设计
            
        Returns:
            重叠对数量
        """
        overlap_count = 0
        modules = list(design.modules.values())
        
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                module1 = modules[i]
                module2 = modules[j]
                
                # 跳过Terminals（端口），它们不参与重叠检查
                if (module1.module_type == ModuleType.TERMINAL or 
                    module2.module_type == ModuleType.TERMINAL):
                    continue
                
                # 检查是否重叠
                if self._modules_overlap(module1, module2):
                    overlap_count += 1
        
        return overlap_count
    
    def _modules_overlap(self, module1: Module, module2: Module) -> bool:
        """
        检查两个模块是否重叠
        Check if two modules overlap
        
        Args:
            module1: 模块1
            module2: 模块2
            
        Returns:
            是否重叠
        """
        # 计算模块边界
        m1_left = module1.x
        m1_right = module1.x + module1.width
        m1_bottom = module1.y
        m1_top = module1.y + module1.height
        
        m2_left = module2.x
        m2_right = module2.x + module2.width
        m2_bottom = module2.y
        m2_top = module2.y + module2.height
        
        # 检查重叠（使用严格的不等式，边界接触不算重叠）
        return not (m1_right <= m2_left or m2_right <= m1_left or 
                   m1_top <= m2_bottom or m2_top <= m1_bottom)
    
    def _enforce_no_overlap(self, design: FloorplanDesign, 
                           gamma_plus: List[int], gamma_minus: List[int]) -> FloorplanDesign:
        """
        强制消除重叠 - ZERO TOLERANCE
        Enforce no overlap - ZERO TOLERANCE
        
        Args:
            design: 当前设计
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            无重叠的设计
        """
        max_attempts = 5
        current_design = design
        
        for attempt in range(max_attempts):
            overlap_count = self._count_overlaps(current_design)
            
            if overlap_count == 0:
                return current_design
            
            # 尝试通过调整软模块形状来消除重叠
            if attempt < 3:
                current_design = self._adjust_soft_modules_to_reduce_overlap(current_design)
            else:
                # 最后的手段：强制重新解码
                current_design = self._force_recompute_positions(gamma_plus, gamma_minus)
        
        # 如果所有尝试都失败，使用最后的强制修复
        return self._force_remove_all_overlaps(current_design)
    
    def _adjust_soft_modules_to_reduce_overlap(self, design: FloorplanDesign) -> FloorplanDesign:
        """
        通过调整软模块形状来减少重叠
        Adjust soft module shapes to reduce overlap
        
        Args:
            design: 当前设计
            
        Returns:
            调整后的设计
        """
        overlapping_pairs = self._find_overlapping_pairs(design)
        
        for module1, module2 in overlapping_pairs:
            # 如果两个模块中有软模块，尝试调整其形状
            if module1.module_type == ModuleType.SOFT:
                self._shrink_soft_module(module1)
            elif module2.module_type == ModuleType.SOFT:
                self._shrink_soft_module(module2)
        
        return design
    
    def _find_overlapping_pairs(self, design: FloorplanDesign) -> List[Tuple[Module, Module]]:
        """
        找到所有重叠的模块对
        Find all overlapping module pairs
        
        Args:
            design: 布图设计
            
        Returns:
            重叠模块对列表
        """
        overlapping_pairs = []
        modules = list(design.modules.values())
        
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                module1 = modules[i]
                module2 = modules[j]
                
                # 跳过Terminals
                if (module1.module_type == ModuleType.TERMINAL or 
                    module2.module_type == ModuleType.TERMINAL):
                    continue
                
                if self._modules_overlap(module1, module2):
                    overlapping_pairs.append((module1, module2))
        
        return overlapping_pairs
    
    def _shrink_soft_module(self, module: Module):
        """
        收缩软模块以减少重叠
        Shrink soft module to reduce overlap
        
        Args:
            module: 软模块
        """
        if module.module_type != ModuleType.SOFT:
            return
        
        # 保持面积不变，调整长宽比使模块更紧凑
        current_area = module.width * module.height
        min_ratio = getattr(module, 'min_aspect_ratio', 0.5)
        max_ratio = getattr(module, 'max_aspect_ratio', 2.0)
        
        # 倾向于使模块更接近正方形（减少重叠概率）
        target_ratio = max(min_ratio, min(max_ratio, 1.0))
        
        new_width = math.sqrt(current_area * target_ratio) * 0.95  # 稍微收缩5%
        new_height = current_area / new_width
        
        module.set_size(new_width, new_height)
    
    def _force_recompute_positions(self, gamma_plus: List[int], 
                                  gamma_minus: List[int]) -> FloorplanDesign:
        """
        强制重新计算位置
        Force recompute positions
        
        Args:
            gamma_plus: 正序列
            gamma_minus: 负序列
            
        Returns:
            重新计算位置的设计
        """
        # 稍微收缩所有软模块然后重新解码
        for module in self.modules:
            if module.module_type == ModuleType.SOFT:
                current_area = module.width * module.height
                scale_factor = 0.9  # 收缩10%
                new_width = module.width * scale_factor
                new_height = current_area / new_width
                module.set_size(new_width, new_height)
        
        return self._decode_with_current_shapes(gamma_plus, gamma_minus)
    
    def _force_remove_all_overlaps(self, design: FloorplanDesign) -> FloorplanDesign:
        """
        强制移除所有重叠 - 最后手段
        Force remove all overlaps - last resort
        
        使用简单的位移策略确保绝对无重叠
        
        Args:
            design: 当前设计
            
        Returns:
            绝对无重叠的设计
        """
        modules = [m for m in design.modules.values() 
                  if m.module_type != ModuleType.TERMINAL]
        
        # 按左下角坐标排序
        modules.sort(key=lambda m: (m.x, m.y))
        
        # 使用简单的贪婪放置策略
        for i, module in enumerate(modules):
            # 检查与之前所有模块的重叠
            while True:
                has_overlap = False
                
                for j in range(i):
                    if self._modules_overlap(module, modules[j]):
                        # 移动当前模块到右侧或上方
                        if random.random() < 0.5:
                            # 移到右侧
                            module.x = modules[j].x + modules[j].width + 1.0
                        else:
                            # 移到上方
                            module.y = modules[j].y + modules[j].height + 1.0
                        
                        has_overlap = True
                        break
                
                if not has_overlap:
                    break
        
        return design

    def generate_neighbor(self, representation: Tuple[List[int], List[int]]) -> Tuple[List[int], List[int]]:
        """生成邻域解"""
        positive_seq, negative_seq = representation
        
        new_positive = positive_seq.copy()
        new_negative = negative_seq.copy()
        
        # 随机选择扰动类型
        operation = random.choice(['swap', 'insert', 'reverse'])
        
        if operation == 'swap':
            # 交换操作
            if random.random() < 0.5:
                # 扰动正序列
                if len(new_positive) >= 2:
                    i, j = random.sample(range(len(new_positive)), 2)
                    new_positive[i], new_positive[j] = new_positive[j], new_positive[i]
            else:
                # 扰动负序列
                if len(new_negative) >= 2:
                    i, j = random.sample(range(len(new_negative)), 2)
                    new_negative[i], new_negative[j] = new_negative[j], new_negative[i]
        
        elif operation == 'insert':
            # 插入操作
            if random.random() < 0.5:
                # 扰动正序列
                if len(new_positive) >= 2:
                    i = random.randint(0, len(new_positive) - 1)
                    j = random.randint(0, len(new_positive) - 1)
                    element = new_positive.pop(i)
                    new_positive.insert(j, element)
            else:
                # 扰动负序列
                if len(new_negative) >= 2:
                    i = random.randint(0, len(new_negative) - 1)
                    j = random.randint(0, len(new_negative) - 1)
                    element = new_negative.pop(i)
                    new_negative.insert(j, element)
        
        elif operation == 'reverse':
            # 反转操作
            if random.random() < 0.5:
                # 扰动正序列
                if len(new_positive) >= 2:
                    i, j = sorted(random.sample(range(len(new_positive)), 2))
                    new_positive[i:j+1] = reversed(new_positive[i:j+1])
            else:
                # 扰动负序列
                if len(new_negative) >= 2:
                    i, j = sorted(random.sample(range(len(new_negative)), 2))
                    new_negative[i:j+1] = reversed(new_negative[i:j+1])
        
        return (new_positive, new_negative)


# 导出主要类
__all__ = ['SequencePair'] 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合法性检查模块 - Legality Checking Module

布图合法性检查的完整实现
Complete implementation of floorplan legality checking

作者: PyFloorplan Team
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
import numpy as np
import time

from ..data.structures import FloorplanDesign, Module, ModuleType


@dataclass
class LegalityViolation:
    """合法性违规信息 - Legality Violation Information"""
    violation_type: str             # 违规类型
    severity: float                 # 严重程度（0-1，1为最严重）
    description: str                # 违规描述
    involved_modules: List[str]     # 涉及的模块
    penalty_cost: float = 0.0       # 惩罚代价
    position: Tuple[float, float] = (0.0, 0.0)  # 违规位置
    suggestion: str = ""            # 修复建议


@dataclass
class LegalityResult:
    """合法性检查结果 - Legality Check Result"""
    is_legal: bool                              # 是否合法
    total_violations: int                       # 违规总数
    total_penalty: float                        # 总惩罚代价
    violations: List[LegalityViolation]         # 详细违规列表
    check_time: float = 0.0                     # 检查耗时
    
    # 按类型分类的违规统计
    overlap_violations: int = 0
    boundary_violations: int = 0
    spacing_violations: int = 0
    alignment_violations: int = 0
    keepout_violations: int = 0
    
    def __post_init__(self):
        # 统计各类违规
        for violation in self.violations:
            if violation.violation_type == "overlap":
                self.overlap_violations += 1
            elif violation.violation_type == "boundary":
                self.boundary_violations += 1
            elif violation.violation_type == "spacing":
                self.spacing_violations += 1
            elif violation.violation_type == "alignment":
                self.alignment_violations += 1
            elif violation.violation_type == "keepout":
                self.keepout_violations += 1


@dataclass
class LegalityConstraints:
    """合法性约束配置 - Legality Constraints Configuration"""
    # 基础约束
    enable_overlap_check: bool = True           # 启用重叠检查
    enable_boundary_check: bool = True          # 启用边界检查
    enable_spacing_check: bool = False          # 启用间距检查
    enable_alignment_check: bool = False        # 启用对齐检查
    enable_keepout_check: bool = False          # 启用禁布区检查
    
    # 边界约束
    chip_boundary: Tuple[float, float, float, float] = (0, 0, 1000, 1000)  # (x1, y1, x2, y2)
    boundary_margin: float = 0.0                # 边界留白
    
    # 间距约束
    min_spacing: float = 10.0                   # 最小间距
    spacing_rules: Dict[str, Dict[str, float]] = field(default_factory=dict)  # 特定模块间距规则
    
    # 对齐约束
    grid_size: float = 1.0                      # 网格大小
    alignment_tolerance: float = 0.1            # 对齐容忍度
    
    # 禁布区约束
    keepout_regions: List[Tuple[float, float, float, float]] = field(default_factory=list)  # 禁布区列表
    
    # 惩罚权重
    overlap_penalty_weight: float = 10000.0     # 重叠惩罚权重
    boundary_penalty_weight: float = 1000.0     # 边界惩罚权重
    spacing_penalty_weight: float = 100.0       # 间距惩罚权重
    alignment_penalty_weight: float = 10.0      # 对齐惩罚权重
    keepout_penalty_weight: float = 1000.0      # 禁布区惩罚权重


class LegalityChecker(ABC):
    """
    合法性检查器抽象基类 - Legality Checker Abstract Base Class
    
    定义合法性检查器接口
    Defines legality checker interface
    """
    
    def __init__(self, name: str, constraints: LegalityConstraints):
        self.name = name
        self.constraints = constraints
        self.check_count = 0
        self.total_check_time = 0.0
        
    @abstractmethod
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """
        执行具体的合法性检查
        Perform specific legality check
        """
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取检查器统计信息"""
        return {
            'name': self.name,
            'check_count': self.check_count,
            'total_check_time': self.total_check_time,
            'avg_check_time': self.total_check_time / max(1, self.check_count)
        }


class OverlapChecker(LegalityChecker):
    """
    重叠检查器 - Overlap Checker
    
    检查模块之间的重叠违规
    Check overlap violations between modules
    """
    
    def __init__(self, constraints: LegalityConstraints):
        super().__init__("OverlapChecker", constraints)
    
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """检查模块重叠"""
        start_time = time.time()
        violations = []
        
        if not self.constraints.enable_overlap_check:
            return violations
        
        # 获取所有模块（排除端口）
        modules = [m for m in design.modules.values() 
                  if m.module_type != ModuleType.TERMINAL]
        
        # 检查每对模块的重叠
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                module1 = modules[i]
                module2 = modules[j]
                
                if module1.overlaps_with(module2):
                    # 计算重叠面积和严重程度
                    overlap_area = self._calculate_overlap_area(module1, module2)
                    severity = min(1.0, overlap_area / min(module1.area, module2.area))
                    
                    # 计算惩罚代价
                    penalty = overlap_area * self.constraints.overlap_penalty_weight
                    
                    # 计算重叠中心
                    overlap_center = self._calculate_overlap_center(module1, module2)
                    
                    violation = LegalityViolation(
                        violation_type="overlap",
                        severity=severity,
                        description=f"模块 {module1.name} 与 {module2.name} 重叠，重叠面积: {overlap_area:.2f}",
                        involved_modules=[module1.name, module2.name],
                        penalty_cost=penalty,
                        position=overlap_center,
                        suggestion=f"移动 {module1.name} 或 {module2.name} 以消除重叠"
                    )
                    violations.append(violation)
        
        self.check_count += 1
        self.total_check_time += time.time() - start_time
        
        return violations
    
    def _calculate_overlap_area(self, module1: Module, module2: Module) -> float:
        """计算重叠面积"""
        bbox1 = module1.get_bounding_box()
        bbox2 = module2.get_bounding_box()
        
        # 计算重叠矩形
        left = max(bbox1[0], bbox2[0])
        bottom = max(bbox1[1], bbox2[1])
        right = min(bbox1[2], bbox2[2])
        top = min(bbox1[3], bbox2[3])
        
        if left >= right or bottom >= top:
            return 0.0
        
        return (right - left) * (top - bottom)
    
    def _calculate_overlap_center(self, module1: Module, module2: Module) -> Tuple[float, float]:
        """计算重叠区域中心"""
        bbox1 = module1.get_bounding_box()
        bbox2 = module2.get_bounding_box()
        
        left = max(bbox1[0], bbox2[0])
        bottom = max(bbox1[1], bbox2[1])
        right = min(bbox1[2], bbox2[2])
        top = min(bbox1[3], bbox2[3])
        
        return ((left + right) / 2, (bottom + top) / 2)


class BoundaryChecker(LegalityChecker):
    """
    边界检查器 - Boundary Checker
    
    检查模块是否超出芯片边界
    Check if modules exceed chip boundary
    """
    
    def __init__(self, constraints: LegalityConstraints):
        super().__init__("BoundaryChecker", constraints)
    
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """检查边界约束"""
        start_time = time.time()
        violations = []
        
        if not self.constraints.enable_boundary_check:
            return violations
        
        chip_x1, chip_y1, chip_x2, chip_y2 = self.constraints.chip_boundary
        margin = self.constraints.boundary_margin
        
        # 调整边界以考虑留白
        effective_x1 = chip_x1 + margin
        effective_y1 = chip_y1 + margin
        effective_x2 = chip_x2 - margin
        effective_y2 = chip_y2 - margin
        
        for module in design.modules.values():
            if module.module_type == ModuleType.TERMINAL:
                continue  # 跳过端口
            
            bbox = module.get_bounding_box()
            module_x1, module_y1, module_x2, module_y2 = bbox
            
            # 检查各个边界
            violations_for_module = []
            
            # 左边界
            if module_x1 < effective_x1:
                violations_for_module.append({
                    'side': 'left',
                    'violation_distance': effective_x1 - module_x1,
                    'position': (module_x1, (module_y1 + module_y2) / 2)
                })
            
            # 右边界
            if module_x2 > effective_x2:
                violations_for_module.append({
                    'side': 'right',
                    'violation_distance': module_x2 - effective_x2,
                    'position': (module_x2, (module_y1 + module_y2) / 2)
                })
            
            # 下边界
            if module_y1 < effective_y1:
                violations_for_module.append({
                    'side': 'bottom',
                    'violation_distance': effective_y1 - module_y1,
                    'position': ((module_x1 + module_x2) / 2, module_y1)
                })
            
            # 上边界
            if module_y2 > effective_y2:
                violations_for_module.append({
                    'side': 'top',
                    'violation_distance': module_y2 - effective_y2,
                    'position': ((module_x1 + module_x2) / 2, module_y2)
                })
            
            # 为每个边界违规创建LegalityViolation
            for v in violations_for_module:
                severity = min(1.0, v['violation_distance'] / (module.width + module.height))
                penalty = v['violation_distance'] * self.constraints.boundary_penalty_weight
                
                violation = LegalityViolation(
                    violation_type="boundary",
                    severity=severity,
                    description=f"模块 {module.name} 超出{v['side']}边界 {v['violation_distance']:.2f} 单位",
                    involved_modules=[module.name],
                    penalty_cost=penalty,
                    position=v['position'],
                    suggestion=f"将 {module.name} 向芯片内部移动以满足边界约束"
                )
                violations.append(violation)
        
        self.check_count += 1
        self.total_check_time += time.time() - start_time
        
        return violations


class SpacingChecker(LegalityChecker):
    """
    间距检查器 - Spacing Checker
    
    检查模块之间的最小间距要求
    Check minimum spacing requirements between modules
    """
    
    def __init__(self, constraints: LegalityConstraints):
        super().__init__("SpacingChecker", constraints)
    
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """检查间距约束"""
        start_time = time.time()
        violations = []
        
        if not self.constraints.enable_spacing_check:
            return violations
        
        modules = [m for m in design.modules.values() 
                  if m.module_type != ModuleType.TERMINAL]
        
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                module1 = modules[i]
                module2 = modules[j]
                
                # 获取特定间距规则或使用默认值
                required_spacing = self._get_required_spacing(module1, module2)
                actual_spacing = self._calculate_spacing(module1, module2)
                
                if actual_spacing < required_spacing:
                    spacing_violation = required_spacing - actual_spacing
                    severity = min(1.0, spacing_violation / required_spacing)
                    penalty = spacing_violation * self.constraints.spacing_penalty_weight
                    
                    # 计算最近点作为违规位置
                    closest_point = self._find_closest_points(module1, module2)
                    
                    violation = LegalityViolation(
                        violation_type="spacing",
                        severity=severity,
                        description=f"模块 {module1.name} 与 {module2.name} 间距不足: {actual_spacing:.2f} < {required_spacing:.2f}",
                        involved_modules=[module1.name, module2.name],
                        penalty_cost=penalty,
                        position=closest_point,
                        suggestion=f"增加 {module1.name} 与 {module2.name} 之间的距离"
                    )
                    violations.append(violation)
        
        self.check_count += 1
        self.total_check_time += time.time() - start_time
        
        return violations
    
    def _get_required_spacing(self, module1: Module, module2: Module) -> float:
        """获取两个模块之间的所需间距"""
        # 检查是否有特定规则
        key1 = f"{module1.name}-{module2.name}"
        key2 = f"{module2.name}-{module1.name}"
        
        if key1 in self.constraints.spacing_rules:
            return self.constraints.spacing_rules[key1].get('spacing', self.constraints.min_spacing)
        elif key2 in self.constraints.spacing_rules:
            return self.constraints.spacing_rules[key2].get('spacing', self.constraints.min_spacing)
        
        return self.constraints.min_spacing
    
    def _calculate_spacing(self, module1: Module, module2: Module) -> float:
        """计算两个模块之间的实际间距"""
        bbox1 = module1.get_bounding_box()
        bbox2 = module2.get_bounding_box()
        
        # 计算水平和垂直方向的间距
        horizontal_spacing = max(0, min(bbox2[0] - bbox1[2], bbox1[0] - bbox2[2]))
        vertical_spacing = max(0, min(bbox2[1] - bbox1[3], bbox1[1] - bbox2[3]))
        
        # 如果模块在水平或垂直方向上不重叠，返回对应方向的间距
        if bbox1[2] <= bbox2[0] or bbox2[2] <= bbox1[0]:
            return horizontal_spacing
        elif bbox1[3] <= bbox2[1] or bbox2[3] <= bbox1[1]:
            return vertical_spacing
        else:
            # 如果重叠，返回0
            return 0.0
    
    def _find_closest_points(self, module1: Module, module2: Module) -> Tuple[float, float]:
        """找到两个模块最近的点"""
        center1 = module1.get_center()
        center2 = module2.get_center()
        return ((center1[0] + center2[0]) / 2, (center1[1] + center2[1]) / 2)


class AlignmentChecker(LegalityChecker):
    """
    对齐检查器 - Alignment Checker
    
    检查模块是否满足网格对齐要求
    Check if modules satisfy grid alignment requirements
    """
    
    def __init__(self, constraints: LegalityConstraints):
        super().__init__("AlignmentChecker", constraints)
    
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """检查对齐约束"""
        start_time = time.time()
        violations = []
        
        if not self.constraints.enable_alignment_check:
            return violations
        
        grid_size = self.constraints.grid_size
        tolerance = self.constraints.alignment_tolerance
        
        for module in design.modules.values():
            if module.module_type == ModuleType.TERMINAL:
                continue
            
            # 检查左下角坐标是否对齐到网格
            x_misalignment = module.x % grid_size
            y_misalignment = module.y % grid_size
            
            # 计算到最近网格点的距离
            x_distance = min(x_misalignment, grid_size - x_misalignment)
            y_distance = min(y_misalignment, grid_size - y_misalignment)
            
            if x_distance > tolerance:
                severity = min(1.0, x_distance / grid_size)
                penalty = x_distance * self.constraints.alignment_penalty_weight
                
                violation = LegalityViolation(
                    violation_type="alignment",
                    severity=severity,
                    description=f"模块 {module.name} X坐标未对齐网格: 偏移 {x_distance:.3f}",
                    involved_modules=[module.name],
                    penalty_cost=penalty,
                    position=(module.x, module.y),
                    suggestion=f"调整 {module.name} X坐标以对齐到网格"
                )
                violations.append(violation)
            
            if y_distance > tolerance:
                severity = min(1.0, y_distance / grid_size)
                penalty = y_distance * self.constraints.alignment_penalty_weight
                
                violation = LegalityViolation(
                    violation_type="alignment",
                    severity=severity,
                    description=f"模块 {module.name} Y坐标未对齐网格: 偏移 {y_distance:.3f}",
                    involved_modules=[module.name],
                    penalty_cost=penalty,
                    position=(module.x, module.y),
                    suggestion=f"调整 {module.name} Y坐标以对齐到网格"
                )
                violations.append(violation)
        
        self.check_count += 1
        self.total_check_time += time.time() - start_time
        
        return violations


class KeepoutChecker(LegalityChecker):
    """
    禁布区检查器 - Keepout Zone Checker
    
    检查模块是否侵入禁布区
    Check if modules intrude into keepout zones
    """
    
    def __init__(self, constraints: LegalityConstraints):
        super().__init__("KeepoutChecker", constraints)
    
    def check(self, design: FloorplanDesign) -> List[LegalityViolation]:
        """检查禁布区约束"""
        start_time = time.time()
        violations = []
        
        if not self.constraints.enable_keepout_check or not self.constraints.keepout_regions:
            return violations
        
        for module in design.modules.values():
            if module.module_type == ModuleType.TERMINAL:
                continue
            
            module_bbox = module.get_bounding_box()
            
            for i, keepout_region in enumerate(self.constraints.keepout_regions):
                intersection_area = self._calculate_intersection_area(module_bbox, keepout_region)
                
                if intersection_area > 0:
                    severity = min(1.0, intersection_area / module.area)
                    penalty = intersection_area * self.constraints.keepout_penalty_weight
                    
                    # 计算交集中心
                    intersection_center = self._calculate_intersection_center(module_bbox, keepout_region)
                    
                    violation = LegalityViolation(
                        violation_type="keepout",
                        severity=severity,
                        description=f"模块 {module.name} 侵入禁布区 {i}: 交集面积 {intersection_area:.2f}",
                        involved_modules=[module.name],
                        penalty_cost=penalty,
                        position=intersection_center,
                        suggestion=f"移动 {module.name} 远离禁布区 {i}"
                    )
                    violations.append(violation)
        
        self.check_count += 1
        self.total_check_time += time.time() - start_time
        
        return violations
    
    def _calculate_intersection_area(self, bbox1: Tuple[float, float, float, float], 
                                   bbox2: Tuple[float, float, float, float]) -> float:
        """计算两个矩形的交集面积"""
        left = max(bbox1[0], bbox2[0])
        bottom = max(bbox1[1], bbox2[1])
        right = min(bbox1[2], bbox2[2])
        top = min(bbox1[3], bbox2[3])
        
        if left >= right or bottom >= top:
            return 0.0
        
        return (right - left) * (top - bottom)
    
    def _calculate_intersection_center(self, bbox1: Tuple[float, float, float, float],
                                     bbox2: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """计算交集中心"""
        left = max(bbox1[0], bbox2[0])
        bottom = max(bbox1[1], bbox2[1])
        right = min(bbox1[2], bbox2[2])
        top = min(bbox1[3], bbox2[3])
        
        return ((left + right) / 2, (bottom + top) / 2)


class ComprehensiveLegalityChecker:
    """
    综合合法性检查器 - Comprehensive Legality Checker
    
    集成所有合法性检查功能的主检查器
    Main checker integrating all legality checking functions
    """
    
    def __init__(self, constraints: Optional[LegalityConstraints] = None):
        self.constraints = constraints or LegalityConstraints()
        
        # 初始化各种检查器
        self.checkers = []
        
        if self.constraints.enable_overlap_check:
            self.checkers.append(OverlapChecker(self.constraints))
        
        if self.constraints.enable_boundary_check:
            self.checkers.append(BoundaryChecker(self.constraints))
        
        if self.constraints.enable_spacing_check:
            self.checkers.append(SpacingChecker(self.constraints))
        
        if self.constraints.enable_alignment_check:
            self.checkers.append(AlignmentChecker(self.constraints))
        
        if self.constraints.enable_keepout_check:
            self.checkers.append(KeepoutChecker(self.constraints))
        
        self.total_checks = 0
        self.total_check_time = 0.0
    
    def check_legality(self, design: FloorplanDesign) -> LegalityResult:
        """
        执行完整的合法性检查
        Perform complete legality check
        """
        start_time = time.time()
        
        all_violations = []
        
        # 执行所有检查器
        for checker in self.checkers:
            violations = checker.check(design)
            all_violations.extend(violations)
        
        # 计算总惩罚
        total_penalty = sum(v.penalty_cost for v in all_violations)
        
        # 创建结果
        result = LegalityResult(
            is_legal=len(all_violations) == 0,
            total_violations=len(all_violations),
            total_penalty=total_penalty,
            violations=all_violations,
            check_time=time.time() - start_time
        )
        
        self.total_checks += 1
        self.total_check_time += result.check_time
        
        return result
    
    def calculate_penalty(self, design: FloorplanDesign) -> float:
        """
        快速计算合法性惩罚代价（用于优化循环）
        Fast calculation of legality penalty cost (for optimization loop)
        """
        start_time = time.time()
        
        total_penalty = 0.0
        
        # 只执行最关键的检查以提高速度
        if self.constraints.enable_overlap_check:
            # 快速重叠检查
            modules = [m for m in design.modules.values() 
                      if m.module_type != ModuleType.TERMINAL]
            
            for i in range(len(modules)):
                for j in range(i + 1, len(modules)):
                    if modules[i].overlaps_with(modules[j]):
                        # 简化的重叠惩罚计算
                        total_penalty += self.constraints.overlap_penalty_weight
        
        if self.constraints.enable_boundary_check:
            # 快速边界检查
            chip_x1, chip_y1, chip_x2, chip_y2 = self.constraints.chip_boundary
            margin = self.constraints.boundary_margin
            
            for module in design.modules.values():
                if module.module_type == ModuleType.TERMINAL:
                    continue
                
                bbox = module.get_bounding_box()
                if (bbox[0] < chip_x1 + margin or bbox[2] > chip_x2 - margin or
                    bbox[1] < chip_y1 + margin or bbox[3] > chip_y2 - margin):
                    total_penalty += self.constraints.boundary_penalty_weight
        
        self.total_check_time += time.time() - start_time
        
        return total_penalty
    
    def self_check(self) -> bool:
        """
        合法性检查器自检功能
        Self-check functionality for legality checker
        """
        print("🔧 合法性检查器 (legality) 自检")
        
        try:
            # 创建测试设计
            design = FloorplanDesign("test_legality")
            
            # 添加一些模块形成各种违规场景
            from ..data.structures import Module, Net, ModuleType
            
            # 正常模块
            m1 = Module("m1", ModuleType.SOFT, width=100, height=100, x=50, y=50, area=10000)
            design.add_module(m1)
            
            # 重叠模块
            m2 = Module("m2", ModuleType.SOFT, width=100, height=100, x=120, y=120, area=10000) 
            design.add_module(m2)
            
            # 超出边界的模块
            m3 = Module("m3", ModuleType.HARD, width=50, height=50, x=980, y=980, area=2500)
            design.add_module(m3)
            
            # 设置约束
            constraints = LegalityConstraints(
                chip_boundary=(0, 0, 1000, 1000),
                min_spacing=20.0,
                grid_size=10.0
            )
            
            # 创建检查器
            checker = ComprehensiveLegalityChecker(constraints)
            
            # 执行检查
            result = checker.check_legality(design)
            
            # 验证结果
            if result.is_legal:
                print("警告: 预期有违规但检测为合法")
                return False
            
            if result.total_violations == 0:
                print("❌ 未检测到预期的违规")
                return False
            
            # 测试快速惩罚计算
            penalty = checker.calculate_penalty(design)
            if penalty <= 0:
                print("❌ 快速惩罚计算返回非正值")
                return False
            
            print("✅ 合法性检查器自检通过")
            print(f"   - 检查器数量: {len(checker.checkers)}")
            print(f"   - 检测到违规: {result.total_violations}")
            print(f"   - 重叠违规: {result.overlap_violations}")
            print(f"   - 边界违规: {result.boundary_violations}")
            print(f"   - 总惩罚: {result.total_penalty:.2f}")
            print(f"   - 快速惩罚: {penalty:.2f}")
            print(f"   - 检查耗时: {result.check_time:.4f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ 合法性检查器自检失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def output_debug_info(self, design: FloorplanDesign, prefix: str = "  ") -> str:
        """
        输出合法性检查器的调试信息
        Output debug information for legality checker
        """
        try:
            result = self.check_legality(design)
            
            debug_info = f"{prefix}=== 合法性检查器调试信息 ===\n"
            debug_info += f"{prefix}检查结果: {'✅ 合法' if result.is_legal else '❌ 不合法'}\n"
            debug_info += f"{prefix}总违规数: {result.total_violations}\n"
            debug_info += f"{prefix}总惩罚: {result.total_penalty:.2f}\n"
            debug_info += f"{prefix}检查耗时: {result.check_time:.4f}s\n"
            
            debug_info += f"{prefix}违规分类:\n"
            debug_info += f"{prefix}  - 重叠违规: {result.overlap_violations}\n"
            debug_info += f"{prefix}  - 边界违规: {result.boundary_violations}\n"
            debug_info += f"{prefix}  - 间距违规: {result.spacing_violations}\n"
            debug_info += f"{prefix}  - 对齐违规: {result.alignment_violations}\n"
            debug_info += f"{prefix}  - 禁布区违规: {result.keepout_violations}\n"
            
            # 列出最严重的违规
            if result.violations:
                severe_violations = sorted(result.violations, key=lambda x: x.severity, reverse=True)[:3]
                debug_info += f"{prefix}最严重违规:\n"
                for i, violation in enumerate(severe_violations, 1):
                    debug_info += f"{prefix}  {i}. {violation.description} (严重度: {violation.severity:.3f})\n"
            
            # 检查器统计
            debug_info += f"{prefix}检查器统计:\n"
            for checker in self.checkers:
                stats = checker.get_statistics()
                debug_info += f"{prefix}  - {stats['name']}: {stats['check_count']}次, 平均{stats['avg_check_time']:.4f}s\n"
            
            return debug_info
            
        except Exception as e:
            return f"{prefix}合法性检查器调试信息获取失败: {e}\n"
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取检查器统计信息"""
        return {
            'total_checks': self.total_checks,
            'total_check_time': self.total_check_time,
            'avg_check_time': self.total_check_time / max(1, self.total_checks),
            'enabled_checkers': [checker.name for checker in self.checkers],
            'checker_stats': [checker.get_statistics() for checker in self.checkers]
        }


# 便捷函数
def create_legality_checker(enable_all: bool = True, **kwargs) -> ComprehensiveLegalityChecker:
    """
    创建合法性检查器的便捷函数
    Convenience function to create legality checker
    """
    if enable_all:
        constraints = LegalityConstraints(
            enable_overlap_check=True,
            enable_boundary_check=True,
            enable_spacing_check=False,  # 默认关闭，因为可能太严格
            enable_alignment_check=False,  # 默认关闭
            enable_keepout_check=False,   # 默认关闭，除非有特定需求
            **kwargs
        )
    else:
        constraints = LegalityConstraints(**kwargs)
    
    return ComprehensiveLegalityChecker(constraints)


def check_design_legality(design: FloorplanDesign, 
                         constraints: Optional[LegalityConstraints] = None) -> LegalityResult:
    """
    检查设计合法性的便捷函数
    Convenience function to check design legality
    """
    checker = ComprehensiveLegalityChecker(constraints)
    return checker.check_legality(design)


# 导出主要类和函数
__all__ = [
    'LegalityViolation',
    'LegalityResult', 
    'LegalityConstraints',
    'ComprehensiveLegalityChecker',
    'OverlapChecker',
    'BoundaryChecker',
    'SpacingChecker',
    'AlignmentChecker',
    'KeepoutChecker',
    'create_legality_checker',
    'check_design_legality'
] 
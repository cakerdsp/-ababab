#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心数据结构 - Core Data Structures

定义VLSI布图规划中的基本数据结构，包括模块、网线、引脚等
Defines basic data structures for VLSI floorplanning including modules, nets, pins, etc.
"""

import numpy as np
try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False
from typing import List, Dict, Tuple, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import copy


class ModuleType(Enum):
    """模块类型枚举 - Module Type Enumeration"""
    SOFT = "soft"           # 软模块，可变形状
    HARD = "hard"           # 硬模块，固定形状  
    TERMINAL = "terminal"   # 端口模块


class PinType(Enum):
    """引脚类型枚举 - Pin Type Enumeration"""
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


@dataclass
class Pin:
    """
    引脚类 - Pin Class
    
    表示模块上的一个引脚，包含位置和类型信息
    Represents a pin on a module with position and type information
    """
    name: str
    pin_type: PinType = PinType.INOUT
    x_offset: float = 0.0    # 相对于模块左下角的x偏移
    y_offset: float = 0.0    # 相对于模块左下角的y偏移
    
    def get_absolute_position(self, module_x: float, module_y: float) -> Tuple[float, float]:
        """获取引脚的绝对位置 - Get absolute position of pin"""
        return (module_x + self.x_offset, module_y + self.y_offset)


@dataclass
class Module:
    """
    模块类 - Module Class
    
    表示布图中的一个模块，支持软模块和硬模块
    Represents a module in floorplan, supporting both soft and hard modules
    """
    name: str
    module_type: ModuleType
    width: float = 0.0
    height: float = 0.0
    x: float = 0.0           # 左下角x坐标
    y: float = 0.0           # 左下角y坐标
    area: float = 0.0        # 模块面积
    
    # 软模块特有属性
    min_aspect_ratio: float = 0.1    # 最小长宽比
    max_aspect_ratio: float = 10.0   # 最大长宽比
    
    # 硬模块特有属性  
    vertices: List[Tuple[float, float]] = field(default_factory=list)  # 顶点坐标
    
    # 引脚信息
    pins: Dict[str, Pin] = field(default_factory=dict)
    
    # 其他属性
    is_fixed: bool = False   # 是否固定位置
    orientation: int = 0     # 旋转角度 (0, 90, 180, 270)
    
    @property
    def module_id(self) -> int:
        """获取模块ID - Get module ID (hash of name for compatibility)"""
        return hash(self.name) % (2**31)  # Ensure positive 32-bit integer
    
    def __post_init__(self):
        """初始化后处理 - Post initialization processing"""
        # 创建默认Pin（如果没有Pin的话）
        if not self.pins:
            if self.module_type == ModuleType.TERMINAL:
                # Terminal模块在中心有一个默认Pin
                default_pin = Pin(name="center", pin_type=PinType.INOUT, 
                                x_offset=0.0, y_offset=0.0)
            else:
                # 其他模块在中心有一个默认Pin
                default_pin = Pin(name="center", pin_type=PinType.INOUT, 
                                x_offset=self.width/2, y_offset=self.height/2)
            self.pins["center"] = default_pin
            # 为了兼容性，也创建一个"default"名称的Pin
            self.pins["default"] = default_pin
        
        if self.module_type == ModuleType.SOFT and self.area > 0:
            # 软模块根据面积和长宽比计算初始尺寸
            if self.width == 0.0 or self.height == 0.0:
                # 修复严重逻辑错误：选择合理的初始长宽比（在允许范围内尽量接近1.0）
                aspect_ratio = max(self.min_aspect_ratio, min(self.max_aspect_ratio, 1.0))
                self.width = np.sqrt(self.area * aspect_ratio)
                self.height = self.area / self.width
                
                # 更新默认Pin位置
                if "center" in self.pins:
                    self.pins["center"].x_offset = self.width / 2
                    self.pins["center"].y_offset = self.height / 2
                    
        elif self.module_type == ModuleType.HARD and len(self.vertices) > 0:
            # 硬模块根据顶点计算边界框
            self._update_bounding_box()
            
            # 更新默认Pin位置
            if "center" in self.pins:
                self.pins["center"].x_offset = self.width / 2
                self.pins["center"].y_offset = self.height / 2
    
    def _update_bounding_box(self):
        """更新边界框 - Update bounding box"""
        if len(self.vertices) == 0:
            return
        
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        self.width = max(xs) - min(xs)
        self.height = max(ys) - min(ys)
        self.area = self.width * self.height  # 简化为矩形面积
    
    def set_position(self, x: float, y: float):
        """设置模块位置 - Set module position"""
        self.x = x
        self.y = y
    
    def set_size(self, width: float, height: float):
        """设置模块尺寸 - Set module size"""
        if self.module_type == ModuleType.SOFT:
            aspect_ratio = width / height if height > 0 else 1.0
            if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                self.width = width
                self.height = height
            else:
                # 调整到允许的长宽比范围
                if aspect_ratio < self.min_aspect_ratio:
                    self.width = np.sqrt(self.area * self.min_aspect_ratio)
                    self.height = self.area / self.width
                else:
                    self.width = np.sqrt(self.area * self.max_aspect_ratio)
                    self.height = self.area / self.width
        else:
            # 硬模块直接设置尺寸
            self.width = width
            self.height = height
        
        # 🔧 **修复Pin偏移更新**: 更新所有Pin的相对位置以适应新尺寸
        self._update_pin_offsets_for_resize()
    
    def _update_pin_offsets_for_resize(self):
        """更新引脚偏移以适应新尺寸"""
        if "center" in self.pins:
            self.pins["center"].x_offset = self.width / 2
            self.pins["center"].y_offset = self.height / 2
        if "default" in self.pins:
            self.pins["default"].x_offset = self.width / 2
            self.pins["default"].y_offset = self.height / 2
    
    def get_center(self) -> Tuple[float, float]:
        """获取模块中心坐标 - Get module center coordinates"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """获取边界框 - Get bounding box (x1, y1, x2, y2)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def overlaps_with(self, other: 'Module') -> bool:
        """检查是否与另一个模块重叠 - Check if overlaps with another module"""
        x1, y1, x2, y2 = self.get_bounding_box()
        ox1, oy1, ox2, oy2 = other.get_bounding_box()
        return not (x2 <= ox1 or ox2 <= x1 or y2 <= oy1 or oy2 <= y1)
    
    def add_pin(self, pin: Pin):
        """添加引脚 - Add pin"""
        self.pins[pin.name] = pin
    
    def get_pin_position(self, pin_name: str) -> Optional[Tuple[float, float]]:
        """获取引脚位置 - Get pin position"""
        if pin_name in self.pins:
            return self.pins[pin_name].get_absolute_position(self.x, self.y)
        return None
    
    def rotate(self, angle: int):
        """
        旋转模块 - Rotate module
        
        🔧 **修复Pin偏移更新**: 正确更新引脚的相对偏移位置
        """
        if angle % 90 != 0:
            raise ValueError("Rotation angle must be multiple of 90 degrees")
        
        # 标准化角度到[0, 360)
        angle = angle % 360
        if angle == 0:
            return
        
        self.orientation = (self.orientation + angle) % 360
        
        # 对于90度和270度旋转，交换宽度和高度
        if angle == 90 or angle == 270:
            self.width, self.height = self.height, self.width
        
        # 🔧 **核心修复**: 更新所有引脚的相对偏移位置
        self._update_pin_offsets_for_rotation(angle)
    
    def _update_pin_offsets_for_rotation(self, angle: int):
        """
        根据旋转角度更新引脚偏移位置
        Update pin offsets based on rotation angle
        
        Args:
            angle: 旋转角度 (90, 180, 270)
        """
        if not self.pins:
            return
        
        # 对每个引脚应用旋转变换
        for pin in self.pins.values():
            old_x = pin.x_offset
            old_y = pin.y_offset
            
            if angle == 90:
                # 顺时针90度：(x, y) -> (y, width - x)
                pin.x_offset = old_y
                pin.y_offset = self.width - old_x  # 注意：旋转后width和height已经交换
            elif angle == 180:
                # 180度：(x, y) -> (width - x, height - y)
                pin.x_offset = self.width - old_x
                pin.y_offset = self.height - old_y
            elif angle == 270:
                # 顺时针270度（或逆时针90度）：(x, y) -> (height - y, x)
                pin.x_offset = self.height - old_y  # 注意：旋转后width和height已经交换
                pin.y_offset = old_x
    
    def clone(self) -> 'Module':
        """克隆模块 - Clone module"""
        return copy.deepcopy(self)


@dataclass  
class Net:
    """
    网线类 - Net Class
    
    表示连接多个模块引脚的网线
    Represents a net connecting multiple module pins
    """
    name: str
    pins: List[Tuple[str, str]] = field(default_factory=list)  # (module_name, pin_name)对
    weight: float = 1.0      # 网线权重
    is_critical: bool = False # 是否为关键路径
    
    def add_pin(self, module_name: str, pin_name: str):
        """添加引脚到网线 - Add pin to net"""
        self.pins.append((module_name, pin_name))
    
    def get_modules(self) -> Set[str]:
        """获取网线连接的所有模块 - Get all modules connected by net"""
        return set(module_name for module_name, _ in self.pins)
    
    def get_degree(self) -> int:
        """获取网线度数 - Get net degree"""
        return len(self.pins)
    
    def is_two_pin_net(self) -> bool:
        """是否为两端点网线 - Is two-pin net"""
        return self.get_degree() == 2
    
    def involves_module(self, module_name: str) -> bool:
        """是否涉及指定模块 - Does it involve specified module"""
        return module_name in self.get_modules()


@dataclass
class FloorplanDesign:
    """
    布图设计类 - Floorplan Design Class
    
    表示完整的布图设计，包含所有模块和网线信息
    Represents complete floorplan design with all modules and nets
    """
    name: str
    modules: Dict[str, Module] = field(default_factory=dict)
    nets: Dict[str, Net] = field(default_factory=dict)
    
    # 设计约束
    chip_width: float = 0.0
    chip_height: float = 0.0
    target_utilization: float = 0.8  # 目标利用率
    
    # 统计信息
    num_soft_modules: int = 0
    num_hard_modules: int = 0
    num_terminals: int = 0
    total_area: float = 0.0
    
    def __post_init__(self):
        """初始化后处理 - Post initialization processing"""
        self.update_statistics()
    
    def add_module(self, module: Module):
        """添加模块 - Add module"""
        self.modules[module.name] = module
        self.update_statistics()
    
    def add_net(self, net: Net):
        """添加网线 - Add net"""
        self.nets[net.name] = net
    
    def get_module(self, name: str) -> Optional[Module]:
        """获取模块 - Get module"""
        return self.modules.get(name)
    
    def get_net(self, name: str) -> Optional[Net]:
        """获取网线 - Get net"""
        return self.nets.get(name)
    
    def update_statistics(self):
        """更新统计信息 - Update statistics"""
        self.num_soft_modules = sum(1 for m in self.modules.values() 
                                   if m.module_type == ModuleType.SOFT)
        self.num_hard_modules = sum(1 for m in self.modules.values() 
                                   if m.module_type == ModuleType.HARD)
        self.num_terminals = sum(1 for m in self.modules.values() 
                               if m.module_type == ModuleType.TERMINAL)
        self.total_area = sum(m.area for m in self.modules.values()
                             if m.module_type != ModuleType.TERMINAL)
    
    def get_movable_modules(self) -> Dict[str, Module]:
        """获取可移动模块 - Get movable modules (包括可移动的端口)"""
        # 🔧 **CRITICAL FIX**: Pin也是可以移动的，只排除明确标记为固定的模块
        return {name: module for name, module in self.modules.items() 
                if not module.is_fixed}
    
    def get_fixed_modules(self) -> Dict[str, Module]:
        """获取固定模块 - Get fixed modules"""
        return {name: module for name, module in self.modules.items() 
                if module.is_fixed}
    
    def update_chip_size(self, padding: float = 0.0):
        """根据当前模块位置计算并更新芯片的边界框"""
        if not self.modules:
            self.chip_width = 0.0
            self.chip_height = 0.0
            return
        
        # 仅考虑非终端模块来确定芯片大小
        movable_and_hard_modules = [
            m for m in self.modules.values() if m.module_type != ModuleType.TERMINAL
        ]

        if not movable_and_hard_modules:
            self.chip_width = 0.0
            self.chip_height = 0.0
            return
            
        min_x = min(m.x for m in movable_and_hard_modules)
        min_y = min(m.y for m in movable_and_hard_modules)
        max_x = max(m.x + m.width for m in movable_and_hard_modules)
        max_y = max(m.y + m.height for m in movable_and_hard_modules)

        self.chip_width = max_x - min_x + padding
        self.chip_height = max_y - min_y + padding

    def check_overlap(self) -> List[Tuple[str, str]]:
        """检查模块重叠 - Check module overlaps"""
        overlaps = []
        module_list = list(self.modules.values())
        
        for i in range(len(module_list)):
            for j in range(i + 1, len(module_list)):
                if module_list[i].overlaps_with(module_list[j]):
                    overlaps.append((module_list[i].name, module_list[j].name))
        
        return overlaps
    
    def calculate_utilization(self) -> float:
        """计算面积利用率 - Calculate area utilization"""
        if self.chip_width == 0 or self.chip_height == 0:
            return 0.0
        chip_area = self.chip_width * self.chip_height
        return self.total_area / chip_area if chip_area > 0 else 0.0
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """获取所有模块的边界框 - Get bounding box of all modules"""
        if not self.modules:
            return (0, 0, 0, 0)
        
        boxes = [module.get_bounding_box() for module in self.modules.values()]
        min_x = min(box[0] for box in boxes)
        min_y = min(box[1] for box in boxes)
        max_x = max(box[2] for box in boxes)
        max_y = max(box[3] for box in boxes)
        
        return (min_x, min_y, max_x, max_y)
    
    def to_tensor(self, device=None) -> Dict[str, Union[np.ndarray, 'torch.Tensor']]:
        """
        转换为张量格式（支持PyTorch和NumPy）
        Convert to tensor format (supports PyTorch and NumPy)
        """
        movable_modules = self.get_movable_modules()
        n_modules = len(movable_modules)
        
        # 模块信息
        module_data = np.zeros((n_modules, 6))  # x, y, w, h, area, type
        module_names = list(movable_modules.keys())
        
        for i, (name, module) in enumerate(movable_modules.items()):
            module_data[i] = [
                module.x, module.y, module.width, module.height,
                module.area, float(module.module_type == ModuleType.SOFT)
            ]
        
        # 网线连接矩阵
        adjacency_matrix = np.zeros((n_modules, n_modules))
        name_to_idx = {name: i for i, name in enumerate(module_names)}
        
        for net in self.nets.values():
            modules_in_net = [name for name in net.get_modules() if name in name_to_idx]
            for i in range(len(modules_in_net)):
                for j in range(i + 1, len(modules_in_net)):
                    idx_i = name_to_idx[modules_in_net[i]]
                    idx_j = name_to_idx[modules_in_net[j]]
                    adjacency_matrix[idx_i, idx_j] = net.weight
                    adjacency_matrix[idx_j, idx_i] = net.weight
        
        # 如果有PyTorch，转换为张量
        if HAS_TORCH and torch is not None:
            return {
                'modules': torch.tensor(module_data, device=device),
                'adjacency': torch.tensor(adjacency_matrix, device=device),
                'module_names': module_names
            }
        else:
            return {
                'modules': module_data,
                'adjacency': adjacency_matrix,
                'module_names': module_names
            }
    
    def from_tensor(self, tensor_data: Dict[str, Union[np.ndarray, 'torch.Tensor']]):
        """
        从张量格式恢复（支持PyTorch和NumPy）
        Restore from tensor format (supports PyTorch and NumPy)
        """
        module_data = tensor_data['modules']
        
        # 如果是PyTorch张量，转换为numpy
        if HAS_TORCH and torch is not None and hasattr(module_data, 'cpu'):
            module_data = module_data.cpu().numpy()
        
        module_names = tensor_data['module_names']
        
        for i, name in enumerate(module_names):
            if name in self.modules:
                module = self.modules[name]
                module.x = float(module_data[i, 0])
                module.y = float(module_data[i, 1])
                module.width = float(module_data[i, 2])
                module.height = float(module_data[i, 3])
    
    def clone(self) -> 'FloorplanDesign':
        """克隆设计 - Clone design"""
        return copy.deepcopy(self)
    
    def summary(self) -> str:
        """获取设计摘要 - Get design summary"""
        return f"""
布图设计摘要 - Floorplan Design Summary:
设计名称: {self.name}
模块总数: {len(self.modules)}
  - 软模块: {self.num_soft_modules}
  - 硬模块: {self.num_hard_modules}  
  - 端口: {self.num_terminals}
网线总数: {len(self.nets)}
总面积: {self.total_area:.2f}
芯片尺寸: {self.chip_width} × {self.chip_height}
利用率: {self.calculate_utilization():.2%}
        """.strip() 

@dataclass
class EvaluationResult:
    """
    统一的评估结果类 - Unified Evaluation Result Class
    
    存储布图评估的各项指标，避免重复定义
    Stores various metrics from floorplan evaluation, avoiding duplicate definitions
    """
    # 主要指标 - Primary metrics
    total_cost: float = 0.0              # 总代价（用于优化）
    wirelength: float = 0.0              # 线长
    feedthrough_count: int = 0           # Feedthrough数量
    feedthrough_wirelength: float = 0.0  # 🎯 新增：Feedthrough线长 (FTAFP方法)
    area: float = 0.0                    # 面积
    whitespace_ratio: float = 0.0        # 空白区域比例
    
    # 详细指标 - Detailed metrics
    hpwl: float = 0.0                    # 半周长线长
    rmst: float = 0.0                    # 矩形最小生成树线长
    max_congestion: float = 0.0          # 最大拥塞
    severe_feedthrough_count: int = 0    # 严重feedthrough数量
    fragmentation_index: float = 0.0     # 碎片化指数
    
    # 面积和芯片尺寸信息
    chip_width: float = 0.0              # 芯片宽度
    chip_height: float = 0.0             # 芯片高度
    utilization: float = 0.0             # 面积利用率
    aspect_ratio: float = 0.0            # 长宽比
    
    # 网线统计
    max_net_length: float = 0.0          # 最大网线长度
    avg_net_length: float = 0.0          # 平均网线长度
    
    # 合法性指标 - Legality metrics
    is_legal: bool = True                # 是否合法
    legality_penalty: float = 0.0        # 合法性惩罚
    violation_count: int = 0             # 违规数量
    overlap_violations: int = 0          # 重叠违规
    boundary_violations: int = 0         # 边界违规
    overlap_area: float = 0.0            # 重叠面积
    overlap_count: int = 0               # 重叠模块对数
    constraint_violations: int = 0       # 约束违反数量
    
    # 归一化指标 - Normalized metrics
    normalized_wirelength: float = 0.0
    normalized_feedthrough_count: float = 0.0      # 归一化feedthrough数量
    normalized_feedthrough_wirelength: float = 0.0 # 归一化feedthrough线长
    normalized_whitespace: float = 0.0
    normalized_congestion: float = 0.0
    normalized_legality: float = 0.0     # 归一化合法性惩罚
    
    # 权重 - Weights used
    weights: Dict[str, float] = None
    
    # 计算时间 - Computation time
    evaluation_time: float = 0.0
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = {}
    
    def get_weighted_cost(self, 
                         area_weight: float = 0.5,
                         wirelength_weight: float = 0.5,
                         feedthrough_weight: float = 0.0,
                         whitespace_weight: float = 0.0,
                         overlap_penalty: float = 1000.0) -> float:
        """
        计算加权代价
        Calculate weighted cost
        """
        cost = (area_weight * self.area + 
                wirelength_weight * self.wirelength +
                feedthrough_weight * self.feedthrough_count +
                whitespace_weight * self.whitespace_ratio +
                overlap_penalty * self.overlap_area +
                self.legality_penalty)
        
        return cost
    
    def summary(self) -> str:
        """获取评估摘要"""
        return f"""
评估结果摘要:
芯片尺寸: {self.chip_width:.1f} × {self.chip_height:.1f}
总面积: {self.area:.1f}
线长: {self.wirelength:.1f} (HPWL: {self.hpwl:.1f})
Feedthrough: {self.feedthrough_count}
空白比例: {self.whitespace_ratio:.2%}
利用率: {self.utilization:.2%}
长宽比: {self.aspect_ratio:.2f}
重叠: {self.overlap_count} 对, 面积 {self.overlap_area:.1f}
是否合法: {'是' if self.is_legal else '否'}
合法性惩罚: {self.legality_penalty:.2f}
        """.strip() 
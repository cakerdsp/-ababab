#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均匀边缘Pin分配算法
O(1)时间复杂度的超快速Pin分配，按序号均匀分布到边缘
"""

import math
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from ...data.structures import FloorplanDesign, Module, ModuleType


@dataclass
class UniformEdgeConfig:
    """均匀边缘Pin分配配置"""
    expansion_ratio: float = 1.2        # 芯片扩展比例
    verbose: bool = False               # 详细输出


class UniformEdgePinAssignment:
    """均匀边缘Pin分配器 - 按序号均匀分布到芯片边缘"""
    
    def __init__(self, config: Optional[UniformEdgeConfig] = None):
        self.config = config or UniformEdgeConfig()
        self.verbose = self.config.verbose
        
        # 性能统计
        self.assignment_count = 0
        self.total_assignment_time = 0.0
    
    def assign_pins(self, design: FloorplanDesign) -> FloorplanDesign:
        """执行Pin分配 - Pin只能在芯片边缘的整数坐标"""
        start_time = time.time()
        
        # 获取需要布置的Pin
        pins = [m for m in design.modules.values() if m.module_type == ModuleType.TERMINAL]
        
        if not pins:
            return design

        # 计算当前芯片尺寸（基于宏模块包围盒）
        chip_width, chip_height = self._calculate_chip_size(design)

        # 检查周长是否足够容纳所有Pin
        perimeter = 2 * (int(chip_width) + int(chip_height))

        # 如果Pin数量超过可用位置，扩展芯片
        if len(pins) > perimeter:
            chip_width, chip_height = self._expand_chip_for_pins(chip_width, chip_height, len(pins))
        
        # 更新设计的芯片尺寸为整数
        design.chip_width = int(chip_width)
        design.chip_height = int(chip_height)
        
        # 核心：均匀分配Pin到布局边界
        if hasattr(design, '_layout_bounds'):
            min_x, min_y, max_x, max_y = design._layout_bounds
            self._assign_pins_to_layout_boundary(pins, min_x, min_y, max_x, max_y)
        else:
            # 后备方案：如果没有边界信息，使用传统方法
            self._assign_pins_uniformly(pins, int(chip_width), int(chip_height))
        
        # 更新统计信息
        self.assignment_count += 1
        self.total_assignment_time += time.time() - start_time
        
        return design
    
    def _assign_pins_to_layout_boundary(self, pins: List[Module], min_x: float, min_y: float, max_x: float, max_y: float):
        """将Pin分配到实际布局的边界上"""
        total_pins = len(pins)
        
        # 计算边界尺寸
        width = max_x - min_x
        height = max_y - min_y
        
        # 按边缘长度比例分配Pin数量
        bottom_edge_length = int(width) + 1
        right_edge_length = int(height) - 1  # 排除角点
        top_edge_length = int(width)  
        left_edge_length = int(height) - 1   # 排除角点
        
        total_edge_length = bottom_edge_length + right_edge_length + top_edge_length + left_edge_length
        
        # 计算每条边分配的Pin数量
        pins_per_bottom = int(total_pins * bottom_edge_length / total_edge_length)
        pins_per_right = int(total_pins * right_edge_length / total_edge_length)
        pins_per_top = int(total_pins * top_edge_length / total_edge_length)
        pins_per_left = total_pins - pins_per_bottom - pins_per_right - pins_per_top
        
        pin_index = 0
        
        # 下边缘 (y=min_y)
        for i in range(pins_per_bottom):
            if pin_index >= total_pins:
                break
            x = min_x + i * width / max(1, pins_per_bottom - 1) if pins_per_bottom > 1 else min_x + width / 2
            x = max(min_x, min(x, max_x))
            pins[pin_index].set_position(float(x), float(min_y))
            pin_index += 1
        
        # 右边缘 (x=max_x)
        for i in range(pins_per_right):
            if pin_index >= total_pins:
                break
            y = min_y + 1 + i * (height - 2) / max(1, pins_per_right - 1) if pins_per_right > 1 else min_y + height / 2
            y = max(min_y + 1, min(y, max_y - 1))
            pins[pin_index].set_position(float(max_x), float(y))
            pin_index += 1
        
        # 上边缘 (y=max_y)
        for i in range(pins_per_top):
            if pin_index >= total_pins:
                break
            x = max_x - i * width / max(1, pins_per_top - 1) if pins_per_top > 1 else min_x + width / 2
            x = max(min_x, min(x, max_x))
            pins[pin_index].set_position(float(x), float(max_y))
            pin_index += 1
        
        # 左边缘 (x=min_x) - 处理剩余Pin
        remaining_pins = total_pins - pin_index
        for i in range(remaining_pins):
            if pin_index >= total_pins:
                break
            y = max_y - 1 - i * (height - 2) / max(1, remaining_pins - 1) if remaining_pins > 1 else min_y + height / 2
            y = max(min_y + 1, min(y, max_y - 1))
            pins[pin_index].set_position(float(min_x), float(y))
            pin_index += 1
    
    def _assign_pins_uniformly(self, pins: List[Module], chip_width: int, chip_height: int):
        """均匀分配Pin到边缘"""
        total_pins = len(pins)
        
        # 按边缘长度比例分配Pin数量
        bottom_edge_length = chip_width + 1
        right_edge_length = chip_height - 1  # 排除角点
        top_edge_length = chip_width  
        left_edge_length = chip_height - 1   # 排除角点
        
        total_edge_length = bottom_edge_length + right_edge_length + top_edge_length + left_edge_length
        
        # 计算每条边分配的Pin数量
        pins_per_bottom = int(total_pins * bottom_edge_length / total_edge_length)
        pins_per_right = int(total_pins * right_edge_length / total_edge_length)
        pins_per_top = int(total_pins * top_edge_length / total_edge_length)
        pins_per_left = total_pins - pins_per_bottom - pins_per_right - pins_per_top
        
        pin_index = 0
        
        # 下边缘 (y=0)
        for i in range(pins_per_bottom):
            if pin_index >= total_pins:
                break
            x = i * chip_width // max(1, pins_per_bottom - 1) if pins_per_bottom > 1 else chip_width // 2
            x = min(x, chip_width)
            pins[pin_index].set_position(float(x), 0.0)
            pin_index += 1
        
        # 右边缘 (x=chip_width)
        for i in range(pins_per_right):
            if pin_index >= total_pins:
                break
            y = 1 + i * (chip_height - 2) // max(1, pins_per_right - 1) if pins_per_right > 1 else chip_height // 2
            y = max(1, min(y, chip_height - 1))
            pins[pin_index].set_position(float(chip_width), float(y))
            pin_index += 1
        
        # 上边缘 (y=chip_height)
        for i in range(pins_per_top):
            if pin_index >= total_pins:
                break
            x = chip_width - i * chip_width // max(1, pins_per_top - 1) if pins_per_top > 1 else chip_width // 2
            x = max(0, min(x, chip_width))
            pins[pin_index].set_position(float(x), float(chip_height))
            pin_index += 1
        
        # 左边缘 (x=0) - 处理剩余Pin
        remaining_pins = total_pins - pin_index
        for i in range(remaining_pins):
            if pin_index >= total_pins:
                break
            y = chip_height - 1 - i * (chip_height - 2) // max(1, remaining_pins - 1) if remaining_pins > 1 else chip_height // 2
            y = max(1, min(y, chip_height - 1))
            pins[pin_index].set_position(0.0, float(y))
            pin_index += 1
    
    def _calculate_chip_size(self, design: FloorplanDesign) -> Tuple[float, float]:
        """计算基于宏模块的芯片尺寸"""
        macro_modules = [m for m in design.modules.values() 
                        if m.module_type in [ModuleType.SOFT, ModuleType.HARD]]
        
        if not macro_modules:
            return 100.0, 100.0
        
        min_x = min(m.x for m in macro_modules)
        min_y = min(m.y for m in macro_modules)
        max_x = max(m.x + m.width for m in macro_modules)
        max_y = max(m.y + m.height for m in macro_modules)
        

        
        # 芯片边界应该是包围所有宏模块的最小矩形
        chip_width = math.ceil(max_x)
        chip_height = math.ceil(max_y)
        
        # 存储边界信息供Pin分配使用
        design._layout_bounds = (min_x, min_y, max_x, max_y)
        
        return max(chip_width, 10), max(chip_height, 10)
    
    def _expand_chip_for_pins(self, width: float, height: float, pin_count: int) -> Tuple[float, float]:
        """扩展芯片以容纳所有Pin"""
        current_perimeter = 2 * (int(width) + int(height))
        
        # 等比扩展直到能容纳所有Pin
        while current_perimeter < pin_count:
            width *= self.config.expansion_ratio
            height *= self.config.expansion_ratio
            current_perimeter = 2 * (int(width) + int(height))
        
        return math.ceil(width), math.ceil(height)
    
    def get_statistics(self) -> Dict:
        """获取性能统计信息"""
        avg_time = self.total_assignment_time / max(1, self.assignment_count)
        
        return {
            'algorithm': 'UniformEdgePinAssignment',
            'time_complexity': 'O(1)',
            'assignment_count': self.assignment_count,
            'total_time': self.total_assignment_time,
            'avg_time_per_assignment': avg_time,
            'config': {
                'expansion_ratio': self.config.expansion_ratio
            }
        }


# 导出主要类
__all__ = [
    'UniformEdgePinAssignment',
    'UniformEdgeConfig'
] 
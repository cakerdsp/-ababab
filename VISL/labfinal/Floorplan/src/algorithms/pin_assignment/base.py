#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
引脚布置基础类 - Pin Assignment Base Classes

定义引脚布置算法的抽象接口和数据结构
Defines abstract interfaces and data structures for pin assignment algorithms

作者: PyFloorplan Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import time
import math

from ...data.structures import FloorplanDesign, Module, ModuleType, Net


@dataclass
class PinAssignmentResult:
    """
    引脚布置结果 - Pin Assignment Result
    
    包含引脚在芯片边缘的布置结果
    Contains pin assignment results on chip edges
    """
    final_design: FloorplanDesign      # 最终完整设计（宏模块+引脚）
    chip_width: float                  # 最终芯片宽度
    chip_height: float                 # 最终芯片高度
    pin_count: int                     # 引脚总数
    assignment_time: float             # 布置耗时
    
    # 引脚布置质量指标
    total_wirelength: float = 0.0      # 总线长（包括宏模块间和引脚连接）
    pin_wirelength: float = 0.0        # 引脚相关线长
    feedthrough_count: int = 0         # Feedthrough数量
    chip_expansion_ratio: float = 1.0   # 芯片扩展比例
    
    # 引脚分布统计
    pins_on_left: int = 0
    pins_on_right: int = 0  
    pins_on_top: int = 0
    pins_on_bottom: int = 0


class PinAssignmentAlgorithm(ABC):
    """
    引脚布置算法抽象基类 - Abstract Base Class for Pin Assignment Algorithms
    
    定义所有引脚布置算法的统一接口
    Defines unified interface for all pin assignment algorithms
    """
    
    def __init__(self, name: str):
        self.name = name
        self.verbose = False
        
    @abstractmethod
    def assign_pins(self, macro_result, original_design: FloorplanDesign):
        """
        执行引脚布置 - Execute pin assignment
        
        Args:
            macro_result: 宏模块布局结果
            original_design: 原始设计（包含所有模块和网线）
            
        Returns:
            PinAssignmentResult: 引脚布置结果
        """
        pass
    
    def extract_pins(self, design: FloorplanDesign) -> Dict[str, Module]:
        """提取引脚模块"""
        pins = {}
        for name, module in design.modules.items():
            if module.module_type == ModuleType.TERMINAL:
                pins[name] = module
        return pins
    
    def set_verbose(self, verbose: bool):
        """设置详细输出模式"""
        self.verbose = verbose 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyFloorplan - 高性能VLSI布图规划优化框架
A Professional VLSI Floorplanning Optimization Framework

作者: PyFloorplan Team
许可证: MIT
版本: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "PyFloorplan Team"
__email__ = "author@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024 PyFloorplan Team"

# 核心模块导入
from .data import *
from .algorithms import *
from .evaluation import *

# 版本信息
def get_version():
    """获取版本信息"""
    return __version__

def get_info():
    """获取包信息"""
    return {
        'name': 'PyFloorplan',
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__,
        'description': '高性能VLSI布图规划优化框架'
    }

# 导出主要类和函数
__all__ = [
    # 版本信息
    '__version__',
    'get_version',
    'get_info',
    
    # 数据模块
    'FloorplanDesign',
    'Module',
    'Net',
    'GSRCParser',
    'MCNCParser',
    
    # 算法模块  
    'SimulatedAnnealing',
    'SequencePair',
    'GeneticAlgorithm',
    
    # 评估模块
    'evaluate_floorplan',
    'calculate_wirelength',
    'calculate_feedthrough',
    'calculate_whitespace',
    'FloorplanEvaluator',
    'WirelengthCalculator',
    'FeedthroughAnalyzer',
    'WhitespaceAnalyzer',
]

# 设置日志
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler()) 
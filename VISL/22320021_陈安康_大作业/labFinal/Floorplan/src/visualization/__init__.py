"""
可视化模块 - Visualization Module

提供布图结果的可视化功能，支持实时绘图和后处理分析
Provides visualization functionality for floorplan results, supporting real-time drawing and post-processing analysis
"""

from .layout_drawer import LayoutDrawer
from .visualization_config import VisualizationConfig

# 添加.pl文件可视化功能导入
try:
    from .pl_visualizer import PLVisualizer, visualize_pl_file
    HAS_PL_VISUALIZER = True
except ImportError:
    HAS_PL_VISUALIZER = False
    PLVisualizer = None
    visualize_pl_file = None

__all__ = [
    'LayoutDrawer',
    'VisualizationConfig',
    'PLVisualizer',
    'visualize_pl_file',
    'HAS_PL_VISUALIZER'
] 
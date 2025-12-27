#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.pl文件可视化器 - .pl File Visualizer

用于从.pl文件反生成视觉图信息，支持独立的可视化分析
Regenerate visual graphics from .pl files for independent visualization analysis
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from ..data.structures import FloorplanDesign, Module, ModuleType
from ..data.exporters import PLToDesignLoader
from .layout_drawer import LayoutDrawer
from .visualization_config import VisualizationConfig


class PLVisualizer:
    """
    .pl文件可视化器 - .pl File Visualizer
    
    专门用于从.pl文件生成可视化图像，不依赖于优化过程
    Specialized for generating visualizations from .pl files, independent of optimization process
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        初始化可视化器
        
        Args:
            config: 可视化配置，如果为None则使用默认配置
        """
        if config is None:
            config = VisualizationConfig()
            config.enabled = True
            config.use_threading = False  # 独立使用时不需要线程
            
        self.config = config
        self.layout_drawer = LayoutDrawer(config)
        self.pl_loader = PLToDesignLoader()
    
    def visualize_from_pl_file(self, pl_file: str, output_path: str = None, 
                              blocks_file: str = None, nets_file: str = None,
                              design_name: str = None) -> bool:
        """
        从.pl文件生成可视化图像
        
        Args:
            pl_file: .pl文件路径
            output_path: 输出图像路径（可选）
            blocks_file: .blocks文件路径（可选，用于获取完整模块信息）
            nets_file: .nets文件路径（可选，用于获取网线信息）
            design_name: 设计名称（可选）
            
        Returns:
            bool: 是否成功生成可视化图像
        """
        try:
            # 加载设计
            design = self.pl_loader.load_from_pl_file(
                pl_file=pl_file,
                blocks_file=blocks_file,
                nets_file=nets_file,
                design_name=design_name
            )
            
            if design is None:
                print(f"❌ 无法从.pl文件加载设计: {pl_file}")
                return False
            
            # 确定输出路径
            if output_path is None:
                pl_path = Path(pl_file)
                output_path = str(pl_path.parent / f"{pl_path.stem}_visualization.png")
            
            # 创建输出目录（修复：正确处理相对路径）
            output_dir = os.path.dirname(output_path)
            if output_dir:  # 只有当目录不为空时才创建
                os.makedirs(output_dir, exist_ok=True)
            
            # 生成可视化
            success = self.layout_drawer.draw_layout(
                design=design,
                iteration=-1,  # 表示最终结果
                metrics=None,
                output_path=output_dir if output_dir else ".",
                filename=os.path.basename(output_path)
            )
            
            if success:
                print(f"✅ 可视化图像已生成: {output_path}")
            else:
                print(f"❌ 可视化生成失败")
                
            return success
            
        except Exception as e:
            print(f"❌ 可视化过程出错: {e}")
            return False
    
    def batch_visualize_pl_files(self, pl_files: Dict[str, str], 
                                output_dir: str = "pl_visualizations") -> Dict[str, bool]:
        """
        批量生成.pl文件的可视化图像
        
        Args:
            pl_files: .pl文件字典，格式为 {design_name: pl_file_path}
            output_dir: 输出目录
            
        Returns:
            Dict[str, bool]: 每个设计的生成结果
        """
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for design_name, pl_file in pl_files.items():
            output_file = output_path / f"{design_name}_visualization.png"
            
            success = self.visualize_from_pl_file(
                pl_file=pl_file,
                output_path=str(output_file),
                design_name=design_name
            )
            
            results[design_name] = success
        
        return results
    
    def visualize_with_comparison(self, original_pl: str, optimized_pl: str, 
                                 output_path: str = None) -> bool:
        """
        生成对比可视化图像（原始vs优化后）
        
        Args:
            original_pl: 原始.pl文件路径
            optimized_pl: 优化后.pl文件路径
            output_path: 输出路径
            
        Returns:
            bool: 是否成功生成对比图像
        """
        try:
            # 加载两个设计
            original_design = self.pl_loader.load_from_pl_file(original_pl)
            optimized_design = self.pl_loader.load_from_pl_file(optimized_pl)
            
            if original_design is None or optimized_design is None:
                print("❌ 无法加载其中一个或两个设计文件")
                return False
            
            # 确定输出路径
            if output_path is None:
                output_path = f"comparison_{int(time.time())}.png"
            
            # 创建对比图像
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=self.config.dpi)
            
            # 绘制原始设计
            self._draw_design_on_axis(ax1, original_design, "原始设计")
            
            # 绘制优化后设计
            self._draw_design_on_axis(ax2, optimized_design, "优化后设计")
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=self.config.dpi, bbox_inches='tight')
            plt.close(fig)
            
            print(f"✅ 对比可视化图像已生成: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 对比可视化生成失败: {e}")
            return False
    
    def _draw_design_on_axis(self, ax, design: FloorplanDesign, title: str):
        """在指定轴上绘制设计"""
        # 计算边界
        bbox = design.get_bounding_box()
        if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            xl, yl, xh, yh = bbox
            margin = max((xh - xl), (yh - yl)) * 0.05
            
            ax.set_xlim(xl - margin, xh + margin)
            ax.set_ylim(yl - margin, yh + margin)
            ax.set_aspect('equal')
            ax.set_title(title, fontsize=14, fontweight='bold')
            
            # 绘制模块
            for module in design.modules.values():
                if module.module_type == ModuleType.TERMINAL:
                    # 引脚模块用圆形表示
                    circle = plt.Circle((module.x, module.y), 0.5, 
                                      color='red', alpha=0.8)
                    ax.add_patch(circle)
                    ax.text(module.x, module.y, module.name, 
                           ha='center', va='center', fontsize=6)
                else:
                    # 普通模块用矩形表示
                    rect = Rectangle((module.x, module.y), module.width, module.height,
                                   linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.7)
                    ax.add_patch(rect)
                    ax.text(module.x + module.width/2, module.y + module.height/2, module.name,
                           ha='center', va='center', fontsize=8)
            
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, "无效的设计数据", ha='center', va='center', transform=ax.transAxes)


def create_pl_visualizer(config_dict: Dict[str, Any] = None) -> PLVisualizer:
    """
    创建.pl文件可视化器的便捷函数
    
    Args:
        config_dict: 配置字典
        
    Returns:
        PLVisualizer: 可视化器实例
    """
    if config_dict:
        config = VisualizationConfig.from_dict(config_dict)
    else:
        config = None
    
    return PLVisualizer(config)


# 便捷函数
def visualize_pl_file(pl_file: str, output_path: str = None, **kwargs) -> bool:
    """
    便捷函数：直接从.pl文件生成可视化图像
    
    Args:
        pl_file: .pl文件路径
        output_path: 输出路径（可选）
        **kwargs: 其他参数
        
    Returns:
        bool: 是否成功
    """
    visualizer = PLVisualizer()
    return visualizer.visualize_from_pl_file(pl_file, output_path, **kwargs)


def compare_pl_files(original_pl: str, optimized_pl: str, output_path: str = None) -> bool:
    """
    便捷函数：对比两个.pl文件的可视化
    
    Args:
        original_pl: 原始.pl文件
        optimized_pl: 优化后.pl文件
        output_path: 输出路径（可选）
        
    Returns:
        bool: 是否成功
    """
    visualizer = PLVisualizer()
    return visualizer.visualize_with_comparison(original_pl, optimized_pl, output_path) 
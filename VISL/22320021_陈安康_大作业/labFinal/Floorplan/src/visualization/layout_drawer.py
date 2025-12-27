"""
布局绘制器 - Layout Drawer

参考DREAMPlace的实现方式，使用matplotlib进行布局可视化
支持独立线程绘图，避免阻塞优化算法
"""

import os
import time
import threading
import queue
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
import numpy as np

# 设置matplotlib使用非交互式后端（参考DREAMPlace）
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合后台绘图
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle

# 🔧 修复中文字体问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号显示为方块的问题

from ..data.structures import FloorplanDesign, Module, ModuleType
from .visualization_config import VisualizationConfig


@dataclass
class DrawRequest:
    """绘图请求数据结构"""
    design: FloorplanDesign
    iteration: Optional[int]
    metrics: Optional[Dict[str, Any]]
    output_path: str
    filename: str


class LayoutDrawer:
    """
    布局绘制器 - Layout Drawer
    
    参考DREAMPlace的PlaceDrawer实现，提供布局结果的可视化功能
    支持独立线程绘图，避免阻塞优化算法
    """
    
    def __init__(self, config: VisualizationConfig):
        """
        初始化绘制器
        
        Args:
            config: 可视化配置
        """
        self.config = config
        self.draw_queue = queue.Queue(maxsize=config.max_queue_size)
        self.worker_thread = None
        self.stop_event = threading.Event()
        
        if config.enabled and config.use_threading:
            self._start_worker_thread()
    
    def _start_worker_thread(self):
        """启动后台绘图线程"""
        if self.worker_thread is not None and self.worker_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """后台线程的工作循环"""
        while not self.stop_event.is_set():
            try:
                # 等待绘图请求，超时时间1秒
                request = self.draw_queue.get(timeout=1.0)
                if request is None:  # 结束信号
                    break
                    
                # 执行绘图
                self._draw_layout_sync(request)
                self.draw_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[WARNING] 可视化绘图出错: {e}")
                continue
    
    def draw_layout(self, design: FloorplanDesign, iteration: Optional[int] = None, 
                   metrics: Optional[Dict[str, Any]] = None, output_path: str = "",
                   filename: Optional[str] = None) -> bool:
        """
        绘制布局（异步版本）
        
        Args:
            design: 布图设计对象
            iteration: 当前迭代次数
            metrics: 关键指标
            output_path: 输出路径
            filename: 文件名（可选）
            
        Returns:
            bool: 是否成功提交绘图请求
        """
        if not self.config.enabled:
            return False
        
        if filename is None:
            suffix = "initial" if iteration == 0 else "final" if iteration == -1 else ""
            filename = self.config.get_filename(iteration, suffix)
        
        request = DrawRequest(
            design=design,
            iteration=iteration,
            metrics=metrics,
            output_path=output_path,
            filename=filename
        )
        
        if self.config.use_threading:
            try:
                # 非阻塞提交，如果队列满了就丢弃旧的请求
                if self.draw_queue.full():
                    try:
                        self.draw_queue.get_nowait()  # 移除一个旧请求
                    except queue.Empty:
                        pass
                
                self.draw_queue.put_nowait(request)
                return True
            except queue.Full:
                print("[WARNING] 可视化队列已满，跳过本次绘图")
                return False
        else:
            # 同步绘图
            return self._draw_layout_sync(request)
    
    def _draw_layout_sync(self, request: DrawRequest) -> bool:
        """
        同步绘制布局（实际绘图逻辑）
        
        Args:
            request: 绘图请求
            
        Returns:
            bool: 是否绘图成功
        """
        try:
            start_time = time.time()
            
            # 创建输出目录
            os.makedirs(request.output_path, exist_ok=True)
            
            # 计算布局边界
            layout_bounds = self._calculate_layout_bounds(request.design)
            
            if layout_bounds is None:
                print("[WARNING] 无法计算布局边界，跳过绘图")
                return False
            
            xl, yl, xh, yh = layout_bounds
            layout_width = xh - xl
            layout_height = yh - yl
            
            # 验证布局尺寸
            if layout_width <= 0 or layout_height <= 0:
                print(f"[WARNING] 无效的布局尺寸: {layout_width} x {layout_height}")
                return False
            
            # 计算图像尺寸
            img_width, img_height = self.config.calculate_image_size(layout_width, layout_height)
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(img_width/self.config.dpi, img_height/self.config.dpi), 
                                  dpi=self.config.dpi)
            
            # 设置坐标轴
            ax.set_xlim(xl - layout_width * 0.05, xh + layout_width * 0.05)
            ax.set_ylim(yl - layout_height * 0.05, yh + layout_height * 0.05)
            ax.set_aspect('equal')
            
            # 设置背景色
            fig.patch.set_facecolor(self.config.background_color)
            ax.set_facecolor(self.config.background_color)
            
            # 绘制布局区域边界
            self._draw_layout_boundary(ax, xl, yl, xh, yh)
            
            # 绘制网格（如果启用）
            if self.config.show_grid:
                self._draw_grid(ax, xl, yl, xh, yh)
            
            # 绘制模块
            if self.config.show_modules:
                self._draw_modules(ax, request.design)
            
            # 绘制端口
            if self.config.show_terminals:
                self._draw_terminals(ax, request.design)
            
            # 绘制网线（如果启用）
            if self.config.show_nets:
                self._draw_nets(ax, request.design)
            
            # 添加迭代信息
            if self.config.show_iteration and request.iteration is not None:
                self._add_iteration_text(ax, request.iteration, xl, yl, xh, yh)
            
            # 添加指标信息
            if self.config.show_metrics and request.metrics:
                self._add_metrics_text(ax, request.metrics, xl, yl, xh, yh)
            
            # 设置标题
            title = f"Layout Visualization"
            if request.iteration is not None:
                if request.iteration == -1:
                    title += " - Final Solution"
                else:
                    title += f" - Iteration {request.iteration}"
            ax.set_title(title, fontsize=16, pad=20)
            
            # 移除坐标轴刻度（更简洁）
            ax.set_xticks([])
            ax.set_yticks([])
            
            # 保存图像
            output_file = os.path.join(request.output_path, request.filename)
            
            plt.savefig(output_file, 
                       format=self.config.image_format,
                       dpi=self.config.dpi,
                       bbox_inches='tight',
                       facecolor=self.config.background_color,
                       edgecolor='none')
            
            plt.close(fig)
            
            elapsed_time = time.time() - start_time
            
            # 验证文件是否真的被创建
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"[I] 布局可视化已保存到 {output_file} (大小: {file_size} bytes, 耗时 {elapsed_time:.3f}s)")
                return True
            else:
                print(f"[ERROR] 图像文件未能创建: {output_file}")
                return False
            
        except Exception as e:
            print(f"[ERROR] 绘制布局失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _calculate_layout_bounds(self, design: FloorplanDesign) -> Optional[Tuple[float, float, float, float]]:
        """计算布局边界（基于宏模块包围盒，与Pin分配保持一致）"""
        if not design.modules:
            return None
        
        # 🎯 优先使用Pin分配时计算的宏模块边界（确保一致性）
        if hasattr(design, '_layout_bounds'):
            return design._layout_bounds
        
        # 🎯 后备方案：只计算宏模块的包围盒，不包括Pin
        macro_modules = [module for module in design.modules.values() 
                        if module.module_type in [ModuleType.SOFT, ModuleType.HARD]]
        
        if not macro_modules:
            # 如果没有宏模块，考虑所有模块（包括Terminal）
            macro_modules = list(design.modules.values())
        
        x_coords = []
        y_coords = []
        
        for module in macro_modules:
            if hasattr(module, 'x') and hasattr(module, 'y'):
                if hasattr(module, 'width') and hasattr(module, 'height'):
                    x_coords.extend([module.x, module.x + module.width])
                    y_coords.extend([module.y, module.y + module.height])
                else:
                    # 对于没有width/height的模块（如terminal），使用点坐标
                    x_coords.append(module.x)
                    y_coords.append(module.y)
        
        if not x_coords or not y_coords:
            return None
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def _draw_layout_boundary(self, ax, xl: float, yl: float, xh: float, yh: float):
        """绘制布局区域边界"""
        boundary = Rectangle((xl, yl), xh - xl, yh - yl,
                           linewidth=2, edgecolor=self.config.border_color,
                           facecolor='none', linestyle='-')
        ax.add_patch(boundary)
    
    def _draw_grid(self, ax, xl: float, yl: float, xh: float, yh: float):
        """绘制网格"""
        # 简单的网格，可以根据需要调整密度
        grid_step_x = (xh - xl) / 20  # 20x20网格
        grid_step_y = (yh - yl) / 20
        
        # 垂直线
        for x in np.arange(xl, xh + grid_step_x, grid_step_x):
            ax.axvline(x, color=self.config.grid_color, linewidth=0.5, alpha=0.7)
        
        # 水平线
        for y in np.arange(yl, yh + grid_step_y, grid_step_y):
            ax.axhline(y, color=self.config.grid_color, linewidth=0.5, alpha=0.7)
    
    def _draw_modules(self, ax, design: FloorplanDesign):
        """绘制模块"""
        for module in design.modules.values():
            if not hasattr(module, 'x') or not hasattr(module, 'y'):
                continue
            
            # 根据模块类型选择颜色
            if module.module_type == ModuleType.SOFT:
                color = self.config.soft_module_color
                alpha = 0.7
            elif module.module_type == ModuleType.HARD:
                color = self.config.hard_module_color
                alpha = 0.7
            else:  # TERMINAL
                continue  # 端口单独绘制
            
            # 绘制模块矩形
            rect = Rectangle((module.x, module.y), module.width, module.height,
                           linewidth=1, edgecolor='black', facecolor=color,
                           alpha=alpha)
            ax.add_patch(rect)
            
            # 添加模块名（如果模块足够大）
            if module.width > 10 and module.height > 10:  # 避免文字重叠
                ax.text(module.x + module.width/2, module.y + module.height/2,
                       module.name, ha='center', va='center',
                       fontsize=8, weight='bold')
    
    def _draw_terminals(self, ax, design: FloorplanDesign):
        """绘制端口"""
        terminal_count = 0
        for module in design.modules.values():
            if module.module_type != ModuleType.TERMINAL:
                continue
            
            if not hasattr(module, 'x') or not hasattr(module, 'y'):
                continue
            
            terminal_count += 1
            

            
            # 端口绘制为小圆点
            ax.scatter(module.x, module.y, c=self.config.terminal_color,
                      s=30, marker='o', edgecolors='black', linewidth=1,
                      alpha=0.8, zorder=10)
            
            # 添加端口名
            ax.text(module.x + 5, module.y + 5, module.name,
                   fontsize=6, ha='left', va='bottom')
        

    
    def _draw_nets(self, ax, design: FloorplanDesign):
        """绘制网线（简化版本）"""
        # 这是一个简化的网线绘制，只绘制连接线
        for net in design.nets.values():
            if len(net.pins) < 2:
                continue
            
            # 获取连接的模块位置
            positions = []
            for module_name, pin_name in net.pins:
                if module_name in design.modules:
                    module = design.modules[module_name]
                    if hasattr(module, 'x') and hasattr(module, 'y'):
                        # 简化：使用模块中心点
                        center_x = module.x + module.width / 2
                        center_y = module.y + module.height / 2
                        positions.append((center_x, center_y))
            
            # 绘制连接线（星形连接）
            if len(positions) >= 2:
                center_x = sum(pos[0] for pos in positions) / len(positions)
                center_y = sum(pos[1] for pos in positions) / len(positions)
                
                for pos in positions:
                    ax.plot([center_x, pos[0]], [center_y, pos[1]],
                           color='gray', linewidth=0.5, alpha=0.5)
    
    def _add_iteration_text(self, ax, iteration: int, xl: float, yl: float, xh: float, yh: float):
        """添加迭代次数文本"""
        if iteration == -1:
            text = "Final Solution"
        else:
            text = f"Iteration: {iteration}"
        
        ax.text(xl + (xh - xl) * 0.95, yh - (yh - yl) * 0.05,
               text,
               fontsize=14, ha='right', va='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def _add_metrics_text(self, ax, metrics: Dict[str, Any], xl: float, yl: float, xh: float, yh: float):
        """添加指标信息文本"""
        text_lines = []
        
        # 格式化主要指标
        if 'area' in metrics:
            text_lines.append(f"Area: {metrics['area']:,.0f}")
        if 'wirelength' in metrics:
            text_lines.append(f"Wirelength: {metrics['wirelength']:,.0f}")
        if 'feedthrough' in metrics:
            text_lines.append(f"FT: {metrics['feedthrough']}")
        
        if text_lines:
            text = "\n".join(text_lines)
            ax.text(xl + (xh - xl) * 0.05, yh - (yh - yl) * 0.05,
                   text, fontsize=10, ha='left', va='top',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def stop(self):
        """停止绘图线程"""
        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.stop_event.set()
            
            # 发送结束信号
            try:
                self.draw_queue.put_nowait(None)
            except queue.Full:
                pass
            
            # 等待线程结束
            self.worker_thread.join(timeout=5.0)
    
    def __del__(self):
        """析构函数，确保线程正确关闭"""
        self.stop() 
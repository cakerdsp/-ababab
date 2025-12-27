"""
可视化配置管理
管理所有与可视化相关的配置参数
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import os


@dataclass
class VisualizationConfig:
    """可视化配置类"""
    
    # 基础设置
    enabled: bool = False
    """是否启用可视化功能"""
    
    # 频率控制
    draw_frequency: int = 100
    """绘图频率：每多少次迭代绘制一次图像"""
    
    save_initial: bool = True
    """是否保存初始布局"""
    
    save_final: bool = True
    """是否保存最终布局"""
    
    # 输出设置
    output_dir: str = "visualization"
    """输出目录（相对于结果目录）"""
    
    filename_prefix: str = "layout"
    """文件名前缀"""
    
    image_format: str = "png"
    """图像格式：png, svg, pdf等"""
    
    # 图像设置
    image_width: int = 1200
    """图像宽度（像素）"""
    
    image_height: Optional[int] = None
    """图像高度（像素），如果为None则根据布局比例自动计算"""
    
    dpi: int = 150
    """图像分辨率"""
    
    # 绘图内容控制
    show_modules: bool = True
    """是否显示模块"""
    
    show_terminals: bool = True
    """是否显示端口"""
    
    show_nets: bool = False
    """是否显示网线（可能很密集，默认关闭）"""
    
    show_grid: bool = True
    """是否显示网格"""
    
    show_iteration: bool = True
    """是否在图上显示迭代次数"""
    
    show_metrics: bool = True
    """是否在图上显示关键指标"""
    
    # 颜色设置
    soft_module_color: str = '#3498db'  # 蓝色
    """软模块颜色"""
    
    hard_module_color: str = '#e74c3c'  # 红色
    """硬模块颜色"""
    
    terminal_color: str = '#2ecc71'  # 绿色
    """端口颜色"""
    
    background_color: str = '#ffffff'  # 白色
    """背景颜色"""
    
    grid_color: str = '#ecf0f1'  # 浅灰色
    """网格颜色"""
    
    border_color: str = '#34495e'  # 深灰色
    """边界颜色"""
    
    # 线程设置
    use_threading: bool = True
    """是否使用独立线程进行绘图（避免阻塞优化）"""
    
    max_queue_size: int = 5
    """绘图队列最大大小（避免内存占用过多）"""
    
    def __post_init__(self):
        """初始化后的验证和设置"""
        # 验证参数
        if self.draw_frequency <= 0:
            self.draw_frequency = 100
            
        if self.image_width <= 0:
            self.image_width = 1200
            
        if self.dpi <= 0:
            self.dpi = 150
            
        # 确保输出目录存在
        if self.enabled and self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'VisualizationConfig':
        """从字典创建配置对象"""
        # 过滤掉不存在的字段
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        
        return cls(**filtered_dict)
    
    def get_output_path(self, base_dir: str) -> str:
        """获取完整的输出路径"""
        return os.path.join(base_dir, self.output_dir)
    
    def get_filename(self, iteration: Optional[int] = None, suffix: str = "") -> str:
        """生成文件名"""
        parts = [self.filename_prefix]
        
        if iteration is not None:
            if iteration == -1:
                parts.append("final")
            elif iteration >= 0:
                parts.append(f"iter_{iteration:04d}")
        
        if suffix:
            parts.append(suffix)
            
        filename = "_".join(parts) + f".{self.image_format}"
        return filename
    
    def should_draw(self, iteration: int) -> bool:
        """判断当前迭代是否应该绘图"""
        if not self.enabled:
            return False
            
        return iteration % self.draw_frequency == 0
    
    def calculate_image_size(self, layout_width: float, layout_height: float) -> Tuple[int, int]:
        """根据布局尺寸计算图像尺寸，保持长宽比"""
        if self.image_height is not None:
            return self.image_width, self.image_height
        
        # 根据布局比例自动计算高度
        if layout_width > 0 and layout_height > 0:
            aspect_ratio = layout_height / layout_width
            calculated_height = int(self.image_width * aspect_ratio)
            return self.image_width, calculated_height
        else:
            return self.image_width, self.image_width 
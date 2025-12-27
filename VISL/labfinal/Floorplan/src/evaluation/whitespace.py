#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
空白区域分析模块 - Whitespace Analysis Module

实现空白面积计算、分布分析和可利用性评估
Implements whitespace area calculation, distribution analysis and utilization assessment
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..data.structures import FloorplanDesign, Module


@dataclass
class WhitespaceRegion:
    """空白区域信息"""
    x: float
    y: float
    width: float
    height: float
    area: float
    is_utilizable: bool  # 是否可利用
    adjacent_modules: List[str]  # 相邻模块


@dataclass
class WhitespaceResult:
    """空白区域分析结果"""
    total_whitespace: float
    whitespace_ratio: float
    utilizable_whitespace: float
    unusable_whitespace: float
    whitespace_regions: List[WhitespaceRegion]
    largest_region_area: float
    avg_region_area: float
    fragmentation_index: float  # 碎片化指数


def calculate_whitespace_ratio(design: FloorplanDesign) -> float:
    """
    计算空白面积比率
    Calculate whitespace ratio
    
    Args:
        design: 布图设计
        
    Returns:
        空白面积比率 (0-1)
    """
    analyzer = WhitespaceAnalyzer()
    result = analyzer.analyze(design)
    return result.whitespace_ratio


def analyze_whitespace_distribution(design: FloorplanDesign) -> List[WhitespaceRegion]:
    """
    分析空白区域分布
    Analyze whitespace distribution
    
    Args:
        design: 布图设计
        
    Returns:
        空白区域列表
    """
    analyzer = WhitespaceAnalyzer()
    result = analyzer.analyze(design)
    return result.whitespace_regions


class WhitespaceAnalyzer:
    """
    空白区域分析器类
    Whitespace Analyzer Class
    
    分析布图中的空白区域，评估可利用性和碎片化程度
    Analyzes whitespace regions in floorplan, evaluates utilization and fragmentation
    """
    
    def __init__(self, grid_resolution: int = 100, min_utilizable_area: float = 100.0):
        """
        初始化分析器
        
        Args:
            grid_resolution: 网格分辨率
            min_utilizable_area: 最小可利用面积阈值
        """
        self.grid_resolution = grid_resolution
        self.min_utilizable_area = min_utilizable_area
    
    def analyze(self, design: FloorplanDesign) -> WhitespaceResult:
        """
        执行完整的空白区域分析
        Perform complete whitespace analysis
        
        Args:
            design: 布图设计
            
        Returns:
            分析结果
        """
        # 获取设计边界
        bbox = design.get_bounding_box()
        total_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        
        if total_area <= 0:
            return self._empty_result()
        
        # 计算已占用面积
        occupied_area = sum(module.area for module in design.modules.values() 
                          if hasattr(module, 'area') and module.area > 0)
        
        # 计算总空白面积
        total_whitespace = total_area - occupied_area
        whitespace_ratio = total_whitespace / total_area if total_area > 0 else 0.0
        
        # 分析空白区域分布
        whitespace_regions = self._find_whitespace_regions(design)
        
        # 计算可利用和不可利用的空白面积
        utilizable_whitespace = sum(region.area for region in whitespace_regions 
                                  if region.is_utilizable)
        unusable_whitespace = total_whitespace - utilizable_whitespace
        
        # 计算统计信息
        region_areas = [region.area for region in whitespace_regions]
        largest_region = max(region_areas) if region_areas else 0.0
        avg_region = np.mean(region_areas) if region_areas else 0.0
        
        # 计算碎片化指数（小区域数量与总区域数量的比值）
        small_regions = sum(1 for area in region_areas if area < self.min_utilizable_area)
        fragmentation_index = small_regions / len(region_areas) if region_areas else 0.0
        
        return WhitespaceResult(
            total_whitespace=total_whitespace,
            whitespace_ratio=whitespace_ratio,
            utilizable_whitespace=utilizable_whitespace,
            unusable_whitespace=unusable_whitespace,
            whitespace_regions=whitespace_regions,
            largest_region_area=largest_region,
            avg_region_area=avg_region,
            fragmentation_index=fragmentation_index
        )
    
    def _empty_result(self) -> WhitespaceResult:
        """返回空结果"""
        return WhitespaceResult(
            total_whitespace=0.0,
            whitespace_ratio=0.0,
            utilizable_whitespace=0.0,
            unusable_whitespace=0.0,
            whitespace_regions=[],
            largest_region_area=0.0,
            avg_region_area=0.0,
            fragmentation_index=0.0
        )
    
    def _find_whitespace_regions(self, design: FloorplanDesign) -> List[WhitespaceRegion]:
        """
        使用网格扫描法找到空白区域
        Find whitespace regions using grid scanning
        """
        bbox = design.get_bounding_box()
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        if width <= 0 or height <= 0:
            return []
        
        # 创建占用网格
        grid = np.zeros((self.grid_resolution, self.grid_resolution), dtype=bool)
        
        # 标记被模块占用的网格
        for module in design.modules.values():
            self._mark_module_on_grid(grid, module, bbox)
        
        # 找到连通的空白区域
        visited = np.zeros_like(grid, dtype=bool)
        regions = []
        
        for i in range(self.grid_resolution):
            for j in range(self.grid_resolution):
                if not grid[i, j] and not visited[i, j]:
                    # 发现新的空白区域，使用BFS扩展
                    region_cells = self._bfs_region(grid, visited, i, j)
                    if region_cells:
                        region = self._cells_to_region(region_cells, bbox, design)
                        if region.area > 0:
                            regions.append(region)
        
        return regions
    
    def _mark_module_on_grid(self, grid: np.ndarray, module: Module, bbox: Tuple[float, float, float, float]):
        """在网格上标记模块占用的区域"""
        module_bbox = module.get_bounding_box()
        
        # 转换为网格坐标
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        grid_x1 = int((module_bbox[0] - bbox[0]) / width * self.grid_resolution)
        grid_y1 = int((module_bbox[1] - bbox[1]) / height * self.grid_resolution)
        grid_x2 = int((module_bbox[2] - bbox[0]) / width * self.grid_resolution)
        grid_y2 = int((module_bbox[3] - bbox[1]) / height * self.grid_resolution)
        
        # 限制在网格范围内
        grid_x1 = max(0, min(grid_x1, self.grid_resolution - 1))
        grid_y1 = max(0, min(grid_y1, self.grid_resolution - 1))
        grid_x2 = max(0, min(grid_x2, self.grid_resolution - 1))
        grid_y2 = max(0, min(grid_y2, self.grid_resolution - 1))
        
        # 标记占用区域
        grid[grid_y1:grid_y2+1, grid_x1:grid_x2+1] = True
    
    def _bfs_region(self, grid: np.ndarray, visited: np.ndarray, 
                   start_i: int, start_j: int) -> List[Tuple[int, int]]:
        """使用BFS找到连通的空白区域"""
        queue = [(start_i, start_j)]
        region_cells = []
        
        while queue:
            i, j = queue.pop(0)
            
            if (i < 0 or i >= self.grid_resolution or 
                j < 0 or j >= self.grid_resolution or
                grid[i, j] or visited[i, j]):
                continue
            
            visited[i, j] = True
            region_cells.append((i, j))
            
            # 添加相邻的8个方向
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    queue.append((i + di, j + dj))
        
        return region_cells
    
    def _cells_to_region(self, cells: List[Tuple[int, int]], 
                        bbox: Tuple[float, float, float, float],
                        design: FloorplanDesign) -> WhitespaceRegion:
        """将网格单元转换为空白区域对象"""
        if not cells:
            return WhitespaceRegion(0, 0, 0, 0, 0, False, [])
        
        # 计算区域边界
        min_i = min(cell[0] for cell in cells)
        max_i = max(cell[0] for cell in cells)
        min_j = min(cell[1] for cell in cells)
        max_j = max(cell[1] for cell in cells)
        
        # 转换回实际坐标
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        cell_width = width / self.grid_resolution
        cell_height = height / self.grid_resolution
        
        region_x = bbox[0] + min_j * cell_width
        region_y = bbox[1] + min_i * cell_height
        region_width = (max_j - min_j + 1) * cell_width
        region_height = (max_i - min_i + 1) * cell_height
        region_area = len(cells) * cell_width * cell_height
        
        # 判断是否可利用
        is_utilizable = (region_area >= self.min_utilizable_area and 
                        region_width >= 10 and region_height >= 10)
        
        # 找到相邻模块
        adjacent_modules = self._find_adjacent_modules(
            design, region_x, region_y, region_width, region_height)
        
        return WhitespaceRegion(
            x=region_x,
            y=region_y,
            width=region_width,
            height=region_height,
            area=region_area,
            is_utilizable=is_utilizable,
            adjacent_modules=adjacent_modules
        )
    
    def _find_adjacent_modules(self, design: FloorplanDesign, 
                              x: float, y: float, width: float, height: float) -> List[str]:
        """找到与空白区域相邻的模块"""
        adjacent_modules = []
        region_bbox = (x, y, x + width, y + height)
        
        # 扩展边界以检测相邻性
        expanded_bbox = (
            region_bbox[0] - 1,
            region_bbox[1] - 1,
            region_bbox[2] + 1,
            region_bbox[3] + 1
        )
        
        for module in design.modules.values():
            module_bbox = module.get_bounding_box()
            
            # 检查是否相邻（扩展边界与模块边界相交）
            if (expanded_bbox[0] < module_bbox[2] and expanded_bbox[2] > module_bbox[0] and
                expanded_bbox[1] < module_bbox[3] and expanded_bbox[3] > module_bbox[1]):
                adjacent_modules.append(module.name)
        
        return adjacent_modules
    
    def get_utilization_map(self, design: FloorplanDesign) -> np.ndarray:
        """
        生成利用率热力图
        Generate utilization heatmap
        
        Returns:
            利用率矩阵 (0: 空白, 1: 占用)
        """
        bbox = design.get_bounding_box()
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            return np.zeros((self.grid_resolution, self.grid_resolution))
        
        grid = np.zeros((self.grid_resolution, self.grid_resolution))
        
        for module in design.modules.values():
            self._mark_module_on_grid(grid, module, bbox)
        
        return grid.astype(float)
    
    def suggest_improvements(self, design: FloorplanDesign) -> List[str]:
        """
        建议空白区域优化策略
        Suggest whitespace optimization strategies
        
        Returns:
            优化建议列表
        """
        result = self.analyze(design)
        suggestions = []
        
        if result.whitespace_ratio > 0.3:
            suggestions.append(f"空白面积比率较高 ({result.whitespace_ratio:.1%})，考虑压缩布局")
        
        if result.fragmentation_index > 0.7:
            suggestions.append(f"空白区域碎片化严重 (碎片化指数: {result.fragmentation_index:.2f})，建议整理布局")
        
        if result.utilizable_whitespace < result.total_whitespace * 0.5:
            suggestions.append("大部分空白区域不可利用，建议重新安排模块位置")
        
        # 找到最大的可利用区域
        utilizable_regions = [r for r in result.whitespace_regions if r.is_utilizable]
        if utilizable_regions:
            largest_utilizable = max(utilizable_regions, key=lambda r: r.area)
            suggestions.append(f"最大可利用空白区域: {largest_utilizable.area:.0f} 平方单位，"
                             f"位置: ({largest_utilizable.x:.0f}, {largest_utilizable.y:.0f})")
        
        return suggestions
    
    def calculate_density_map(self, design: FloorplanDesign, window_size: int = 10) -> np.ndarray:
        """
        计算局部密度图
        Calculate local density map
        
        Args:
            design: 布图设计
            window_size: 滑动窗口大小
            
        Returns:
            密度矩阵
        """
        utilization_map = self.get_utilization_map(design)
        density_map = np.zeros_like(utilization_map)
        
        half_window = window_size // 2
        
        for i in range(self.grid_resolution):
            for j in range(self.grid_resolution):
                # 计算窗口范围
                i_start = max(0, i - half_window)
                i_end = min(self.grid_resolution, i + half_window + 1)
                j_start = max(0, j - half_window)
                j_end = min(self.grid_resolution, j + half_window + 1)
                
                # 计算窗口内的平均占用率
                window = utilization_map[i_start:i_end, j_start:j_end]
                density_map[i, j] = np.mean(window)
        
        return density_map


def self_check_whitespace() -> bool:
    """
    空白区域模块自检功能
    Self-check functionality for whitespace module
    """
    print("🔧 空白区域模块 (whitespace) 自检")
    
    try:
        # 创建测试设计
        from ..data.structures import FloorplanDesign, Module, Net, ModuleType
        
        design = FloorplanDesign("test_whitespace")
        
        # 创建具有明显空白区域的布局
        # 左侧放置模块，右侧留空
        m1 = Module("m1", ModuleType.SOFT, width=100, height=100, x=0, y=0, area=10000)
        m2 = Module("m2", ModuleType.SOFT, width=100, height=100, x=0, y=120, area=10000)
        m3 = Module("m3", ModuleType.SOFT, width=100, height=100, x=120, y=0, area=10000)
        
        # 在右侧留出大片空白区域
        design.add_module(m1)
        design.add_module(m2)
        design.add_module(m3)
        
        # 添加一些网线
        net1 = Net("net1", [("m1", "pin1"), ("m2", "pin1")])
        design.add_net(net1)
        
        # 测试基础函数
        ws_ratio = calculate_whitespace_ratio(design)
        ws_distribution = analyze_whitespace_distribution(design)
        
        # 验证基本合理性
        if not 0 <= ws_ratio <= 1:
            print(f"❌ calculate_whitespace_ratio() 错误: 超出范围 {ws_ratio}")
            return False
        
        if not isinstance(ws_distribution, list):
            print(f"❌ analyze_whitespace_distribution() 返回类型错误")
            return False
        
        # 测试WhitespaceAnalyzer
        analyzer = WhitespaceAnalyzer(grid_resolution=50, min_utilizable_area=100.0)
        result = analyzer.analyze(design)
        
        if not isinstance(result, WhitespaceResult):
            print(f"❌ WhitespaceAnalyzer.analyze() 返回类型错误")
            return False
        
        # 验证结果的合理性
        if result.total_whitespace < 0:
            print(f"❌ 总空白面积为负: {result.total_whitespace}")
            return False
        
        if not 0 <= result.whitespace_ratio <= 1:
            print(f"❌ 空白比率超出范围: {result.whitespace_ratio}")
            return False
        
        if result.utilizable_whitespace > result.total_whitespace:
            print(f"❌ 可利用空白大于总空白: {result.utilizable_whitespace} > {result.total_whitespace}")
            return False
        
        if not 0 <= result.fragmentation_index <= 1:
            print(f"❌ 碎片化指数超出范围: {result.fragmentation_index}")
            return False
        
        # 测试利用率热力图
        utilization_map = analyzer.get_utilization_map(design)
        if utilization_map.shape != (50, 50):
            print(f"❌ get_utilization_map() 尺寸错误: {utilization_map.shape}")
            return False
        
        # 测试密度图
        density_map = analyzer.calculate_density_map(design, window_size=5)
        if density_map.shape != utilization_map.shape:
            print(f"❌ calculate_density_map() 尺寸不匹配")
            return False
        
        # 测试优化建议
        suggestions = analyzer.suggest_improvements(design)
        if not isinstance(suggestions, list):
            print(f"❌ suggest_improvements() 返回类型错误")
            return False
        
        print("✅ 空白区域模块自检通过")
        print(f"   - 空白比率: {ws_ratio:.3f}")
        print(f"   - 分布区域数: {len(ws_distribution)}")
        print(f"   - 总空白面积: {result.total_whitespace:.0f}")
        print(f"   - 可利用空白: {result.utilizable_whitespace:.0f}")
        print(f"   - 碎片化指数: {result.fragmentation_index:.3f}")
        print(f"   - 空白区域数: {len(result.whitespace_regions)}")
        print(f"   - 最大区域面积: {result.largest_region_area:.0f}")
        print(f"   - 优化建议: {len(suggestions)} 条")
        print(f"   - 利用率地图: {utilization_map.shape}, 平均利用率: {utilization_map.mean():.3f}")
        
        # 验证空白检测的准确性
        if result.whitespace_ratio > 0:
            print(f"   ✓ 成功检测到空白区域")
        else:
            print("   ⚠️  警告: 未检测到空白区域（可能布局过于紧凑）")
        
        return True
        
    except Exception as e:
        print(f"❌ 空白区域模块自检失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def output_whitespace_debug_info(design: FloorplanDesign, prefix: str = "  ") -> str:
    """
    输出空白区域模块的调试信息
    Output debug information for whitespace module
    """
    try:
        ws_ratio = calculate_whitespace_ratio(design)
        analyzer = WhitespaceAnalyzer(grid_resolution=50, min_utilizable_area=100.0)
        result = analyzer.analyze(design)
        suggestions = analyzer.suggest_improvements(design)
        utilization_map = analyzer.get_utilization_map(design)
        density_map = analyzer.calculate_density_map(design)
        
        debug_info = f"{prefix}=== 空白区域模块调试信息 ===\n"
        debug_info += f"{prefix}基础统计:\n"
        debug_info += f"{prefix}  - 空白比率: {ws_ratio:.3f}\n"
        debug_info += f"{prefix}  - 总空白面积: {result.total_whitespace:.0f}\n"
        debug_info += f"{prefix}  - 可利用空白: {result.utilizable_whitespace:.0f}\n"
        debug_info += f"{prefix}  - 不可利用空白: {result.unusable_whitespace:.0f}\n"
        debug_info += f"{prefix}  - 碎片化指数: {result.fragmentation_index:.3f}\n"
        
        debug_info += f"{prefix}区域分析:\n"
        debug_info += f"{prefix}  - 空白区域数: {len(result.whitespace_regions)}\n"
        debug_info += f"{prefix}  - 最大区域面积: {result.largest_region_area:.0f}\n"
        debug_info += f"{prefix}  - 平均区域面积: {result.avg_region_area:.0f}\n"
        
        # 可利用区域统计
        utilizable_regions = [r for r in result.whitespace_regions if r.is_utilizable]
        debug_info += f"{prefix}  - 可利用区域数: {len(utilizable_regions)}\n"
        
        if utilizable_regions:
            largest_utilizable = max(utilizable_regions, key=lambda r: r.area)
            debug_info += f"{prefix}  - 最大可利用区域: {largest_utilizable.area:.0f} "
            debug_info += f"at ({largest_utilizable.x:.0f}, {largest_utilizable.y:.0f})\n"
        
        debug_info += f"{prefix}热力图分析:\n"
        debug_info += f"{prefix}  - 网格分辨率: {utilization_map.shape}\n"
        debug_info += f"{prefix}  - 平均利用率: {utilization_map.mean():.3f}\n"
        debug_info += f"{prefix}  - 最大密度: {density_map.max():.3f}\n"
        debug_info += f"{prefix}  - 低密度区域: {(density_map < 0.3).sum()} 网格\n"
        
        # 优化建议
        debug_info += f"{prefix}优化建议 ({len(suggestions)} 条):\n"
        for i, suggestion in enumerate(suggestions[:3], 1):
            debug_info += f"{prefix}  {i}. {suggestion}\n"
        
        return debug_info
        
    except Exception as e:
        return f"{prefix}空白区域模块调试信息获取失败: {e}\n"


# 导出函数和类
__all__ = [
    'calculate_whitespace_ratio',
    'analyze_whitespace_distribution',
    'WhitespaceAnalyzer',
    'WhitespaceRegion',
    'WhitespaceResult',
    'self_check_whitespace',
    'output_whitespace_debug_info'
] 
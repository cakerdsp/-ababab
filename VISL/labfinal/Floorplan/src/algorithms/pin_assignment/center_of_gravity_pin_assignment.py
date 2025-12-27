import math
import time
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass

try:
    from ...data.structures import FloorplanDesign, Module, ModuleType
except ImportError:
    # 适用于独立测试
    from data.structures import FloorplanDesign, Module, ModuleType


@dataclass
class CenterOfGravityConfig:
    """重心法Pin分配配置"""
    expansion_ratio: float = 1.1        # 芯片扩展比例
    verbose: bool = False               # 详细输出
    prefer_corner_pins: bool = False    # 是否优先放置角落Pin（在均匀分布模式下通常关闭）
    congestion_avoidance: bool = False  # 拥塞避免（在均匀分布下意义不大，因为每个slot只放一个pin）
    max_pins_per_edge_unit: int = 1     # 每个边缘单位最大Pin数


class CenterOfGravityPinAssignment:
    """
    重心法Pin分配器 - 使用重心法快速分配Pin到芯片边缘的均匀分布点位
    """
    
    def __init__(self, config: Optional[CenterOfGravityConfig] = None):
        self.config = config or CenterOfGravityConfig()
        self.verbose = self.config.verbose
        self.assignment_count = 0
        self.total_assignment_time = 0.0

    def assign_pins(self, design: FloorplanDesign) -> FloorplanDesign:
        """
        执行Pin分配 - Pin将被均匀地分配到芯片边缘的整数坐标上
        """
        start_time = time.time()
        
        pins = [m for m in design.modules.values() if m.module_type == ModuleType.TERMINAL]
        if not pins:
            return design

        # 1. 计算当前宏模块布局的实际边界和尺寸
        bounds = self._calculate_macro_bounds(design)
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        
        # 2. 检查并按需扩展芯片尺寸，确保周长足够大以避免插槽重叠
        #    一个简单的标准：周长至少是引脚数的两倍
        perimeter = 2 * (int(width) + int(height))
        if perimeter < len(pins) * 2:
            width, height = self._expand_chip_for_pins(width, height, len(pins) * 2)
            
            # 更新扩展后的边界
            bounds['max_x'] = bounds['min_x'] + width
            bounds['max_y'] = bounds['min_y'] + height

        # 3. ✨ 核心修改：生成均匀分布的插槽
        available_slots = self._generate_uniform_slots(
            len(pins), 
            int(width), 
            int(height),
            int(bounds['min_x']),
            int(bounds['min_y'])
        )
        
        # 4. 执行分配
        self._assign_pins_to_slots(pins, design, available_slots)
        
        # 5. 更新design对象的最终尺寸
        design.chip_width = math.ceil(bounds['max_x'])
        design.chip_height = math.ceil(bounds['max_y'])
        
        self.assignment_count += 1
        self.total_assignment_time += time.time() - start_time
        return design

    def _assign_pins_to_slots(self, pins: List[Module], design: FloorplanDesign, slots: List[Tuple[int, int]]):
        """将Pin分配到给定的插槽中"""
        pin_to_nets = self._build_pin_to_nets_mapping(pins, design)
        sorted_pins = self._sort_pins_by_network_priority(pins, pin_to_nets)
        
        available_slots = list(slots)
        
        for pin in sorted_pins:
            gravity_center = self._calculate_gravity_center(pin, design, pin_to_nets)
            
            if not available_slots:
                if self.verbose:
                    print(f"⚠️ 警告: 没有足够的可用插槽来放置Pin {pin.name}")
                # 作为后备，将pin放在原点或某个角落
                pin.set_position(0.0, 0.0)
                continue

            # 寻找离重心最近的可用插槽
            best_slot = min(
                available_slots, 
                key=lambda s: math.sqrt((s[0] - gravity_center[0])**2 + (s[1] - gravity_center[1])**2)
            )
            
            pin.set_position(float(best_slot[0]), float(best_slot[1]))
            available_slots.remove(best_slot)

    # ✨ NEW: 新增的核心函数，用于生成均匀分布的插槽
    def _generate_uniform_slots(self, num_pins: int, width: int, height: int, min_x: int = 0, min_y: int = 0) -> List[Tuple[int, int]]:
        """在芯片边缘生成N个均匀分布的整数坐标插槽"""
        if num_pins == 0:
            return []
            
        slots = []
        perimeter = 2 * (width + height)
        
        # 如果周长为0，无法分配
        if perimeter == 0:
            return [(min_x, min_y)] * num_pins

        # 计算每个插槽的间距
        spacing = perimeter / num_pins
        
        for i in range(num_pins):
            distance_along_edge = i * spacing
            
            x, y = 0, 0
            
            # 根据距离分配到四个边缘
            if distance_along_edge < width:
                # 下边缘
                x = min_x + distance_along_edge
                y = min_y
            elif distance_along_edge < width + height:
                # 右边缘
                x = min_x + width
                y = min_y + (distance_along_edge - width)
            elif distance_along_edge < 2 * width + height:
                # 上边缘
                x = min_x + width - (distance_along_edge - (width + height))
                y = min_y + height
            else:
                # 左边缘
                x = min_x
                y = min_y + height - (distance_along_edge - (2 * width + height))

            slots.append((round(x), round(y)))
            
        # 去除因四舍五入可能产生的重复点位
        # 使用dict来去重并保持顺序
        return list(dict.fromkeys(slots))

    def _calculate_macro_bounds(self, design: FloorplanDesign) -> Dict[str, float]:
        """计算基于宏模块的实际布局边界"""
        macro_modules = [m for m in design.modules.values() 
                         if m.module_type in [ModuleType.SOFT, ModuleType.HARD]]
        
        if not macro_modules:
            return {'min_x': 0.0, 'min_y': 0.0, 'max_x': 100.0, 'max_y': 100.0}
        
        min_x = min(m.x for m in macro_modules)
        min_y = min(m.y for m in macro_modules)
        max_x = max(m.x + m.width for m in macro_modules)
        max_y = max(m.y + m.height for m in macro_modules)
        
        return {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y}

    def _expand_chip_for_pins(self, width: float, height: float, required_perimeter: int) -> Tuple[float, float]:
        """按比例扩展芯片以满足周长要求"""
        current_perimeter = 2 * (int(width) + int(height))
        
        while current_perimeter < required_perimeter:
            width *= self.config.expansion_ratio
            height *= self.config.expansion_ratio
            current_perimeter = 2 * (int(width) + int(height))
        
        return math.ceil(width), math.ceil(height)

    # 以下是无需修改的辅助函数
    def _build_pin_to_nets_mapping(self, pins: List[Module], design: FloorplanDesign) -> Dict[str, List[str]]:
        pin_to_nets = {}
        pin_names = {p.name for p in pins}
        for net_name, net in design.nets.items():
            for module_name, _ in net.pins:
                if module_name in pin_names:
                    if module_name not in pin_to_nets:
                        pin_to_nets[module_name] = []
                    pin_to_nets[module_name].append(net_name)
        return pin_to_nets

    def _sort_pins_by_network_priority(self, pins: List[Module], pin_to_nets: Dict[str, List[str]]) -> List[Module]:
        return sorted(pins, key=lambda p: len(pin_to_nets.get(p.name, [])), reverse=True)

    def _calculate_gravity_center(self, pin: Module, design: FloorplanDesign, pin_to_nets: Dict[str, List[str]]) -> Tuple[float, float]:
        connected_nets = pin_to_nets.get(pin.name, [])
        connected_positions = []
        
        for net_name in connected_nets:
            net = design.nets.get(net_name)
            if net:
                for module_name, _ in net.pins:
                    if module_name != pin.name and module_name in design.modules:
                        module = design.modules[module_name]
                        # 只考虑宏模块的重心
                        if module.module_type in [ModuleType.SOFT, ModuleType.HARD]:
                            connected_positions.append(module.get_center())
        
        if not connected_positions:
            # 如果没有连接的宏模块，重心视为芯片中心
            bounds = self._calculate_macro_bounds(design)
            return ((bounds['min_x'] + bounds['max_x']) / 2, (bounds['min_y'] + bounds['max_y']) / 2)
        
        avg_x = sum(pos[0] for pos in connected_positions) / len(connected_positions)
        avg_y = sum(pos[1] for pos in connected_positions) / len(connected_positions)
        return avg_x, avg_y

    def get_statistics(self) -> Dict:
        """获取性能统计信息"""
        # ... (此函数无需修改)
        pass
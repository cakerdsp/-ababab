#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据解析器 - Data Parsers

解析GSRC和MCNC格式的布图数据文件
Parsers for GSRC and MCNC format floorplan data files
"""

import re
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
from .structures import Module, Net, FloorplanDesign, ModuleType, Pin


class GSRCParser:
    """
    GSRC格式解析器 - GSRC Format Parser
    
    解析GSRC基准测试集的.blocks, .nets, .pl文件
    Parses GSRC benchmark .blocks, .nets, .pl files
    """
    
    def __init__(self):
        self.design_name = ""
        self.verbose = False  # 添加verbose属性
        
    def parse_blocks_file(self, filepath: str) -> Dict[str, Module]:
        """
        解析.blocks文件 - Parse .blocks file
        
        格式示例:
        UCSC blocks 1.0
        NumSoftRectangularBlocks : 10
        NumHardRectilinearBlocks : 0
        NumTerminals : 69
        
        sb0 softrectangular 16318 0.300 3.000
        bk1 hardrectilinear 4 (0, 0) (0, 133) (336, 133) (336, 0)
        p1 terminal
        """
        modules = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析模块信息
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('UCSC'):
                continue
            
            # 跳过统计信息行，但要容错处理格式问题
            if ('NumSoftRectangularBlocks' in line or 
                'NumHardRectilinearBlocks' in line or 
                'NumTerminals' in line):
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
            
            module_name = parts[0]
            module_type_str = parts[1].lower()
            
            try:
                if 'softrectangular' in module_type_str:
                    # 软模块：sb0 softrectangular 16318 0.300 3.000
                    if len(parts) >= 5:
                        area = float(parts[2])
                        min_ratio = float(parts[3])
                        max_ratio = float(parts[4])
                        
                        module = Module(module_name, ModuleType.SOFT)
                        module.area = area
                        module.min_aspect_ratio = min_ratio
                        module.max_aspect_ratio = max_ratio
                        
                        # 计算初始尺寸
                        aspect_ratio = (min_ratio + max_ratio) / 2
                        module.width = np.sqrt(area * aspect_ratio)
                        module.height = area / module.width
                        
                        modules[module_name] = module
                
                elif 'hardrectilinear' in module_type_str:
                    # 硬模块：bk1 hardrectilinear 4 (0, 0) (0, 133) (336, 133) (336, 0)
                    if len(parts) >= 4:
                        vertex_count = int(parts[2])
                        
                        # 解析顶点坐标
                        vertices = []
                        coord_str = ' '.join(parts[3:])
                        
                        # 提取括号中的坐标
                        coords = re.findall(r'\(([-\d\.]+),\s*([-\d\.]+)\)', coord_str)
                        
                        for coord in coords:
                            x, y = float(coord[0]), float(coord[1])
                            vertices.append((x, y))
                        
                        if len(vertices) >= 3:  # 至少需要3个顶点
                            module = Module(module_name, ModuleType.HARD)
                            module.vertices = vertices
                            
                            # 计算边界框
                            xs = [v[0] for v in vertices]
                            ys = [v[1] for v in vertices]
                            module.width = max(xs) - min(xs)
                            module.height = max(ys) - min(ys)
                            module.area = module.width * module.height
                            
                            modules[module_name] = module
                
                elif 'terminal' in module_type_str:
                    # 端口模块：p1 terminal
                    module = Module(module_name, ModuleType.TERMINAL)
                    module.width = 1.0  # 端口默认尺寸
                    module.height = 1.0
                    module.area = 1.0
                    module.is_fixed = False
                    
                    modules[module_name] = module
                    
            except (ValueError, IndexError) as e:
                print(f"警告：解析模块 {module_name} 时出错: {e}")
                continue
        
        return modules
    
    def parse_nets_file(self, filepath: str) -> Dict[str, Net]:
        """
        解析.nets文件 - Parse .nets file
        
        🔧 **CRITICAL FIX**: 正确处理引脚方向标识符，而不是错误地当作引脚名
        
        格式示例:
        UCLA nets 1.0
        NumNets : 118
        NumPins : 248
        
        NetDegree : 2
        p1 B        # B是方向标识符(bidirectional)，不是引脚名
        sb6 B       # B是方向标识符(bidirectional)，不是引脚名
        NetDegree : 2
        p2 I        # I是方向标识符(input)，不是引脚名
        sb8 O       # O是方向标识符(output)，不是引脚名
        """
        nets = {}
        current_net_id = 0
        current_pins = []
        reading_pins = False
        
        # 🔧 **CRITICAL FIX**: 定义引脚方向标识符
        PIN_DIRECTIONS = {'I', 'O', 'B', 'IO', 'input', 'output', 'bidirectional'}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('UCLA'):
                continue
            
            # 跳过统计信息行
            if ('NumNets' in line or 'NumPins' in line):
                continue
                
            # 开始新的网络
            if line.startswith('NetDegree'):
                # 如果之前有网络，先保存
                if current_pins:
                    net_name = f"net_{current_net_id}"
                    pins = []
                    for pin_info in current_pins:
                        parts = pin_info.strip().split()
                        if len(parts) >= 1:
                            module_name = parts[0]  # 模块名
                            
                            # 🔧 **CRITICAL FIX**: 正确处理引脚方向标识符
                            if len(parts) >= 2 and parts[1] in PIN_DIRECTIONS:
                                # 第二个字段是方向标识符，使用默认引脚名
                                pin_name = "default"
                            elif len(parts) >= 2:
                                # 第二个字段是真正的引脚名
                                pin_name = parts[1]
                            else:
                                # 只有模块名，使用默认引脚名
                                pin_name = "default"
                            
                            pins.append((module_name, pin_name))
                        
                    if len(pins) >= 2:  # 至少需要2个引脚的网络才有意义
                        nets[net_name] = Net(net_name, pins)
                    current_net_id += 1
                
                # 重置状态
                current_pins = []
                reading_pins = True
                continue
            
            # 读取引脚信息
            if reading_pins and line:
                parts = line.split()
                if parts:
                    current_pins.append(line)
        
        # 处理最后一个网络
        if current_pins:
            net_name = f"net_{current_net_id}"
            pins = []
            for pin_info in current_pins:
                parts = pin_info.strip().split()
                if len(parts) >= 1:
                    module_name = parts[0]  # 模块名
                    
                    # 🔧 **CRITICAL FIX**: 正确处理引脚方向标识符
                    if len(parts) >= 2 and parts[1] in PIN_DIRECTIONS:
                        # 第二个字段是方向标识符，使用默认引脚名
                        pin_name = "default"
                    elif len(parts) >= 2:
                        # 第二个字段是真正的引脚名
                        pin_name = parts[1]
                    else:
                        # 只有模块名，使用默认引脚名
                        pin_name = "default"
                    
                    pins.append((module_name, pin_name))
                
            if len(pins) >= 2:
                nets[net_name] = Net(net_name, pins)
        
        return nets
    
    def parse_pl_file(self, filepath: str, modules: Dict[str, Module]) -> Dict[str, Module]:
        """
        解析.pl文件 - Parse .pl file
        
        格式示例:
        UCSC pl 1.0
        
        sb0    152    284
        sb1    348    284
        bk1    520    284
        
        p1     0      900
        p2     0      800
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 跳过空行和注释行，直到找到模块位置定义
        movable_section = True
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#') or line.startswith('UCSC'):
                continue
            
            # 检查是否到了固定模块（terminal）部分
            if line == "":
                movable_section = False
                continue
            
            parts = line.split()
            if len(parts) >= 3:
                module_name = parts[0]
                x = float(parts[1])
                y = float(parts[2])
                
                if module_name in modules:
                    modules[module_name].set_position(x, y)
                    
                    # 🔧 **CRITICAL FIX**: Pin也是可以移动的，不设置Terminal模块为固定
                    # if modules[module_name].module_type == ModuleType.TERMINAL:
                    #     modules[module_name].is_fixed = True
        
        return modules
    
    def parse_design(self, base_path: str, design_name: str, load_pin_positions: bool = False) -> FloorplanDesign:
        """
        解析GSRC格式设计 - Parse GSRC format design
        
        Args:
            base_path: 数据集根目录
            design_name: 设计名称
            load_pin_positions: 是否从pl文件加载引脚位置（新分离架构下默认为False）
        """
        self.design_name = design_name
        
        # 文件路径
        blocks_file = os.path.join(base_path, f"{design_name}.blocks")
        nets_file = os.path.join(base_path, f"{design_name}.nets")
        pl_file = os.path.join(base_path, f"{design_name}.pl")
        
        if self.verbose:
            print(f"解析GSRC设计: {design_name}")
            print(f"  blocks文件: {blocks_file}")
            print(f"  nets文件: {nets_file}")
            print(f"  pl文件: {pl_file}")
            print(f"  加载引脚位置: {load_pin_positions}")
        
        # 解析模块信息
        modules = self.parse_blocks_file(blocks_file)
        
        # 🔧 **新架构修改**: 为引脚设置默认尺寸，但不从pl文件加载位置
        for module in modules.values():
            if module.module_type == ModuleType.TERMINAL:
                # 给引脚设置标准尺寸（1.0x1.0）
                module.width = 1.0
                module.height = 1.0
                module.area = 1.0
                # 不设置位置，位置将由引脚布置算法决定
        
        # 解析网络信息
        nets = self.parse_nets_file(nets_file)
        
        # 🔧 **分离架构**: 只在明确要求时才加载引脚位置
        if load_pin_positions and os.path.exists(pl_file):
            modules = self.parse_pl_file(pl_file, modules)
            if self.verbose:
                print(f"  从pl文件加载了位置信息")
        else:
            # 只为宏模块加载位置信息（如果pl文件存在）
            if os.path.exists(pl_file):
                macro_modules = {name: module for name, module in modules.items() 
                               if module.module_type in [ModuleType.SOFT, ModuleType.HARD]}
                self.parse_pl_file(pl_file, macro_modules)
                # 将更新后的宏模块位置复制回去
                for name, module in macro_modules.items():
                    if name in modules:
                        modules[name].set_position(module.x, module.y)
                if self.verbose:
                    print(f"  只加载了宏模块的位置信息，跳过引脚位置")
        
        # 创建设计
        design = FloorplanDesign(design_name)
        
        # 添加模块
        for module in modules.values():
            design.add_module(module)
        
        # 添加网络
        for net in nets.values():
            design.add_net(net)
        
        # 计算芯片尺寸（基于宏模块包围盒）
        macro_modules = {name: module for name, module in modules.items() 
                        if module.module_type in [ModuleType.SOFT, ModuleType.HARD]}
        if macro_modules:
            min_x = min(m.x for m in macro_modules.values())
            min_y = min(m.y for m in macro_modules.values())
            max_x = max(m.x + m.width for m in macro_modules.values())
            max_y = max(m.y + m.height for m in macro_modules.values())
            
            design.chip_width = max_x - min_x if max_x > min_x else 100.0
            design.chip_height = max_y - min_y if max_y > min_y else 100.0
        else:
            design.chip_width = 100.0
            design.chip_height = 100.0
        
        if self.verbose:
            print(f"设计解析完成:")
            print(f"  总模块数: {len(modules)}")
            print(f"  软模块: {sum(1 for m in modules.values() if m.module_type == ModuleType.SOFT)}")
            print(f"  硬模块: {sum(1 for m in modules.values() if m.module_type == ModuleType.HARD)}")
            print(f"  引脚数: {sum(1 for m in modules.values() if m.module_type == ModuleType.TERMINAL)}")
            print(f"  网络数: {len(nets)}")
            print(f"  芯片尺寸: {design.chip_width:.1f} x {design.chip_height:.1f}")
        
        return design


class MCNCParser:
    """
    MCNC格式解析器 - MCNC Format Parser
    
    解析MCNC基准测试集的数据文件
    Parses MCNC benchmark data files
    """
    
    def __init__(self):
        self.design_name = ""
        self.verbose = False  # 添加verbose属性
    
    def parse_blocks_file(self, filepath: str) -> Dict[str, Module]:
        """
        解析MCNC格式的.blocks文件
        Parse MCNC format .blocks file
        
        🔧 **核心修复**: 正确解析MCNC格式
        
        MCNC真实格式：
        bk1 softrectangular 44688 0.395 2.526  # 模块名 类型 面积 最小长宽比 最大长宽比
        VSS terminal                           # 模块名 类型
        """
        modules = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 跳过空行、注释行和头信息
            if not line or line.startswith('#') or line.startswith('UCSC') or 'Num' in line:
                continue
            
            try:
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                module_name = parts[0]
                
                # 🔧 **CRITICAL FIX**: 为所有模块类型处理重复模块名
                original_name = module_name
                counter = 1
                while module_name in modules:
                    module_name = f"{original_name}_{counter}"
                    counter += 1
                
                # 检查是否是terminal模块
                if len(parts) == 2 and parts[1] == 'terminal':
                    # Terminal模块: "VSS terminal"
                    # 🔧 **CRITICAL FIX**: Pin也是可以移动的，不设置is_fixed=True
                    module = Module(
                        name=module_name,
                        module_type=ModuleType.TERMINAL,
                        width=0.0,
                        height=0.0,
                        area=0.0,
                        is_fixed=False  # Pin也可以移动
                    )
                elif len(parts) >= 5 and parts[1] == 'softrectangular':
                    # 软模块: "bk1 softrectangular 44688 0.395 2.526"
                    area = float(parts[2])
                    min_aspect = float(parts[3])
                    max_aspect = float(parts[4])
                    
                    # 根据面积和长宽比计算初始尺寸
                    # 使用几何平均长宽比
                    aspect_ratio = (min_aspect * max_aspect) ** 0.5
                    width = (area * aspect_ratio) ** 0.5
                    height = area / width
                    
                    module = Module(
                        name=module_name,
                        module_type=ModuleType.SOFT,
                        width=width,
                        height=height,
                        area=area,
                        min_aspect_ratio=min_aspect,
                        max_aspect_ratio=max_aspect
                    )
                elif len(parts) >= 5 and parts[1] == 'hardrectilinear':
                    # 硬模块格式（如果存在）
                    # 这个格式比较复杂，现在先简单处理
                    area = float(parts[2]) if len(parts) > 2 else 0
                    module = Module(
                        name=module_name,
                        module_type=ModuleType.HARD,
                        width=100.0,  # 临时值
                        height=100.0,  # 临时值
                        area=area
                    )
                else:
                    # 跳过无法识别的行
                    if self.verbose:
                        print(f"警告：第{line_num}行格式无法识别: {line}")
                    continue
                
                modules[module_name] = module
                
            except (ValueError, IndexError) as e:
                if self.verbose:
                    print(f"警告：第{line_num}行解析失败: {line} - {e}")
                continue
        
        return modules
    
    def parse_nets_file(self, filepath: str) -> Dict[str, Net]:
        """
        解析MCNC格式的.nets文件
        Parse MCNC format .nets file
        
        🔧 **核心修复**: 实现完整的MCNC nets文件解析功能
        
        MCNC格式示例：
        NetDegree : 2
        p1 I
        a O
        NetDegree : 3  
        p2 I
        a I
        b O
        """
        nets = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_net_id = 1
        current_pins = []
        current_net_degree = 0
        reading_pins = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue
            
            try:
                # 检查是否是网络度数定义
                if line.startswith('NetDegree') or 'netdegree' in line.lower():
                    # 保存之前的网络
                    if current_pins and len(current_pins) >= 2:
                        net_name = f"net_{current_net_id}"
                        pins = []
                        for pin_info in current_pins:
                            parts = pin_info.strip().split()
                            if len(parts) >= 1:
                                module_name = parts[0]
                                # 🔧 **CRITICAL FIX**: 正确处理引脚方向标识符
                                if len(parts) >= 2 and parts[1] in ['I', 'O', 'B', 'IO']:
                                    # 第二个字段是方向标识符，使用默认引脚名
                                    pin_name = "default"
                                elif len(parts) >= 2:
                                    # 第二个字段是真正的引脚名
                                    pin_name = parts[1]
                                else:
                                    # 只有模块名，使用默认引脚名
                                    pin_name = "default"
                                pins.append((module_name, pin_name))
                        
                        if len(pins) >= 2:
                            nets[net_name] = Net(net_name, pins)
                        current_net_id += 1
                    
                    # 解析新的网络度数
                    parts = line.split()
                    if len(parts) >= 3:  # NetDegree : X
                        try:
                            current_net_degree = int(parts[2])
                        except ValueError:
                            current_net_degree = 0
                    
                    # 重置状态
                    current_pins = []
                    reading_pins = True
                    continue
                
                # 读取引脚信息
                if reading_pins and line:
                    current_pins.append(line)
                    
                    # 如果已收集足够的引脚，处理这个网络
                    if current_net_degree > 0 and len(current_pins) >= current_net_degree:
                        reading_pins = False
                
            except Exception as e:
                if self.verbose:
                    print(f"警告：第{line_num}行解析失败: {line} - {e}")
                continue
        
        # 处理最后一个网络
        if current_pins and len(current_pins) >= 2:
            net_name = f"net_{current_net_id}"
            pins = []
            for pin_info in current_pins:
                parts = pin_info.strip().split()
                if len(parts) >= 1:
                    module_name = parts[0]
                    # 🔧 **CRITICAL FIX**: 正确处理引脚方向标识符
                    if len(parts) >= 2 and parts[1] in ['I', 'O', 'B', 'IO']:
                        # 第二个字段是方向标识符，使用默认引脚名
                        pin_name = "default"
                    elif len(parts) >= 2:
                        # 第二个字段是真正的引脚名
                        pin_name = parts[1]
                    else:
                        # 只有模块名，使用默认引脚名
                        pin_name = "default"
                    pins.append((module_name, pin_name))
            
            if len(pins) >= 2:
                nets[net_name] = Net(net_name, pins)
        
        return nets
    
    def parse_pl_file(self, filepath: str, modules: Dict[str, Module]) -> Dict[str, Module]:
        """
        解析MCNC格式的.pl文件
        Parse MCNC format .pl file
        
        🔧 **核心修复**: 实现完整的MCNC placement文件解析功能
        
        MCNC格式示例：
        # placement file for ami33
        p1    0    100
        p2    0    200
        a     100  100
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            try:
                parts = line.split()
                if len(parts) >= 3:
                    module_name = parts[0]
                    x = float(parts[1])
                    y = float(parts[2])
                    
                    if module_name in modules:
                        modules[module_name].set_position(x, y)
                        
                        # 🔧 **CRITICAL FIX**: Pin也是可以移动的，不设置Terminal模块为固定
                        # if modules[module_name].module_type == ModuleType.TERMINAL:
                        #     modules[module_name].is_fixed = True
                            
            except (ValueError, IndexError) as e:
                if self.verbose:
                    print(f"警告：第{line_num}行解析失败: {line} - {e}")
                continue
        
        return modules
    
    def parse_design(self, base_path: str, design_name: str, load_pin_positions: bool = False) -> FloorplanDesign:
        """
        解析MCNC格式设计 - Parse MCNC format design
        
        Args:
            base_path: 数据集根目录
            design_name: 设计名称
            load_pin_positions: 是否从pl文件加载引脚位置（新分离架构下默认为False）
        """
        self.design_name = design_name
        
        # 文件路径
        blocks_file = os.path.join(base_path, f"{design_name}.blocks")
        nets_file = os.path.join(base_path, f"{design_name}.nets")
        pl_file = os.path.join(base_path, f"{design_name}.pl")
        
        if self.verbose:
            print(f"解析MCNC设计: {design_name}")
            print(f"  blocks文件: {blocks_file}")
            print(f"  nets文件: {nets_file}")
            print(f"  pl文件: {pl_file}")
            print(f"  加载引脚位置: {load_pin_positions}")
        
        # 解析模块信息
        modules = self.parse_blocks_file(blocks_file)
        
        # 🔧 **新架构修改**: 为引脚设置默认尺寸，但不从pl文件加载位置
        for module in modules.values():
            if module.module_type == ModuleType.TERMINAL:
                # 给引脚设置标准尺寸（1.0x1.0）
                module.width = 1.0
                module.height = 1.0
                module.area = 1.0
                # 不设置位置，位置将由引脚布置算法决定
        
        # 解析网络信息
        nets = self.parse_nets_file(nets_file)
        
        # 🔧 **分离架构**: 只在明确要求时才加载引脚位置
        if load_pin_positions and os.path.exists(pl_file):
            modules = self.parse_pl_file(pl_file, modules)
            if self.verbose:
                print(f"  从pl文件加载了位置信息")
        else:
            # 只为宏模块加载位置信息（如果pl文件存在）
            if os.path.exists(pl_file):
                macro_modules = {name: module for name, module in modules.items() 
                               if module.module_type in [ModuleType.SOFT, ModuleType.HARD]}
                self.parse_pl_file(pl_file, macro_modules)
                # 将更新后的宏模块位置复制回去
                for name, module in macro_modules.items():
                    if name in modules:
                        modules[name].set_position(module.x, module.y)
                if self.verbose:
                    print(f"  只加载了宏模块的位置信息，跳过引脚位置")
        
        # 创建设计
        design = FloorplanDesign(design_name)
        
        # 添加模块
        for module in modules.values():
            design.add_module(module)
        
        # 添加网络
        for net in nets.values():
            design.add_net(net)
        
        # 计算芯片尺寸（基于宏模块包围盒）
        macro_modules = {name: module for name, module in modules.items() 
                        if module.module_type in [ModuleType.SOFT, ModuleType.HARD]}
        if macro_modules:
            min_x = min(m.x for m in macro_modules.values())
            min_y = min(m.y for m in macro_modules.values())
            max_x = max(m.x + m.width for m in macro_modules.values())
            max_y = max(m.y + m.height for m in macro_modules.values())
            
            design.chip_width = max_x - min_x if max_x > min_x else 100.0
            design.chip_height = max_y - min_y if max_y > min_y else 100.0
        else:
            design.chip_width = 100.0
            design.chip_height = 100.0
        
        if self.verbose:
            print(f"设计解析完成:")
            print(f"  总模块数: {len(modules)}")
            print(f"  软模块: {sum(1 for m in modules.values() if m.module_type == ModuleType.SOFT)}")
            print(f"  硬模块: {sum(1 for m in modules.values() if m.module_type == ModuleType.HARD)}")
            print(f"  引脚数: {sum(1 for m in modules.values() if m.module_type == ModuleType.TERMINAL)}")
            print(f"  网络数: {len(nets)}")
            print(f"  芯片尺寸: {design.chip_width:.1f} x {design.chip_height:.1f}")
        
        return design


def parse_gsrc_design(base_path: str, design_name: str) -> FloorplanDesign:
    """
    快速解析GSRC设计的便捷函数
    Convenient function to quickly parse GSRC design
    """
    parser = GSRCParser()
    return parser.parse_design(base_path, design_name)


def parse_mcnc_design(base_path: str, design_name: str) -> FloorplanDesign:
    """
    快速解析MCNC设计的便捷函数
    Convenient function to quickly parse MCNC design
    """
    parser = MCNCParser()
    return parser.parse_design(base_path, design_name)


def detect_format(filepath: str) -> str:
    """
    自动检测文件格式
    Automatically detect file format
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    
    if 'UCSC' in first_line:
        return 'GSRC'
    elif 'UCLA' in first_line:
        return 'GSRC'  # UCLA格式也归类为GSRC
    else:
        return 'MCNC'  # 默认为MCNC格式


def auto_parse_design(base_path: str, design_name: str) -> FloorplanDesign:
    """
    自动检测格式并解析设计
    Automatically detect format and parse design
    """
    blocks_file = os.path.join(base_path, f"{design_name}.blocks")
    
    if os.path.exists(blocks_file):
        format_type = detect_format(blocks_file)
        
        if format_type == 'GSRC':
            return parse_gsrc_design(base_path, design_name)
        else:
            return parse_mcnc_design(base_path, design_name)
    else:
        raise FileNotFoundError(f"Blocks file not found: {blocks_file}")


def load_gsrc_design(design_name: str, load_pin_positions: bool = False, 
                    pin_width: float = 1.0, pin_height: float = 1.0) -> FloorplanDesign:
    """
    加载GSRC设计的便捷函数 - Convenient function to load GSRC design
    
    Args:
        design_name: 设计名称
        load_pin_positions: 是否从pl文件加载引脚位置
        pin_width: 引脚宽度
        pin_height: 引脚高度
    """
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'benchmarks', 'GSRC', 'SOFT')
    base_path = os.path.abspath(base_path)
    
    # 使用解析器
    parser = GSRCParser()
    design = parser.parse_design(base_path, design_name, load_pin_positions)
    
    # 设置引脚尺寸
    for module in design.modules.values():
        if module.module_type == ModuleType.TERMINAL:
            module.width = pin_width
            module.height = pin_height
            module.area = pin_width * pin_height
    
    return design


def load_mcnc_design(design_name: str, load_pin_positions: bool = False,
                    pin_width: float = 1.0, pin_height: float = 1.0) -> FloorplanDesign:
    """
    加载MCNC设计的便捷函数 - Convenient function to load MCNC design
    
    Args:
        design_name: 设计名称
        load_pin_positions: 是否从pl文件加载引脚位置
        pin_width: 引脚宽度
        pin_height: 引脚高度
    """
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'benchmarks', 'MCNC', 'SOFT')
    base_path = os.path.abspath(base_path)
    
    # 使用解析器
    parser = MCNCParser()
    design = parser.parse_design(base_path, design_name, load_pin_positions)
    
    # 设置引脚尺寸
    for module in design.modules.values():
        if module.module_type == ModuleType.TERMINAL:
            module.width = pin_width
            module.height = pin_height
            module.area = pin_width * pin_height
    
    return design


# 导出主要函数
__all__ = [
    'GSRCParser',
    'MCNCParser',
    'parse_gsrc_design',
    'parse_mcnc_design',
    'load_gsrc_design',
    'load_mcnc_design',
    'auto_parse_design',
    'detect_format'
] 
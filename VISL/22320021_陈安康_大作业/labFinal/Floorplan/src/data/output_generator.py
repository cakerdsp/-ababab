#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
输出生成器 - Output Generator

负责生成.pl文件和组织结果文件夹结构
Responsible for generating .pl files and organizing result folder structure
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from .structures import FloorplanDesign, Module, ModuleType


class ResultOrganizer:
    """
    结果组织器 - Result Organizer
    
    负责组织每次规划结果的文件夹结构
    """
    
    def __init__(self, base_output_dir: str = "results"):
        """
        初始化结果组织器
        
        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = Path(base_output_dir)
        
    def create_result_folder(self, config: Dict[str, Any], run_id: int = 0) -> Path:
        """
        创建单次规划的结果文件夹
        
        Args:
            config: 配置信息
            run_id: 运行编号
            
        Returns:
            Path: 结果文件夹路径
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        dataset = config.get('dataset', 'unknown')
        benchmark = config.get('benchmark', 'unknown')
        algorithm = config.get('algorithm', 'unknown')
        representation = config.get('representation', 'unknown')
        
        # 创建文件夹名称：dataset_benchmark_algorithm_representation_timestamp_runX
        folder_name = f"{dataset}_{benchmark}_{algorithm}_{representation}_{timestamp}"
        if config.get('runs', 1) > 1:
            folder_name += f"_run{run_id}"
            
        result_folder = self.base_output_dir / folder_name
        result_folder.mkdir(parents=True, exist_ok=True)
        
        # 创建子文件夹
        (result_folder / "visualization").mkdir(exist_ok=True)
        
        return result_folder
    
    def save_result_set(self, design: FloorplanDesign, config: Dict[str, Any], 
                       optimization_result: Dict[str, Any], evaluation_result: Dict[str, Any],
                       run_id: int = 0) -> Path:
        """
        保存完整的结果集
        
        Args:
            design: 布图设计
            config: 配置信息
            optimization_result: 优化结果
            evaluation_result: 评估结果
            run_id: 运行编号
            
        Returns:
            Path: 结果文件夹路径
        """
        result_folder = self.create_result_folder(config, run_id)
        
        # 1. 生成.pl文件
        pl_generator = PlacementFileGenerator()
        pl_file_path = result_folder / f"{config['benchmark']}.pl"
        pl_generator.generate_pl_file(design, config, str(pl_file_path))
        
        # 2. 保存评估统计数据（不包含布局信息）
        evaluation_file = result_folder / "evaluation.json"
        self.save_evaluation_metadata(evaluation_result, config, optimization_result, evaluation_file)
        
        # 3. 可视化文件夹已经创建，可视化图片会在优化过程中保存到这里
        
        return result_folder
    
    def save_evaluation_metadata(self, evaluation_result: Dict[str, Any], 
                                config: Dict[str, Any], optimization_result: Dict[str, Any],
                                file_path: Path):
        """
        保存评估元数据（不包含布局位置信息）
        
        Args:
            evaluation_result: 评估结果
            config: 配置信息
            optimization_result: 优化结果
            file_path: 输出文件路径
        """
        # 构建元数据（排除布局位置信息）
        data_config = config.get('data', {})
        algorithm_config = config.get('algorithm', {})
        evaluation_config = config.get('evaluation', {})
        pin_config = config.get('pin_assignment', {})
        sa_config = config.get('simulated_annealing', {})
        ga_config = config.get('genetic_algorithm', {})
        
        metadata = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "dataset": data_config.get('dataset'),
                "benchmark": data_config.get('benchmark'),
                "algorithm": algorithm_config.get('name'),
                "representation": algorithm_config.get('representation'),
                "module_type": data_config.get('module_type', 'hard'),
                "max_iterations": algorithm_config.get('max_iterations'),
                "seed": config.get('seed'),
                "pin_algorithm": pin_config.get('algorithm'),
                "feedthrough_method": evaluation_config.get('feedthrough_method', 'original'),  # 🎯 新增：feedthrough方法
                # 🎯 更新权重配置 - 支持分离的feedthrough权重
                "weights": {
                    "area_weight": evaluation_config.get('weights', {}).get('area', 0.4),
                    "wirelength_weight": evaluation_config.get('weights', {}).get('hpwl', 0.4),
                    "feedthrough_count_weight": evaluation_config.get('weights', {}).get('feedthrough_count', 
                                               evaluation_config.get('weights', {}).get('feedthrough', 0.1)),
                    "feedthrough_wirelength_weight": evaluation_config.get('weights', {}).get('feedthrough_wirelength', 0.0),
                    "whitespace_weight": evaluation_config.get('weights', {}).get('whitespace', 0.1)
                },
                "algorithm_params": {
                    "simulated_annealing": {
                        "initial_temperature": sa_config.get('initial_temperature'),
                        "final_temperature": sa_config.get('final_temperature'),
                        "cooling_rate": sa_config.get('cooling_rate'),
                        "moves_per_temperature": sa_config.get('moves_per_temperature')
                    } if sa_config else None,
                    "genetic_algorithm": {
                        "population_size": ga_config.get('population_size'),
                        "crossover_rate": ga_config.get('crossover_rate'),
                        "mutation_rate": ga_config.get('mutation_rate')
                    } if ga_config else None,
                    "pin_assignment": {
                        "expansion_ratio": pin_config.get('expansion_ratio'),
                        "prefer_corner_pins": pin_config.get('prefer_corner_pins'),
                        "congestion_avoidance": pin_config.get('congestion_avoidance'),
                        "max_pins_per_edge_unit": pin_config.get('max_pins_per_edge_unit')
                    } if pin_config else None
                }
            },
            "optimization": {
                "iterations": optimization_result.get('iterations', 0),
                "optimization_time": optimization_result.get('optimization_time', 0.0),
                "convergence": optimization_result.get('convergence', False),
                "final_temperature": optimization_result.get('final_temperature'),
                "best_iteration": optimization_result.get('best_iteration', 0)
            },
            "evaluation": {
                # 主要指标
                "area": evaluation_result.get('area', 0.0),
                "wirelength": evaluation_result.get('wirelength', 0.0),
                "hpwl": evaluation_result.get('hpwl', 0.0),
                "feedthrough_count": evaluation_result.get('feedthrough_count', 0),
                "feedthrough_wirelength": evaluation_result.get('feedthrough_wirelength', 0.0),  # 🎯 新增：feedthrough线长
                "feedthrough_method": evaluation_result.get('feedthrough_method', 'original'),    # 🎯 新增：评估方法
                "whitespace_ratio": evaluation_result.get('whitespace_ratio', 0.0),
                
                # 芯片信息
                "chip_width": evaluation_result.get('chip_width', 0.0),
                "chip_height": evaluation_result.get('chip_height', 0.0),
                "utilization": evaluation_result.get('utilization', 0.0),
                "aspect_ratio": evaluation_result.get('aspect_ratio', 0.0),
                
                # 合法性指标
                "is_legal": evaluation_result.get('is_legal', True),
                "overlap_count": evaluation_result.get('overlap_count', 0),
                "overlap_area": evaluation_result.get('overlap_area', 0.0),
                
                # 质量指标
                "quality_score": evaluation_result.get('quality_score', 0.0),
                "total_cost": evaluation_result.get('total_cost', 0.0),
                
                # 统计信息
                "num_modules": evaluation_result.get('num_modules', 0),
                "num_nets": evaluation_result.get('num_nets', 0),
                "max_net_length": evaluation_result.get('max_net_length', 0.0),
                "avg_net_length": evaluation_result.get('avg_net_length', 0.0),
                
                # 🎯 新增：归一化指标
                "normalized_feedthrough_count": evaluation_result.get('normalized_feedthrough_count', 0.0),
                "normalized_feedthrough_wirelength": evaluation_result.get('normalized_feedthrough_wirelength', 0.0),
                
                # 🎯 新增：权重信息
                "weights_used": evaluation_result.get('weights_used', {})
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)


class PlacementFileGenerator:
    """
    布局文件生成器 - Placement File Generator
    
    负责生成.pl格式的布局文件
    """
    
    def generate_pl_file(self, design: FloorplanDesign, config: Dict[str, Any], 
                        output_path: str):
        """
        生成.pl文件
        
        Args:
            design: 布图设计
            config: 配置信息  
            output_path: 输出文件路径
        """
        dataset = config.get('dataset', '').lower()
        
        # 根据数据集选择合适的格式
        if dataset == 'gsrc':
            self._generate_gsrc_pl_file(design, output_path)
        elif dataset == 'mcnc':
            self._generate_mcnc_pl_file(design, output_path)
        else:
            # 默认使用GSRC格式
            self._generate_gsrc_pl_file(design, output_path)
    
    def _generate_gsrc_pl_file(self, design: FloorplanDesign, output_path: str):
        """
        生成GSRC格式的.pl文件
        
        格式：
        UCSC blocks 1.0
        # Created by PyFloorplan
        module_name x y
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头部信息
            f.write("UCSC blocks 1.0\n")
            f.write(f"# Created by PyFloorplan at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Design: {design.name}\n")
            f.write("\n")
            
            # 写入模块位置信息
            # 先写入非终端模块
            for module_name, module in design.modules.items():
                if module.module_type != ModuleType.TERMINAL:
                    f.write(f"{module_name}\t{int(module.x)}\t{int(module.y)}\n")
            
            # 再写入终端模块
            f.write("\n")
            for module_name, module in design.modules.items():
                if module.module_type == ModuleType.TERMINAL:
                    f.write(f"{module_name}\t{int(module.x)}\t{int(module.y)}\n")
    
    def _generate_mcnc_pl_file(self, design: FloorplanDesign, output_path: str):
        """
        生成MCNC格式的.pl文件
        
        格式：
        UCLA pl 1.0
        # Created by PyFloorplan
        module_name x y
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入头部信息
            f.write("UCLA pl 1.0\n")
            f.write(f"# Created by PyFloorplan at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Design: {design.name}\n")
            f.write("\n")
            
            # 写入模块位置信息
            # 先写入非终端模块
            for module_name, module in design.modules.items():
                if module.module_type != ModuleType.TERMINAL:
                    f.write(f"{module_name}\t{int(module.x)}\t{int(module.y)}\n")
            
            # 再写入终端模块
            f.write("\n")
            for module_name, module in design.modules.items():
                if module.module_type == ModuleType.TERMINAL:
                    f.write(f"{module_name}\t{int(module.x)}\t{int(module.y)}\n")


class PlacementFileReader:
    """
    布局文件读取器 - Placement File Reader
    
    负责从.pl文件读取布局信息并应用到设计中
    """
    
    def read_pl_file(self, pl_file_path: str, design: FloorplanDesign) -> bool:
        """
        从.pl文件读取布局信息并应用到设计中
        
        Args:
            pl_file_path: .pl文件路径
            design: 目标设计对象
            
        Returns:
            bool: 是否成功读取
        """
        if not os.path.exists(pl_file_path):
            print(f"错误：.pl文件不存在: {pl_file_path}")
            return False
        
        try:
            with open(pl_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            positions_loaded = 0
            
            for line in lines:
                line = line.strip()
                
                # 跳过注释和头部信息
                if not line or line.startswith('#') or 'blocks' in line or 'pl' in line:
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    module_name = parts[0]
                    x = float(parts[1])
                    y = float(parts[2])
                    
                    # 应用位置到设计中的模块
                    if module_name in design.modules:
                        design.modules[module_name].set_position(x, y)
                        positions_loaded += 1
                    else:
                        print(f"警告：.pl文件中的模块 '{module_name}' 在设计中不存在")
            
            print(f"成功从.pl文件加载了 {positions_loaded} 个模块的位置信息")
            return positions_loaded > 0
            
        except Exception as e:
            print(f"错误：读取.pl文件时出现异常: {e}")
            return False
    
    def create_design_from_pl(self, pl_file_path: str, blocks_file_path: str, 
                             nets_file_path: str, dataset: str = "gsrc") -> Optional[FloorplanDesign]:
        """
        从.pl文件和配套的.blocks, .nets文件创建完整的设计
        
        Args:
            pl_file_path: .pl文件路径
            blocks_file_path: .blocks文件路径
            nets_file_path: .nets文件路径
            dataset: 数据集类型
            
        Returns:
            FloorplanDesign: 创建的设计对象，如果失败则返回None
        """
        # 首先解析blocks和nets文件
        if dataset.lower() == "gsrc":
            from .parsers import GSRCParser
            parser = GSRCParser()
        else:
            from .parsers import MCNCParser
            parser = MCNCParser()
        
        try:
            # 解析blocks和nets文件
            modules = parser.parse_blocks_file(blocks_file_path)
            nets = parser.parse_nets_file(nets_file_path)
            
            # 创建设计对象
            design_name = Path(pl_file_path).stem
            design = FloorplanDesign(design_name)
            
            # 添加模块和网线
            for module in modules.values():
                design.add_module(module)
            for net in nets.values():
                design.add_net(net)
            
            # 从.pl文件读取位置信息
            if self.read_pl_file(pl_file_path, design):
                return design
            else:
                return None
                
        except Exception as e:
            print(f"错误：从.pl文件创建设计时出现异常: {e}")
            return None 
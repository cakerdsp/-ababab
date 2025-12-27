#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据导出器 - Data Exporters

用于将布图设计导出为各种格式，包括.pl文件、JSON等
Export floorplan designs to various formats including .pl files, JSON, etc.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .structures import FloorplanDesign, Module, ModuleType


class PLExporter:
    """
    .pl文件导出器 - .pl File Exporter
    
    将FloorplanDesign导出为GSRC/MCNC格式的.pl文件
    Export FloorplanDesign to GSRC/MCNC format .pl files
    """
    
    def __init__(self):
        pass
    
    def export(self, design: FloorplanDesign, output_path: str, include_header: bool = True) -> bool:
        """
        导出设计为.pl文件
        
        Args:
            design: 布图设计对象
            output_path: 输出文件路径
            include_header: 是否包含文件头
            
        Returns:
            bool: 是否导出成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if include_header:
                    f.write("UCSC blocks 1.0\n")
                    f.write(f"# Created by PyFloorplan at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Design: {design.name}\n")
                    f.write("\n")
                
                # 分组模块
                non_terminal_modules = []
                terminal_modules = []
                
                for module in design.modules.values():
                    if module.module_type == ModuleType.TERMINAL:
                        terminal_modules.append(module)
                    else:
                        non_terminal_modules.append(module)
                
                # 写入非引脚模块
                for module in non_terminal_modules:
                    f.write(f"{module.name}\t{module.x}\t{module.y}\n")
                
                # 写入引脚模块
                if terminal_modules:
                    f.write("\n")
                    for module in terminal_modules:
                        f.write(f"{module.name}\t{module.x}\t{module.y}\n")
            
            return True
            
        except Exception as e:
            print(f"❌ 导出.pl文件失败: {e}")
            return False


class JsonMetadataExporter:
    """
    JSON元数据导出器 - JSON Metadata Exporter
    
    导出评估结果和配置信息（不包含详细布局信息）
    Export evaluation results and configuration info (without detailed layout info)
    """
    
    def __init__(self):
        pass
    
    def export(self, evaluation_result: Dict[str, Any], config: Dict[str, Any], 
               output_path: str, include_config: bool = True) -> bool:
        """
        导出元数据为JSON文件
        
        Args:
            evaluation_result: 评估结果
            config: 配置信息
            output_path: 输出文件路径
            include_config: 是否包含配置信息
            
        Returns:
            bool: 是否导出成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            output_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'evaluation_result': evaluation_result
            }
            
            if include_config:
                filtered_config = {k: v for k, v in config.items() 
                                 if k not in ['solution', 'design', 'modules', 'layout']}
                output_data['config'] = filtered_config
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            return True
            
        except Exception as e:
            print(f"❌ 导出JSON元数据失败: {e}")
            return False


class ResultsOrganizer:
    """
    结果组织器 - Results Organizer
    
    按照用户要求的格式组织规划结果
    Organize planning results according to user requirements
    """
    
    def __init__(self, base_output_dir: str = "results"):
        self.base_output_dir = Path(base_output_dir)
        self.pl_exporter = PLExporter()
        self.json_exporter = JsonMetadataExporter()
    
    def create_result_folder(self, dataset: str, benchmark: str, algorithm: str = None) -> Path:
        """
        创建结果文件夹
        
        Args:
            dataset: 数据集名称
            benchmark: 基准测试名称
            algorithm: 算法名称（可选）
            
        Returns:
            Path: 结果文件夹路径
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if algorithm:
            folder_name = f"{dataset}_{benchmark}_{algorithm}_{timestamp}"
        else:
            folder_name = f"{dataset}_{benchmark}_{timestamp}"
        
        result_folder = self.base_output_dir / folder_name
        result_folder.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (result_folder / "visualization").mkdir(exist_ok=True)
        
        return result_folder
    
    def save_results(self, design: FloorplanDesign, evaluation_result: Dict[str, Any], 
                     config: Dict[str, Any], result_folder: Path) -> Dict[str, str]:
        """
        保存所有结果文件
        
        Args:
            design: 布图设计对象
            evaluation_result: 评估结果
            config: 配置信息
            result_folder: 结果文件夹
            
        Returns:
            Dict[str, str]: 保存的文件路径
        """
        saved_files = {}
        
        # 1. 保存.pl文件
        pl_file = result_folder / f"{design.name}.pl"
        if self.pl_exporter.export(design, str(pl_file)):
            saved_files['pl_file'] = str(pl_file)
        
        # 2. 保存JSON元数据
        json_file = result_folder / f"{design.name}_metadata.json"
        if self.json_exporter.export(evaluation_result, config, str(json_file)):
            saved_files['metadata_file'] = str(json_file)
        
        # 3. 保存可视化路径（供可视化模块使用）
        vis_folder = result_folder / "visualization"
        saved_files['visualization_folder'] = str(vis_folder)
        
        return saved_files


class PLToDesignLoader:
    """
    从.pl文件重新加载设计 - Load Design from .pl File
    
    用于从.pl文件反生成布图设计，支持可视化分析
    Load floorplan design from .pl file for visualization analysis
    """
    
    def __init__(self):
        pass
    
    def load_from_pl_file(self, pl_file: str, blocks_file: str = None, 
                         nets_file: str = None, design_name: str = None) -> Optional[FloorplanDesign]:
        """
        从.pl文件加载设计
        
        Args:
            pl_file: .pl文件路径
            blocks_file: .blocks文件路径（可选，用于获取完整模块信息）
            nets_file: .nets文件路径（可选，用于获取网线信息）
            design_name: 设计名称（可选）
            
        Returns:
            FloorplanDesign: 布图设计对象，如果失败则返回None
        """
        try:
            # 如果提供了完整的文件信息，使用完整解析
            if blocks_file and nets_file:
                from .parsers import auto_parse_design
                base_path = os.path.dirname(blocks_file)
                if not design_name:
                    design_name = os.path.splitext(os.path.basename(blocks_file))[0]
                return auto_parse_design(base_path, design_name)
            
            # 否则仅从.pl文件解析位置信息
            if not design_name:
                design_name = os.path.splitext(os.path.basename(pl_file))[0]
            
            design = FloorplanDesign(name=design_name)
            
            with open(pl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析模块位置
            reading_terminals = False
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('#') or line.startswith('UCSC'):
                    continue
                
                # 空行表示开始读取引脚模块
                if line == "":
                    reading_terminals = True
                    continue
                
                parts = line.split()
                if len(parts) >= 3:
                    module_name = parts[0]
                    x = float(parts[1])
                    y = float(parts[2])
                    
                    # 创建模块（简化版本）
                    if reading_terminals:
                        module = Module(
                            name=module_name,
                            module_type=ModuleType.TERMINAL,
                            width=1.0,  # 默认尺寸
                            height=1.0,
                            x=x,
                            y=y,
                            area=1.0
                        )
                    else:
                        module = Module(
                            name=module_name,
                            module_type=ModuleType.SOFT,  # 假设为软模块
                            width=10.0,  # 默认尺寸
                            height=10.0,
                            x=x,
                            y=y,
                            area=100.0
                        )
                    
                    design.add_module(module)
            
            return design
            
        except Exception as e:
            print(f"❌ 从.pl文件加载设计失败: {e}")
            return None 
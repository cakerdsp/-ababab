#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据加载器 - Data Loaders

高级数据加载接口，支持批量加载、缓存和数据预处理
High-level data loading interface with batch loading, caching and preprocessing
"""

import os
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False

from dataclasses import dataclass

from .parsers import GSRCParser, MCNCParser, auto_parse_design
from .structures import FloorplanDesign


@dataclass
class DatasetInfo:
    """数据集信息 - Dataset Information"""
    name: str
    format_type: str  # 'GSRC' or 'MCNC'
    num_modules: int
    num_nets: int
    total_area: float
    description: str = ""


class DataLoader:
    """
    基础数据加载器 - Base Data Loader
    
    提供缓存、预处理等通用功能
    Provides common functionality like caching and preprocessing
    """
    
    def __init__(self, cache_enabled: bool = True, cache_dir: str = "./cache"):
        """
        初始化数据加载器
        
        Args:
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录
        """
        self.cache_enabled = cache_enabled
        self.cache_dir = Path(cache_dir)
        
        if cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, dataset_name: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{dataset_name}.pkl"
    
    def _save_to_cache(self, design: FloorplanDesign, dataset_name: str):
        """保存到缓存"""
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(dataset_name)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(design, f)
        except Exception as e:
            print(f"Warning: Failed to save cache for {dataset_name}: {e}")
    
    def _load_from_cache(self, dataset_name: str) -> Optional[FloorplanDesign]:
        """从缓存加载"""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(dataset_name)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for {dataset_name}: {e}")
            return None
    
    def clear_cache(self, dataset_name: Optional[str] = None):
        """清理缓存"""
        if not self.cache_enabled:
            return
        
        if dataset_name:
            cache_path = self._get_cache_path(dataset_name)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # 清理所有缓存
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
    
    def preprocess_design(self, design: FloorplanDesign) -> FloorplanDesign:
        """
        预处理设计数据
        Preprocess design data
        
        可以在子类中重写以添加特定的预处理逻辑
        Can be overridden in subclasses for specific preprocessing logic
        """
        # 计算芯片边界
        if design.chip_width == 0 or design.chip_height == 0:
            bbox = design.get_bounding_box()
            if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                design.chip_width = bbox[2] - bbox[0]
                design.chip_height = bbox[3] - bbox[1]
        
        # 更新统计信息
        design.update_statistics()
        
        return design


class GSRCLoader(DataLoader):
    """
    GSRC数据集加载器 - GSRC Dataset Loader
    
    专门用于加载GSRC基准测试集
    Specialized for loading GSRC benchmark datasets
    """
    
    def __init__(self, data_root: str, cache_enabled: bool = True, cache_dir: str = "./cache"):
        """
        初始化GSRC加载器
        
        Args:
            data_root: GSRC数据集根目录
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录
        """
        super().__init__(cache_enabled, cache_dir)
        self.data_root = Path(data_root)
        self.parser = GSRCParser()
        
        if not self.data_root.exists():
            raise FileNotFoundError(f"GSRC data root not found: {data_root}")
    
    def load(self, design_name: str, use_cache: bool = True) -> FloorplanDesign:
        """
        加载单个GSRC设计
        Load single GSRC design
        
        Args:
            design_name: 设计名称（如'n10', 'n30'）
            use_cache: 是否使用缓存
        
        Returns:
            FloorplanDesign: 布图设计对象
        """
        # 尝试从缓存加载
        if use_cache:
            cached_design = self._load_from_cache(design_name)
            if cached_design:
                print(f"Loaded {design_name} from cache")
                return cached_design
        
        # 从文件加载
        print(f"Loading {design_name} from files...")
        design_path = self.data_root / design_name
        
        if not design_path.exists():
            raise FileNotFoundError(f"Design directory not found: {design_path}")
        
        design = self.parser.parse_design(str(design_path), design_name)
        design = self.preprocess_design(design)
        
        # 保存到缓存
        if use_cache:
            self._save_to_cache(design, design_name)
        
        return design
    
    def load_batch(self, design_names: List[str], use_cache: bool = True) -> Dict[str, FloorplanDesign]:
        """
        批量加载多个设计
        Load multiple designs in batch
        """
        designs = {}
        
        for name in design_names:
            try:
                designs[name] = self.load(name, use_cache)
                print(f"Successfully loaded {name}")
            except Exception as e:
                print(f"Failed to load {name}: {e}")
        
        return designs
    
    def list_available_designs(self) -> List[str]:
        """列出可用的设计"""
        designs = []
        
        for item in self.data_root.iterdir():
            if item.is_dir():
                # 检查是否包含必要的文件
                blocks_file = item / f"{item.name}.blocks"
                nets_file = item / f"{item.name}.nets"
                pl_file = item / f"{item.name}.pl"
                
                if blocks_file.exists() and nets_file.exists() and pl_file.exists():
                    designs.append(item.name)
        
        return sorted(designs)
    
    def get_dataset_info(self, design_name: str) -> DatasetInfo:
        """获取数据集信息"""
        design = self.load(design_name)
        
        return DatasetInfo(
            name=design_name,
            format_type='GSRC',
            num_modules=len(design.modules),
            num_nets=len(design.nets),
            total_area=design.total_area,
            description=f"GSRC benchmark {design_name}"
        )


class MCNCLoader(DataLoader):
    """
    MCNC数据集加载器 - MCNC Dataset Loader
    
    专门用于加载MCNC基准测试集
    Specialized for loading MCNC benchmark datasets
    """
    
    def __init__(self, data_root: str, cache_enabled: bool = True, cache_dir: str = "./cache"):
        """
        初始化MCNC加载器
        
        Args:
            data_root: MCNC数据集根目录
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录
        """
        super().__init__(cache_enabled, cache_dir)
        self.data_root = Path(data_root)
        self.parser = MCNCParser()
        
        if not self.data_root.exists():
            raise FileNotFoundError(f"MCNC data root not found: {data_root}")
    
    def load(self, design_name: str, use_cache: bool = True) -> FloorplanDesign:
        """加载单个MCNC设计"""
        # 尝试从缓存加载
        if use_cache:
            cached_design = self._load_from_cache(design_name)
            if cached_design:
                print(f"Loaded {design_name} from cache")
                return cached_design
        
        # 从文件加载
        print(f"Loading {design_name} from files...")
        design_path = self.data_root / design_name
        
        if not design_path.exists():
            raise FileNotFoundError(f"Design directory not found: {design_path}")
        
        design = self.parser.parse_design(str(design_path), design_name)
        design = self.preprocess_design(design)
        
        # 保存到缓存
        if use_cache:
            self._save_to_cache(design, design_name)
        
        return design
    
    def load_batch(self, design_names: List[str], use_cache: bool = True) -> Dict[str, FloorplanDesign]:
        """批量加载多个设计"""
        designs = {}
        
        for name in design_names:
            try:
                designs[name] = self.load(name, use_cache)
                print(f"Successfully loaded {name}")
            except Exception as e:
                print(f"Failed to load {name}: {e}")
        
        return designs
    
    def list_available_designs(self) -> List[str]:
        """列出可用的设计"""
        designs = []
        
        for item in self.data_root.iterdir():
            if item.is_dir():
                # 检查是否包含必要的文件
                blocks_file = item / f"{item.name}.blocks"
                nets_file = item / f"{item.name}.nets"
                pl_file = item / f"{item.name}.pl"
                
                if blocks_file.exists() and nets_file.exists() and pl_file.exists():
                    designs.append(item.name)
        
        return sorted(designs)
    
    def get_dataset_info(self, design_name: str) -> DatasetInfo:
        """获取数据集信息"""
        design = self.load(design_name)
        
        return DatasetInfo(
            name=design_name,
            format_type='MCNC',
            num_modules=len(design.modules),
            num_nets=len(design.nets),
            total_area=design.total_area,
            description=f"MCNC benchmark {design_name}"
        )


class UniversalLoader(DataLoader):
    """
    通用数据加载器 - Universal Data Loader
    
    自动检测格式并选择合适的解析器
    Automatically detects format and selects appropriate parser
    """
    
    def __init__(self, data_root: str, cache_enabled: bool = True, cache_dir: str = "./cache"):
        """
        初始化通用加载器
        
        Args:
            data_root: 数据集根目录
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录
        """
        super().__init__(cache_enabled, cache_dir)
        self.data_root = Path(data_root)
        
        if not self.data_root.exists():
            raise FileNotFoundError(f"Data root not found: {data_root}")
    
    def load(self, design_name: str, use_cache: bool = True) -> FloorplanDesign:
        """自动检测格式并加载设计"""
        # 尝试从缓存加载
        if use_cache:
            cached_design = self._load_from_cache(design_name)
            if cached_design:
                print(f"Loaded {design_name} from cache")
                return cached_design
        
        # 从文件加载
        print(f"Loading {design_name} from files...")
        design_path = self.data_root / design_name
        
        if not design_path.exists():
            raise FileNotFoundError(f"Design directory not found: {design_path}")
        
        design = auto_parse_design(str(design_path), design_name)
        design = self.preprocess_design(design)
        
        # 保存到缓存
        if use_cache:
            self._save_to_cache(design, design_name)
        
        return design


class TensorDataLoader:
    """
    张量数据加载器 - Tensor Data Loader
    
    为深度学习模型提供批量张量数据
    Provides batched tensor data for deep learning models
    """
    
    def __init__(self, designs: Dict[str, FloorplanDesign], device=None):
        """
        初始化张量数据加载器
        
        Args:
            designs: 设计字典
            device: PyTorch设备（如果有torch）
        """
        if not HAS_TORCH:
            raise ImportError(
                "PyTorch is required for TensorDataLoader. "
                "Please install PyTorch: pip install torch torchvision"
            )
        
        self.designs = designs
        self.device = device or torch.device('cpu')
        self.design_names = list(designs.keys())
    
    def __len__(self) -> int:
        return len(self.designs)
    
    def __getitem__(self, idx: int) -> Tuple[str, Dict[str, Union['torch.Tensor', list]]]:
        """获取单个设计的张量数据"""
        design_name = self.design_names[idx]
        design = self.designs[design_name]
        tensor_data = design.to_tensor(self.device)
        return design_name, tensor_data
    
    def get_batch(self, indices: List[int]) -> Dict[str, List]:
        """获取批量数据"""
        batch = {
            'names': [],
            'modules': [],
            'adjacency': [],
            'module_names': []
        }
        
        for idx in indices:
            name, tensor_data = self[idx]
            batch['names'].append(name)
            batch['modules'].append(tensor_data['modules'])
            batch['adjacency'].append(tensor_data['adjacency'])
            batch['module_names'].append(tensor_data['module_names'])
        
        return batch
    
    def collate_batch(self, batch_data: Dict[str, List]) -> Dict[str, 'torch.Tensor']:
        """整理批量数据为统一张量"""
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for batch collation")
        
        # 找到最大模块数
        max_modules = max(modules.size(0) for modules in batch_data['modules'])
        batch_size = len(batch_data['names'])
        
        # 创建填充后的张量
        padded_modules = torch.zeros((batch_size, max_modules, 6), device=self.device)
        padded_adjacency = torch.zeros((batch_size, max_modules, max_modules), device=self.device)
        
        for i, (modules, adjacency) in enumerate(zip(batch_data['modules'], batch_data['adjacency'])):
            n_modules = modules.size(0)
            padded_modules[i, :n_modules] = modules
            padded_adjacency[i, :n_modules, :n_modules] = adjacency
        
        return {
            'modules': padded_modules,
            'adjacency': padded_adjacency,
            'names': batch_data['names'],
            'module_names': batch_data['module_names']
        }


def create_loader(data_root: str, format_type: str = 'auto', **kwargs) -> DataLoader:
    """
    工厂函数：创建合适的数据加载器
    Factory function: create appropriate data loader
    
    Args:
        data_root: 数据根目录
        format_type: 格式类型 ('gsrc', 'mcnc', 'auto')
        **kwargs: 其他参数
    
    Returns:
        DataLoader: 数据加载器实例
    """
    format_type = format_type.lower()
    
    if format_type == 'gsrc':
        return GSRCLoader(data_root, **kwargs)
    elif format_type == 'mcnc':
        return MCNCLoader(data_root, **kwargs)
    elif format_type == 'auto':
        return UniversalLoader(data_root, **kwargs)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


# 导出主要类和函数
__all__ = [
    'DataLoader',
    'GSRCLoader',
    'MCNCLoader', 
    'UniversalLoader',
    'TensorDataLoader',
    'DatasetInfo',
    'create_loader'
] 
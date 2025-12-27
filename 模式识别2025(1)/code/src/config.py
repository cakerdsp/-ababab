"""
配置管理模块
提供统一的配置管理接口，支持不同环境和模型的配置
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
import yaml


@dataclass
class DataConfig:
    """数据相关配置"""
    data_dir: str = "../anonymisedData/anonymisedData"
    output_dir: str = "../outputs"
    target_column: str = "at_risk"
    random_state: int = 42
    test_size: float = 0.2
    validation_size: float = 0.2


@dataclass
class CleaningConfig:
    """数据清洗配置"""
    missing_threshold: float = 0.5  # 缺失值超过50%的列删除
    outlier_method: str = "iqr"  # iqr, zscore, isolation
    outlier_threshold: float = 3.0
    correlation_threshold: float = 0.95  # 高相关性特征删除阈值
    min_category_freq: int = 10  # 最小类别频次


@dataclass
class EDAConfig:
    """探索性数据分析配置"""
    plot_dpi: int = 300
    figure_size: tuple = (12, 8)
    max_categories_display: int = 10
    correlation_method: str = "pearson"  # pearson, spearman
    show_correlation_values: bool = False  # 是否在热力图中显示数值


@dataclass
class ModelConfig:
    """模型训练配置"""
    cross_validation_folds: int = 5
    scoring_metric: str = "f1"
    n_jobs: int = -1
    verbose: bool = True
    
    # 网格搜索配置
    grid_search_cv: int = 3
    grid_search_scoring: str = "f1"
    
    # 模型特定参数
    model_params: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "random_forest": {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4]
        },
        "logistic_regression": {
            "C": [0.1, 1.0, 10.0],
            "penalty": ["l1", "l2"],
            "solver": ["liblinear", "saga"]
        },
        "gradient_boosting": {
            "n_estimators": [100, 200],
            "learning_rate": [0.1, 0.01],
            "max_depth": [3, 5, 7]
        },
        "svm": {
            "C": [0.1, 1.0, 10.0],
            "kernel": ["rbf", "linear"],
            "gamma": ["scale", "auto"]
        }
    })


@dataclass
class PlotConfig:
    """绘图配置"""
    style: str = "whitegrid"
    palette: str = "Set1"
    font_family: str = "SimHei"  # 中文字体
    font_size: int = 12
    title_size: int = 14
    label_size: int = 11
    
    # 颜色配置
    colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#2E86C1",
        "secondary": "#F39C12",
        "success": "#27AE60",
        "danger": "#E74C3C",
        "warning": "#F1C40F",
        "info": "#8E44AD"
    })


@dataclass
class Config:
    """主配置类"""
    data: DataConfig = field(default_factory=DataConfig)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    eda: EDAConfig = field(default_factory=EDAConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    plot: PlotConfig = field(default_factory=PlotConfig)
    
    # 运行时配置
    debug: bool = False
    log_level: str = "INFO"
    save_intermediate: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """从配置文件加载配置"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        if config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        elif config_path.suffix in ['.yml', '.yaml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
        config = cls()
        
        # 更新各个子配置
        if 'data' in config_dict:
            for key, value in config_dict['data'].items():
                if hasattr(config.data, key):
                    setattr(config.data, key, value)
        
        if 'cleaning' in config_dict:
            for key, value in config_dict['cleaning'].items():
                if hasattr(config.cleaning, key):
                    setattr(config.cleaning, key, value)
        
        if 'eda' in config_dict:
            for key, value in config_dict['eda'].items():
                if hasattr(config.eda, key):
                    setattr(config.eda, key, value)
        
        if 'model' in config_dict:
            for key, value in config_dict['model'].items():
                if hasattr(config.model, key):
                    setattr(config.model, key, value)
        
        if 'plot' in config_dict:
            for key, value in config_dict['plot'].items():
                if hasattr(config.plot, key):
                    setattr(config.plot, key, value)
        
        # 更新根级别配置
        for key in ['debug', 'log_level', 'save_intermediate']:
            if key in config_dict:
                setattr(config, key, config_dict[key])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data': self.data.__dict__,
            'cleaning': self.cleaning.__dict__,
            'eda': self.eda.__dict__,
            'model': self.model.__dict__,
            'plot': self.plot.__dict__,
            'debug': self.debug,
            'log_level': self.log_level,
            'save_intermediate': self.save_intermediate
        }
    
    def save_to_file(self, config_path: str):
        """保存配置到文件"""
        config_path = Path(config_path)
        config_data = self.to_dict()
        
        if config_path.suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        elif config_path.suffix in ['.yml', '.yaml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")


class ConfigManager:
    """配置管理器"""
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    
    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 如果提供了配置文件路径，立即加载配置
            if config_path:
                cls._instance.load_config(config_path)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器"""
        # 如果还没有加载配置，则加载
        if self._config is None and config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: Optional[str] = None) -> Config:
        """加载配置"""
        if config_path and Path(config_path).exists():
            self._config = Config.from_file(config_path)
        else:
            self._config = Config()  # 使用默认配置
        
        return self._config
    
    def get_config(self) -> Config:
        """获取当前配置"""
        if self._config is None:
            self._config = Config()
        return self._config
    
    def update_config(self, **kwargs):
        """更新配置"""
        if self._config is None:
            self._config = Config()
        
        config_dict = self._config.to_dict()
        config_dict.update(kwargs)
        self._config = Config.from_dict(config_dict)
    
    def get(self, path: str, default=None):
        """获取配置值，支持点分隔的路径"""
        if self._config is None:
            return default
        
        # 将配置转换为嵌套字典
        config_dict = self._config.to_dict()
        
        # 解析路径
        keys = path.split('.')
        value = config_dict
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_models_to_run(self):
        """获取要运行的模型列表"""
        return self.get('modeling.models_to_run', ['logistic_regression'])
    
    def print_config_summary(self):
        """打印配置摘要"""
        if self._config is None:
            print("使用默认配置")
            return
        
        print("=" * 60)
        print("配置摘要")
        print("=" * 60)
        print(f"数据目录: {self.get('data.data_dir', 'N/A')}")
        print(f"目标变量: {self.get('data.target_column', 'N/A')}")
        print(f"测试集比例: {self.get('data.test_size', 'N/A')}")
        print(f"启用EDA: {self.get('modules.enable_eda', 'N/A')}")
        print(f"启用建模: {self.get('modules.enable_modeling', 'N/A')}")
        print(f"要运行的模型: {self.get_models_to_run()}")
        print("=" * 60)


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> Config:
    """获取全局配置"""
    return config_manager.get_config()


def load_config(config_path: Optional[str] = None) -> Config:
    """加载配置文件"""
    return config_manager.load_config(config_path) 
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器，用于加载和管理YAML配置文件"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            # 加载指定的配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            # 加载默认配置文件
            default_config_path = Path(__file__).parent / "default_config.yaml"
            if default_config_path.exists():
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                # 如果默认配置文件不存在，使用内置默认配置
                config = self._get_default_config()
        
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取内置默认配置"""
        return {
            'data': {
                'target_courses': None,
                'target_column': 'at_risk',
                'test_size': 0.2
            },
            'cleaning': {
                'missing_strategy': 'auto',
                'outlier_method': 'percentile',
                'outlier_threshold': 0.98,
                'enable_feature_engineering': True,
                'enable_encoding': True,
                'enable_normalization': False
            },
            'modules': {
                'enable_eda': True,
                'enable_modeling': True
            },
            'modeling': {
                'models_to_run': ['random_forest'],
                'random_forest': {'auto_optimize': True, 'n_trials': 10},
                'logistic_regression': {'auto_optimize': True, 'n_trials': 10},
                'kmeans': {'n_clusters': 2, 'auto_optimize': True, 'n_trials': 10},
                'neural_network': {'auto_optimize': True, 'n_trials': 10}
            },
            'output': {
                'plot_dir': 'outputs/plots/modeling',
                'report_dir': 'outputs',
                'save_models': True,
                'model_dir': 'models'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'outputs/analysis.log'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，如 'data.target_column'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取特定模型的配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置字典
        """
        return self.config.get('modeling', {}).get(model_name, {})
    
    def get_models_to_run(self) -> list:
        """获取要运行的模型列表"""
        return self.config.get('modeling', {}).get('models_to_run', ['random_forest'])
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        try:
            # 检查必要的配置项
            required_sections = ['data', 'cleaning', 'modules', 'modeling', 'output']
            for section in required_sections:
                if section not in self.config:
                    print(f"警告: 缺少配置节 '{section}'")
                    return False
            
            # 检查模型配置
            models_to_run = self.get_models_to_run()
            if not models_to_run:
                print("警告: 没有指定要运行的模型")
                return False
            
            # 检查模型名称的有效性
            valid_models = ['random_forest', 'logistic_regression', 'kmeans', 'neural_network']
            for model in models_to_run:
                if model not in valid_models:
                    print(f"警告: 无效的模型名称 '{model}'")
                    return False
            
            return True
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("=" * 60)
        print("配置摘要")
        print("=" * 60)
        print(f"配置文件: {self.config_path or '默认配置'}")
        print(f"目标课程: {self.get('data.target_courses', '所有课程')}")
        print(f"目标变量: {self.get('data.target_column')}")
        print(f"测试集比例: {self.get('data.test_size')}")
        print(f"启用EDA: {self.get('modules.enable_eda')}")
        print(f"启用建模: {self.get('modules.enable_modeling')}")
        print(f"要运行的模型: {', '.join(self.get_models_to_run())}")
        print("=" * 60)
    
    def save_config(self, output_path: str):
        """保存当前配置到文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        print(f"配置已保存到: {output_path}")
    
    def update_config(self, updates: Dict[str, Any]):
        """
        更新配置
        
        Args:
            updates: 要更新的配置字典
        """
        def update_nested_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    update_nested_dict(d[k], v)
                else:
                    d[k] = v
        
        update_nested_dict(self.config, updates) 
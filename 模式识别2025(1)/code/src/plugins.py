"""
插件系统模块
提供可扩展的插件框架，支持动态加载新的分析方法和模型
"""

import importlib
import inspect
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from pathlib import Path
import pandas as pd
import numpy as np

from .interfaces import PluginInterface, ModelInterface
from .config import get_config


class BasePlugin(PluginInterface):
    """基础插件类"""
    
    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        self._name = name
        self._version = version
        self._description = description
        self.config = {}
        self.is_initialized = False
    
    def get_name(self) -> str:
        return self._name
    
    def get_version(self) -> str:
        return self._version
    
    def get_description(self) -> str:
        return self._description
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化插件"""
        self.config = config
        self.is_initialized = True
        self._on_initialize()
    
    def _on_initialize(self):
        """子类可重写的初始化方法"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass


class ModelPlugin(BasePlugin):
    """模型插件基类"""
    
    def __init__(self, name: str, model_class: Type, default_params: Dict[str, Any] = None, **kwargs):
        super().__init__(name, **kwargs)
        self.model_class = model_class
        self.default_params = default_params or {}
    
    def create_model(self, **kwargs) -> ModelInterface:
        """创建模型实例"""
        from .model_factory import BaseMLModel
        
        params = self.default_params.copy()
        params.update(kwargs)
        
        sklearn_model = self.model_class(**params)
        return BaseMLModel(sklearn_model, self._name)
    
    def execute(self, *args, **kwargs) -> ModelInterface:
        """执行插件（创建模型）"""
        return self.create_model(**kwargs)


class AnalysisPlugin(BasePlugin):
    """分析插件基类"""
    
    def __init__(self, name: str, analysis_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.analysis_func = analysis_func
    
    def execute(self, df: pd.DataFrame, *args, **kwargs) -> Any:
        """执行分析"""
        if not self.is_initialized:
            raise RuntimeError("插件尚未初始化")
        
        return self.analysis_func(df, *args, **kwargs)


class VisualizationPlugin(BasePlugin):
    """可视化插件基类"""
    
    def __init__(self, name: str, plot_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.plot_func = plot_func
    
    def execute(self, data: Any, save_path: str = None, *args, **kwargs) -> Any:
        """执行可视化"""
        if not self.is_initialized:
            raise RuntimeError("插件尚未初始化")
        
        result = self.plot_func(data, *args, **kwargs)
        
        if save_path:
            import matplotlib.pyplot as plt
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        return result


class PreprocessingPlugin(BasePlugin):
    """数据预处理插件基类"""
    
    def __init__(self, name: str, preprocess_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.preprocess_func = preprocess_func
    
    def execute(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
        """执行预处理"""
        if not self.is_initialized:
            raise RuntimeError("插件尚未初始化")
        
        return self.preprocess_func(df, *args, **kwargs)


class FeatureEngineeringPlugin(BasePlugin):
    """特征工程插件基类"""
    
    def __init__(self, name: str, feature_func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self.feature_func = feature_func
    
    def execute(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
        """执行特征工程"""
        if not self.is_initialized:
            raise RuntimeError("插件尚未初始化")
        
        return self.feature_func(df, *args, **kwargs)


# 具体插件实现
class XGBoostPlugin(ModelPlugin):
    """XGBoost模型插件"""
    
    def __init__(self):
        try:
            import xgboost as xgb
            model_class = xgb.XGBClassifier
        except ImportError:
            raise ImportError("XGBoost未安装，请运行: pip install xgboost")
        
        default_params = {
            'random_state': 42,
            'eval_metric': 'logloss'
        }
        
        super().__init__(
            name="xgboost",
            model_class=model_class,
            default_params=default_params,
            description="XGBoost梯度提升模型"
        )


class LightGBMPlugin(ModelPlugin):
    """LightGBM模型插件"""
    
    def __init__(self):
        try:
            import lightgbm as lgb
            model_class = lgb.LGBMClassifier
        except ImportError:
            raise ImportError("LightGBM未安装，请运行: pip install lightgbm")
        
        default_params = {
            'random_state': 42,
            'verbosity': -1
        }
        
        super().__init__(
            name="lightgbm",
            model_class=model_class,
            default_params=default_params,
            description="LightGBM梯度提升模型"
        )


class CatBoostPlugin(ModelPlugin):
    """CatBoost模型插件"""
    
    def __init__(self):
        try:
            import catboost as cb
            model_class = cb.CatBoostClassifier
        except ImportError:
            raise ImportError("CatBoost未安装，请运行: pip install catboost")
        
        default_params = {
            'random_state': 42,
            'verbose': False
        }
        
        super().__init__(
            name="catboost",
            model_class=model_class,
            default_params=default_params,
            description="CatBoost梯度提升模型"
        )


class SHAPAnalysisPlugin(AnalysisPlugin):
    """SHAP模型解释插件"""
    
    def __init__(self):
        try:
            import shap
        except ImportError:
            raise ImportError("SHAP未安装，请运行: pip install shap")
        
        def shap_analysis(model, X_test, feature_names=None):
            """SHAP分析"""
            import shap
            
            # 获取sklearn模型
            if hasattr(model, 'sklearn_model'):
                sklearn_model = model.sklearn_model
            else:
                sklearn_model = model
            
            # 创建解释器
            explainer = shap.Explainer(sklearn_model)
            shap_values = explainer(X_test)
            
            # 生成摘要图
            shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
            
            return {
                'explainer': explainer,
                'shap_values': shap_values,
                'feature_importance': np.abs(shap_values.values).mean(axis=0)
            }
        
        super().__init__(
            name="shap_analysis",
            analysis_func=shap_analysis,
            description="SHAP模型可解释性分析"
        )


class AdvancedVisualizationPlugin(VisualizationPlugin):
    """高级可视化插件"""
    
    def __init__(self):
        def advanced_plots(df, target_column='at_risk'):
            """高级可视化"""
            import matplotlib.pyplot as plt
            import seaborn as sns
            from sklearn.manifold import TSNE
            from sklearn.decomposition import PCA
            
            # t-SNE降维可视化
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            X = df[numeric_cols].fillna(0)
            
            # PCA
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X)
            
            # t-SNE
            tsne = TSNE(n_components=2, random_state=42)
            X_tsne = tsne.fit_transform(X)
            
            # 绘图
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # PCA图
            scatter = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=df[target_column], alpha=0.6)
            axes[0].set_title('PCA Dimensionality Reduction Visualization')
            axes[0].set_xlabel(f'PC1 (Variance Explained: {pca.explained_variance_ratio_[0]:.2f})')
            axes[0].set_ylabel(f'PC2 (Variance Explained: {pca.explained_variance_ratio_[1]:.2f})')
            plt.colorbar(scatter, ax=axes[0])
            
            # t-SNE图
            scatter = axes[1].scatter(X_tsne[:, 0], X_tsne[:, 1], c=df[target_column], alpha=0.6)
            axes[1].set_title('t-SNE Dimensionality Reduction Visualization')
            axes[1].set_xlabel('t-SNE 1')
            axes[1].set_ylabel('t-SNE 2')
            plt.colorbar(scatter, ax=axes[1])
            
            return fig
        
        super().__init__(
            name="advanced_visualization",
            plot_func=advanced_plots,
            description="高级数据可视化（PCA、t-SNE等）"
        )


class AutoFeatureEngineeringPlugin(FeatureEngineeringPlugin):
    """自动特征工程插件"""
    
    def __init__(self):
        def auto_feature_engineering(df, target_column='at_risk'):
            """自动特征工程"""
            df_new = df.copy()
            
            # 数值特征的统计特征
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            numeric_cols = [col for col in numeric_cols if col != target_column]
            
            # 平均值、标准差、偏度、峰度
            for col in numeric_cols:
                if df[col].dtype in ['int64', 'float64']:
                    # 分组统计特征
                    df_new[f'{col}_zscore'] = (df[col] - df[col].mean()) / df[col].std()
                    df_new[f'{col}_is_outlier'] = (np.abs(df_new[f'{col}_zscore']) > 3).astype(int)
                    
                    # 分箱特征
                    df_new[f'{col}_binned'] = pd.cut(df[col], bins=5, labels=False)
            
            # 交互特征（选择前几个重要特征）
            important_cols = numeric_cols[:5]  # 前5个数值特征
            for i, col1 in enumerate(important_cols):
                for col2 in important_cols[i+1:]:
                    df_new[f'{col1}_x_{col2}'] = df[col1] * df[col2]
                    df_new[f'{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-8)
            
            return df_new
        
        super().__init__(
            name="auto_feature_engineering",
            feature_func=auto_feature_engineering,
            description="自动特征工程（统计特征、交互特征等）"
        )


class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.loaded_plugins: Dict[str, PluginInterface] = {}
    
    def load_plugin_from_file(self, plugin_file: str) -> List[PluginInterface]:
        """从文件加载插件"""
        plugin_path = Path(plugin_file)
        
        if not plugin_path.exists():
            raise FileNotFoundError(f"插件文件不存在: {plugin_file}")
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
        plugin_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin_module)
        
        # 查找插件类
        plugins = []
        for name, obj in inspect.getmembers(plugin_module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PluginInterface) and 
                obj != PluginInterface and
                obj != BasePlugin):
                
                try:
                    plugin_instance = obj()
                    plugins.append(plugin_instance)
                    self.loaded_plugins[plugin_instance.get_name()] = plugin_instance
                except Exception as e:
                    print(f"加载插件 {name} 失败: {e}")
        
        return plugins
    
    def load_plugins_from_directory(self, plugin_dir: str = None) -> List[PluginInterface]:
        """从目录加载所有插件"""
        if plugin_dir:
            self.plugin_dir = Path(plugin_dir)
        
        if not self.plugin_dir.exists():
            return []
        
        plugins = []
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name != "__init__.py":
                try:
                    file_plugins = self.load_plugin_from_file(plugin_file)
                    plugins.extend(file_plugins)
                except Exception as e:
                    print(f"加载插件文件 {plugin_file} 失败: {e}")
        
        return plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """获取插件"""
        return self.loaded_plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self.loaded_plugins.keys())


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_loader = PluginLoader()
        
        # 注册内置插件
        self._register_builtin_plugins()
    
    def _register_builtin_plugins(self):
        """注册内置插件"""
        builtin_plugins = []
        
        # 尝试注册高级模型插件
        try:
            builtin_plugins.append(XGBoostPlugin())
        except ImportError:
            pass
        
        try:
            builtin_plugins.append(LightGBMPlugin())
        except ImportError:
            pass
        
        try:
            builtin_plugins.append(CatBoostPlugin())
        except ImportError:
            pass
        
        # 分析插件
        try:
            builtin_plugins.append(SHAPAnalysisPlugin())
        except ImportError:
            pass
        
        # 可视化插件
        builtin_plugins.append(AdvancedVisualizationPlugin())
        
        # 特征工程插件
        builtin_plugins.append(AutoFeatureEngineeringPlugin())
        
        # 注册插件
        for plugin in builtin_plugins:
            self.register_plugin(plugin)
    
    def register_plugin(self, plugin: PluginInterface):
        """注册插件"""
        self.plugins[plugin.get_name()] = plugin
    
    def unregister_plugin(self, plugin_name: str):
        """取消注册插件"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """获取插件"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, str]:
        """列出所有插件及其描述"""
        return {name: plugin.get_description() for name, plugin in self.plugins.items()}
    
    def load_external_plugins(self, plugin_dir: str = "plugins"):
        """加载外部插件"""
        external_plugins = self.plugin_loader.load_plugins_from_directory(plugin_dir)
        for plugin in external_plugins:
            self.register_plugin(plugin)
    
    def get_plugins_by_type(self, plugin_type: Type) -> List[PluginInterface]:
        """按类型获取插件"""
        return [plugin for plugin in self.plugins.values() if isinstance(plugin, plugin_type)]


# 全局插件注册表
plugin_registry = PluginRegistry()


def get_plugin(plugin_name: str) -> Optional[PluginInterface]:
    """获取插件的便捷函数"""
    return plugin_registry.get_plugin(plugin_name)


def list_available_plugins() -> Dict[str, str]:
    """列出可用插件的便捷函数"""
    return plugin_registry.list_plugins()


def register_plugin(plugin: PluginInterface):
    """注册插件的便捷函数"""
    plugin_registry.register_plugin(plugin) 
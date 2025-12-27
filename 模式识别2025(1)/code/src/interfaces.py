"""
抽象接口模块
定义各个组件的抽象基类，确保松耦合设计
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.base import BaseEstimator
from sklearn.metrics import classification_report


class DataLoaderInterface(ABC):
    """数据加载器接口"""
    
    @abstractmethod
    def load_data(self, data_path: str) -> Dict[str, pd.DataFrame]:
        """加载数据"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """验证数据完整性"""
        pass


class DataProcessorInterface(ABC):
    """数据处理器接口"""
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换数据"""
        pass
    
    @abstractmethod
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """拟合并转换数据"""
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """获取特征名称"""
        pass


class DataCleanerInterface(ABC):
    """数据清洗器接口"""
    
    @abstractmethod
    def clean_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        pass
    
    @abstractmethod
    def handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理异常值"""
        pass
    
    @abstractmethod
    def encode_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特征编码"""
        pass
    
    @abstractmethod
    def get_cleaning_report(self) -> Dict[str, Any]:
        """获取清洗报告"""
        pass


class EDAAnalyzerInterface(ABC):
    """探索性数据分析器接口"""
    
    @abstractmethod
    def generate_data_profile(self) -> Dict[str, Any]:
        """生成数据概览"""
        pass
    
    @abstractmethod
    def univariate_analysis(self) -> None:
        """单变量分析"""
        pass
    
    @abstractmethod
    def bivariate_analysis(self) -> None:
        """双变量分析"""
        pass
    
    @abstractmethod
    def multivariate_analysis(self) -> None:
        """多变量分析"""
        pass
    
    @abstractmethod
    def generate_report(self) -> str:
        """生成分析报告"""
        pass


class ModelInterface(ABC):
    """机器学习模型接口"""
    
    @abstractmethod
    def train(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> 'ModelInterface':
        """训练模型"""
        pass
    
    @abstractmethod
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """预测"""
        pass
    
    @abstractmethod
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """预测概率"""
        pass
    
    @abstractmethod
    def evaluate(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """评估模型"""
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """获取特征重要性"""
        pass
    
    @abstractmethod
    def save_model(self, path: str) -> None:
        """保存模型"""
        pass
    
    @abstractmethod
    def load_model(self, path: str) -> None:
        """加载模型"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称"""
        pass


class ModelTrainerInterface(ABC):
    """模型训练器接口"""
    
    @abstractmethod
    def train_model(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                   y: Union[pd.Series, np.ndarray]) -> ModelInterface:
        """训练单个模型"""
        pass
    
    @abstractmethod
    def train_multiple_models(self, models: List[ModelInterface], 
                            X: Union[pd.DataFrame, np.ndarray], 
                            y: Union[pd.Series, np.ndarray]) -> Dict[str, ModelInterface]:
        """训练多个模型"""
        pass
    
    @abstractmethod
    def cross_validate(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                      y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """交叉验证"""
        pass
    
    @abstractmethod
    def hyperparameter_tuning(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                            y: Union[pd.Series, np.ndarray]) -> ModelInterface:
        """超参数调优"""
        pass


class ModelEvaluatorInterface(ABC):
    """模型评估器接口"""
    
    @abstractmethod
    def evaluate_model(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                      y: Union[pd.Series, np.ndarray]) -> Dict[str, Any]:
        """评估单个模型"""
        pass
    
    @abstractmethod
    def compare_models(self, models: Dict[str, ModelInterface], 
                      X: Union[pd.DataFrame, np.ndarray], 
                      y: Union[pd.Series, np.ndarray]) -> pd.DataFrame:
        """比较多个模型"""
        pass
    
    @abstractmethod
    def generate_evaluation_report(self, models: Dict[str, ModelInterface], 
                                 X: Union[pd.DataFrame, np.ndarray], 
                                 y: Union[pd.Series, np.ndarray]) -> str:
        """生成评估报告"""
        pass


class VisualizerInterface(ABC):
    """可视化器接口"""
    
    @abstractmethod
    def plot_distribution(self, data: Union[pd.Series, np.ndarray], title: str) -> None:
        """绘制分布图"""
        pass
    
    @abstractmethod
    def plot_correlation(self, df: pd.DataFrame) -> None:
        """绘制相关性图"""
        pass
    
    @abstractmethod
    def plot_feature_importance(self, importance: np.ndarray, feature_names: List[str]) -> None:
        """绘制特征重要性图"""
        pass
    
    @abstractmethod
    def plot_model_comparison(self, results: pd.DataFrame) -> None:
        """绘制模型比较图"""
        pass
    
    @abstractmethod
    def save_plot(self, filename: str) -> None:
        """保存图片"""
        pass


class PipelineInterface(ABC):
    """流水线接口"""
    
    @abstractmethod
    def add_step(self, name: str, processor: Any) -> 'PipelineInterface':
        """添加处理步骤"""
        pass
    
    @abstractmethod
    def remove_step(self, name: str) -> 'PipelineInterface':
        """移除处理步骤"""
        pass
    
    @abstractmethod
    def run(self, data: Any) -> Any:
        """运行流水线"""
        pass
    
    @abstractmethod
    def get_steps(self) -> Dict[str, Any]:
        """获取所有步骤"""
        pass


class PluginInterface(ABC):
    """插件接口"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass


class ReportGeneratorInterface(ABC):
    """报告生成器接口"""
    
    @abstractmethod
    def add_section(self, title: str, content: str) -> None:
        """添加章节"""
        pass
    
    @abstractmethod
    def add_table(self, title: str, data: pd.DataFrame) -> None:
        """添加表格"""
        pass
    
    @abstractmethod
    def add_plot(self, title: str, plot_path: str) -> None:
        """添加图片"""
        pass
    
    @abstractmethod
    def generate_report(self, output_path: str) -> None:
        """生成报告"""
        pass


class CacheInterface(ABC):
    """缓存接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass


class LoggerInterface(ABC):
    """日志接口"""
    
    @abstractmethod
    def debug(self, message: str) -> None:
        """调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str) -> None:
        """信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str) -> None:
        """错误日志"""
        pass
    
    @abstractmethod
    def critical(self, message: str) -> None:
        """严重错误日志"""
        pass


# 类型别名
DataDict = Dict[str, pd.DataFrame]
FeatureArray = Union[pd.DataFrame, np.ndarray]
TargetArray = Union[pd.Series, np.ndarray]
ModelDict = Dict[str, ModelInterface]
ConfigDict = Dict[str, Any] 
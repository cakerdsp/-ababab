"""
模型工厂模块
提供统一的模型创建和管理接口，支持动态加载不同的机器学习模型
"""

import importlib
import inspect
from typing import Dict, Any, List, Optional, Type, Union
import numpy as np
import pandas as pd
from pathlib import Path
import joblib

# scikit-learn模型
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import AdaBoostClassifier, ExtraTreesClassifier
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, f1_score

from .interfaces import ModelInterface, ModelTrainerInterface, ConfigDict
from .config import get_config


class BaseMLModel(ModelInterface):
    """基础机器学习模型包装器"""
    
    def __init__(self, sklearn_model, model_name: str, **kwargs):
        self.sklearn_model = sklearn_model
        self._model_name = model_name
        self.is_fitted = False
        self.feature_names_ = None
        
        # 设置模型参数
        if kwargs:
            self.sklearn_model.set_params(**kwargs)
    
    def train(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> 'BaseMLModel':
        """训练模型"""
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = X.columns.tolist()
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        self.sklearn_model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """预测"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，请先调用train方法")
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        return self.sklearn_model.predict(X)
    
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """预测概率"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，请先调用train方法")
        
        if isinstance(X, pd.DataFrame):
            X = X.values
        
        if hasattr(self.sklearn_model, 'predict_proba'):
            return self.sklearn_model.predict_proba(X)
        else:
            # 对于不支持概率预测的模型，返回决策函数结果
            if hasattr(self.sklearn_model, 'decision_function'):
                decision = self.sklearn_model.decision_function(X)
                # 将决策函数转换为伪概率
                exp_decision = np.exp(decision)
                return exp_decision / (1 + exp_decision)
            else:
                raise ValueError(f"模型 {self.model_name} 不支持概率预测")
    
    def evaluate(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """评估模型"""
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        y_pred = self.predict(X)
        
        metrics = {
            'accuracy': self.sklearn_model.score(X, y),
            'f1_score': f1_score(y, y_pred, average='weighted')
        }
        
        # 添加AUC（如果支持概率预测）
        try:
            y_proba = self.predict_proba(X)
            if y_proba.shape[1] == 2:  # 二分类
                metrics['auc'] = roc_auc_score(y, y_proba[:, 1])
            else:  # 多分类
                metrics['auc'] = roc_auc_score(y, y_proba, multi_class='ovr')
        except:
            metrics['auc'] = 0.0
        
        return metrics
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """获取特征重要性"""
        if hasattr(self.sklearn_model, 'feature_importances_'):
            return self.sklearn_model.feature_importances_
        elif hasattr(self.sklearn_model, 'coef_'):
            return np.abs(self.sklearn_model.coef_[0])
        else:
            return None
    
    def save_model(self, path: str) -> None:
        """保存模型"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，无法保存")
        
        model_data = {
            'sklearn_model': self.sklearn_model,
            'model_name': self._model_name,
            'feature_names': self.feature_names_,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, path)
    
    def load_model(self, path: str) -> None:
        """加载模型"""
        model_data = joblib.load(path)
        
        self.sklearn_model = model_data['sklearn_model']
        self._model_name = model_data['model_name']
        self.feature_names_ = model_data['feature_names']
        self.is_fitted = model_data['is_fitted']
    
    @property
    def model_name(self) -> str:
        """模型名称"""
        return self._model_name


class ModelFactory:
    """模型工厂类"""
    
    def __init__(self):
        self.config = get_config()
        self._registered_models = {}
        self._register_default_models()
    
    def _register_default_models(self):
        """注册默认模型"""
        default_models = {
            'random_forest': {
                'class': RandomForestClassifier,
                'default_params': {
                    'n_estimators': 100,
                    'random_state': self.config.data.random_state,
                    'n_jobs': self.config.model.n_jobs
                }
            },
            'logistic_regression': {
                'class': LogisticRegression,
                'default_params': {
                    'random_state': self.config.data.random_state,
                    'max_iter': 1000
                }
            },
            'gradient_boosting': {
                'class': GradientBoostingClassifier,
                'default_params': {
                    'random_state': self.config.data.random_state,
                    'n_estimators': 100
                }
            },
            'svm': {
                'class': SVC,
                'default_params': {
                    'random_state': self.config.data.random_state,
                    'probability': True
                }
            },
            'neural_network': {
                'class': MLPClassifier,
                'default_params': {
                    'random_state': self.config.data.random_state,
                    'max_iter': 500
                }
            },
            'decision_tree': {
                'class': DecisionTreeClassifier,
                'default_params': {
                    'random_state': self.config.data.random_state
                }
            },
            'naive_bayes': {
                'class': GaussianNB,
                'default_params': {}
            },
            'knn': {
                'class': KNeighborsClassifier,
                'default_params': {
                    'n_neighbors': 5
                }
            },
            'ada_boost': {
                'class': AdaBoostClassifier,
                'default_params': {
                    'random_state': self.config.data.random_state
                }
            },
            'extra_trees': {
                'class': ExtraTreesClassifier,
                'default_params': {
                    'random_state': self.config.data.random_state,
                    'n_jobs': self.config.model.n_jobs
                }
            }
        }
        
        for name, model_config in default_models.items():
            self.register_model(name, model_config['class'], model_config['default_params'])
    
    def register_model(self, name: str, model_class: Type, default_params: Dict[str, Any] = None):
        """注册新模型"""
        self._registered_models[name] = {
            'class': model_class,
            'default_params': default_params or {}
        }
    
    def create_model(self, model_name: str, **kwargs) -> ModelInterface:
        """创建模型实例"""
        if model_name not in self._registered_models:
            raise ValueError(f"未知的模型类型: {model_name}. 可用模型: {list(self._registered_models.keys())}")
        
        model_config = self._registered_models[model_name]
        
        # 合并默认参数和自定义参数
        params = model_config['default_params'].copy()
        params.update(kwargs)
        
        # 创建sklearn模型实例
        sklearn_model = model_config['class'](**params)
        
        # 包装为统一接口
        return BaseMLModel(sklearn_model, model_name)
    
    def create_multiple_models(self, model_names: List[str], **kwargs) -> Dict[str, ModelInterface]:
        """创建多个模型实例"""
        models = {}
        for name in model_names:
            # 获取模型特定参数
            model_params = kwargs.get(name, {})
            models[name] = self.create_model(name, **model_params)
        return models
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self._registered_models.keys())
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name not in self._registered_models:
            raise ValueError(f"未知的模型类型: {model_name}")
        
        model_config = self._registered_models[model_name]
        return {
            'name': model_name,
            'class': model_config['class'],
            'default_params': model_config['default_params'],
            'doc': model_config['class'].__doc__
        }


class ModelTrainer(ModelTrainerInterface):
    """模型训练器"""
    
    def __init__(self, factory: ModelFactory = None):
        self.factory = factory or ModelFactory()
        self.config = get_config()
    
    def train_model(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                   y: Union[pd.Series, np.ndarray]) -> ModelInterface:
        """训练单个模型"""
        return model.train(X, y)
    
    def train_multiple_models(self, models: List[ModelInterface], 
                            X: Union[pd.DataFrame, np.ndarray], 
                            y: Union[pd.Series, np.ndarray]) -> Dict[str, ModelInterface]:
        """训练多个模型"""
        trained_models = {}
        
        for model in models:
            print(f"正在训练模型: {model.model_name}")
            trained_model = self.train_model(model, X, y)
            trained_models[model.model_name] = trained_model
            print(f"模型 {model.model_name} 训练完成")
        
        return trained_models
    
    def cross_validate(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                      y: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """交叉验证"""
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        # 确保模型是sklearn兼容的
        if hasattr(model, 'sklearn_model'):
            sklearn_model = model.sklearn_model
        else:
            raise ValueError("模型必须是sklearn兼容的")
        
        cv_scores = cross_val_score(
            sklearn_model, X, y, 
            cv=self.config.model.cross_validation_folds,
            scoring=self.config.model.scoring_metric,
            n_jobs=self.config.model.n_jobs
        )
        
        return {
            'mean_score': cv_scores.mean(),
            'std_score': cv_scores.std(),
            'scores': cv_scores.tolist()
        }
    
    def hyperparameter_tuning(self, model: ModelInterface, X: Union[pd.DataFrame, np.ndarray], 
                            y: Union[pd.Series, np.ndarray]) -> ModelInterface:
        """超参数调优"""
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values
        
        # 获取模型参数空间
        param_grid = self.config.model.model_params.get(model.model_name, {})
        
        if not param_grid:
            print(f"模型 {model.model_name} 没有定义参数空间，跳过超参数调优")
            return model.train(X, y)
        
        # 确保模型是sklearn兼容的
        if hasattr(model, 'sklearn_model'):
            sklearn_model = model.sklearn_model
        else:
            raise ValueError("模型必须是sklearn兼容的")
        
        # 网格搜索
        grid_search = GridSearchCV(
            sklearn_model,
            param_grid,
            cv=self.config.model.grid_search_cv,
            scoring=self.config.model.grid_search_scoring,
            n_jobs=self.config.model.n_jobs,
            verbose=1 if self.config.model.verbose else 0
        )
        
        grid_search.fit(X, y)
        
        # 使用最佳参数创建新模型
        best_model = self.factory.create_model(model.model_name, **grid_search.best_params_)
        best_model.train(X, y)
        
        print(f"模型 {model.model_name} 最佳参数: {grid_search.best_params_}")
        print(f"最佳交叉验证得分: {grid_search.best_score_:.4f}")
        
        return best_model


# 全局模型工厂实例
model_factory = ModelFactory()


def create_model(model_name: str, **kwargs) -> ModelInterface:
    """创建模型实例的便捷函数"""
    return model_factory.create_model(model_name, **kwargs)


def create_multiple_models(model_names: List[str], **kwargs) -> Dict[str, ModelInterface]:
    """创建多个模型实例的便捷函数"""
    return model_factory.create_multiple_models(model_names, **kwargs)


def get_available_models() -> List[str]:
    """获取可用模型列表的便捷函数"""
    return model_factory.get_available_models() 
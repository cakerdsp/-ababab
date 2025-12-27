#!/usr/bin/env python3
"""
随机森林模型实现
使用统一的基础模型类，支持SHAP分析和可视化
"""

import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import time
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class RandomForestModeler(BaseModel):
    """随机森林模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化随机森林模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.feature_importance_ = None
        
        # 获取模型特定配置
        self.auto_optimize = self._get_config_value('modeling.random_forest.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.random_forest.n_trials', 10)
        self.manual_params = self._get_config_value('modeling.random_forest.manual_params', {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'max_features': 'sqrt',
            'bootstrap': True,
            'random_state': 42
        })
        
    def train(self, X, y):
        """训练随机森林模型"""
        _LOG.info("训练随机森林模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始random_forest超参数优化，共{self.n_trials}次尝试...")
            
            def objective(trial):
                # 定义超参数搜索空间
                n_estimators = trial.suggest_int('n_estimators', 50, 200, step=50)
                max_depth = trial.suggest_categorical('max_depth', [None, 10, 20, 30])
                min_samples_split = trial.suggest_int('min_samples_split', 2, 10)
                min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 5)
                max_features = trial.suggest_categorical('max_features', ['sqrt', 'log2'])
                
                # 训练模型
                model = RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    max_features=max_features,
                    random_state=42,
                    n_jobs=-1
                )
                
                # 交叉验证
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(model, X, y, cv=5, scoring='f1')
                return scores.mean()
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            best_params['random_state'] = 42
            best_params['n_jobs'] = -1
            self.best_params = best_params.copy()
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳交叉验证分数: {study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练随机森林: {best_params}")
            self.model = RandomForestClassifier(**best_params)
        else:
            # 使用手动参数
            _LOG.info(f"使用手动参数训练随机森林: {self.manual_params}")
            self.model = RandomForestClassifier(**self.manual_params)
        
        # 训练模型
        self.model.fit(X, y)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        # 获取特征重要性
        self.feature_importance_ = self.model.feature_importances_
        
        self.is_trained = True
        _LOG.info(f"随机森林模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """预测概率"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        return self.model.predict_proba(X)
    
    def _plot_feature_importance(self):
        """绘制特征重要性"""
        if self.feature_importance_ is None:
            return
        
        try:
            # 获取top 15特征
            feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(self.feature_importance_))]
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': self.feature_importance_
            }).sort_values('importance', ascending=False).head(15)
            
            plt.figure(figsize=(10, 8))
            sns.barplot(data=importance_df, x='importance', y='feature')
            plt.title('Random Forest - Feature Importance')
            plt.xlabel('Feature Importance')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器 - 使用Tree explainer针对随机森林优化"""
        try:
            import shap
            # 对于树模型，使用Tree explainer更高效
            return shap.TreeExplainer(self.model)
        except:
            # 如果Tree explainer失败，使用通用explainer
            import shap
            return shap.Explainer(self.model.predict_proba, X_sample)
    
    def get_feature_importance(self):
        """获取特征重要性DataFrame"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(self.feature_importance_))]
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': self.feature_importance_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def plot_trees(self, max_trees=3):
        """绘制决策树可视化"""
        try:
            from sklearn.tree import plot_tree
            
            n_trees = min(max_trees, len(self.model.estimators_))
            
            for i in range(n_trees):
                plt.figure(figsize=(20, 10))
                plot_tree(
                    self.model.estimators_[i],
                    feature_names=self.feature_names,
                    class_names=['Not At Risk', 'At Risk'],
                    filled=True,
                    max_depth=3,  # 限制深度以提高可读性
                    fontsize=10
                )
                plt.title(f'Random Forest - Decision Tree {i+1}')
                
                filename = f'{self.__class__.__name__.lower()}_tree_{i+1}.{self.plot_format}'
                plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
            
            _LOG.info(f"决策树可视化已保存 ({n_trees}棵树)")
        except Exception as e:
            _LOG.warning(f"绘制决策树失败: {e}")
#!/usr/bin/env python3
"""
逻辑回归模型实现
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

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class LogisticRegressionModeler(BaseModel):
    """逻辑回归模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化逻辑回归模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.scaler = StandardScaler()
        self.feature_importance_ = None
        
        # 获取模型特定配置
        self.auto_optimize = self._get_config_value('modeling.logistic_regression.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.logistic_regression.n_trials', 10)
        self.manual_params = self._get_config_value('modeling.logistic_regression.manual_params', {
            'C': 1.0,
            'penalty': 'l2',
            'solver': 'lbfgs',
            'max_iter': 1000,
            'tol': 1e-4,
            'random_state': 42
        })
        
    def train(self, X, y):
        """训练逻辑回归模型"""
        _LOG.info("训练逻辑回归模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始logistic_regression超参数优化，共{self.n_trials}次尝试...")
            
            def objective(trial):
                # 定义超参数搜索空间
                penalty = trial.suggest_categorical('penalty', ['l1', 'l2'])
                C = trial.suggest_float('C', 0.01, 10.0, log=True)
                max_iter = trial.suggest_categorical('max_iter', [300, 400, 500])
                
                # 根据penalty选择solver
                if penalty == 'l1':
                    solver = 'liblinear'
                else:
                    solver = 'lbfgs'
                
                # 训练模型
                model = LogisticRegression(
                    penalty=penalty,
                    C=C,
                    solver=solver,
                    max_iter=max_iter,
                    random_state=42
                )
                
                # 交叉验证
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(model, X_scaled, y, cv=5, scoring='f1')
                return scores.mean()
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            self.best_params = best_params.copy()
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳交叉验证分数: {study.best_value:.4f}")
            
            # 确定solver
            if best_params['penalty'] == 'l1':
                best_params['solver'] = 'liblinear'
            else:
                best_params['solver'] = 'lbfgs'
            
            # 使用最佳参数训练最终模型
            best_params['random_state'] = 42
            self.best_params = best_params.copy()
            _LOG.info(f"使用最佳参数训练逻辑回归: {best_params}")
            self.model = LogisticRegression(**best_params)
        else:
            # 使用手动参数
            _LOG.info(f"使用手动参数训练逻辑回归: {self.manual_params}")
            self.model = LogisticRegression(**self.manual_params)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        # 计算特征重要性（系数的绝对值）
        self.feature_importance_ = np.abs(self.model.coef_[0])
        
        self.is_trained = True
        _LOG.info(f"逻辑回归模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """预测概率"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
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
            plt.title('Logistic Regression - Feature Importance (Coefficient Magnitude)')
            plt.xlabel('Coefficient Magnitude')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器 - 使用Linear explainer针对逻辑回归优化"""
        try:
            import shap
            # 对于逻辑回归，使用Linear explainer更高效
            X_scaled = self.scaler.transform(X_sample)
            return shap.LinearExplainer(self.model, X_scaled)
        except:
            # 如果Linear explainer失败，使用通用explainer
            import shap
            X_scaled = self.scaler.transform(X_sample)
            return shap.Explainer(self.model.predict_proba, X_scaled)
    
    def get_coefficients(self):
        """获取模型系数"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(self.model.coef_[0]))]
        
        coef_df = pd.DataFrame({
            'feature': feature_names,
            'coefficient': self.model.coef_[0],
            'abs_coefficient': np.abs(self.model.coef_[0])
        }).sort_values('abs_coefficient', ascending=False)
        
        return coef_df 
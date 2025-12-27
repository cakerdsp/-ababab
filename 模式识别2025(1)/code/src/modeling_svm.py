#!/usr/bin/env python3
"""
SVM支持向量机模型实现
使用统一的基础模型类，支持可视化分析
"""

import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import time
from pathlib import Path

from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class SVMModeler(BaseModel):
    """SVM支持向量机模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化SVM模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.scaler = StandardScaler()
        
        # 获取模型特定配置
        self.auto_optimize = self._get_config_value('modeling.svm.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.svm.n_trials', 20)
        self.manual_params = self._get_config_value('modeling.svm.manual_params', {
            'C': 1.0,
            'kernel': 'rbf',
            'gamma': 'scale',
            'probability': True,
            'random_state': 42
        })
        
    def train(self, X, y):
        """训练SVM模型"""
        _LOG.info("训练SVM支持向量机模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 标准化特征（SVM对特征尺度敏感）
        X_scaled = self.scaler.fit_transform(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始SVM超参数优化，共{self.n_trials}次尝试...")
            
            def objective(trial):
                # 定义超参数搜索空间
                C = trial.suggest_float('C', 0.1, 100.0, log=True)
                kernel = trial.suggest_categorical('kernel', ['linear', 'rbf', 'poly', 'sigmoid'])
                
                if kernel == 'rbf' or kernel == 'poly' or kernel == 'sigmoid':
                    gamma = trial.suggest_categorical('gamma', ['scale', 'auto'])
                else:
                    gamma = 'scale'
                
                if kernel == 'poly':
                    degree = trial.suggest_int('degree', 2, 5)
                else:
                    degree = 3
                
                # 训练模型
                model = SVC(
                    C=C,
                    kernel=kernel,
                    gamma=gamma,
                    degree=degree,
                    probability=True,
                    random_state=42
                )
                
                # 使用交叉验证评估
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(model, X_scaled, y, cv=3, scoring='f1')
                return scores.mean()
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            best_params['probability'] = True
            best_params['random_state'] = 42
            self.best_params = best_params
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳F1分数: {study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练SVM: {best_params}")
            self.model = SVC(**best_params)
        else:
            # 使用手动参数
            _LOG.info(f"使用手动参数训练SVM: {self.manual_params}")
            self.model = SVC(**self.manual_params)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        self.is_trained = True
        _LOG.info(f"SVM支持向量机模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测类别"""
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
    
    def evaluate(self, X_test, y_test, feature_names=None):
        """评估模型性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        self.feature_names = feature_names
        
        # 预测并测量时间
        y_pred = self.measure_prediction_time(X_test)
        y_proba = self.predict_proba(X_test)[:, 1]
        
        # 计算评估指标
        metrics = {
            'model_name': self.__class__.__name__,
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'roc_auc': roc_auc_score(y_test, y_proba)
        }
        
        _LOG.info(f"SVM模型评估完成 - F1分数: {metrics['f1_score']:.4f}")
        
        # 生成可视化
        self._plot_confusion_matrix(y_test, y_pred)
        self._plot_roc_curve(y_test, y_proba)
        self._plot_feature_importance()
        self._plot_support_vectors()
        
        # SHAP分析
        if self.enable_shap:
            self._perform_shap_analysis(X_test, y_test)
        
        return metrics
    
    def _plot_support_vectors(self):
        """绘制支持向量分析图"""
        try:
            if not hasattr(self.model, 'support_vectors_'):
                _LOG.warning("模型不支持支持向量可视化")
                return
            
            plt.figure(figsize=(12, 8))
            
            # 支持向量统计
            n_support = self.model.n_support_
            support_vectors = self.model.support_vectors_
            
            # 创建子图
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 支持向量数量统计
            axes[0, 0].bar(['Class 0', 'Class 1'], n_support)
            axes[0, 0].set_title('Number of Support Vectors by Class')
            axes[0, 0].set_ylabel('Count')
            
            # 2. 支持向量比例
            total_support = sum(n_support)
            support_ratio = [n / total_support for n in n_support]
            axes[0, 1].pie(support_ratio, labels=['Class 0', 'Class 1'], autopct='%1.1f%%')
            axes[0, 1].set_title('Support Vector Distribution')
            
            # 3. 核函数信息
            kernel_info = f"Kernel: {self.model.kernel}\n"
            kernel_info += f"C: {self.model.C:.3f}\n"
            kernel_info += f"Gamma: {self.model.gamma}\n"
            kernel_info += f"Total Support Vectors: {total_support}"
            
            axes[1, 0].text(0.1, 0.5, kernel_info, fontsize=12, 
                           verticalalignment='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Model Parameters')
            axes[1, 0].axis('off')
            
            # 4. 决策函数分布
            if hasattr(self.model, 'decision_function'):
                # 这里需要测试数据，暂时显示模型复杂度信息
                complexity_info = f"Model Complexity Analysis\n"
                complexity_info += f"Support Vector Ratio: {total_support/len(self.model.support_):.3f}\n"
                complexity_info += f"Dual Coefficients Range: [{self.model.dual_coef_.min():.3f}, {self.model.dual_coef_.max():.3f}]"
                
                axes[1, 1].text(0.1, 0.5, complexity_info, fontsize=12,
                               verticalalignment='center', transform=axes[1, 1].transAxes)
                axes[1, 1].set_title('Model Complexity')
                axes[1, 1].axis('off')
            
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_support_vectors.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"支持向量分析图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制支持向量分析图失败: {e}")
    
    def _plot_feature_importance(self):
        """绘制特征重要性（对于SVM，使用权重系数）"""
        try:
            if not hasattr(self.model, 'coef_'):
                _LOG.warning("SVM模型不支持特征重要性（非线性核）")
                return
            
            # 获取特征重要性（权重系数的绝对值）
            if self.model.kernel == 'linear':
                importances = np.abs(self.model.coef_[0])
                feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(importances))]
                
                # 创建DataFrame并排序
                importance_df = pd.DataFrame({
                    'feature': feature_names,
                    'importance': importances
                }).sort_values('importance', ascending=False).head(20)
                
                plt.figure(figsize=(10, 8))
                sns.barplot(data=importance_df, x='importance', y='feature')
                plt.title('SVM - Feature Importance (Linear Kernel)')
                plt.xlabel('Absolute Coefficient Value')
                plt.tight_layout()
                
                filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
                plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
                _LOG.info(f"特征重要性图已保存: {filename}")
            else:
                _LOG.info("非线性SVM核不支持直接特征重要性，请使用SHAP分析")
                
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器"""
        try:
            import shap
            
            # 对于SVM，使用KernelExplainer
            def model_predict(X):
                return self.model.predict_proba(X)[:, 1]
            
            # 使用较小的背景数据集
            background_size = min(100, len(X_sample))
            background = X_sample.iloc[:background_size] if hasattr(X_sample, 'iloc') else X_sample[:background_size]
            
            explainer = shap.KernelExplainer(model_predict, background)
            return explainer
            
        except Exception as e:
            _LOG.warning(f"创建SHAP解释器失败: {e}")
            return None 
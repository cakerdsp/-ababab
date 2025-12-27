#!/usr/bin/env python3
"""
神经网络模型实现
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

from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class NeuralNetworkModeler(BaseModel):
    """神经网络模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化神经网络模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.scaler = StandardScaler()
        self.feature_importance_ = None
        
        # 获取模型特定配置
        self.auto_optimize = self._get_config_value('modeling.neural_network.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.neural_network.n_trials', 10)
        self.manual_params = self._get_config_value('modeling.neural_network.manual_params', {
            'hidden_layer_sizes': (64, 32),
            'activation': 'relu',
            'solver': 'adam',
            'learning_rate': 0.001,
            'max_iter': 1000,
            'random_state': 42,
            'early_stopping': True,
            'validation_fraction': 0.1
        })
        
    def train(self, X, y):
        """训练神经网络模型"""
        _LOG.info("训练神经网络模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始neural_network超参数优化，共{self.n_trials}次尝试...")
            
            def objective(trial):
                # 定义超参数搜索空间
                n_layers = trial.suggest_int('n_layers', 1, 3)
                hidden_sizes = []
                for i in range(n_layers):
                    size = trial.suggest_int(f'layer_{i}_size', 32, 128, step=16)
                    hidden_sizes.append(size)
                
                activation = trial.suggest_categorical('activation', ['relu', 'tanh'])
                solver = trial.suggest_categorical('solver', ['adam', 'sgd'])
                learning_rate_init = trial.suggest_float('learning_rate_init', 1e-4, 1e-2, log=True)
                alpha = trial.suggest_float('alpha', 1e-5, 1e-2, log=True)
                
                try:
                    # 训练模型
                    model = MLPClassifier(
                        hidden_layer_sizes=tuple(hidden_sizes),
                        activation=activation,
                        solver=solver,
                        learning_rate_init=learning_rate_init,
                        alpha=alpha,
                        max_iter=500,
                        early_stopping=True,
                        validation_fraction=0.1,
                        random_state=42
                    )
                    
                    # 交叉验证
                    from sklearn.model_selection import cross_val_score
                    scores = cross_val_score(model, X_scaled, y, cv=3, scoring='f1')
                    return scores.mean()
                except:
                    return 0.0  # 训练失败返回0
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            
            # 重构hidden_layer_sizes
            n_layers = best_params.pop('n_layers')
            hidden_sizes = []
            for i in range(n_layers):
                hidden_sizes.append(best_params.pop(f'layer_{i}_size'))
            best_params['hidden_layer_sizes'] = tuple(hidden_sizes)
            best_params['random_state'] = 42
            best_params['max_iter'] = 1000
            best_params['early_stopping'] = True
            best_params['validation_fraction'] = 0.1
            self.best_params = best_params.copy()
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳交叉验证分数: {study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练神经网络: {best_params}")
            self.model = MLPClassifier(**best_params)
        else:
            # 使用手动参数
            _LOG.info(f"使用手动参数训练神经网络: {self.manual_params}")
            self.model = MLPClassifier(**self.manual_params)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        # 计算特征重要性（使用排列重要性）
        self._calculate_feature_importance(X_scaled, y)
        
        self.is_trained = True
        _LOG.info(f"神经网络模型训练完成，耗时: {self.training_time:.2f}秒")
        
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
    
    def _calculate_feature_importance(self, X, y):
        """计算特征重要性（使用排列重要性）"""
        try:
            from sklearn.inspection import permutation_importance
            
            _LOG.info("计算神经网络特征重要性...")
            # 使用排列重要性
            perm_importance = permutation_importance(
                self.model, X, y, 
                n_repeats=5, 
                random_state=42,
                scoring='f1'
            )
            self.feature_importance_ = perm_importance.importances_mean
            _LOG.info("特征重要性计算完成")
        except Exception as e:
            _LOG.warning(f"计算特征重要性失败: {e}")
            self.feature_importance_ = None
    
    def evaluate(self, X_test, y_test, feature_names=None):
        """评估模型性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        self.feature_names = feature_names
        
        # 标准化测试数据
        X_scaled = self.scaler.transform(X_test)
        
        # 基础预测
        y_pred = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)
        
        # 计算指标
        metrics = {
            'model_name': self.__class__.__name__,
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
        }
        
        # ROC AUC (仅二分类)
        if len(np.unique(y_test)) == 2:
            if y_proba.ndim > 1 and y_proba.shape[1] > 1:
                metrics['roc_auc'] = roc_auc_score(y_test, y_proba[:, 1])
            else:
                metrics['roc_auc'] = roc_auc_score(y_test, y_proba)
        
        _LOG.info(f"神经网络评估完成 - F1: {metrics['f1_score']:.4f}, AUC: {metrics.get('roc_auc', 'N/A')}")
        
        # 生成可视化
        self._plot_training_curve()
        self._plot_confusion_matrix(y_test, y_pred)
        self._plot_roc_curve(y_test, y_proba)
        self._plot_feature_importance()
        self._plot_network_architecture()
        
        # SHAP分析
        if self.enable_shap:
            self._perform_shap_analysis(X_test, y_test)
        
        return metrics
    
    def _plot_training_curve(self):
        """绘制训练损失曲线"""
        try:
            if hasattr(self.model, 'loss_curve_') and self.model.loss_curve_ is not None:
                plt.figure(figsize=(10, 6))
                plt.plot(self.model.loss_curve_, linewidth=2)
                plt.title('Neural Network - Training Loss Curve')
                plt.xlabel('Iteration')
                plt.ylabel('Loss')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                filename = f'{self.__class__.__name__.lower()}_training_curve.{self.plot_format}'
                plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
                _LOG.info(f"训练曲线已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制训练曲线失败: {e}")
    
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
            plt.title('Neural Network - Feature Importance (Permutation)')
            plt.xlabel('Permutation Importance')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def _plot_network_architecture(self):
        """绘制网络架构图"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # 获取网络结构信息
            layer_sizes = [self.model.n_features_in_] + list(self.model.hidden_layer_sizes) + [self.model.n_outputs_]
            n_layers = len(layer_sizes)
            
            # 设置每层的位置
            layer_positions = np.linspace(0, 10, n_layers)
            max_neurons = max(layer_sizes)
            
            # 绘制每一层
            for i, (pos, size) in enumerate(zip(layer_positions, layer_sizes)):
                # 计算神经元的y坐标
                if size <= 10:  # 如果神经元数量少，显示所有
                    y_positions = np.linspace(-size/2, size/2, size)
                    for y in y_positions:
                        circle = plt.Circle((pos, y), 0.1, color='lightblue', ec='black')
                        ax.add_patch(circle)
                else:  # 如果神经元数量多，只显示部分并用...表示
                    y_positions = np.linspace(-2, 2, 5)
                    for j, y in enumerate(y_positions):
                        if j == 2:  # 中间位置显示省略号
                            ax.text(pos, y, f'...\\n({size})', ha='center', va='center', fontsize=8)
                        else:
                            circle = plt.Circle((pos, y), 0.1, color='lightblue', ec='black')
                            ax.add_patch(circle)
                
                # 添加层标签
                if i == 0:
                    ax.text(pos, -max_neurons/2 - 1, f'Input\\n({size})', ha='center', fontsize=10, weight='bold')
                elif i == n_layers - 1:
                    ax.text(pos, -max_neurons/2 - 1, f'Output\\n({size})', ha='center', fontsize=10, weight='bold')
                else:
                    ax.text(pos, -max_neurons/2 - 1, f'Hidden {i}\\n({size})', ha='center', fontsize=10, weight='bold')
            
            # 绘制连接线（简化显示）
            for i in range(n_layers - 1):
                ax.plot([layer_positions[i] + 0.1, layer_positions[i+1] - 0.1], 
                       [0, 0], 'k-', alpha=0.3, linewidth=1)
            
            ax.set_xlim(-0.5, 10.5)
            ax.set_ylim(-max_neurons/2 - 2, max_neurons/2 + 1)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title('Neural Network Architecture', fontsize=14, weight='bold', pad=20)
            
            # 添加激活函数信息
            activation_text = f"Activation: {self.model.activation}\\nSolver: {self.model.solver}\\nLayers: {len(self.model.hidden_layer_sizes)}"
            ax.text(5, max_neurons/2 + 0.5, activation_text, ha='center', fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            
            plt.tight_layout()
            filename = f'{self.__class__.__name__.lower()}_architecture.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"网络架构图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制网络架构失败: {e}")
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器 - 神经网络使用通用explainer"""
        try:
            import shap
            # 对于神经网络，使用KernelExplainer更稳定
            X_scaled = self.scaler.transform(X_sample)
            
            # 创建一个包装函数用于预测
            def model_predict(X):
                return self.model.predict_proba(X)[:, 1]  # 返回正类概率
            
            # 使用KernelExplainer，取少量样本作为背景
            background_size = min(50, len(X_scaled))
            background = X_scaled[:background_size]
            
            return shap.KernelExplainer(model_predict, background)
        except Exception as e:
            _LOG.warning(f"创建SHAP KernelExplainer失败，尝试Explainer: {e}")
            try:
                import shap
                X_scaled = self.scaler.transform(X_sample)
                return shap.Explainer(self.model.predict_proba, X_scaled)
            except Exception as e2:
                _LOG.warning(f"创建SHAP Explainer失败: {e2}")
                # 最后的备选方案
                import shap
                X_scaled = self.scaler.transform(X_sample)
                return shap.Explainer(self.model.predict, X_scaled)
    
    def get_network_info(self):
        """获取网络信息"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        return {
            'hidden_layer_sizes': self.model.hidden_layer_sizes,
            'activation': self.model.activation,
            'solver': self.model.solver,
            'n_layers': len(self.model.hidden_layer_sizes) + 1,
            'n_parameters': sum([w.size for w in self.model.coefs_]) + sum([b.size for b in self.model.intercepts_]),
            'n_iterations': self.model.n_iter_,
            'loss': self.model.loss_ if hasattr(self.model, 'loss_') else None
        } 
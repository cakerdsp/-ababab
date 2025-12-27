#!/usr/bin/env python3
"""
EM（期望最大化）模型实现
使用高斯混合模型进行聚类和概率估计
"""

import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import time
from pathlib import Path

from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import silhouette_score, adjusted_rand_score, calinski_harabasz_score
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class EMModeler(BaseModel):
    """EM（期望最大化）模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化EM模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.scaler = StandardScaler()
        
        # 获取模型特定配置
        self.n_components = self._get_config_value('modeling.em.n_components', 2)
        self.auto_optimize = self._get_config_value('modeling.em.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.em.n_trials', 15)
        self.manual_params = self._get_config_value('modeling.em.manual_params', {
            'n_components': 2,
            'covariance_type': 'full',
            'max_iter': 100,
            'tol': 1e-3,
            'random_state': 42
        })
        
    def train(self, X, y=None):
        """训练EM模型"""
        _LOG.info("训练EM（高斯混合）模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始EM超参数优化，共{self.n_trials}次尝试...")
            _LOG.info(f"固定组件数为: {self.n_components}")
            
            def objective(trial):
                # 定义超参数搜索空间（固定组件数）
                covariance_type = trial.suggest_categorical('covariance_type', 
                                                           ['full', 'tied', 'diag', 'spherical'])
                max_iter = trial.suggest_int('max_iter', 50, 200)
                tol = trial.suggest_float('tol', 1e-4, 1e-2, log=True)
                
                # 训练模型
                model = GaussianMixture(
                    n_components=self.n_components,
                    covariance_type=covariance_type,
                    max_iter=max_iter,
                    tol=tol,
                    random_state=42
                )
                
                try:
                    model.fit(X_scaled)
                    # 使用BIC作为评估指标（越小越好）
                    bic_score = model.bic(X_scaled)
                    return -bic_score  # 转换为最大化问题
                except Exception as e:
                    _LOG.warning(f"模型训练失败: {e}")
                    return -np.inf
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            best_params['n_components'] = self.n_components
            best_params['random_state'] = 42
            self.best_params = best_params
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳BIC分数: {-study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练EM: {best_params}")
            self.model = GaussianMixture(**best_params)
        else:
            # 使用手动参数
            params = self.manual_params.copy()
            params['n_components'] = self.n_components
            _LOG.info(f"使用手动参数训练EM: {params}")
            self.model = GaussianMixture(**params)
        
        # 训练模型
        self.model.fit(X_scaled)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        self.is_trained = True
        _LOG.info(f"EM（高斯混合）模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测类别（聚类标签）"""
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
    
    def evaluate(self, X_test, y_test=None, feature_names=None):
        """评估模型性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        self.feature_names = feature_names
        X_scaled = self.scaler.transform(X_test)
        
        # 预测聚类标签并测量时间
        start_pred_time = time.time()
        cluster_labels = self.model.predict(X_scaled)
        cluster_proba = self.model.predict_proba(X_scaled)
        self.prediction_time = time.time() - start_pred_time
        
        # 计算聚类评估指标
        metrics = {
            'model_name': self.__class__.__name__,
            'n_components': self.n_components,
            'bic_score': self.model.bic(X_scaled),
            'aic_score': self.model.aic(X_scaled),
            'log_likelihood': self.model.score(X_scaled),
            'silhouette_score': silhouette_score(X_scaled, cluster_labels)
        }
        
        # 如果有真实标签，计算监督学习指标
        if y_test is not None:
            # 尝试将聚类结果映射到真实标签
            cluster_to_label = self._map_clusters_to_labels(cluster_labels, y_test)
            mapped_predictions = np.array([cluster_to_label[c] for c in cluster_labels])
            
            metrics.update({
                'adjusted_rand_score': adjusted_rand_score(y_test, cluster_labels),
                'mapped_accuracy': accuracy_score(y_test, mapped_predictions),
                'mapped_precision': precision_score(y_test, mapped_predictions, average='weighted'),
                'mapped_recall': recall_score(y_test, mapped_predictions, average='weighted'),
                'mapped_f1_score': f1_score(y_test, mapped_predictions, average='weighted')
            })
            
            # 如果是二分类问题，计算ROC-AUC
            if len(np.unique(y_test)) == 2:
                # 使用属于正类的概率
                positive_proba = cluster_proba[:, cluster_to_label.get(1, 0)]
                metrics['mapped_roc_auc'] = roc_auc_score(y_test, positive_proba)
        
        _LOG.info(f"EM模型评估完成 - BIC分数: {metrics['bic_score']:.4f}")
        
        # 生成可视化
        self._plot_clusters(X_test, cluster_labels, y_test)
        self._plot_gaussian_components(X_test)
        self._plot_model_selection_criteria()
        self._plot_feature_importance()
        
        # 注意：EM是无监督学习算法，SHAP分析需要特殊处理
        _LOG.info("EM模型为无监督学习，不使用标准SHAP分析")
        
        return metrics
    
    def _map_clusters_to_labels(self, cluster_labels, true_labels):
        """将聚类标签映射到真实标签"""
        from collections import Counter
        
        cluster_to_label = {}
        for cluster_id in np.unique(cluster_labels):
            cluster_mask = cluster_labels == cluster_id
            cluster_true_labels = true_labels[cluster_mask]
            most_common_label = Counter(cluster_true_labels).most_common(1)[0][0]
            cluster_to_label[cluster_id] = most_common_label
        
        return cluster_to_label
    
    def _plot_clusters(self, X, cluster_labels, y_true=None):
        """绘制聚类结果"""
        try:
            from sklearn.decomposition import PCA
            
            # 使用PCA降维到2D进行可视化
            pca = PCA(n_components=2)
            X_scaled = self.scaler.transform(X)
            X_pca = pca.fit_transform(X_scaled)
            
            fig, axes = plt.subplots(1, 2 if y_true is not None else 1, figsize=(15, 6))
            if y_true is None:
                axes = [axes]
            
            # 聚类结果
            scatter = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=cluster_labels, 
                                    cmap='viridis', alpha=0.7)
            axes[0].set_title('EM Clustering Results')
            axes[0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
            axes[0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
            plt.colorbar(scatter, ax=axes[0])
            
            # 真实标签对比
            if y_true is not None:
                scatter2 = axes[1].scatter(X_pca[:, 0], X_pca[:, 1], c=y_true, 
                                         cmap='coolwarm', alpha=0.7)
                axes[1].set_title('True Labels')
                axes[1].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
                axes[1].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
                plt.colorbar(scatter2, ax=axes[1])
            
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_clustering_results.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"聚类结果图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制聚类结果失败: {e}")
    
    def _plot_gaussian_components(self, X):
        """绘制高斯组件分析"""
        try:
            X_scaled = self.scaler.transform(X)
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 组件权重
            weights = self.model.weights_
            axes[0, 0].bar(range(len(weights)), weights)
            axes[0, 0].set_title('Component Weights')
            axes[0, 0].set_xlabel('Component')
            axes[0, 0].set_ylabel('Weight')
            
            # 2. 组件均值对比（选择前几个特征）
            means = self.model.means_
            n_features_to_show = min(10, means.shape[1])
            feature_names = (self.feature_names[:n_features_to_show] 
                           if self.feature_names else [f'Feature_{i}' for i in range(n_features_to_show)])
            
            x_pos = np.arange(len(feature_names))
            width = 0.35
            
            for i in range(self.n_components):
                axes[0, 1].bar(x_pos + i * width, means[i, :n_features_to_show], 
                             width, label=f'Component {i}', alpha=0.7)
            
            axes[0, 1].set_title('Component Means (Top Features)')
            axes[0, 1].set_xlabel('Features')
            axes[0, 1].set_ylabel('Mean Value')
            axes[0, 1].set_xticks(x_pos + width / 2)
            axes[0, 1].set_xticklabels(feature_names, rotation=45)
            axes[0, 1].legend()
            
            # 3. 模型信息
            model_info = f"Model Information\n"
            model_info += f"Components: {self.n_components}\n"
            model_info += f"Covariance Type: {self.model.covariance_type}\n"
            model_info += f"Converged: {self.model.converged_}\n"
            model_info += f"Iterations: {self.model.n_iter_}\n"
            model_info += f"Log Likelihood: {self.model.score(X_scaled):.3f}"
            
            axes[1, 0].text(0.1, 0.5, model_info, fontsize=12,
                           verticalalignment='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Model Information')
            axes[1, 0].axis('off')
            
            # 4. 责任度分布
            responsibilities = self.model.predict_proba(X_scaled)
            axes[1, 1].hist([responsibilities[:, i] for i in range(self.n_components)], 
                           bins=30, alpha=0.7, label=[f'Component {i}' for i in range(self.n_components)])
            axes[1, 1].set_title('Responsibility Distribution')
            axes[1, 1].set_xlabel('Responsibility')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].legend()
            
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_gaussian_components.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"高斯组件分析图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制高斯组件分析失败: {e}")
    
    def _plot_model_selection_criteria(self):
        """绘制模型选择准则"""
        try:
            # 计算不同组件数的BIC和AIC
            n_components_range = range(1, min(10, self.n_components * 3))
            bic_scores = []
            aic_scores = []
            
            X_scaled = self.scaler.transform(self.model.means_.T)  # 使用训练时的数据维度
            
            for n_comp in n_components_range:
                try:
                    temp_model = GaussianMixture(n_components=n_comp, random_state=42)
                    temp_model.fit(X_scaled)
                    bic_scores.append(temp_model.bic(X_scaled))
                    aic_scores.append(temp_model.aic(X_scaled))
                except:
                    # 如果某个组件数失败，跳过
                    continue
            
            if len(bic_scores) > 1:
                plt.figure(figsize=(10, 6))
                plt.plot(n_components_range[:len(bic_scores)], bic_scores, 'bo-', label='BIC')
                plt.plot(n_components_range[:len(aic_scores)], aic_scores, 'ro-', label='AIC')
                plt.axvline(x=self.n_components, color='g', linestyle='--', label=f'Selected: {self.n_components}')
                plt.xlabel('Number of Components')
                plt.ylabel('Information Criterion')
                plt.title('Model Selection Criteria')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                filename = f'{self.__class__.__name__.lower()}_model_selection.{self.plot_format}'
                plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
                _LOG.info(f"模型选择准则图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制模型选择准则失败: {e}")
    
    def _plot_feature_importance(self):
        """绘制特征重要性（对于EM，使用组件均值的方差）"""
        try:
            if not hasattr(self.model, 'means_'):
                _LOG.warning("EM模型不支持特征重要性")
                return
            
            # 计算每个特征在不同组件间的方差作为重要性指标
            means = self.model.means_  # shape: (n_components, n_features)
            feature_variance = np.var(means, axis=0)
            
            feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(feature_variance))]
            
            # 创建DataFrame并排序
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': feature_variance
            }).sort_values('importance', ascending=False).head(20)
            
            plt.figure(figsize=(10, 8))
            sns.barplot(data=importance_df, x='importance', y='feature')
            plt.title('EM - Feature Importance (Component Mean Variance)')
            plt.xlabel('Variance Across Components')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}") 
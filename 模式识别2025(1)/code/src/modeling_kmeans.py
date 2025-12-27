#!/usr/bin/env python3
"""
K-Means聚类模型实现
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

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, adjusted_rand_score, calinski_harabasz_score
from sklearn.decomposition import PCA
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class KMeansModeler(BaseModel):
    """K-Means聚类模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化K-Means模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)  # 用于可视化
        self.cluster_centers_ = None
        self.labels_ = None
        
        # 获取模型特定配置
        self.n_clusters = self._get_config_value('modeling.kmeans.n_clusters', 2)
        self.auto_optimize = self._get_config_value('modeling.kmeans.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.kmeans.n_trials', 10)
        self.manual_params = self._get_config_value('modeling.kmeans.manual_params', {
            'init': 'k-means++',
            'max_iter': 300,
            'tol': 1e-4,
            'random_state': 42,
            'n_init': 10
        })
        
    def train(self, X, y=None):
        """训练K-Means模型"""
        _LOG.info("训练K-Means聚类模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始kmeans超参数优化，共{self.n_trials}次尝试...")
            _LOG.info(f"固定聚类数为: {self.n_clusters}")
            
            def objective(trial):
                # 定义超参数搜索空间（固定聚类数）
                init = trial.suggest_categorical('init', ['k-means++', 'random'])
                n_init = trial.suggest_int('n_init', 5, 20)
                
                # 训练模型
                model = KMeans(
                    n_clusters=self.n_clusters,  # 使用配置中的固定聚类数
                    init=init,
                    n_init=n_init,
                    random_state=42
                )
                
                # 使用轮廓系数作为评估指标
                cluster_labels = model.fit_predict(X_scaled)
                score = silhouette_score(X_scaled, cluster_labels)
                return score
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            best_params['random_state'] = 42
            best_params['n_clusters'] = self.n_clusters  # 确保使用配置中的聚类数
            self.best_params = best_params.copy()
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳轮廓系数: {study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练K-Means: {best_params}")
            self.model = KMeans(**best_params)
        else:
            # 使用手动参数
            params = self.manual_params.copy()
            params['n_clusters'] = self.n_clusters
            _LOG.info(f"使用手动参数训练K-Means: {params}")
            self.model = KMeans(**params)
        
        # 训练模型
        self.model.fit(X_scaled)
        self.labels_ = self.model.labels_
        self.cluster_centers_ = self.model.cluster_centers_
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        # 准备可视化数据
        self.pca.fit(X_scaled)
        
        self.is_trained = True
        _LOG.info(f"K-Means聚类模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测聚类标签"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """K-Means没有概率预测，返回距离的倒数作为"概率"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        X_scaled = self.scaler.transform(X)
        distances = self.model.transform(X_scaled)
        
        # 将距离转换为相似度分数
        # 使用距离的倒数，然后标准化
        similarities = 1 / (1 + distances)
        probabilities = similarities / similarities.sum(axis=1, keepdims=True)
        
        # 返回属于每个聚类的概率
        return probabilities
    
    def evaluate(self, X_test, y_test=None, feature_names=None):
        """评估聚类性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        self.feature_names = feature_names
        X_scaled = self.scaler.transform(X_test)
        
        # 预测并测量时间
        start_pred_time = time.time()
        cluster_labels = self.model.predict(X_scaled)
        self.prediction_time = time.time() - start_pred_time
        
        # 计算聚类指标
        metrics = {
            'model_name': self.__class__.__name__,
            'silhouette_score': silhouette_score(X_scaled, cluster_labels),
            'calinski_harabasz_score': calinski_harabasz_score(X_scaled, cluster_labels),
            'n_clusters': self.n_clusters
        }
        
        # 如果有真实标签，计算ARI
        if y_test is not None:
            metrics['adjusted_rand_score'] = adjusted_rand_score(y_test, cluster_labels)
        
        _LOG.info(f"聚类评估完成 - 轮廓系数: {metrics['silhouette_score']:.4f}")
        
        # 生成可视化
        self._plot_clusters(X_test, cluster_labels, y_test)
        self._plot_cluster_analysis(X_test, cluster_labels, y_test)
        self._plot_feature_importance()
        
        # 注意：K-Means是无监督聚类算法，不适用SHAP分析
        # SHAP分析主要用于有监督学习模型的特征重要性解释
        # 对于聚类，我们使用聚类中心方差等方法来分析特征重要性
        _LOG.info("K-Means聚类不使用SHAP分析（无监督学习），使用聚类中心方差分析特征重要性")
        
        return metrics
    
    def _plot_clusters(self, X, cluster_labels, y_true=None):
        """绘制聚类结果"""
        try:
            X_scaled = self.scaler.transform(X)
            X_pca = self.pca.transform(X_scaled)
            
            fig, axes = plt.subplots(1, 2 if y_true is not None else 1, figsize=(15, 6))
            if y_true is None:
                axes = [axes]
            
            # 聚类结果
            scatter = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=cluster_labels, cmap='viridis', alpha=0.7)
            axes[0].set_title('K-Means Clustering Results')
            axes[0].set_xlabel('First Principal Component')
            axes[0].set_ylabel('Second Principal Component')
            plt.colorbar(scatter, ax=axes[0])
            
            # 绘制聚类中心
            centers_pca = self.pca.transform(self.cluster_centers_)
            axes[0].scatter(centers_pca[:, 0], centers_pca[:, 1], 
                          c='red', marker='x', s=200, linewidths=3, label='Centroids')
            axes[0].legend()
            
            # 如果有真实标签，也绘制真实分布
            if y_true is not None:
                scatter2 = axes[1].scatter(X_pca[:, 0], X_pca[:, 1], c=y_true, cmap='coolwarm', alpha=0.7)
                axes[1].set_title('True Labels')
                axes[1].set_xlabel('First Principal Component')
                axes[1].set_ylabel('Second Principal Component')
                plt.colorbar(scatter2, ax=axes[1])
            
            plt.tight_layout()
            filename = f'{self.__class__.__name__.lower()}_clustering_results.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"聚类结果图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制聚类结果失败: {e}")
    
    def _plot_cluster_analysis(self, X, cluster_labels, y_true=None):
        """绘制聚类分析图"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 聚类大小分布
            cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
            axes[0, 0].bar(cluster_counts.index, cluster_counts.values)
            axes[0, 0].set_title('Cluster Size Distribution')
            axes[0, 0].set_xlabel('Cluster')
            axes[0, 0].set_ylabel('Number of Points')
            
            # 2. 聚类内距离分布
            X_scaled = self.scaler.transform(X)
            distances = []
            for i in range(self.n_clusters):
                cluster_mask = cluster_labels == i
                if np.any(cluster_mask):
                    cluster_points = X_scaled[cluster_mask]
                    center = self.cluster_centers_[i]
                    cluster_distances = np.linalg.norm(cluster_points - center, axis=1)
                    distances.extend(cluster_distances)
            
            axes[0, 1].hist(distances, bins=30, alpha=0.7)
            axes[0, 1].set_title('Distance to Cluster Centers')
            axes[0, 1].set_xlabel('Distance')
            axes[0, 1].set_ylabel('Frequency')
            
            # 3. 如果有真实标签，绘制混淆矩阵风格的聚类vs真实标签
            if y_true is not None:
                confusion_like = pd.crosstab(cluster_labels, y_true, margins=True)
                sns.heatmap(confusion_like.iloc[:-1, :-1], annot=True, fmt='d', ax=axes[1, 0])
                axes[1, 0].set_title('Clusters vs True Labels')
                axes[1, 0].set_xlabel('True Labels')
                axes[1, 0].set_ylabel('Cluster Labels')
            else:
                axes[1, 0].text(0.5, 0.5, 'No True Labels Available', 
                              ha='center', va='center', transform=axes[1, 0].transAxes)
                axes[1, 0].set_title('True Labels Not Available')
            
            # 4. 轮廓分析
            from sklearn.metrics import silhouette_samples
            sample_silhouette_values = silhouette_samples(X_scaled, cluster_labels)
            y_lower = 10
            
            for i in range(self.n_clusters):
                cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]
                cluster_silhouette_values.sort()
                
                size_cluster_i = cluster_silhouette_values.shape[0]
                y_upper = y_lower + size_cluster_i
                
                color = plt.cm.nipy_spectral(float(i) / self.n_clusters)
                axes[1, 1].fill_betweenx(np.arange(y_lower, y_upper),
                                       0, cluster_silhouette_values,
                                       facecolor=color, edgecolor=color, alpha=0.7)
                
                axes[1, 1].text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))
                y_lower = y_upper + 10
            
            axes[1, 1].set_xlabel('Silhouette Coefficient Values')
            axes[1, 1].set_ylabel('Cluster Label')
            axes[1, 1].set_title('Silhouette Analysis for Clustering Quality')
            
            # 添加平均轮廓系数线
            avg_score = np.mean(sample_silhouette_values)
            axes[1, 1].axvline(x=avg_score, color="red", linestyle="--", 
                             label=f'Average Score: {avg_score:.3f}')
            axes[1, 1].legend()
            
            # 添加说明文字
            axes[1, 1].text(0.02, 0.98, 
                           'Higher values indicate better clustering\n'
                           'Values close to 1: well-clustered\n'
                           'Values close to 0: on cluster boundaries\n'
                           'Negative values: wrongly clustered',
                           transform=axes[1, 1].transAxes, fontsize=8,
                           verticalalignment='top',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
            
            plt.tight_layout()
            filename = f'{self.__class__.__name__.lower()}_cluster_analysis.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"聚类分析图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制聚类分析失败: {e}")
    
    def _plot_feature_importance(self):
        """绘制特征重要性（基于聚类中心的方差）"""
        if self.cluster_centers_ is None:
            return
        
        try:
            # 计算特征在不同聚类中心间的方差作为重要性
            feature_variance = np.var(self.cluster_centers_, axis=0)
            
            feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(feature_variance))]
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': feature_variance
            }).sort_values('importance', ascending=False).head(15)
            
            plt.figure(figsize=(10, 8))
            sns.barplot(data=importance_df, x='importance', y='feature')
            plt.title('K-Means - Feature Importance (Cluster Center Variance)')
            plt.xlabel('Variance Across Cluster Centers')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def get_cluster_characteristics(self, X):
        """获取每个聚类的特征统计"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        cluster_labels = self.predict(X)
        characteristics = {}
        
        for cluster_id in range(self.n_clusters):
            mask = cluster_labels == cluster_id
            cluster_data = X[mask]
            
            characteristics[f'Cluster_{cluster_id}'] = {
                'size': np.sum(mask),
                'percentage': np.sum(mask) / len(X) * 100,
                'mean': cluster_data.mean().to_dict() if hasattr(cluster_data, 'mean') else np.mean(cluster_data, axis=0),
                'std': cluster_data.std().to_dict() if hasattr(cluster_data, 'std') else np.std(cluster_data, axis=0)
            }
        
        return characteristics 
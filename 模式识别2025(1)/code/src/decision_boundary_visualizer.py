#!/usr/bin/env python3
"""
决策边界可视化模块
专门用于绘制2D决策边界图的独立模块
松耦合设计，不依赖于现有的核心文件
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import logging
import warnings
warnings.filterwarnings('ignore')

_LOG = logging.getLogger(__name__)


class DecisionBoundaryVisualizer:
    """决策边界可视化器"""
    
    def __init__(self, output_dir="outputs/plots/decision_boundaries"):
        """
        初始化可视化器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置颜色映射
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        self.cmap = ListedColormap(self.colors[:2])
        
        # 设置图形参数
        self.fig_size = (10, 8)
        self.dpi = 300
        
    def _select_best_features(self, X, y, feature_names, n_features=2, method='variance'):
        """
        选择最佳特征用于2D可视化
        
        Args:
            X: 特征矩阵
            y: 标签
            feature_names: 特征名称
            n_features: 选择的特征数量
            method: 选择方法 ('variance', 'correlation', 'random_forest')
            
        Returns:
            selected_features: 选择的特征索引
            selected_names: 选择的特征名称
        """
        if method == 'variance':
            # 基于方差选择特征
            variances = np.var(X, axis=0)
            selected_indices = np.argsort(variances)[-n_features:]
            
        elif method == 'correlation':
            # 基于与目标变量的相关性选择特征
            if hasattr(y, 'values'):
                y_values = y.values
            else:
                y_values = y
            
            correlations = []
            for i in range(X.shape[1]):
                corr = np.corrcoef(X[:, i], y_values)[0, 1]
                correlations.append(abs(corr) if not np.isnan(corr) else 0)
            
            correlations = np.array(correlations)
            selected_indices = np.argsort(correlations)[-n_features:]
            
        elif method == 'random_forest':
            # 基于随机森林特征重要性选择
            from sklearn.ensemble import RandomForestClassifier
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X, y)
            importances = rf.feature_importances_
            selected_indices = np.argsort(importances)[-n_features:]
            
        else:
            # 默认选择前两个特征
            selected_indices = np.arange(min(n_features, X.shape[1]))
        
        selected_names = [feature_names[i] for i in selected_indices]
        return selected_indices, selected_names
    
    def _create_mesh_grid(self, X, resolution=100):
        """
        创建网格用于决策边界绘制
        
        Args:
            X: 二维特征矩阵
            resolution: 网格分辨率
            
        Returns:
            xx, yy: 网格坐标
        """
        h = 0.02  # 网格步长
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                           np.arange(y_min, y_max, h))
        
        return xx, yy
    
    def plot_decision_boundary(self, model, X, y, feature_names, 
                             model_name="Model", title=None, 
                             feature_selection_method='variance',
                             dimensionality_reduction=None):
        """
        绘制决策边界图
        
        Args:
            model: 训练好的模型
            X: 特征矩阵
            y: 标签
            feature_names: 特征名称列表
            model_name: 模型名称
            title: 图表标题
            feature_selection_method: 特征选择方法
            dimensionality_reduction: 降维方法 ('pca', 'tsne', None)
        """
        try:
            # 确保X是numpy数组
            if hasattr(X, 'values'):
                X_array = X.values
            else:
                X_array = np.array(X)
            
            # 确保y是numpy数组
            if hasattr(y, 'values'):
                y_array = y.values
            else:
                y_array = np.array(y)
            
            # 处理高维数据
            if X_array.shape[1] > 2:
                if dimensionality_reduction == 'pca':
                    # 使用PCA降维
                    pca = PCA(n_components=2, random_state=42)
                    X_2d = pca.fit_transform(X_array)
                    feature_names_2d = [f'PC1 ({pca.explained_variance_ratio_[0]:.2f})', 
                                      f'PC2 ({pca.explained_variance_ratio_[1]:.2f})']
                    
                    # 训练2D模型
                    model_2d = self._clone_model(model)
                    model_2d.fit(X_2d, y_array)
                    
                elif dimensionality_reduction == 'tsne':
                    # 使用t-SNE降维
                    tsne = TSNE(n_components=2, random_state=42)
                    X_2d = tsne.fit_transform(X_array)
                    feature_names_2d = ['t-SNE 1', 't-SNE 2']
                    
                    # 训练2D模型
                    model_2d = self._clone_model(model)
                    model_2d.fit(X_2d, y_array)
                    
                else:
                    # 选择最佳特征
                    selected_indices, selected_names = self._select_best_features(
                        X_array, y_array, feature_names, 
                        n_features=2, method=feature_selection_method
                    )
                    
                    X_2d = X_array[:, selected_indices]
                    feature_names_2d = selected_names
                    
                    # 训练2D模型
                    model_2d = self._clone_model(model)
                    model_2d.fit(X_2d, y_array)
            else:
                X_2d = X_array
                feature_names_2d = feature_names[:2]
                model_2d = model
            
            # 创建图形
            plt.figure(figsize=self.fig_size)
            
            # 创建网格
            xx, yy = self._create_mesh_grid(X_2d)
            
            # 预测网格点
            mesh_points = np.c_[xx.ravel(), yy.ravel()]
            
            # 获取预测结果
            if hasattr(model_2d, 'predict_proba'):
                Z = model_2d.predict_proba(mesh_points)[:, 1]
            else:
                Z = model_2d.predict(mesh_points)
            
            Z = Z.reshape(xx.shape)
            
            # 绘制决策边界
            plt.contourf(xx, yy, Z, levels=50, alpha=0.8, cmap=self.cmap)
            plt.contour(xx, yy, Z, levels=[0.5], linewidths=2, colors='black')
            
            # 绘制数据点
            scatter = plt.scatter(X_2d[:, 0], X_2d[:, 1], c=y_array, 
                                cmap=self.cmap, s=60, edgecolors='black', 
                                linewidth=0.5, alpha=0.7)
            
            # 设置标签和标题
            plt.xlabel(feature_names_2d[0], fontsize=12)
            plt.ylabel(feature_names_2d[1], fontsize=12)
            
            if title:
                plt.title(title, fontsize=14, fontweight='bold')
            else:
                plt.title(f'{model_name} - Decision Boundary', fontsize=14, fontweight='bold')
            
            # 添加颜色条
            plt.colorbar(scatter, label='Class')
            
            # 添加网格
            plt.grid(True, alpha=0.3)
            
            # 保存图形
            filename = f"{model_name.lower().replace(' ', '_')}_decision_boundary.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()
            
            _LOG.info(f"决策边界图已保存: {filepath}")
            
            return filepath
            
        except Exception as e:
            _LOG.error(f"绘制决策边界图失败: {e}")
            plt.close()
            return None
    
    def _clone_model(self, model):
        """
        克隆模型以创建2D版本
        
        Args:
            model: 原始模型
            
        Returns:
            克隆的模型
        """
        from sklearn.base import clone
        try:
            return clone(model)
        except:
            # 如果克隆失败，创建相同类型的新模型
            model_type = type(model)
            
            if model_type == LogisticRegression:
                return LogisticRegression(random_state=42)
            elif model_type == SVC:
                return SVC(probability=True, random_state=42)
            else:
                # 尝试获取模型参数
                try:
                    params = model.get_params()
                    return model_type(**params)
                except:
                    return model_type()
    
    def create_comparison_plot(self, models_data, title="Decision Boundary Comparison"):
        """
        创建多个模型的决策边界对比图
        
        Args:
            models_data: 列表，每个元素包含 (model, X, y, feature_names, model_name)
            title: 图表标题
        """
        n_models = len(models_data)
        cols = 2
        rows = (n_models + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(12, 6*rows))
        if rows == 1:
            axes = [axes] if cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, (model, X, y, feature_names, model_name) in enumerate(models_data):
            ax = axes[i]
            
            # 处理数据
            if hasattr(X, 'values'):
                X_array = X.values
            else:
                X_array = np.array(X)
            
            if hasattr(y, 'values'):
                y_array = y.values
            else:
                y_array = np.array(y)
            
            # 选择特征
            if X_array.shape[1] > 2:
                selected_indices, selected_names = self._select_best_features(
                    X_array, y_array, feature_names, n_features=2
                )
                X_2d = X_array[:, selected_indices]
                feature_names_2d = selected_names
                
                # 训练2D模型
                model_2d = self._clone_model(model)
                model_2d.fit(X_2d, y_array)
            else:
                X_2d = X_array
                feature_names_2d = feature_names[:2]
                model_2d = model
            
            # 创建网格
            xx, yy = self._create_mesh_grid(X_2d)
            
            # 预测网格点
            mesh_points = np.c_[xx.ravel(), yy.ravel()]
            
            if hasattr(model_2d, 'predict_proba'):
                Z = model_2d.predict_proba(mesh_points)[:, 1]
            else:
                Z = model_2d.predict(mesh_points)
            
            Z = Z.reshape(xx.shape)
            
            # 绘制决策边界
            ax.contourf(xx, yy, Z, levels=50, alpha=0.8, cmap=self.cmap)
            ax.contour(xx, yy, Z, levels=[0.5], linewidths=2, colors='black')
            
            # 绘制数据点
            scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=y_array, 
                               cmap=self.cmap, s=60, edgecolors='black', 
                               linewidth=0.5, alpha=0.7)
            
            # 设置标签和标题
            ax.set_xlabel(feature_names_2d[0], fontsize=10)
            ax.set_ylabel(feature_names_2d[1], fontsize=10)
            ax.set_title(f'{model_name}', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        for j in range(i+1, len(axes)):
            axes[j].set_visible(False)
        
        plt.tight_layout()
        
        # 保存图形
        filename = "decision_boundary_comparison.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        
        _LOG.info(f"决策边界对比图已保存: {filepath}")
        
        return filepath


def create_decision_boundary_for_model(model, X, y, feature_names, model_name, 
                                     output_dir="outputs/plots/decision_boundaries"):
    """
    为单个模型创建决策边界图的便捷函数
    
    Args:
        model: 训练好的模型
        X: 特征矩阵
        y: 标签
        feature_names: 特征名称列表
        model_name: 模型名称
        output_dir: 输出目录
        
    Returns:
        保存的文件路径
    """
    visualizer = DecisionBoundaryVisualizer(output_dir)
    return visualizer.plot_decision_boundary(model, X, y, feature_names, model_name) 
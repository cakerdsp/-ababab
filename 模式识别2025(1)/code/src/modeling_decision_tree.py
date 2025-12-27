#!/usr/bin/env python3
"""
决策树模型实现
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

from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import optuna
import warnings
warnings.filterwarnings('ignore')

from base_model import BaseModel

_LOG = logging.getLogger(__name__)

class DecisionTreeModeler(BaseModel):
    """决策树模型训练器"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化决策树模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        super().__init__(target_column, config, **kwargs)
        
        # 决策树通常不需要特征标准化，但为了统一接口保留
        self.scaler = StandardScaler()
        self.use_scaling = self._get_config_value('modeling.decision_tree.use_scaling', False)
        
        # 获取模型特定配置
        self.auto_optimize = self._get_config_value('modeling.decision_tree.auto_optimize', True)
        self.n_trials = self._get_config_value('modeling.decision_tree.n_trials', 20)
        self.manual_params = self._get_config_value('modeling.decision_tree.manual_params', {
            'max_depth': 10,
            'min_samples_split': 10,
            'min_samples_leaf': 5,
            'max_features': 'sqrt',
            'criterion': 'gini',
            'random_state': 42
        })
        
    def train(self, X, y):
        """训练决策树模型"""
        _LOG.info("训练决策树模型...")
        
        # 记录训练开始时间
        start_time = time.time()
        
        # 可选的特征标准化
        if self.use_scaling:
            X_processed = self.scaler.fit_transform(X)
        else:
            X_processed = X
            # 仍然fit scaler以保持接口一致性
            self.scaler.fit(X)
        
        if self.auto_optimize:
            # 使用Optuna进行超参数优化
            _LOG.info(f"开始决策树超参数优化，共{self.n_trials}次尝试...")
            
            def objective(trial):
                # 定义超参数搜索空间
                max_depth = trial.suggest_int('max_depth', 3, 20)
                min_samples_split = trial.suggest_int('min_samples_split', 2, 50)
                min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 20)
                max_features = trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
                criterion = trial.suggest_categorical('criterion', ['gini', 'entropy'])
                
                # 训练模型
                model = DecisionTreeClassifier(
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    max_features=max_features,
                    criterion=criterion,
                    random_state=42
                )
                
                # 使用交叉验证评估
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(model, X_processed, y, cv=5, scoring='f1')
                return scores.mean()
            
            # 优化超参数
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=self.n_trials)
            
            # 保存优化历史
            self.optimization_study = study
            
            best_params = study.best_params
            best_params['random_state'] = 42
            self.best_params = best_params
            
            _LOG.info(f"最佳超参数: {best_params}")
            _LOG.info(f"最佳F1分数: {study.best_value:.4f}")
            
            # 使用最佳参数训练最终模型
            _LOG.info(f"使用最佳参数训练决策树: {best_params}")
            self.model = DecisionTreeClassifier(**best_params)
        else:
            # 使用手动参数
            _LOG.info(f"使用手动参数训练决策树: {self.manual_params}")
            self.model = DecisionTreeClassifier(**self.manual_params)
        
        # 训练模型
        self.model.fit(X_processed, y)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        
        self.is_trained = True
        _LOG.info(f"决策树模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存优化历史
        if self.auto_optimize:
            self.save_optimization_history()
        
        return self.model
    
    def predict(self, X):
        """预测类别"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        if self.use_scaling:
            X_processed = self.scaler.transform(X)
        else:
            X_processed = X
            
        return self.model.predict(X_processed)
    
    def predict_proba(self, X):
        """预测概率"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        if self.use_scaling:
            X_processed = self.scaler.transform(X)
        else:
            X_processed = X
            
        return self.model.predict_proba(X_processed)
    
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
        
        _LOG.info(f"决策树模型评估完成 - F1分数: {metrics['f1_score']:.4f}")
        
        # 生成可视化
        self._plot_confusion_matrix(y_test, y_pred)
        self._plot_roc_curve(y_test, y_proba)
        self._plot_feature_importance()
        self._plot_tree_structure()
        self._plot_tree_analysis()
        
        # SHAP分析
        if self.enable_shap:
            self._perform_shap_analysis(X_test, y_test)
        
        return metrics
    
    def _plot_feature_importance(self):
        """绘制特征重要性"""
        try:
            if not hasattr(self.model, 'feature_importances_'):
                _LOG.warning("模型不支持特征重要性")
                return
            
            # 获取特征重要性
            importances = self.model.feature_importances_
            feature_names = self.feature_names if self.feature_names else [f'Feature_{i}' for i in range(len(importances))]
            
            # 创建DataFrame并排序
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False).head(20)
            
            plt.figure(figsize=(10, 8))
            sns.barplot(data=importance_df, x='importance', y='feature')
            plt.title('Decision Tree - Feature Importance')
            plt.xlabel('Importance')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_feature_importance.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"特征重要性图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制特征重要性失败: {e}")
    
    def _plot_tree_structure(self):
        """绘制决策树结构"""
        try:
            # 限制树的深度以便可视化
            max_depth_for_plot = min(4, self.model.max_depth or 10)
            
            plt.figure(figsize=(20, 12))
            
            # 绘制决策树
            plot_tree(self.model, 
                     max_depth=max_depth_for_plot,
                     feature_names=self.feature_names[:20] if self.feature_names else None,
                     class_names=['Not At Risk', 'At Risk'],
                     filled=True,
                     rounded=True,
                     fontsize=8)
            
            plt.title(f'Decision Tree Structure (Max Depth: {max_depth_for_plot})')
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_tree_structure.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"决策树结构图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制决策树结构失败: {e}")
    
    def _plot_tree_analysis(self):
        """绘制决策树分析图"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 树的统计信息
            tree_stats = f"Tree Statistics\n"
            tree_stats += f"Max Depth: {self.model.max_depth}\n"
            tree_stats += f"Tree Depth: {self.model.tree_.max_depth}\n"
            tree_stats += f"Number of Nodes: {self.model.tree_.node_count}\n"
            tree_stats += f"Number of Leaves: {self.model.tree_.n_leaves}\n"
            tree_stats += f"Min Samples Split: {self.model.min_samples_split}\n"
            tree_stats += f"Min Samples Leaf: {self.model.min_samples_leaf}"
            
            axes[0, 0].text(0.1, 0.5, tree_stats, fontsize=12,
                           verticalalignment='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Tree Statistics')
            axes[0, 0].axis('off')
            
            # 2. 节点深度分布
            if hasattr(self.model.tree_, 'children_left'):
                # 计算每个节点的深度
                def get_node_depths(tree, node_id=0, depth=0):
                    depths = {}
                    depths[node_id] = depth
                    
                    if tree.children_left[node_id] != -1:  # 不是叶节点
                        depths.update(get_node_depths(tree, tree.children_left[node_id], depth + 1))
                        depths.update(get_node_depths(tree, tree.children_right[node_id], depth + 1))
                    
                    return depths
                
                node_depths = get_node_depths(self.model.tree_)
                depth_counts = pd.Series(list(node_depths.values())).value_counts().sort_index()
                
                axes[0, 1].bar(depth_counts.index, depth_counts.values)
                axes[0, 1].set_title('Node Distribution by Depth')
                axes[0, 1].set_xlabel('Depth')
                axes[0, 1].set_ylabel('Number of Nodes')
            
            # 3. 特征使用频率
            if hasattr(self.model.tree_, 'feature'):
                feature_usage = pd.Series(self.model.tree_.feature).value_counts()
                # 过滤掉-2（叶节点）
                feature_usage = feature_usage[feature_usage.index != -2]
                
                if len(feature_usage) > 0:
                    top_features = feature_usage.head(10)
                    feature_names_used = [self.feature_names[i] if self.feature_names and i < len(self.feature_names) 
                                        else f'Feature_{i}' for i in top_features.index]
                    
                    axes[1, 0].barh(range(len(top_features)), top_features.values)
                    axes[1, 0].set_yticks(range(len(top_features)))
                    axes[1, 0].set_yticklabels(feature_names_used)
                    axes[1, 0].set_title('Feature Usage in Tree')
                    axes[1, 0].set_xlabel('Usage Count')
            
            # 4. 叶节点样本分布
            if hasattr(self.model.tree_, 'n_node_samples'):
                leaf_samples = []
                for i in range(self.model.tree_.node_count):
                    if self.model.tree_.children_left[i] == -1:  # 叶节点
                        leaf_samples.append(self.model.tree_.n_node_samples[i])
                
                if leaf_samples:
                    axes[1, 1].hist(leaf_samples, bins=20, alpha=0.7)
                    axes[1, 1].set_title('Leaf Node Sample Distribution')
                    axes[1, 1].set_xlabel('Number of Samples')
                    axes[1, 1].set_ylabel('Frequency')
            
            plt.tight_layout()
            
            filename = f'{self.__class__.__name__.lower()}_tree_analysis.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"决策树分析图已保存: {filename}")
            
        except Exception as e:
            _LOG.warning(f"绘制决策树分析图失败: {e}")
    
    def get_tree_rules(self, max_rules=10):
        """获取决策树规则"""
        try:
            if not self.is_trained:
                return "模型尚未训练"
            
            # 导出文本格式的决策树
            tree_rules = export_text(self.model, 
                                   feature_names=self.feature_names,
                                   max_depth=5)  # 限制深度以便阅读
            
            return tree_rules
            
        except Exception as e:
            _LOG.warning(f"获取决策树规则失败: {e}")
            return "获取规则失败"
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器"""
        try:
            import shap
            
            # 对于决策树，使用TreeExplainer
            explainer = shap.TreeExplainer(self.model)
            return explainer
            
        except Exception as e:
            _LOG.warning(f"创建SHAP解释器失败: {e}")
            return None 
#!/usr/bin/env python3
"""
基础模型类
提供统一的配置管理、图片保存和SHAP分析功能
"""

import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from abc import ABC, abstractmethod
import time
import psutil
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report, roc_curve
import warnings
warnings.filterwarnings('ignore')

# 设置matplotlib后端
import matplotlib
matplotlib.use('Agg')

_LOG = logging.getLogger(__name__)

class BaseModel(ABC):
    """所有模型的基础类"""
    
    def __init__(self, target_column='at_risk', config=None, **kwargs):
        """
        初始化基础模型
        
        Args:
            target_column: 目标变量列名
            config: 配置字典
            **kwargs: 其他参数
        """
        self.target_column = target_column
        self.config = config or {}
        self.model = None
        self.is_trained = False
        self.feature_names = None
        
        # 性能指标
        self.training_time = 0
        self.prediction_time = 0
        self.model_size = 0
        self.hyperparameter_tuning_history = []
        self.best_params = None
        self.optimization_study = None
        
        # 从配置中获取路径设置
        self.plot_dir = Path(self._get_config_value('output.plot_dir', 'outputs/plots/modeling'))
        self.shap_dir = Path(self._get_config_value('output.shap_plot_dir', 'outputs/plots/shap'))
        self.model_dir = Path(self._get_config_value('output.model_dir', 'models'))
        self.dataframes_dir = Path(self._get_config_value('output.dataframes_dir', 'outputs/dataframes'))
        
        # 创建目录
        self.plot_dir.mkdir(parents=True, exist_ok=True)
        self.shap_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.dataframes_dir.mkdir(parents=True, exist_ok=True)
        
        # 图片设置
        self.plot_dpi = self._get_config_value('output.plot_dpi', 300)
        self.plot_format = self._get_config_value('output.plot_format', 'png')
        
        # SHAP设置
        self.enable_shap = self._get_config_value('shap.enable_shap', True)
        self.shap_sample_size = self._get_config_value('shap.shap_sample_size', 100)
        
        _LOG.info(f"初始化 {self.__class__.__name__}")
        _LOG.info(f"图片保存目录: {self.plot_dir}")
        _LOG.info(f"SHAP分析目录: {self.shap_dir}")
    
    def _get_config_value(self, path, default=None):
        """从配置中获取值，支持点分隔路径"""
        if not self.config:
            return default
        
        keys = path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    @abstractmethod
    def train(self, X, y):
        """训练模型 - 子类必须实现"""
        pass
    
    @abstractmethod
    def predict(self, X):
        """预测 - 子类必须实现"""
        pass
    
    @abstractmethod
    def predict_proba(self, X):
        """预测概率 - 子类必须实现"""
        pass
    
    def evaluate(self, X_test, y_test, feature_names=None):
        """评估模型性能"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        self.feature_names = feature_names
        
        # 基础预测
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
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
        
        _LOG.info(f"模型评估完成 - F1: {metrics['f1_score']:.4f}, AUC: {metrics.get('roc_auc', 'N/A')}")
        
        # 生成可视化
        self._plot_confusion_matrix(y_test, y_pred)
        self._plot_roc_curve(y_test, y_proba)
        self._plot_feature_importance()
        
        # SHAP分析
        if self.enable_shap:
            self._perform_shap_analysis(X_test, y_test)
        
        return metrics
    
    def _plot_confusion_matrix(self, y_true, y_pred):
        """绘制混淆矩阵"""
        try:
            plt.figure(figsize=(8, 6))
            cm = confusion_matrix(y_true, y_pred)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title(f'{self.__class__.__name__} - Confusion Matrix')
            plt.xlabel('Predicted Label')
            plt.ylabel('True Label')
            
            filename = f'{self.__class__.__name__.lower()}_confusion_matrix.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"混淆矩阵已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制混淆矩阵失败: {e}")
    
    def _plot_roc_curve(self, y_true, y_proba):
        """绘制ROC曲线"""
        try:
            if len(np.unique(y_true)) != 2:
                return  # 仅支持二分类
            
            plt.figure(figsize=(8, 6))
            
            if y_proba.ndim > 1 and y_proba.shape[1] > 1:
                fpr, tpr, _ = roc_curve(y_true, y_proba[:, 1])
            else:
                fpr, tpr, _ = roc_curve(y_true, y_proba)
            
            auc_score = roc_auc_score(y_true, y_proba[:, 1] if y_proba.ndim > 1 else y_proba)
            
            plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc_score:.3f})')
            plt.plot([0, 1], [0, 1], 'k--', linewidth=1)
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title(f'{self.__class__.__name__} - ROC Curve')
            plt.legend(loc="lower right")
            
            filename = f'{self.__class__.__name__.lower()}_roc_curve.{self.plot_format}'
            plt.savefig(self.plot_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
            plt.close()
            _LOG.info(f"ROC曲线已保存: {filename}")
        except Exception as e:
            _LOG.warning(f"绘制ROC曲线失败: {e}")
    
    @abstractmethod
    def _plot_feature_importance(self):
        """绘制特征重要性 - 子类实现"""
        pass
    
    def _perform_shap_analysis(self, X_test, y_test):
        """执行SHAP分析"""
        try:
            import shap
            
            # 限制样本数量以提高计算效率
            sample_size = min(self.shap_sample_size, len(X_test))
            X_sample = X_test.iloc[:sample_size] if hasattr(X_test, 'iloc') else X_test[:sample_size]
            
            _LOG.info(f"开始SHAP分析，样本数: {sample_size}")
            
            # 根据模型类型选择explainer
            explainer = self._get_shap_explainer(X_sample)
            shap_values = explainer.shap_values(X_sample)
            
            # 如果是多分类，选择正类
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # 选择正类
            
            # SHAP摘要图
            if self._get_config_value('shap.save_summary_plot', True):
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, feature_names=self.feature_names, show=False)
                filename = f'{self.__class__.__name__.lower()}_shap_summary.{self.plot_format}'
                plt.savefig(self.shap_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
                _LOG.info(f"SHAP摘要图已保存: {filename}")
            
            # SHAP重要性图
            if self._get_config_value('shap.save_importance_plot', True):
                plt.figure(figsize=(10, 6))
                shap.summary_plot(shap_values, X_sample, feature_names=self.feature_names, plot_type="bar", show=False)
                filename = f'{self.__class__.__name__.lower()}_shap_importance.{self.plot_format}'
                plt.savefig(self.shap_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                plt.close()
                _LOG.info(f"SHAP重要性图已保存: {filename}")
            
            # SHAP依赖图
            if self._get_config_value('shap.save_dependence_plots', True):
                self._plot_shap_dependence(shap_values, X_sample)
            
            # SHAP瀑布图
            if self._get_config_value('shap.save_waterfall_plots', True):
                self._plot_shap_waterfall(explainer, X_sample)
            
        except ImportError:
            _LOG.warning("SHAP库未安装，跳过SHAP分析")
        except Exception as e:
            _LOG.warning(f"SHAP分析失败: {e}")
    
    def _get_shap_explainer(self, X_sample):
        """获取SHAP解释器 - 子类可重写"""
        import shap
        return shap.Explainer(self.model, X_sample)
    
    def _plot_shap_dependence(self, shap_values, X_sample):
        """绘制SHAP依赖图"""
        try:
            import shap
            
            # 获取特征重要性排序
            importance = np.abs(shap_values).mean(0)
            top_features = np.argsort(importance)[-self._get_config_value('shap.max_dependence_features', 10):]
            
            for i, feature_idx in enumerate(top_features):
                try:
                    plt.figure(figsize=(8, 6))
                    feature_name = self.feature_names[feature_idx] if self.feature_names else f'Feature_{feature_idx}'
                    
                    # 使用简单的scatter plot代替complex dependence plot
                    feature_values = X_sample.iloc[:, feature_idx] if hasattr(X_sample, 'iloc') else X_sample[:, feature_idx]
                    plt.scatter(feature_values, shap_values[:, feature_idx], alpha=0.6)
                    plt.xlabel(f'{feature_name}')
                    plt.ylabel(f'SHAP value for {feature_name}')
                    plt.title(f'SHAP Dependence Plot: {feature_name}')
                    plt.grid(True, alpha=0.3)
                    
                    filename = f'{self.__class__.__name__.lower()}_shap_dependence_{feature_name}.{self.plot_format}'
                    plt.savefig(self.shap_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                    plt.close()
                except Exception as e:
                    _LOG.warning(f"绘制特征 {feature_name} 的SHAP依赖图失败: {e}")
                    continue
            
            _LOG.info(f"SHAP依赖图已保存 ({len(top_features)}个)")
        except Exception as e:
            _LOG.warning(f"绘制SHAP依赖图失败: {e}")
    
    def _plot_shap_waterfall(self, explainer, X_sample):
        """绘制SHAP瀑布图"""
        try:
            import shap
            
            n_samples = min(self._get_config_value('shap.waterfall_samples', 3), len(X_sample))
            
            for i in range(n_samples):
                try:
                    plt.figure(figsize=(10, 8))
                    
                    # 获取单个样本
                    sample = X_sample.iloc[[i]] if hasattr(X_sample, 'iloc') else X_sample[[i]]
                    
                    # 重新计算SHAP值以获得正确的Explanation对象
                    explanation = explainer(sample)
                    
                    # 如果是多分类，选择正类
                    if hasattr(explanation, 'values') and len(explanation.values.shape) > 2:
                        explanation.values = explanation.values[:, :, 1]  # 选择正类
                    
                    # 绘制瀑布图
                    shap.plots.waterfall(explanation[0], show=False)
                    
                    filename = f'{self.__class__.__name__.lower()}_shap_waterfall_sample_{i}.{self.plot_format}'
                    plt.savefig(self.shap_dir / filename, dpi=self.plot_dpi, bbox_inches='tight')
                    plt.close()
                except Exception as e:
                    _LOG.warning(f"绘制样本 {i} 的SHAP瀑布图失败: {e}")
                    continue
            
            _LOG.info(f"SHAP瀑布图已保存 ({n_samples}个)")
        except Exception as e:
            _LOG.warning(f"绘制SHAP瀑布图失败: {e}")
    
    def measure_prediction_time(self, X):
        """测量预测时间"""
        start_time = time.time()
        predictions = self.predict(X)
        self.prediction_time = time.time() - start_time
        return predictions
    
    def calculate_model_size(self):
        """计算模型大小"""
        try:
            # 临时保存模型到内存中计算大小
            import io
            import pickle
            buffer = io.BytesIO()
            pickle.dump(self.model, buffer)
            self.model_size = buffer.tell() / 1024 / 1024  # MB
            buffer.close()
        except Exception as e:
            _LOG.warning(f"计算模型大小失败: {e}")
            self.model_size = 0
    
    def save_optimization_history(self):
        """保存超参数优化历史"""
        if not self.optimization_study:
            return
        
        try:
            # 保存优化历史数据
            trials_df = self.optimization_study.trials_dataframe()
            history_path = self.dataframes_dir / f"{self.__class__.__name__.lower()}_hyperparameter_tuning.csv"
            trials_df.to_csv(history_path, index=False)
            _LOG.info(f"超参数优化历史已保存: {history_path}")
            
            # 绘制优化历史图
            self._plot_optimization_history()
            self._plot_parameter_importance()
            
        except Exception as e:
            _LOG.warning(f"保存优化历史失败: {e}")
    
    def _plot_optimization_history(self):
        """使用Optuna原生可视化绘制优化历史图"""
        try:
            import optuna.visualization as vis
            import plotly.io as pio
            
            if not self.optimization_study:
                return
            
            model_name = self.__class__.__name__.lower()
            
            # 1. 优化历史图
            try:
                fig_history = vis.plot_optimization_history(self.optimization_study)
                fig_history.update_layout(
                    title=f'{self.__class__.__name__} - Optimization History',
                    width=800, height=600
                )
                history_path = self.plot_dir / f"{model_name}_optuna_history.png"
                pio.write_image(fig_history, history_path)
                _LOG.info(f"优化历史图已保存: {history_path}")
            except Exception as e:
                _LOG.warning(f"绘制优化历史图失败: {e}")
            
            # 2. 中间值图（如果有的话）
            try:
                # 检查是否有中间值
                has_intermediate = any(len(trial.intermediate_values) > 0 for trial in self.optimization_study.trials)
                if has_intermediate:
                    fig_intermediate = vis.plot_intermediate_values(self.optimization_study)
                    fig_intermediate.update_layout(
                        title=f'{self.__class__.__name__} - Intermediate Values',
                        width=800, height=600
                    )
                    intermediate_path = self.plot_dir / f"{model_name}_optuna_intermediate.png"
                    pio.write_image(fig_intermediate, intermediate_path)
                    _LOG.info(f"中间值图已保存: {intermediate_path}")
            except Exception as e:
                _LOG.warning(f"绘制中间值图失败: {e}")
            
            # 3. 并行坐标图
            try:
                if len(self.optimization_study.trials) > 1:
                    fig_parallel = vis.plot_parallel_coordinate(self.optimization_study)
                    fig_parallel.update_layout(
                        title=f'{self.__class__.__name__} - Parallel Coordinate Plot',
                        width=1000, height=600
                    )
                    parallel_path = self.plot_dir / f"{model_name}_optuna_parallel_coordinate.png"
                    pio.write_image(fig_parallel, parallel_path)
                    _LOG.info(f"并行坐标图已保存: {parallel_path}")
            except Exception as e:
                _LOG.warning(f"绘制并行坐标图失败: {e}")
            
            # 4. 切片图（单个参数的影响）
            try:
                if len(self.optimization_study.trials) > 5:
                    fig_slice = vis.plot_slice(self.optimization_study)
                    fig_slice.update_layout(
                        title=f'{self.__class__.__name__} - Parameter Slice Plot',
                        width=1200, height=800
                    )
                    slice_path = self.plot_dir / f"{model_name}_optuna_slice.png"
                    pio.write_image(fig_slice, slice_path)
                    _LOG.info(f"参数切片图已保存: {slice_path}")
            except Exception as e:
                _LOG.warning(f"绘制参数切片图失败: {e}")
            
            # 5. 等高线图（参数对的影响）
            try:
                if len(self.optimization_study.trials) > 10:
                    # 获取参数名
                    param_names = list(self.optimization_study.trials[0].params.keys())
                    if len(param_names) >= 2:
                        # 绘制前两个参数的等高线图
                        fig_contour = vis.plot_contour(self.optimization_study, 
                                                     params=[param_names[0], param_names[1]])
                        fig_contour.update_layout(
                            title=f'{self.__class__.__name__} - Parameter Contour Plot',
                            width=800, height=600
                        )
                        contour_path = self.plot_dir / f"{model_name}_optuna_contour.png"
                        pio.write_image(fig_contour, contour_path)
                        _LOG.info(f"参数等高线图已保存: {contour_path}")
            except Exception as e:
                _LOG.warning(f"绘制参数等高线图失败: {e}")
            
            # 6. EDF图（经验分布函数）
            try:
                if len(self.optimization_study.trials) > 5:
                    fig_edf = vis.plot_edf(self.optimization_study)
                    fig_edf.update_layout(
                        title=f'{self.__class__.__name__} - Empirical Distribution Function',
                        width=800, height=600
                    )
                    edf_path = self.plot_dir / f"{model_name}_optuna_edf.png"
                    pio.write_image(fig_edf, edf_path)
                    _LOG.info(f"经验分布函数图已保存: {edf_path}")
            except Exception as e:
                _LOG.warning(f"绘制EDF图失败: {e}")
                
        except ImportError:
            _LOG.warning("plotly未安装，无法生成Optuna可视化图表")
        except Exception as e:
            _LOG.warning(f"绘制Optuna可视化图表失败: {e}")
    
    def _plot_parameter_importance(self):
        """使用Optuna原生可视化绘制参数重要性图"""
        try:
            import optuna.visualization as vis
            import plotly.io as pio
            
            if not self.optimization_study:
                return
            
            model_name = self.__class__.__name__.lower()
            
            # 1. 参数重要性图
            try:
                fig_importance = vis.plot_param_importances(self.optimization_study)
                fig_importance.update_layout(
                    title=f'{self.__class__.__name__} - Parameter Importance',
                    width=800, height=600
                )
                importance_path = self.plot_dir / f"{model_name}_optuna_param_importance.png"
                pio.write_image(fig_importance, importance_path)
                _LOG.info(f"参数重要性图已保存: {importance_path}")
            except Exception as e:
                _LOG.warning(f"绘制参数重要性图失败: {e}")
            
            # 2. 超体积图（如果是多目标优化）
            try:
                # 检查是否是多目标优化
                if hasattr(self.optimization_study, 'directions') and len(self.optimization_study.directions) > 1:
                    fig_hypervolume = vis.plot_hypervolume_history(self.optimization_study)
                    fig_hypervolume.update_layout(
                        title=f'{self.__class__.__name__} - Hypervolume History',
                        width=800, height=600
                    )
                    hypervolume_path = self.plot_dir / f"{model_name}_optuna_hypervolume.png"
                    pio.write_image(fig_hypervolume, hypervolume_path)
                    _LOG.info(f"超体积历史图已保存: {hypervolume_path}")
            except Exception as e:
                _LOG.warning(f"绘制超体积图失败: {e}")
            
            # 3. Pareto前沿图（多目标优化）
            try:
                if hasattr(self.optimization_study, 'directions') and len(self.optimization_study.directions) > 1:
                    fig_pareto = vis.plot_pareto_front(self.optimization_study)
                    fig_pareto.update_layout(
                        title=f'{self.__class__.__name__} - Pareto Front',
                        width=800, height=600
                    )
                    pareto_path = self.plot_dir / f"{model_name}_optuna_pareto_front.png"
                    pio.write_image(fig_pareto, pareto_path)
                    _LOG.info(f"Pareto前沿图已保存: {pareto_path}")
            except Exception as e:
                _LOG.warning(f"绘制Pareto前沿图失败: {e}")
                
        except ImportError:
            _LOG.warning("plotly未安装，无法生成参数重要性图表")
        except Exception as e:
            _LOG.warning(f"绘制参数重要性图表失败: {e}")
    
    def get_performance_metrics(self):
        """获取性能指标"""
        return {
            'training_time_seconds': self.training_time,
            'prediction_time_seconds': self.prediction_time,
            'model_size_mb': self.model_size,
            'best_parameters': self.best_params,
            'optimization_trials': len(self.hyperparameter_tuning_history) if self.hyperparameter_tuning_history else 0
        }
    
    def save_model(self, filename=None):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        if filename is None:
            filename = f'{self.__class__.__name__.lower()}.joblib'
        
        # 计算模型大小
        self.calculate_model_size()
        
        # 保存模型和相关信息
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'target_column': self.target_column,
            'is_trained': self.is_trained,
            'performance_metrics': self.get_performance_metrics()
        }
        
        model_path = self.model_dir / filename
        joblib.dump(model_data, model_path)
        _LOG.info(f"模型已保存: {model_path}")
        return model_path
    
    def load_model(self, filename):
        """加载模型"""
        model_path = self.model_dir / filename
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.feature_names = model_data.get('feature_names')
        self.target_column = model_data.get('target_column', self.target_column)
        self.is_trained = model_data.get('is_trained', True)
        
        _LOG.info(f"模型已加载: {model_path}") 
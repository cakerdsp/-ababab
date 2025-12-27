#!/usr/bin/env python3
"""
综合模型对比分析
从准确性、效率、可解释性等多个维度对比不同算法的表现
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

_LOG = logging.getLogger(__name__)

class ComprehensiveModelAnalysis:
    """综合模型分析器"""
    
    def __init__(self, output_dir="outputs"):
        self.output_dir = Path(output_dir)
        self.metrics_dir = self.output_dir / "dataframes"
        self.plots_dir = self.output_dir / "plots" / "analysis"
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型分类
        self.supervised_models = ['svm', 'decision_tree', 'logistic_regression', 'random_forest', 'neural_network']
        self.unsupervised_models = ['kmeans', 'em']
        
    def load_model_metrics(self):
        """加载所有模型的指标数据"""
        all_metrics = []
        
        for csv_file in self.output_dir.glob("model_metrics_*.csv"):
            try:
                df = pd.read_csv(csv_file)
                model_name = csv_file.stem.replace("model_metrics_", "")
                df['model_name_clean'] = model_name
                all_metrics.append(df)
                _LOG.info(f"加载模型指标: {model_name}")
            except Exception as e:
                _LOG.warning(f"加载指标文件失败 {csv_file}: {e}")
        
        if not all_metrics:
            raise ValueError("未找到任何模型指标文件")
        
        return pd.concat(all_metrics, ignore_index=True)
    
    def analyze_accuracy_performance(self, metrics_df):
        """分析准确性性能"""
        supervised_df = metrics_df[metrics_df['model_name_clean'].isin(self.supervised_models)]
        
        if supervised_df.empty:
            return
        
        # 准确性指标对比
        accuracy_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
        available_metrics = [m for m in accuracy_metrics if m in supervised_df.columns]
        
        if not available_metrics:
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        for i, metric in enumerate(available_metrics):
            if i < len(axes):
                ax = axes[i]
                supervised_df.plot(x='model_name_clean', y=metric, kind='bar', ax=ax, 
                                 color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(supervised_df)])
                ax.set_title(f'{metric.replace("_", " ").title()}')
                ax.set_xlabel('Model')
                ax.set_ylabel('Score')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        for i in range(len(available_metrics), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.plots_dir / "accuracy_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        _LOG.info("准确性对比图已保存")
    
    def analyze_efficiency_performance(self, metrics_df):
        """分析效率性能"""
        efficiency_metrics = ['training_time_seconds', 'prediction_time_seconds', 'model_size_mb']
        available_metrics = [m for m in efficiency_metrics if m in metrics_df.columns]
        
        if not available_metrics:
            return
        
        fig, axes = plt.subplots(1, len(available_metrics), figsize=(6*len(available_metrics), 6))
        if len(available_metrics) == 1:
            axes = [axes]
        
        for i, metric in enumerate(available_metrics):
            ax = axes[i]
            
            # 过滤有效数据
            valid_data = metrics_df[metrics_df[metric].notna() & (metrics_df[metric] > 0)]
            
            if not valid_data.empty:
                bars = ax.bar(valid_data['model_name_clean'], valid_data[metric], 
                            color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'][:len(valid_data)])
                
                # 在柱子上显示具体数值
                for j, (bar, value) in enumerate(zip(bars, valid_data[metric])):
                    height = bar.get_height()
                    if metric == 'training_time_seconds':
                        text = f'{value:.2f}s'
                    elif metric == 'prediction_time_seconds':
                        text = f'{value:.4f}s'
                    elif metric == 'model_size_mb':
                        text = f'{value:.2f}MB'
                    else:
                        text = f'{value:.2f}'
                    
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           text, ha='center', va='bottom', fontsize=9)
                
                ax.set_title(f'{metric.replace("_", " ").title()}')
                ax.set_xlabel('Model')
                ax.set_ylabel('Value')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.plots_dir / "efficiency_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        _LOG.info("效率对比图已保存")
    
    def analyze_hyperparameter_complexity(self):
        """分析超参数调优复杂度"""
        tuning_files = list(self.metrics_dir.glob("*_hyperparameter_tuning.csv"))
        
        if not tuning_files:
            _LOG.warning("未找到超参数调优历史文件")
            return
        
        complexity_data = []
        
        for file_path in tuning_files:
            try:
                df = pd.read_csv(file_path)
                model_name = file_path.stem.replace("_hyperparameter_tuning", "")
                
                # 分析优化复杂度
                n_trials = len(df)
                n_params = len([col for col in df.columns if col.startswith('params_')])
                
                # 计算收敛性指标
                if 'value' in df.columns:
                    values = df['value'].dropna()
                    if len(values) > 1:
                        # 计算相对改进
                        best_value = values.max() if df['state'].iloc[0] == 'COMPLETE' else values.min()
                        improvement_ratio = (best_value - values.iloc[0]) / abs(values.iloc[0]) if values.iloc[0] != 0 else 0
                        
                        # 计算稳定性（后50%试验的标准差）
                        stability = values.iloc[len(values)//2:].std() if len(values) > 10 else 0
                    else:
                        improvement_ratio = 0
                        stability = 0
                else:
                    improvement_ratio = 0
                    stability = 0
                
                complexity_data.append({
                    'model': model_name,
                    'n_trials': n_trials,
                    'n_parameters': n_params,
                    'improvement_ratio': improvement_ratio,
                    'stability': stability
                })
                
            except Exception as e:
                _LOG.warning(f"分析文件失败 {file_path}: {e}")
        
        if not complexity_data:
            return
        
        complexity_df = pd.DataFrame(complexity_data)
        
        # 绘制复杂度分析图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 试验次数
        axes[0, 0].bar(complexity_df['model'], complexity_df['n_trials'])
        axes[0, 0].set_title('Number of Trials')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 参数数量
        axes[0, 1].bar(complexity_df['model'], complexity_df['n_parameters'])
        axes[0, 1].set_title('Number of Parameters')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 改进比例
        axes[1, 0].bar(complexity_df['model'], complexity_df['improvement_ratio'])
        axes[1, 0].set_title('Improvement Ratio')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 稳定性
        axes[1, 1].bar(complexity_df['model'], complexity_df['stability'])
        axes[1, 1].set_title('Optimization Stability (Lower is Better)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.plots_dir / "hyperparameter_complexity.png", dpi=300, bbox_inches='tight')
        plt.close()
        _LOG.info("超参数复杂度分析图已保存")
        
        return complexity_df
    
    def create_comprehensive_ranking(self, metrics_df, complexity_df=None):
        """创建综合排名"""
        supervised_df = metrics_df[metrics_df['model_name_clean'].isin(self.supervised_models)]
        
        if supervised_df.empty:
            return
        
        # 准备排名数据
        ranking_data = []
        
        for _, row in supervised_df.iterrows():
            model_name = row['model_name_clean']
            
            # 准确性得分 (归一化到0-1)
            accuracy_score = 0
            accuracy_metrics = ['accuracy', 'f1_score', 'roc_auc']
            valid_metrics = [m for m in accuracy_metrics if m in row and pd.notna(row[m])]
            if valid_metrics:
                accuracy_score = np.mean([row[m] for m in valid_metrics])
            
            # 效率得分 (时间越少越好，归一化)
            efficiency_score = 0
            if pd.notna(row.get('training_time_seconds', 0)) and row.get('training_time_seconds', 0) > 0:
                max_time = supervised_df['training_time_seconds'].max()
                efficiency_score = 1 - (row['training_time_seconds'] / max_time)
            
            # 复杂度得分 (参数越少，改进比例越高越好)
            complexity_score = 0.5  # 默认中等
            if complexity_df is not None:
                model_complexity = complexity_df[complexity_df['model'] == model_name]
                if not model_complexity.empty:
                    # 归一化参数数量 (越少越好)
                    max_params = complexity_df['n_parameters'].max()
                    param_score = 1 - (model_complexity['n_parameters'].iloc[0] / max_params) if max_params > 0 else 0.5
                    
                    # 改进比例得分
                    improvement_score = min(1, abs(model_complexity['improvement_ratio'].iloc[0])) if pd.notna(model_complexity['improvement_ratio'].iloc[0]) else 0.5
                    
                    complexity_score = (param_score + improvement_score) / 2
            
            # 可解释性得分 (基于模型类型)
            interpretability_scores = {
                'decision_tree': 1.0,
                'logistic_regression': 0.8,
                'svm': 0.6,
                'random_forest': 0.5,
                'neural_network': 0.3
            }
            interpretability_score = interpretability_scores.get(model_name, 0.5)
            
            # 综合得分 (加权平均)
            weights = {
                'accuracy': 0.4,
                'efficiency': 0.2,
                'complexity': 0.2,
                'interpretability': 0.2
            }
            
            overall_score = (
                accuracy_score * weights['accuracy'] +
                efficiency_score * weights['efficiency'] +
                complexity_score * weights['complexity'] +
                interpretability_score * weights['interpretability']
            )
            
            ranking_data.append({
                'Model': model_name,
                'Accuracy': accuracy_score,
                'Efficiency': efficiency_score,
                'Complexity': complexity_score,
                'Interpretability': interpretability_score,
                'Overall': overall_score
            })
        
        ranking_df = pd.DataFrame(ranking_data)
        ranking_df = ranking_df.sort_values('Overall', ascending=False)
        
        # 保存排名表
        ranking_path = self.metrics_dir / "comprehensive_model_ranking.csv"
        ranking_df.to_csv(ranking_path, index=False)
        _LOG.info(f"综合排名已保存: {ranking_path}")
        
        # 绘制雷达图
        self._plot_radar_chart(ranking_df)
        
        return ranking_df
    
    def _plot_radar_chart(self, ranking_df):
        """绘制雷达图"""
        import numpy as np
        
        # 设置雷达图
        categories = ['Accuracy', 'Efficiency', 'Complexity', 'Interpretability']
        n_cats = len(categories)
        
        angles = [n / float(n_cats) * 2 * np.pi for n in range(n_cats)]
        angles += angles[:1]  # 闭合
        
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, (_, row) in enumerate(ranking_df.iterrows()):
            if i >= len(colors):
                break
                
            values = [row[cat] for cat in categories]
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, label=row['Model'], color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('Model Performance Radar Chart', size=16, y=1.1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.plots_dir / "performance_radar_chart.png", dpi=300, bbox_inches='tight')
        plt.close()
        _LOG.info("性能雷达图已保存")
    
    def generate_analysis_report(self, metrics_df, ranking_df):
        """生成分析报告"""
        report_lines = []
        report_lines.append("# 综合模型对比分析报告")
        report_lines.append("")
        
        # 模型概览
        report_lines.append("## 模型概览")
        report_lines.append(f"- 监督学习模型: {len(metrics_df[metrics_df['model_name_clean'].isin(self.supervised_models)])} 个")
        report_lines.append(f"- 无监督学习模型: {len(metrics_df[metrics_df['model_name_clean'].isin(self.unsupervised_models)])} 个")
        report_lines.append("")
        
        # 最佳模型
        if not ranking_df.empty:
            best_model = ranking_df.iloc[0]
            report_lines.append("## 综合排名")
            report_lines.append(f"**最佳综合性能模型**: {best_model['Model']}")
            report_lines.append(f"- 综合得分: {best_model['Overall']:.3f}")
            report_lines.append(f"- 准确性: {best_model['Accuracy']:.3f}")
            report_lines.append(f"- 效率: {best_model['Efficiency']:.3f}")
            report_lines.append(f"- 复杂度: {best_model['Complexity']:.3f}")
            report_lines.append(f"- 可解释性: {best_model['Interpretability']:.3f}")
            report_lines.append("")
        
        # 各维度最佳
        supervised_df = metrics_df[metrics_df['model_name_clean'].isin(self.supervised_models)]
        
        if not supervised_df.empty:
            report_lines.append("## 各维度表现")
            
            # 准确性最佳
            if 'f1_score' in supervised_df.columns:
                best_f1 = supervised_df.loc[supervised_df['f1_score'].idxmax()]
                report_lines.append(f"**最高F1分数**: {best_f1['model_name_clean']} ({best_f1['f1_score']:.3f})")
            
            # 效率最佳
            if 'training_time_seconds' in supervised_df.columns:
                fastest = supervised_df.loc[supervised_df['training_time_seconds'].idxmin()]
                report_lines.append(f"**训练速度最快**: {fastest['model_name_clean']} ({fastest['training_time_seconds']:.2f}s)")
            
            # 模型最小
            if 'model_size_mb' in supervised_df.columns:
                smallest = supervised_df.loc[supervised_df['model_size_mb'].idxmin()]
                report_lines.append(f"**模型最小**: {smallest['model_name_clean']} ({smallest['model_size_mb']:.2f}MB)")
            
            report_lines.append("")
        
        # 建议
        report_lines.append("## 模型选择建议")
        report_lines.append("### 根据应用场景")
        report_lines.append("- **高准确性需求**: 选择F1分数最高的模型")
        report_lines.append("- **实时预测需求**: 选择训练和预测时间最短的模型")
        report_lines.append("- **资源受限环境**: 选择模型文件最小的模型")
        report_lines.append("- **需要解释性**: 优先选择决策树或逻辑回归")
        report_lines.append("- **综合平衡**: 选择综合排名最高的模型")
        
        # 保存报告
        report_path = self.output_dir / "comprehensive_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        _LOG.info(f"综合分析报告已保存: {report_path}")
    
    def run_analysis(self):
        """运行完整分析"""
        _LOG.info("开始综合模型分析...")
        
        # 加载数据
        metrics_df = self.load_model_metrics()
        _LOG.info(f"加载了 {len(metrics_df)} 个模型的指标")
        
        # 各维度分析
        self.analyze_accuracy_performance(metrics_df)
        self.analyze_efficiency_performance(metrics_df)
        complexity_df = self.analyze_hyperparameter_complexity()
        
        # 综合排名
        ranking_df = self.create_comprehensive_ranking(metrics_df, complexity_df)
        
        # 生成报告
        if ranking_df is not None:
            self.generate_analysis_report(metrics_df, ranking_df)
        
        _LOG.info("综合模型分析完成!")
        return metrics_df, ranking_df

def main():
    """主函数"""
    analyzer = ComprehensiveModelAnalysis()
    analyzer.run_analysis()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main() 
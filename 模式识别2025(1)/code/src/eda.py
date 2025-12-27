"""
探索性数据分析 (EDA) 模块
包含单变量、双变量和多变量分析功能
"""

# 设置matplotlib后端，避免Tkinter错误
import matplotlib
matplotlib.use('Agg')

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from scipy import stats
from itertools import combinations
from utils import (
    save_dataframe, create_directories, PLOTS_PATH,
    get_numeric_columns, get_categorical_columns, setup_chinese_fonts
)

_LOG = logging.getLogger(__name__)

# 设置中文字体和图表样式
setup_chinese_fonts()
plt.style.use('default')
sns.set_palette("husl")


class EDAAnalyzer:
    """探索性数据分析器"""
    
    def __init__(self, df, target_column='at_risk'):
        self.df = df.copy()
        self.target_column = target_column
        
        # 更准确识别数值和分类变量
        self._identify_column_types()
        
        # 创建输出目录
        self.plot_dir = Path(PLOTS_PATH) / "eda"
        self.plot_dir.mkdir(parents=True, exist_ok=True)
        
    def _identify_column_types(self):
        """更精确地识别列类型，防止分类变量被当作数值变量"""
        # 初步识别数值和分类变量
        self.numeric_cols = get_numeric_columns(self.df)
        self.categorical_cols = get_categorical_columns(self.df)
        
        # 排除ID列
        exclude_cols = ['id_student', 'id_site', 'id_assessment']
        self.numeric_cols = [col for col in self.numeric_cols if col not in exclude_cols]
        
        # 检查数值列是否可能是分类变量
        for col in list(self.numeric_cols):
            # 如果唯一值数量少于总数据量的5%且少于20，很可能是分类变量
            if (self.df[col].nunique() < min(20, len(self.df) * 0.05) or 
                col.startswith('is_') or 
                col.endswith('_type') or
                col.endswith('_id')):
                self.numeric_cols.remove(col)
                if col not in self.categorical_cols:
                    # 转换为分类型
                    self.df[col] = self.df[col].astype('category')
                    self.categorical_cols.append(col)
        
        _LOG.info(f"识别到 {len(self.numeric_cols)} 个数值变量，{len(self.categorical_cols)} 个分类变量")
    
    def generate_data_profile(self):
        """生成数据概况报告"""
        _LOG.info("生成数据概况报告...")
        
        profile = {
            'basic_info': {
                'rows': self.df.shape[0],
                'columns': self.df.shape[1],
                'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
                'numeric_columns': len(self.numeric_cols),
                'categorical_columns': len(self.categorical_cols)
            },
            'missing_values': self.df.isnull().sum().to_dict(),
            'data_types': self.df.dtypes.to_dict(),
            'target_distribution': self.df[self.target_column].value_counts().to_dict() if self.target_column in self.df.columns else {}
        }
        
        # 数值变量统计
        if self.numeric_cols:
            numeric_stats = self.df[self.numeric_cols].describe()
            profile['numeric_statistics'] = numeric_stats.to_dict()
        
        # 分类变量统计
        categorical_stats = {}
        for col in self.categorical_cols:
            if col in self.df.columns:
                categorical_stats[col] = {
                    'unique_values': self.df[col].nunique(),
                    'top_values': self.df[col].value_counts().head().to_dict()
                }
        profile['categorical_statistics'] = categorical_stats
        
        # 保存报告
        profile_df = pd.DataFrame([profile['basic_info']])
        save_dataframe(profile_df, "data_profile_summary")
        
        return profile
    
    def univariate_analysis(self):
        """单变量分析"""
        _LOG.info("开始单变量分析...")
        
        # 数值变量分布
        self._plot_numeric_distributions()
        
        # 分类变量分布
        self._plot_categorical_distributions()
        
        # 目标变量分析
        if self.target_column in self.df.columns:
            self._plot_target_distribution()
    
    def _plot_numeric_distributions(self):
        """绘制数值变量分布图"""
        if not self.numeric_cols:
            return
        
        n_cols = min(4, len(self.numeric_cols))
        n_rows = (len(self.numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(self.numeric_cols):
            if i < len(axes):
                ax = axes[i]
                
                # 直方图
                self.df[col].hist(bins=30, alpha=0.7, ax=ax)
                ax.set_title(f'{col}\nMean: {self.df[col].mean():.2f}, Std: {self.df[col].std():.2f}')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency')
                ax.grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        for i in range(len(self.numeric_cols), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.plot_dir / "numeric_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info("数值变量分布图已保存")
    
    def _plot_categorical_distributions(self):
        """绘制分类变量分布图"""
        categorical_cols_subset = [col for col in self.categorical_cols if col in self.df.columns]
        
        if not categorical_cols_subset:
            return
        
        n_cols = min(3, len(categorical_cols_subset))
        n_rows = (len(categorical_cols_subset) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 4*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(categorical_cols_subset):
            if i < len(axes):
                ax = axes[i]
                
                value_counts = self.df[col].value_counts()
                
                # 如果类别太多，只显示前10个
                if len(value_counts) > 10:
                    value_counts = value_counts.head(10)
                    title_suffix = f" (前10个, 共{self.df[col].nunique()}个类别)"
                else:
                    title_suffix = f" ({self.df[col].nunique()}个类别)"
                
                value_counts.plot(kind='bar', ax=ax)
                ax.set_title(f'{col}{title_suffix}')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency')
                ax.tick_params(axis='x', rotation=45)
        
        # 隐藏多余的子图
        for i in range(len(categorical_cols_subset), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.plot_dir / "categorical_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info("分类变量分布图已保存")
    
    def _plot_target_distribution(self):
        """绘制目标变量分布"""
        plt.figure(figsize=(10, 6))
        
        # 子图1: 柱状图
        plt.subplot(1, 2, 1)
        target_counts = self.df[self.target_column].value_counts()
        target_counts.plot(kind='bar')
        plt.title(f'{self.target_column} 分布')
        plt.xlabel(self.target_column)
        plt.ylabel('频次')
        
        # 添加百分比标签
        total = len(self.df)
        for i, v in enumerate(target_counts.values):
            plt.text(i, v + total*0.01, f'{v}\n({v/total*100:.1f}%)', 
                    ha='center', va='bottom')
        
        # 子图2: 饼图
        plt.subplot(1, 2, 2)
        target_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title(f'{self.target_column} 比例')
        plt.ylabel('')
        
        plt.tight_layout()
        plt.savefig(self.plot_dir / "target_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info("目标变量分布图已保存")
    
    def bivariate_analysis(self):
        """双变量分析"""
        _LOG.info("开始双变量分析...")
        
        if self.target_column in self.df.columns:
            # 数值变量 vs 目标变量
            self._plot_numeric_vs_target()
            
            # 分类变量 vs 目标变量
            self._plot_categorical_vs_target()
        
        # 数值变量间相关性
        self._plot_correlation_matrix()
        
        # 散点图矩阵
        self._plot_scatter_matrix()
    
    def _plot_numeric_vs_target(self):
        """数值变量与目标变量的关系"""
        if not self.numeric_cols:
            return
        
        n_cols = min(3, len(self.numeric_cols))
        n_rows = (len(self.numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 4*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(self.numeric_cols):
            if i < len(axes):
                ax = axes[i]
                
                # 箱线图
                sns.boxplot(data=self.df, x=self.target_column, y=col, ax=ax)
                ax.set_title(f'{col} by {self.target_column}')
                
                # 计算统计显著性
                groups = [group[col].dropna() for name, group in self.df.groupby(self.target_column)]
                if len(groups) == 2:
                    stat, p_value = stats.ttest_ind(groups[0], groups[1])
                    ax.text(0.02, 0.98, f'p-value: {p_value:.3f}', 
                           transform=ax.transAxes, va='top', ha='left',
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 隐藏多余的子图
        for i in range(len(self.numeric_cols), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.plot_dir / "numeric_vs_target.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info("数值变量与目标变量关系图已保存")
    
    def _plot_categorical_vs_target(self):
        """分类变量与目标变量的关系"""
        categorical_cols_subset = [col for col in self.categorical_cols if col in self.df.columns and col != self.target_column]
        
        if not categorical_cols_subset:
            return
        
        n_cols = min(2, len(categorical_cols_subset))
        n_rows = (len(categorical_cols_subset) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(8*n_cols, 5*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(categorical_cols_subset):
            if i < len(axes):
                ax = axes[i]
                
                # 交叉表
                cross_tab = pd.crosstab(self.df[col], self.df[self.target_column], normalize='index')
                cross_tab.plot(kind='bar', stacked=True, ax=ax)
                ax.set_title(f'{col} vs {self.target_column}')
                ax.set_xlabel(col)
                ax.set_ylabel('Proportion')
                ax.legend(title=self.target_column)
                ax.tick_params(axis='x', rotation=45)
        
        # 隐藏多余的子图
        for i in range(len(categorical_cols_subset), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(self.plot_dir / "categorical_vs_target.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info("分类变量与目标变量关系图已保存")
    
    def _plot_correlation_matrix(self):
        """绘制相关性矩阵"""
        if len(self.numeric_cols) < 2:
            return
        
        # 计算相关性矩阵
        corr_matrix = self.df[self.numeric_cols].corr()
        
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        # 只显示颜色，不显示数值
        sns.heatmap(corr_matrix, mask=mask, annot=False, cmap='coolwarm', center=0,
                   square=True, cbar_kws={"shrink": .8})
        plt.title('Variable Correlation Matrix')
        plt.tight_layout()
        plt.savefig(self.plot_dir / "correlation_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存相关性数据
        save_dataframe(corr_matrix, "correlation_matrix")
        
        _LOG.info("相关性矩阵已保存")
    
    def _plot_scatter_matrix(self):
        """绘制散点图矩阵"""
        if len(self.numeric_cols) < 2:
            return
        
        # 选择前6个最重要的数值变量
        important_cols = self.numeric_cols[:6]
        
        if self.target_column in self.df.columns:
            # 使用目标变量着色
            scatter_df = self.df[important_cols + [self.target_column]]
            
            fig = px.scatter_matrix(
                scatter_df, 
                dimensions=important_cols,
                color=self.target_column,
                title="Numeric Variables Scatter Matrix"
            )
            fig.write_html(self.plot_dir / "scatter_matrix.html")
        
        _LOG.info("散点图矩阵已保存")
    
    def feature_importance_analysis(self):
        """特征重要性分析"""
        _LOG.info("开始特征重要性分析...")
        
        if self.target_column not in self.df.columns:
            _LOG.warning("目标变量不存在，跳过特征重要性分析")
            return
        
        try:
            # 使用随机森林计算特征重要性
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder
            
            # 准备数据
            feature_cols = self.numeric_cols + [col for col in self.categorical_cols if col != self.target_column]
            feature_cols = [col for col in feature_cols if col in self.df.columns]
            
            X = self.df[feature_cols].copy()
            
            # 处理目标变量
            if self.df[self.target_column].dtype.name == 'category':
                y = self.df[self.target_column].astype(int)
            else:
                y = self.df[self.target_column]
            
            # 编码分类变量并处理可能的category类型
            for col in X.columns:
                if X[col].dtype == 'object' or X[col].dtype.name == 'category':
                    # 将category类型转换为字符串，然后进行标签编码
                    X[col] = X[col].astype(str)
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col])
            
            # 填充缺失值 - 分别对不同类型的列应用不同策略
            for col in X.columns:
                if pd.api.types.is_numeric_dtype(X[col]):
                    X[col] = X[col].fillna(X[col].median())
                else:
                    # 如果有非数值型列，使用最频繁值填充
                    X[col] = X[col].fillna(X[col].mode()[0] if not X[col].mode().empty else 0)
            
            # 确保所有列都是数值型
            for col in X.columns:
                if not pd.api.types.is_numeric_dtype(X[col]):
                    X[col] = X[col].astype(float)
            
            # 训练随机森林
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X, y)
            
            # 特征重要性
            importance_df = pd.DataFrame({
                'feature': feature_cols,
                'importance': rf.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # 绘制特征重要性图
            plt.figure(figsize=(10, 8))
            top_features = importance_df.head(15)
            
            sns.barplot(data=top_features, y='feature', x='importance')
            plt.title('Top 15 Feature Importance (Random Forest)')
            plt.xlabel('Importance Score')
            plt.tight_layout()
            plt.savefig(self.plot_dir / "feature_importance.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # 保存特征重要性数据
            save_dataframe(importance_df, "feature_importance")
            
            _LOG.info("特征重要性分析完成")
            return importance_df
            
        except Exception as e:
            _LOG.warning(f"特征重要性分析失败: {e}")
            return None
    
    def vle_behavior_analysis(self):
        """VLE学习行为分析"""
        _LOG.info("开始VLE行为分析...")
        
        # 找到VLE相关列
        vle_click_cols = [col for col in self.df.columns if 'avg_sum_clicks' in col]
        vle_days_cols = [col for col in self.df.columns if 'n_days' in col]
        
        if not vle_click_cols and not vle_days_cols:
            _LOG.warning("未找到VLE相关特征")
            return
        
        # VLE活动类型分析
        if vle_click_cols:
            # 提取活动类型
            activity_types = []
            for col in vle_click_cols:
                if 'avg_sum_clicks_' in col:
                    activity_type = col.replace('avg_sum_clicks_', '')
                    activity_types.append(activity_type)
            
            if activity_types:
                # 每种活动类型的平均使用情况
                vle_summary = {}
                for activity in activity_types:
                    click_col = f'avg_sum_clicks_{activity}'
                    days_col = f'n_days_{activity}'
                    
                    if click_col in self.df.columns:
                        # 确保数据是数值型
                        if self.df[click_col].dtype.name == 'category':
                            avg_clicks = self.df[click_col].astype(float).mean()
                            usage_rate = (self.df[click_col].astype(float) > 0).mean()
                        else:
                            avg_clicks = self.df[click_col].mean()
                            usage_rate = (self.df[click_col] > 0).mean()
                        
                        vle_summary[activity] = {
                            'avg_clicks': avg_clicks,
                            'usage_rate': usage_rate
                        }
                        
                        if days_col in self.df.columns:
                            # 确保数据是数值型
                            if self.df[days_col].dtype.name == 'category':
                                avg_days = self.df[days_col].astype(float).mean()
                            else:
                                avg_days = self.df[days_col].mean()
                            vle_summary[activity]['avg_days'] = avg_days
                
                # 转换为DataFrame并保存
                vle_summary_df = pd.DataFrame(vle_summary).T
                save_dataframe(vle_summary_df, "vle_activity_summary")
                
                # 可视化
                fig, axes = plt.subplots(1, 2, figsize=(15, 6))
                
                # 提取数据用于绘图
                activity_names = list(vle_summary.keys())
                usage_rates = [vle_summary[activity]['usage_rate'] for activity in activity_names]
                avg_clicks_list = [vle_summary[activity]['avg_clicks'] for activity in activity_names]
                
                # 使用率
                axes[0].bar(range(len(activity_names)), usage_rates, color='skyblue')
                axes[0].set_title('VLE Activity Type Usage Rate')
                axes[0].set_ylabel('Usage Rate')
                axes[0].set_xticks(range(len(activity_names)))
                axes[0].set_xticklabels(activity_names, rotation=45)
                
                # 平均点击数
                axes[1].bar(range(len(activity_names)), avg_clicks_list, color='lightcoral')
                axes[1].set_title('VLE Activity Type Average Clicks')
                axes[1].set_ylabel('Average Clicks')
                axes[1].set_xticks(range(len(activity_names)))
                axes[1].set_xticklabels(activity_names, rotation=45)
                
                plt.tight_layout()
                plt.savefig(self.plot_dir / "vle_activity_analysis.png", dpi=300, bbox_inches='tight')
                plt.close()
        
        _LOG.info("VLE行为分析完成")
    
    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        _LOG.info("生成综合分析报告...")
        
        # 1. 数据概况
        profile = self.generate_data_profile()
        
        # 2. 单变量分析
        self.univariate_analysis()
        
        # 3. 双变量分析
        self.bivariate_analysis()
        
        # 4. 特征重要性分析
        importance_df = self.feature_importance_analysis()
        
        # 5. VLE行为分析
        self.vle_behavior_analysis()
        
        # 6. 生成文字报告
        report = self._generate_text_report(profile, importance_df)
        
        # 保存报告
        with open(self.plot_dir / "eda_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        _LOG.info("综合分析报告生成完成")
        return report
    
    def _generate_text_report(self, profile, importance_df):
        """生成文字分析报告"""
        report = []
        report.append("="*80)
        report.append("OULAD 数据集 - 探索性数据分析报告")
        report.append("="*80)
        
        # 数据概况
        report.append("\n1. 数据概况")
        report.append("-" * 40)
        report.append(f"• 数据规模: {profile['basic_info']['rows']:,} 行 × {profile['basic_info']['columns']} 列")
        report.append(f"• 内存使用: {profile['basic_info']['memory_usage_mb']:.1f} MB")
        report.append(f"• 数值变量: {profile['basic_info']['numeric_columns']} 个")
        report.append(f"• 分类变量: {profile['basic_info']['categorical_columns']} 个")
        
        # 目标变量分布
        if profile['target_distribution']:
            report.append(f"\n2. 目标变量分布 ({self.target_column})")
            report.append("-" * 40)
            total = sum(profile['target_distribution'].values())
            for value, count in profile['target_distribution'].items():
                percentage = (count / total) * 100
                report.append(f"• {value}: {count:,} ({percentage:.1f}%)")
        
        # 缺失值情况
        missing_values = {k: v for k, v in profile['missing_values'].items() if v > 0}
        if missing_values:
            report.append("\n3. 缺失值情况")
            report.append("-" * 40)
            for col, missing_count in missing_values.items():
                missing_pct = (missing_count / profile['basic_info']['rows']) * 100
                report.append(f"• {col}: {missing_count:,} ({missing_pct:.1f}%)")
        
        # 特征重要性
        if importance_df is not None:
            report.append("\n4. Top 10 重要特征")
            report.append("-" * 40)
            for _, row in importance_df.head(10).iterrows():
                report.append(f"• {row['feature']}: {row['importance']:.4f}")
        
        # 关键发现
        report.append("\n5. 关键发现")
        report.append("-" * 40)
        
        # 学业困难率分析
        if self.target_column in self.df.columns:
            # 确保目标变量是数值型
            if self.df[self.target_column].dtype.name == 'category':
                at_risk_rate = self.df[self.target_column].astype(float).mean()
            else:
                at_risk_rate = self.df[self.target_column].mean()
                
            report.append(f"• 学业困难率: {at_risk_rate:.1%}")
            
            if at_risk_rate > 0.5:
                report.append("  - High risk group majority, need to pay attention")
            else:
                report.append("  - Successful students majority, but still need to warn high risk students")
        
        # VLE使用情况
        vle_cols = [col for col in self.df.columns if 'total_n_days' in col]
        if vle_cols:
            # 确保数据是数值型
            if self.df[vle_cols[0]].dtype.name == 'category':
                avg_days = self.df[vle_cols[0]].astype(float).mean()
            else:
                avg_days = self.df[vle_cols[0]].mean()
                
            report.append(f"• Average learning days: {avg_days:.1f} days")
        
        # 数据质量评估
        total_missing = sum(profile['missing_values'].values())
        missing_rate = (total_missing / (profile['basic_info']['rows'] * profile['basic_info']['columns'])) * 100
        report.append(f"• Overall missing rate: {missing_rate:.1f}%")
        
        if missing_rate < 5:
            report.append("  - Data quality is good")
        elif missing_rate < 15:
            report.append("  - Medium data quality, need to handle appropriately")
        else:
            report.append("  - Poor data quality, need to focus on cleaning")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)


def run_eda(df, target_column='at_risk'):
    """
    运行完整的探索性数据分析
    
    Args:
        df: 输入数据框
        target_column: 目标变量列名
        
    Returns:
        EDA分析器实例和分析报告
    """
    _LOG.info("开始探索性数据分析...")
    
    # 创建分析器
    analyzer = EDAAnalyzer(df, target_column)
    
    # 生成综合报告
    report = analyzer.generate_comprehensive_report()
    
    _LOG.info("探索性数据分析完成")
    print("\n" + "="*80)
    print("EDA 分析完成！")
    print("="*80)
    print(f"图表保存位置: {analyzer.plot_dir}")
    print(f"分析报告: {analyzer.plot_dir / 'eda_report.txt'}")
    
    return analyzer, report


if __name__ == "__main__":
    # 测试EDA模块
    logging.basicConfig(level=logging.INFO)
    print("EDA模块已加载") 
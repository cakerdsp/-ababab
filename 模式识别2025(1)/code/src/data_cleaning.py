"""
数据清洗模块
处理缺失值、异常值、重复值和特征工程
"""

# 设置matplotlib后端，避免Tkinter错误
import matplotlib
matplotlib.use('Agg')

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, StandardScaler
from pathlib import Path
from utils import (
    save_dataframe, create_directories, PLOTS_PATH,
    get_numeric_columns, get_categorical_columns, setup_chinese_fonts
)

_LOG = logging.getLogger(__name__)

# 设置中文字体支持
setup_chinese_fonts()


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        
    def handle_missing_values(self, df, strategy='auto'):
        """
        处理缺失值
        
        Args:
            df: 输入数据框
            strategy: 处理策略 ('auto', 'drop', 'impute')
        """
        _LOG.info("开始处理缺失值...")
        
        df_cleaned = df.copy()
        missing_info = df_cleaned.isnull().sum()
        
        print("\n缺失值情况:")
        for col, missing_count in missing_info.items():
            if missing_count > 0:
                missing_pct = (missing_count / len(df_cleaned)) * 100
                print(f"  {col}: {missing_count} ({missing_pct:.1f}%)")
        
        if strategy == 'auto':
            # 自动策略：根据缺失比例决定处理方法
            for col in df_cleaned.columns:
                missing_pct = (df_cleaned[col].isnull().sum() / len(df_cleaned)) * 100
                
                if missing_pct >= 70:
                    # 缺失超过70%，删除列
                    df_cleaned = df_cleaned.drop(columns=[col])
                    _LOG.info(f"删除列 {col} (缺失 {missing_pct:.1f}%)")
                    
                elif missing_pct > 0:
                    if df_cleaned[col].dtype in ['object']:
                        # 分类变量：删除缺失行或填充众数
                        if missing_pct < 10:
                            mode_value = df_cleaned[col].mode().iloc[0] if not df_cleaned[col].mode().empty else 'Unknown'
                            df_cleaned[col] = df_cleaned[col].fillna(mode_value)
                            _LOG.info(f"用众数填充 {col}: {mode_value}")
                        else:
                            df_cleaned = df_cleaned.dropna(subset=[col])
                            _LOG.info(f"删除 {col} 的缺失行")
                    else:
                        # 数值变量：用中位数填充
                        median_value = df_cleaned[col].median()
                        df_cleaned[col] = df_cleaned[col].fillna(median_value)
                        _LOG.info(f"用中位数填充 {col}: {median_value}")
        
        elif strategy == 'drop':
            # 删除策略
            df_cleaned = df_cleaned.dropna()
            
        elif strategy == 'impute':
            # 填充策略
            for col in df_cleaned.columns:
                if df_cleaned[col].isnull().sum() > 0:
                    if df_cleaned[col].dtype in ['object']:
                        df_cleaned[col] = df_cleaned[col].fillna('Unknown')
                    else:
                        df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
        
        _LOG.info(f"缺失值处理完成，数据形状: {df.shape} -> {df_cleaned.shape}")
        return df_cleaned
    
    def remove_duplicates(self, df):
        """删除重复行"""
        original_shape = df.shape
        df_cleaned = df.drop_duplicates()
        duplicates_count = original_shape[0] - df_cleaned.shape[0]
        
        if duplicates_count > 0:
            _LOG.info(f"删除重复行: {duplicates_count} 行")
        else:
            _LOG.info("未发现重复行")
            
        return df_cleaned
    
    def handle_outliers(self, df, method='iqr', threshold=0.98):
        """
        处理异常值
        
        Args:
            df: 输入数据框
            method: 处理方法 ('iqr', 'percentile', 'zscore')
            threshold: 阈值
        """
        _LOG.info(f"开始处理异常值，方法: {method}")
        
        df_cleaned = df.copy()
        numeric_cols = get_numeric_columns(df_cleaned)
        
        # 排除ID类和目标变量
        exclude_cols = ['id_student', 'id_site', 'id_assessment', 'at_risk', 'final_result']
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        outlier_info = {}
        
        for col in numeric_cols:
            original_values = df_cleaned[col].copy()
            
            if method == 'percentile':
                # 百分位数方法
                upper_limit = df_cleaned[col].quantile(threshold)
                lower_limit = df_cleaned[col].quantile(1 - threshold)
                
                outliers_mask = (df_cleaned[col] > upper_limit) | (df_cleaned[col] < lower_limit)
                outliers_count = outliers_mask.sum()
                
                # 裁剪异常值
                df_cleaned[col] = df_cleaned[col].clip(lower=lower_limit, upper=upper_limit)
                
            elif method == 'iqr':
                # 四分位距方法
                Q1 = df_cleaned[col].quantile(0.25)
                Q3 = df_cleaned[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_limit = Q1 - 1.5 * IQR
                upper_limit = Q3 + 1.5 * IQR
                
                outliers_mask = (df_cleaned[col] > upper_limit) | (df_cleaned[col] < lower_limit)
                outliers_count = outliers_mask.sum()
                
                # 裁剪异常值
                df_cleaned[col] = df_cleaned[col].clip(lower=lower_limit, upper=upper_limit)
                
            elif method == 'zscore':
                # Z分数方法
                z_scores = np.abs((df_cleaned[col] - df_cleaned[col].mean()) / df_cleaned[col].std())
                outliers_mask = z_scores > 3
                outliers_count = outliers_mask.sum()
                
                # 用中位数替换异常值
                df_cleaned.loc[outliers_mask, col] = df_cleaned[col].median()
            
            if outliers_count > 0:
                outlier_info[col] = {
                    'count': outliers_count,
                    'percentage': (outliers_count / len(df_cleaned)) * 100,
                    'original_range': [original_values.min(), original_values.max()],
                    'cleaned_range': [df_cleaned[col].min(), df_cleaned[col].max()]
                }
        
        # 打印异常值处理报告
        if outlier_info:
            print(f"\n异常值处理报告 ({method} 方法):")
            for col, info in outlier_info.items():
                print(f"  {col}: {info['count']} 个异常值 ({info['percentage']:.1f}%)")
                print(f"    原始范围: [{info['original_range'][0]:.2f}, {info['original_range'][1]:.2f}]")
                print(f"    处理后范围: [{info['cleaned_range'][0]:.2f}, {info['cleaned_range'][1]:.2f}]")
        
        _LOG.info("异常值处理完成")
        return df_cleaned, outlier_info
    
    def create_boxplots(self, df_before, df_after, outlier_info, save_path):
        """创建异常值处理前后的箱线图对比"""
        numeric_cols = list(outlier_info.keys())
        
        if not numeric_cols:
            return
        
        n_cols = min(4, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(numeric_cols):
            if i < len(axes):
                ax = axes[i]
                
                # 创建对比数据
                data_before = df_before[col].dropna()
                data_after = df_after[col].dropna()
                
                box_data = [data_before, data_after]
                
                ax.boxplot(box_data, labels=['Before', 'After'])
                ax.set_title(f'{col}\nOutliers: {outlier_info[col]["count"]} items')
                ax.grid(True, alpha=0.3)
        
        # 隐藏多余的子图
        for i in range(len(numeric_cols), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        _LOG.info(f"异常值处理箱线图已保存: {save_path}")
    
    def feature_engineering(self, df):
        """特征工程"""
        _LOG.info("开始特征工程...")
        
        df_engineered = df.copy()
        
        # 1. 时间特征提取
        if 'code_presentation' in df_engineered.columns:
            df_engineered['year'] = df_engineered['code_presentation'].str[:4].astype(int)
            df_engineered['semester'] = df_engineered['code_presentation'].str[-1]
            df_engineered['is_february'] = (df_engineered['semester'] == 'J').astype(int)
            
        # 2. 学习行为特征
        # 总点击量特征
        vle_click_cols = [col for col in df_engineered.columns if 'avg_sum_clicks' in col]
        if vle_click_cols:
            df_engineered['total_clicks'] = df_engineered[vle_click_cols].sum(axis=1)
        
        # 学习活跃度特征
        vle_days_cols = [col for col in df_engineered.columns if 'n_days' in col and col != 'total_n_days']
        if vle_days_cols:
            df_engineered['activity_diversity'] = (df_engineered[vle_days_cols] > 0).sum(axis=1)
        
        # 3. 学习强度特征
        if 'total_n_days' in df_engineered.columns and 'avg_total_clicks' in df_engineered.columns:
            df_engineered['learning_intensity'] = df_engineered['total_n_days'] * df_engineered['avg_total_clicks']
        
        # 4. 注册行为特征
        if 'date_registration' in df_engineered.columns:
            df_engineered['early_registration'] = (df_engineered['date_registration'] < -30).astype(int)
            df_engineered['late_registration'] = (df_engineered['date_registration'] > -7).astype(int)
        
        # 5. 教育背景特征
        if 'highest_education' in df_engineered.columns:
            education_mapping = {
                'No Formal quals': 0,
                'Lower Than A Level': 1,
                'A Level or Equivalent': 2,
                'HE Qualification': 3,
                'Post Graduate Qualification': 4
            }
            df_engineered['education_level'] = df_engineered['highest_education'].map(education_mapping)
            df_engineered['education_level'] = df_engineered['education_level'].fillna(1)  # 默认为 Lower Than A Level
        
        _LOG.info(f"特征工程完成，新增特征数: {df_engineered.shape[1] - df.shape[1]}")
        return df_engineered
    
    def encode_categorical_variables(self, df, target_cols=None):
        """编码分类变量"""
        _LOG.info("开始编码分类变量...")
        
        df_encoded = df.copy()
        categorical_cols = get_categorical_columns(df_encoded)
        
        # 排除目标变量和已处理的列
        exclude_cols = ['final_result']  # 目标变量单独处理
        if target_cols:
            exclude_cols.extend(target_cols)
            
        categorical_cols = [col for col in categorical_cols if col not in exclude_cols]
        
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                # 确保转换为字符串类型后再进行编码
                df_encoded[col] = self.label_encoders[col].fit_transform(df_encoded[col].astype(str))
                _LOG.info(f"编码列 {col}: {len(self.label_encoders[col].classes_)} 个类别")
            else:
                df_encoded[col] = self.label_encoders[col].transform(df_encoded[col].astype(str))
        
        _LOG.info("分类变量编码完成")
        return df_encoded
    
    def normalize_features(self, df, exclude_cols=None):
        """标准化数值特征"""
        _LOG.info("开始特征标准化...")
        
        df_normalized = df.copy()
        numeric_cols = get_numeric_columns(df_normalized)
        
        # 排除不需要标准化的列
        if exclude_cols is None:
            exclude_cols = ['id_student', 'at_risk']  # 移除year，让它也被标准化
        
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        if numeric_cols:
            df_normalized[numeric_cols] = self.scaler.fit_transform(df_normalized[numeric_cols])
            _LOG.info(f"标准化 {len(numeric_cols)} 个数值特征")
        
        return df_normalized


def clean_data(df, cleaning_config=None):
    """
    完整的数据清洗流程
    
    Args:
        df: 输入数据框
        cleaning_config: 清洗配置字典
        
    Returns:
        清洗后的数据框和清洗报告
    """
    _LOG.info("开始数据清洗流程...")
    
    # 默认配置
    if cleaning_config is None:
        cleaning_config = {
            'missing_strategy': 'auto',
            'outlier_method': 'percentile',
            'outlier_threshold': 0.98,
            'enable_feature_engineering': True,
            'enable_encoding': True,
            'enable_normalization': False
        }
    
    # 创建输出目录
    create_directories()
    
    # 初始化清洗器
    cleaner = DataCleaner()
    
    # 保存原始数据信息
    original_shape = df.shape
    cleaning_report = {
        'original_shape': original_shape,
        'steps': []
    }
    
    # 1. 处理缺失值
    df_cleaned = cleaner.handle_missing_values(df, cleaning_config['missing_strategy'])
    cleaning_report['steps'].append({
        'step': '处理缺失值',
        'shape_change': f"{df.shape} -> {df_cleaned.shape}"
    })
    
    # 2. 删除重复行
    df_cleaned = cleaner.remove_duplicates(df_cleaned)
    cleaning_report['steps'].append({
        'step': '删除重复行',
        'shape_change': f"{df.shape} -> {df_cleaned.shape}"
    })
    
    # 3. 处理异常值
    df_before_outliers = df_cleaned.copy()
    df_cleaned, outlier_info = cleaner.handle_outliers(
        df_cleaned, 
        method=cleaning_config['outlier_method'],
        threshold=cleaning_config['outlier_threshold']
    )
    
    # 创建异常值处理对比图
    if outlier_info:
        plot_path = Path(PLOTS_PATH) / "cleaning" / "outlier_comparison.png"
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        cleaner.create_boxplots(df_before_outliers, df_cleaned, outlier_info, plot_path)
    
    cleaning_report['steps'].append({
        'step': '处理异常值',
        'outlier_info': outlier_info
    })
    
    # 4. 特征工程
    if cleaning_config['enable_feature_engineering']:
        df_before_fe = df_cleaned.copy()
        df_cleaned = cleaner.feature_engineering(df_cleaned)
        cleaning_report['steps'].append({
            'step': '特征工程',
            'new_features': df_cleaned.shape[1] - df_before_fe.shape[1]
        })
    
    # 5. 编码分类变量
    if cleaning_config['enable_encoding']:
        df_cleaned = cleaner.encode_categorical_variables(df_cleaned)
        cleaning_report['steps'].append({
            'step': '编码分类变量',
            'encoders': list(cleaner.label_encoders.keys())
        })
    
    # 6. 特征标准化
    if cleaning_config['enable_normalization']:
        df_cleaned = cleaner.normalize_features(df_cleaned)
        cleaning_report['steps'].append({
            'step': '特征标准化',
            'normalized': True
        })
    
    # 最终清洗报告
    cleaning_report['final_shape'] = df_cleaned.shape
    cleaning_report['data_reduction'] = {
        'rows_removed': original_shape[0] - df_cleaned.shape[0],
        'reduction_percentage': ((original_shape[0] - df_cleaned.shape[0]) / original_shape[0]) * 100
    }
    
    # 保存清洗后的数据和报告
    save_dataframe(df_cleaned, "master_dataframe_cleaned")
    
    # 打印清洗总结
    print("\n" + "="*80)
    print("数据清洗总结")
    print("="*80)
    print(f"原始数据形状: {original_shape}")
    print(f"清洗后形状: {df_cleaned.shape}")
    print(f"删除行数: {cleaning_report['data_reduction']['rows_removed']}")
    print(f"数据减少: {cleaning_report['data_reduction']['reduction_percentage']:.1f}%")
    
    for step in cleaning_report['steps']:
        print(f"- {step['step']}: {step.get('shape_change', '完成')}")
    
    _LOG.info("数据清洗流程完成")
    return df_cleaned, cleaning_report, cleaner


if __name__ == "__main__":
    # 测试数据清洗模块
    logging.basicConfig(level=logging.INFO)
    
    # 这里可以添加测试代码
    print("数据清洗模块已加载") 
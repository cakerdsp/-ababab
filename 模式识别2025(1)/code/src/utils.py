"""
通用工具模块
包含公共函数、常量和配置
"""

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager


# 配置常量
DATA_PATH = "anonymisedData/anonymisedData"
OUTPUT_PATH = "outputs"
PLOTS_PATH = "outputs/plots"
DATAFRAMES_PATH = "outputs/dataframes"

# 数据文件映射
DATA_FILES = {
    'student_info': 'studentInfo.csv',
    'student_vle': 'studentVle.csv', 
    'student_assessment': 'studentAssessment.csv',
    'student_registration': 'studentRegistration.csv',
    'vle': 'vle.csv',
    'courses': 'courses.csv',
    'assessments': 'assessments.csv'
}

# 学业困难定义
AT_RISK_OUTCOMES = ['Fail', 'Withdrawn']
SUCCESS_OUTCOMES = ['Pass', 'Distinction']

def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def setup_chinese_fonts():
    """设置matplotlib中文字体支持"""
    try:
        # 设置非交互式后端，避免Tkinter错误
        import matplotlib
        matplotlib.use('Agg')
        
        # 直接设置中文字体，不搞复杂的检测
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置图表样式
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['savefig.bbox'] = 'tight'
        
        print("✅ 中文字体设置完成")
        return True
        
    except Exception as e:
        print(f"❌ 字体设置失败: {e}")
        return False

def create_directories():
    """创建必要的输出目录"""
    directories = [
        OUTPUT_PATH,
        PLOTS_PATH,
        DATAFRAMES_PATH,
        f"{PLOTS_PATH}/eda",
        f"{PLOTS_PATH}/cleaning",
        f"{PLOTS_PATH}/modeling"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    return directories

def save_dataframe(df, filename, subfolder=""):
    """保存DataFrame到CSV文件"""
    if subfolder:
        filepath = Path(DATAFRAMES_PATH) / subfolder / f"{filename}.csv"
        filepath.parent.mkdir(parents=True, exist_ok=True)
    else:
        filepath = Path(DATAFRAMES_PATH) / f"{filename}.csv"
    
    df.to_csv(filepath, index=False)
    return filepath

def load_dataframe(filename, subfolder=""):
    """从CSV文件加载DataFrame"""
    if subfolder:
        filepath = Path(DATAFRAMES_PATH) / subfolder / f"{filename}.csv"
    else:
        filepath = Path(DATAFRAMES_PATH) / f"{filename}.csv"
    
    return pd.read_csv(filepath)

def get_timestamp():
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def print_dataframe_info(df, name="DataFrame"):
    """打印DataFrame的基本信息"""
    print(f"\n=== {name} 信息 ===")
    print(f"形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(f"数据类型:\n{df.dtypes}")
    print(f"缺失值:\n{df.isnull().sum()}")
    print(f"内存使用: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

def calculate_missing_percentage(df):
    """计算每列的缺失值百分比"""
    missing_percent = (df.isnull().sum() / len(df)) * 100
    missing_df = pd.DataFrame({
        'Column': df.columns,
        'Missing_Count': df.isnull().sum(),
        'Missing_Percentage': missing_percent
    })
    return missing_df.sort_values('Missing_Percentage', ascending=False)

def get_numeric_columns(df):
    """获取数值型列名"""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_categorical_columns(df):
    """获取分类型列名"""
    # 同时获取object类型和category类型的列
    object_cols = df.select_dtypes(include=['object']).columns.tolist()
    category_cols = df.select_dtypes(include=['category']).columns.tolist()
    return object_cols + category_cols 
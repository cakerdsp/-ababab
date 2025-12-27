"""
ETL (Extract, Transform, Load) 模块
负责数据加载、初步探索和数据合并
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from utils import (
    DATA_PATH, DATA_FILES, create_directories, save_dataframe,
    print_dataframe_info, calculate_missing_percentage
)

_LOG = logging.getLogger(__name__)


class OULADDataLoader:
    """OULAD数据加载器"""
    
    def __init__(self, data_path=DATA_PATH):
        self.data_path = Path(data_path)
        self.data_dict = {}
        
    def load_all_data(self):
        """加载所有CSV文件"""
        _LOG.info("开始加载OULAD数据集...")
        
        for key, filename in DATA_FILES.items():
            file_path = self.data_path / filename
            if file_path.exists():
                _LOG.info(f"加载 {filename}...")
                try:
                    self.data_dict[key] = pd.read_csv(file_path)
                    _LOG.info(f"  - 成功加载，形状: {self.data_dict[key].shape}")
                except Exception as e:
                    _LOG.error(f"  - 加载失败: {e}")
            else:
                _LOG.warning(f"文件不存在: {file_path}")
        
        _LOG.info(f"数据加载完成，共加载 {len(self.data_dict)} 个表")
        return self.data_dict
    
    def get_data_summary(self):
        """获取数据概况摘要"""
        if not self.data_dict:
            self.load_all_data()
        
        summary_data = []
        for name, df in self.data_dict.items():
            missing_info = calculate_missing_percentage(df)
            summary_data.append({
                'Table': name,
                'Rows': df.shape[0],
                'Cols': df.shape[1],
                'Missing_Rows': df.isnull().any(axis=1).sum(),
                'Missing_Percentage': missing_info['Missing_Percentage'].max(),
                'Memory_MB': df.memory_usage(deep=True).sum() / 1024**2,
                'Columns': list(df.columns)
            })
        
        summary_df = pd.DataFrame(summary_data)
        return summary_df


def prep_vle_data(student_vle_df, vle_df, research_question='rq1'):
    """
    预处理VLE数据，聚合学生与虚拟学习环境的交互数据
    
    Args:
        student_vle_df: 学生VLE交互数据
        vle_df: VLE活动信息数据
        research_question: 研究问题类型 ('rq1' 或 'rq2')
        
    Returns:
        处理后的VLE特征数据
    """
    _LOG.info("开始处理VLE数据...")
    
    # 合并VLE交互数据和活动信息
    merged_vle = student_vle_df.merge(
        vle_df, 
        on=['code_module', 'code_presentation', 'id_site'], 
        how='inner'
    ).drop(['week_from', 'week_to'], axis=1)
    
    # 根据研究问题选择聚合键
    if research_question == 'rq1':
        keys_activity = ['code_module', 'code_presentation', 'id_student', 'activity_type']
        keys_student = ['code_module', 'code_presentation', 'id_student']
    else:
        keys_activity = ['code_module', 'code_presentation', 'id_student', 'id_assessment', 'activity_type']
        keys_student = ['code_module', 'code_presentation', 'id_student', 'id_assessment']
    
    # 按活动类型聚合：每种活动类型的天数和平均点击数
    n_days = merged_vle.groupby(keys_activity)['date'].nunique().reset_index()
    n_days.rename(columns={'date': 'n_days'}, inplace=True)
    
    avg_clicks = merged_vle.groupby(keys_activity)['sum_click'].mean().reset_index()
    avg_clicks.rename(columns={'sum_click': 'avg_sum_clicks'}, inplace=True)
    
    # 合并天数和点击数数据
    vle_activity = n_days.merge(avg_clicks, on=keys_activity, how='inner')
    
    # 透视表：将活动类型转为列
    vle_pivot = vle_activity.set_index(keys_activity).unstack('activity_type').reset_index()
    vle_pivot.columns = ['_'.join(str(c) for c in col if c != '').strip('_') for col in vle_pivot.columns]
    
    # 按学生聚合：总的学习天数和平均点击数
    total_n_days = merged_vle.groupby(keys_student)['date'].nunique().reset_index()
    total_n_days.rename(columns={'date': 'total_n_days'}, inplace=True)
    
    total_avg_clicks = merged_vle.groupby(keys_student)['sum_click'].mean().reset_index()
    total_avg_clicks.rename(columns={'sum_click': 'avg_total_clicks'}, inplace=True)
    
    # 合并总计数据
    vle_total = total_n_days.merge(total_avg_clicks, on=keys_student, how='inner')
    
    # 最终合并
    vle_final = vle_pivot.merge(vle_total, on=keys_student, how='inner')
    
    # 填充缺失值
    vle_final = vle_final.fillna(0)
    
    _LOG.info(f"VLE数据处理完成，特征维度: {vle_final.shape}")
    return vle_final


def create_master_dataframe(data_dict, target_courses=None):
    """
    创建用于建模的主数据框
    
    Args:
        data_dict: 原始数据字典
        target_courses: 目标课程列表，None表示使用所有课程
        
    Returns:
        合并后的主数据框
    """
    _LOG.info("开始创建主数据框...")
    
    # 获取核心数据表
    student_info = data_dict['student_info'].copy()
    student_vle = data_dict['student_vle'].copy()
    student_registration = data_dict['student_registration'].copy()
    vle = data_dict['vle'].copy()
    student_assessment = data_dict['student_assessment'].copy()
    assessments = data_dict['assessments'].copy()
    
    # 筛选目标课程
    if target_courses:
        _LOG.info(f"筛选课程: {target_courses}")
        student_info = student_info[student_info['code_module'].isin(target_courses)]
        student_vle = student_vle[student_vle['code_module'].isin(target_courses)]
        student_registration = student_registration[student_registration['code_module'].isin(target_courses)]
        vle = vle[vle['code_module'].isin(target_courses)]
        student_assessment = student_assessment[student_assessment['code_module'].isin(target_courses)]  # 需确保有 code_module
        assessments = assessments[assessments['code_module'].isin(target_courses)]
    
    # 合并学生基本信息和注册信息
    master_df = student_info.merge(
        student_registration,
        on=['code_module', 'code_presentation', 'id_student'],
        how='inner'
    )
    
    # 处理和合并VLE数据
    vle_features = prep_vle_data(student_vle, vle, 'rq1')
    master_df = master_df.merge(
        vle_features,
        on=['code_module', 'code_presentation', 'id_student'],
        how='inner'
    )
    
    # 计算最终得分（仅当前成绩）
    assessment_data = student_assessment.merge(
        assessments,
        on='id_assessment',
        how='left'
    )
    current_scores = assessment_data[assessment_data['is_banked'] == 0].groupby(
        ['code_module', 'code_presentation', 'id_student']
    ).apply(lambda x: (x['score'] * x['weight']).sum() / 100 
    ).reset_index(name='final_score_current')
    
    # 计算银行化比例
    banked_count = assessment_data[assessment_data['is_banked'] == 1].groupby(
        ['code_module', 'code_presentation', 'id_student']
    ).size().reset_index(name='banked_count')
    total_count = assessment_data.groupby(
        ['code_module', 'code_presentation', 'id_student']
    ).size().reset_index(name='total_count')
    banked_ratio = banked_count.merge(total_count, on=['code_module', 'code_presentation', 'id_student'], how='left')
    banked_ratio['banked_ratio'] = banked_ratio['banked_count'] / banked_ratio['total_count'].replace(0, 1)
    banked_ratio = banked_ratio.fillna({'banked_ratio': 0})
    
    # 合并到 master_df
    master_df = master_df.merge(current_scores, on=['code_module', 'code_presentation', 'id_student'], how='left').fillna({'final_score_current': 0})
    master_df = master_df.merge(banked_ratio[['code_module', 'code_presentation', 'id_student', 'banked_ratio']], 
                               on=['code_module', 'code_presentation', 'id_student'], 
                               how='left').fillna({'banked_ratio': 0})
    
    # 创建目标变量
    master_df['at_risk'] = master_df['final_result'].isin(['Fail', 'Withdrawn']).astype(int)
    
    _LOG.info(f"主数据框创建完成，形状: {master_df.shape}")
    _LOG.info(f"学业困难学生比例: {master_df['at_risk'].mean():.3f}")
    _LOG.info(f"当前最终得分平均值: {master_df['final_score_current'].mean():.2f}")
    _LOG.info(f"银行化比例平均值: {master_df['banked_ratio'].mean():.2f}")
    
    return master_df


def run_initial_eda(data_dict):
    """运行初步探索性数据分析"""
    _LOG.info("开始初步EDA...")
    
    # 创建输出目录
    create_directories()
    
    # 生成数据概况报告
    loader = OULADDataLoader()
    loader.data_dict = data_dict
    summary_df = loader.get_data_summary()
    
    # 保存概况报告
    save_dataframe(summary_df, "raw_data_summary")
    
    # 打印关键信息
    print("\n" + "="*80)
    print("OULAD 数据集概况")
    print("="*80)
    print(summary_df.to_string(index=False))
    
    # 分析每个表的详细信息
    for name, df in data_dict.items():
        print_dataframe_info(df, name)
        
        # 保存缺失值分析
        missing_df = calculate_missing_percentage(df)
        save_dataframe(missing_df, f"missing_analysis_{name}")
    
    _LOG.info("初步EDA完成")
    return summary_df


def run_etl(target_courses=None):
    """
    执行完整的ETL流程
    
    Args:
        target_courses: 目标课程列表
        
    Returns:
        处理后的主数据框
    """
    _LOG.info("开始ETL流程...")
    
    # 1. 加载数据
    loader = OULADDataLoader()
    data_dict = loader.load_all_data()
    
    # 2. 初步EDA
    summary_df = run_initial_eda(data_dict)
    
    # 3. 创建主数据框
    master_df = create_master_dataframe(data_dict, target_courses)
    
    # 4. 保存结果
    save_dataframe(master_df, "master_dataframe_raw")
    save_dataframe(summary_df, "etl_summary")
    
    _LOG.info("ETL流程完成")
    return master_df, data_dict


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行ETL
    master_df, data_dict = run_etl()
    print(f"\n主数据框形状: {master_df.shape}")
    print(f"前5行数据:\n{master_df.head()}")
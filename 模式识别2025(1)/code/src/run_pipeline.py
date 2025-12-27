#!/usr/bin/env python3
"""
OULAD数据分析主流程
整合ETL、数据清洗、EDA和建模的完整分析流程
"""

# 设置matplotlib后端，避免Tkinter错误
import matplotlib
matplotlib.use('Agg')

import logging
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import os
import sys
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modeling_random_forest import RandomForestModeler
from src.modeling_logistic_regression import LogisticRegressionModeler
from src.modeling_kmeans import KMeansModeler
from src.modeling_neural_network import NeuralNetworkModeler
from src.modeling_svm import SVMModeler
from src.modeling_em import EMModeler
from src.modeling_decision_tree import DecisionTreeModeler

# 导入自定义模块
from utils import setup_logging, create_directories, setup_chinese_fonts
from etl import run_etl
from data_cleaning import clean_data
from eda import run_eda

def load_yaml_config(config_path):
    """加载YAML配置文件"""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # 返回默认配置
        return {
            'data': {'target_column': 'at_risk', 'test_size': 0.2, 'target_courses': None},
            'modules': {'enable_eda': True, 'enable_modeling': True},
            'modeling': {'models_to_run': ['logistic_regression']},
            'cleaning': {
                'missing_strategy': 'auto',
                'outlier_method': 'percentile', 
                'outlier_threshold': 0.98,
                'enable_feature_engineering': True,
                'enable_encoding': True,
                'enable_normalization': False
            }
        }

def get_config_value(config, path, default=None):
    """从配置字典中获取值，支持点分隔路径"""
    keys = path.split('.')
    value = config
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def print_config_summary(config, config_path=None):
    """打印配置摘要"""
    print("=" * 60)
    print("配置摘要")
    print("=" * 60)
    print(f"配置文件: {config_path or '默认配置'}")
    print(f"数据目录: {get_config_value(config, 'data.data_dir', '../anonymisedData/anonymisedData')}")
    print(f"目标变量: {get_config_value(config, 'data.target_column')}")
    print(f"测试集比例: {get_config_value(config, 'data.test_size')}")
    print(f"启用EDA: {get_config_value(config, 'modules.enable_eda')}")
    print(f"启用建模: {get_config_value(config, 'modules.enable_modeling')}")
    print(f"要运行的模型: {', '.join(get_config_value(config, 'modeling.models_to_run', []))}")
    print("=" * 60)

def main(args, config):
    """主执行函数"""

    setup_chinese_fonts()
    logger = setup_logging(level=logging.INFO)
    logger.info("开始OULAD数据分析流程...")
    start_time = datetime.now()
    try:
        create_directories()
        # ========================================
        # 第1步: ETL - 数据加载和初步处理
        # ========================================
        logger.info("=" * 80)
        logger.info("第1步: ETL - 数据加载和初步处理")
        logger.info("=" * 80)
        etl_start = datetime.now()
        master_df, data_dict = run_etl(target_courses=get_config_value(config, 'data.target_courses'))
        etl_time = datetime.now() - etl_start
        logger.info(f"ETL完成，耗时: {etl_time}")
        # ========================================
        # 第2步: 数据清洗
        # ========================================
        logger.info("=" * 80)
        logger.info("第2步: 数据清洗")
        logger.info("=" * 80)
        cleaning_start = datetime.now()
        cleaning_config = {
            'missing_strategy': get_config_value(config, 'cleaning.missing_strategy'),
            'outlier_method': get_config_value(config, 'cleaning.outlier_method'),
            'outlier_threshold': get_config_value(config, 'cleaning.outlier_threshold'),
            'enable_feature_engineering': get_config_value(config, 'cleaning.enable_feature_engineering'),
            'enable_encoding': get_config_value(config, 'cleaning.enable_encoding'),
            'enable_normalization': get_config_value(config, 'cleaning.enable_normalization')
        }
        cleaned_df, cleaning_report, cleaner = clean_data(master_df, cleaning_config)
        cleaning_time = datetime.now() - cleaning_start
        logger.info(f"数据清洗完成，耗时: {cleaning_time}")
        # ========================================
        # 第3步: 探索性数据分析 (EDA)
        # ========================================
        eda_report = None
        analyzer = None
        if get_config_value(config, 'modules.enable_eda'):
            logger.info("=" * 80)
            logger.info("第3步: 探索性数据分析 (EDA)")
            logger.info("=" * 80)
            eda_start = datetime.now()
            analyzer, eda_report = run_eda(cleaned_df, target_column=get_config_value(config, 'data.target_column'))
            eda_time = datetime.now() - eda_start
            logger.info(f"EDA完成，耗时: {eda_time}")
        # ========================================
        # 第4步: 机器学习建模
        # ========================================
        if get_config_value(config, 'modules.enable_modeling'):
            logger.info("=" * 80)
            logger.info("第4步: 机器学习建模")
            logger.info("=" * 80)
            modeling_start = datetime.now()
            df = cleaned_df.copy()
            target_column = get_config_value(config, 'data.target_column', 'at_risk')
            test_size = get_config_value(config, 'data.test_size', 0.2)
            exclude_cols = ['id_student', 'final_result', target_column]
            feature_cols = [col for col in df.columns if col not in exclude_cols]
            X = df[feature_cols]
            y = df[target_column]
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
            # 从配置获取要运行的模型
            models_to_run = config.get('modeling', {}).get('models_to_run', ['logistic_regression'])
            logger.info(f"将运行的模型: {models_to_run}")
            
            model_results = {}
            
            for model_name in models_to_run:
                logger.info(f"\n{'='*50}")
                logger.info(f"开始训练模型: {model_name}")
                logger.info(f"{'='*50}")
                
                try:
                    # 根据模型名称选择相应的模型类
                    if model_name == 'random_forest':
                        from modeling_random_forest import RandomForestModeler
                        modeler = RandomForestModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'logistic_regression':
                        from modeling_logistic_regression import LogisticRegressionModeler
                        modeler = LogisticRegressionModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'kmeans':
                        from modeling_kmeans import KMeansModeler
                        modeler = KMeansModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'neural_network':
                        from modeling_neural_network import NeuralNetworkModeler
                        modeler = NeuralNetworkModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'svm':
                        from modeling_svm import SVMModeler
                        modeler = SVMModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'em':
                        from modeling_em import EMModeler
                        modeler = EMModeler(target_column=target_column, config=config)
                    
                    elif model_name == 'decision_tree':
                        from modeling_decision_tree import DecisionTreeModeler
                        modeler = DecisionTreeModeler(target_column=target_column, config=config)
                    
                    else:
                        logger.error(f"未知的模型名称: {model_name}")
                        continue
                    
                    # 训练模型
                    logger.info(f"开始训练 {model_name} 模型...")
                    if model_name in ['kmeans', 'em']:
                        # K-Means和EM是无监督学习，不需要y_train
                        model = modeler.train(X_train)
                    else:
                        model = modeler.train(X_train, y_train)
                    
                    # 评估模型
                    logger.info(f"开始评估 {model_name} 模型...")
                    if model_name in ['kmeans', 'em']:
                        # K-Means和EM评估时传入真实标签用于分析
                        metrics = modeler.evaluate(X_test, y_test, feature_names=feature_cols)
                    else:
                        metrics = modeler.evaluate(X_test, y_test, feature_names=feature_cols)
                    
                    # 添加性能指标
                    performance_metrics = modeler.get_performance_metrics()
                    metrics.update(performance_metrics)
                    
                    model_results[model_name] = metrics
                    
                    # 保存模型指标到CSV
                    metrics_df = pd.DataFrame([metrics])
                    metrics_path = Path("outputs") / f"model_metrics_{model_name}.csv"
                    metrics_df.to_csv(metrics_path, index=False)
                    logger.info(f"模型 {model_name} 指标已保存: {metrics_path}")
                    
                    # 保存模型
                    if config.get('output', {}).get('save_models', True):
                        model_path = modeler.save_model()
                        logger.info(f"模型 {model_name} 已保存: {model_path}")
                    
                    # 检查图片生成情况
                    if hasattr(modeler, 'plot_dir'):
                        logger.info(f"模型 {model_name} 图片保存目录: {modeler.plot_dir}")
                        if hasattr(modeler.plot_dir, 'exists') and modeler.plot_dir.exists():
                            plot_files = list(modeler.plot_dir.glob('*.png'))
                            logger.info(f"模型 {model_name} 生成了 {len(plot_files)} 个图片文件")
                            for plot_file in plot_files:
                                logger.info(f"  - {plot_file.name}")
                        else:
                            logger.warning(f"模型 {model_name} 图片目录不存在或为空")
                    
                    # 检查SHAP图片生成情况
                    if hasattr(modeler, 'shap_dir'):
                        logger.info(f"模型 {model_name} SHAP图片保存目录: {modeler.shap_dir}")
                        if hasattr(modeler.shap_dir, 'exists') and modeler.shap_dir.exists():
                            shap_files = list(modeler.shap_dir.glob('*.png'))
                            logger.info(f"模型 {model_name} 生成了 {len(shap_files)} 个SHAP图片文件")
                            for shap_file in shap_files:
                                logger.info(f"  - {shap_file.name}")
                        else:
                            logger.warning(f"模型 {model_name} SHAP图片目录不存在或为空")
                    
                    logger.info(f"模型 {model_name} 训练和评估完成!")
                    
                except Exception as e:
                    logger.error(f"模型 {model_name} 训练失败: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息:\n{traceback.format_exc()}")
                    continue
            
            modeling_time = datetime.now() - modeling_start
            logger.info(f"建模完成，耗时: {modeling_time}")
        total_time = datetime.now() - start_time
        logger.info("=" * 80)
        logger.info("分析流程完成总结")
        logger.info("=" * 80)
        logger.info(f"总耗时: {total_time}")
        logger.info(f"原始数据形状: {master_df.shape}")
        logger.info(f"清洗后数据形状: {cleaned_df.shape}")
        logger.info(f"数据减少: {((master_df.shape[0] - cleaned_df.shape[0]) / master_df.shape[0] * 100):.1f}%")
        # 生成最终报告
        final_report = generate_final_report(
            master_df, cleaned_df, cleaning_report,
            eda_report if get_config_value(config, 'modules.enable_eda') else None,
            total_time
        )
        # 保存最终报告
        report_path = Path("outputs") / "final_analysis_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(final_report)
        logger.info(f"最终报告已保存: {report_path}")
        print("\n" + "="*80)
        print("🎉 OULAD数据分析流程全部完成！")
        print("="*80)
        print(f"📊 数据概况: {master_df.shape[0]:,} 学生记录")
        print(f"🧹 数据清洗: 保留 {cleaned_df.shape[0]:,} 记录")
        print(f"📈 输出目录: outputs/")
        print(f"📋 最终报告: {report_path}")
        print(f"⏱️  总耗时: {total_time}")
        print("="*80)
        return {
            'master_df': master_df,
            'cleaned_df': cleaned_df,
            'cleaning_report': cleaning_report,
            'eda_analyzer': analyzer if get_config_value(config, 'modules.enable_eda') else None,
            'final_report': final_report
        }
    except Exception as e:
        logger.error(f"分析流程出错: {str(e)}")
        raise

def generate_final_report(master_df, cleaned_df, cleaning_report, eda_report, total_time):
    """生成最终综合报告"""
    
    report = []
    report.append("="*100)
    report.append("OULAD 数据集 - 完整分析报告")
    report.append("="*100)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"分析耗时: {total_time}")
    report.append("")
    
    # 1. 执行摘要
    report.append("🎯 执行摘要")
    report.append("-" * 50)
    report.append(f"• 分析了 {master_df.shape[0]:,} 名学生的学习数据")
    report.append(f"• 包含 {master_df.shape[1]} 个特征维度")
    report.append(f"• 数据清洗后保留 {cleaned_df.shape[0]:,} 条记录")
    
    at_risk_rate = cleaned_df['at_risk'].mean() if 'at_risk' in cleaned_df.columns else 0
    report.append(f"• 学业困难学生比例: {at_risk_rate:.1%}")
    report.append("")
    
    # 2. 数据处理总结
    report.append("📊 数据处理总结")
    report.append("-" * 50)
    report.append(f"原始数据: {master_df.shape[0]:,} 行 × {master_df.shape[1]} 列")
    report.append(f"清洗后: {cleaned_df.shape[0]:,} 行 × {cleaned_df.shape[1]} 列")
    
    reduction_rate = ((master_df.shape[0] - cleaned_df.shape[0]) / master_df.shape[0]) * 100
    report.append(f"数据减少: {reduction_rate:.1f}%")
    
    if cleaning_report['steps']:
        report.append("清洗步骤:")
        for step in cleaning_report['steps']:
            report.append(f"  • {step['step']}")
    report.append("")
    
    # 3. EDA发现
    if eda_report:
        report.append("🔍 关键发现 (EDA)")
        report.append("-" * 50)
        # 提取EDA报告的关键部分
        eda_lines = eda_report.split('\n')
        in_findings = False
        for line in eda_lines:
            if "关键发现" in line:
                in_findings = True
                continue
            if in_findings and line.startswith("• "):
                report.append(line)
            elif in_findings and line.startswith("="*40):
                break
        report.append("")
    
    # 5. 建议与结论
    report.append("💡 建议与结论")
    report.append("-" * 50)
    
    if at_risk_rate > 0.5:
        report.append("• 高风险学生占多数，建议实施全面的学业支持计划")
    else:
        report.append("• 成功学生占多数，但需要建立早期预警系统")
    
    report.append("• 学生的VLE学习行为是预测学业成功的重要指标")
    report.append("• 建议加强对学习行为数据的收集和分析")
    report.append("• 可以基于预测模型开发个性化干预措施")
    report.append("• 定期更新模型以保持预测准确性")
    
    report.append("")
    report.append("="*100)
    
    return "\n".join(report)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="OULAD数据分析流程")
    parser.add_argument('--config', type=str, default=None, help='YAML配置文件路径')
    parser.add_argument('--model', type=str, default=None, help='只运行指定模型，如 random_forest/logistic_regression/kmeans/neural_network')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    # 加载配置
    config = load_yaml_config(args.config)
    # 命令行参数覆盖YAML
    if args.model:
        config['modeling']['models_to_run'] = [args.model]
    # 打印配置摘要
    print_config_summary(config, args.config)
    # 运行主流程
    results = main(args, config) 
#!/usr/bin/env python3
"""
决策边界生成脚本
独立脚本，用于为已训练的模型生成决策边界图
"""

import sys
import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import argparse
from datetime import datetime

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置matplotlib后端
import matplotlib
matplotlib.use('Agg')

from src.decision_boundary_visualizer import DecisionBoundaryVisualizer, create_decision_boundary_for_model
from src.utils import setup_chinese_fonts, setup_logging

def load_model_and_data():
    """
    加载已训练的模型和数据
    
    Returns:
        models: 已训练的模型字典
        X: 特征矩阵
        y: 标签
        feature_names: 特征名称
    """
    # 加载清洗后的数据并按照训练时的方式分割
    try:
        cleaned_data_path = "outputs/dataframes/master_dataframe_cleaned.csv"
        if not os.path.exists(cleaned_data_path):
            raise FileNotFoundError(f"未找到清洗后的数据文件: {cleaned_data_path}")
        
        df = pd.read_csv(cleaned_data_path)
        print(f"成功加载完整数据: {df.shape}")
        
        # 准备特征和标签（与训练时完全一致）
        target_column = 'at_risk'
        exclude_cols = ['id_student', 'final_result', target_column]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X_full = df[feature_cols]
        y_full = df[target_column]
        
        # 使用与训练时相同的数据分割
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_full, y_full, 
            test_size=0.2, 
            random_state=42,
            stratify=y_full
        )
        
        print(f"使用训练数据绘制决策边界")
        print(f"训练集形状: {X_train.shape}")
        print(f"特征数量: {len(feature_cols)}")
        print(f"训练样本数量: {len(X_train)}")
        
        X = X_train
        y = y_train
        feature_names = feature_cols
        
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None, None, None, None
    
    # 加载已训练的模型
    models = {}
    model_dir = Path("models")
    
    if not model_dir.exists():
        print(f"模型目录不存在: {model_dir}")
        return None, None, None, None
    
    # 定义模型文件映射
    model_files = {
        "Logistic Regression": ["logistic_regression.joblib", "logisticregressionmodeler.joblib"],
        "Random Forest": ["random_forest.joblib", "randomforestmodeler.joblib"],
        "SVM": ["svmmodeler.joblib"],
        "Decision Tree": ["decisiontreemodeler.joblib"],
        "Neural Network": ["neuralnetworkmodeler.joblib"]
    }
    
    for model_name, filenames in model_files.items():
        model_loaded = False
        for filename in filenames:
            model_path = model_dir / filename
            if model_path.exists():
                try:
                    loaded_data = joblib.load(model_path)
                    
                    # 处理不同的模型保存格式
                    if isinstance(loaded_data, dict):
                        if 'model' in loaded_data:
                            model = loaded_data['model']
                        else:
                            print(f"字典格式模型但无'model'键: {model_name}")
                            continue
                    else:
                        model = loaded_data
                    
                    # 验证模型对象是否有fit方法
                    if hasattr(model, 'fit') and hasattr(model, 'predict'):
                        models[model_name] = model
                        print(f"成功加载模型: {model_name} (from {filename})")
                        model_loaded = True
                        break
                    else:
                        print(f"加载的对象不是有效的机器学习模型: {model_name}")
                        
                except Exception as e:
                    print(f"加载模型失败 {model_name} (from {filename}): {e}")
        
        if not model_loaded:
            print(f"无法加载模型: {model_name}")
    
    if not models:
        print("没有找到可用的模型文件")
        return None, None, None, None
    
    return models, X, y, feature_names

def generate_individual_boundaries(models, X, y, feature_names, output_dir="outputs/plots/decision_boundaries"):
    """
    为每个模型生成独立的决策边界图
    """
    print(f"\n生成独立决策边界图")
    print(f"=" * 60)
    
    visualizer = DecisionBoundaryVisualizer(output_dir)
    
    for model_name, model in models.items():
        print(f"\n正在为 {model_name} 生成决策边界图...")
        
        try:
            filepath = visualizer.plot_decision_boundary(
                model=model,
                X=X,
                y=y,
                feature_names=feature_names,
                model_name=model_name,
                feature_selection_method='random_forest'
            )
            
            if filepath:
                print(f"成功生成: {filepath}")
            else:
                print(f"生成失败: {model_name}")
                
        except Exception as e:
            print(f"生成 {model_name} 决策边界图失败: {e}")

def generate_comparison_plot(models, X, y, feature_names, output_dir="outputs/plots/decision_boundaries"):
    """
    生成多个模型的对比图
    """
    print(f"\n生成决策边界对比图")
    print(f"=" * 60)
    
    if len(models) < 2:
        print("需要至少2个模型才能生成对比图")
        return
    
    visualizer = DecisionBoundaryVisualizer(output_dir)
    
    # 准备模型数据
    models_data = []
    for model_name, model in models.items():
        models_data.append((model, X, y, feature_names, model_name))
    
    try:
        print(f"正在生成 {len(models)} 个模型的对比图...")
        
        filepath = visualizer.create_comparison_plot(
            models_data,
            title="Machine Learning Models - Decision Boundary Comparison"
        )
        
        if filepath:
            print(f"成功生成对比图: {filepath}")
        else:
            print("生成对比图失败")
            
    except Exception as e:
        print(f"生成对比图失败: {e}")

def generate_pca_boundaries(models, X, y, feature_names, output_dir="outputs/plots/decision_boundaries"):
    """
    使用PCA降维生成决策边界图
    """
    print(f"\n生成PCA降维决策边界图")
    print(f"=" * 60)
    
    visualizer = DecisionBoundaryVisualizer(output_dir)
    
    for model_name, model in models.items():
        print(f"\n正在为 {model_name} 生成PCA决策边界图...")
        
        try:
            filepath = visualizer.plot_decision_boundary(
                model=model,
                X=X,
                y=y,
                feature_names=feature_names,
                model_name=f"{model_name}_PCA",
                title=f"{model_name} - PCA Decision Boundary",
                dimensionality_reduction='pca'
            )
            
            if filepath:
                print(f"成功生成: {filepath}")
            else:
                print(f"生成失败: {model_name}")
                
        except Exception as e:
            print(f"生成 {model_name} PCA决策边界图失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成决策边界图")
    parser.add_argument("--mode", choices=["individual", "comparison", "pca", "all"], 
                       default="all", help="生成模式")
    parser.add_argument("--output-dir", default="outputs/plots/decision_boundaries", 
                       help="输出目录")
    parser.add_argument("--models", nargs="+", 
                       help="指定要生成的模型 (如果不指定则生成所有可用模型)")
    
    args = parser.parse_args()
    
    # 设置日志和中文字体
    setup_chinese_fonts()
    logger = setup_logging(level=logging.INFO)
    
    print(f"=" * 80)
    print("决策边界生成器")
    print(f"=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"生成模式: {args.mode}")
    print(f"输出目录: {args.output_dir}")
    
    # 加载模型和数据
    print(f"\n加载模型和数据")
    print(f"=" * 60)
    
    models, X, y, feature_names = load_model_and_data()
    
    if models is None:
        print("加载失败，退出程序")
        return
    
    # 过滤指定的模型
    if args.models:
        filtered_models = {name: model for name, model in models.items() 
                         if name in args.models}
        if not filtered_models:
            print(f"未找到指定的模型: {args.models}")
            return
        models = filtered_models
    
    print(f"\n将处理的模型: {list(models.keys())}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据模式生成决策边界图
    if args.mode == "individual" or args.mode == "all":
        generate_individual_boundaries(models, X, y, feature_names, args.output_dir)
    
    if args.mode == "comparison" or args.mode == "all":
        generate_comparison_plot(models, X, y, feature_names, args.output_dir)
    
    if args.mode == "pca" or args.mode == "all":
        generate_pca_boundaries(models, X, y, feature_names, args.output_dir)
    
    print(f"\n=" * 80)
    print("决策边界生成完成")
    print(f"=" * 80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {args.output_dir}")

if __name__ == "__main__":
    main() 
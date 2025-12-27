"""
高级分析模块
包含SHAP可解释性分析、AutoML自动化参数优化和交互式可视化
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# SHAP和AutoML相关
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    
try:
    from auto_ml import Predictor
    AUTOML_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False

try:
    from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from scipy.stats import randint, uniform
    ADVANCED_ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False

from utils import save_dataframe, PLOTS_PATH, get_numeric_columns
from modeling import OULADModeler

_LOG = logging.getLogger(__name__)


class SHAPAnalyzer:
    """SHAP可解释性分析器"""
    
    def __init__(self, model, X_data, feature_names):
        self.model = model
        self.X_data = X_data
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None
        
        # 创建输出目录
        self.plot_dir = Path(PLOTS_PATH) / "shap_analysis"
        self.plot_dir.mkdir(parents=True, exist_ok=True)
    
    def create_explainer(self):
        """创建SHAP解释器"""
        if not SHAP_AVAILABLE:
            _LOG.warning("SHAP库未安装，跳过SHAP分析")
            return False
        
        try:
            _LOG.info("创建SHAP解释器...")
            
            # 对于随机森林使用TreeExplainer
            if hasattr(self.model, 'estimators_'):
                self.explainer = shap.TreeExplainer(self.model)
            else:
                # 对于其他模型使用KernelExplainer（采样以提高速度）
                background = shap.sample(self.X_data, 100)
                self.explainer = shap.KernelExplainer(self.model.predict_proba, background)
            
            return True
            
        except Exception as e:
            _LOG.error(f"创建SHAP解释器失败: {e}")
            return False
    
    def calculate_shap_values(self, sample_size=500):
        """计算SHAP值"""
        if not self.explainer:
            return False
        
        try:
            _LOG.info("计算SHAP值...")
            
            # 使用样本数据提高效率
            if len(self.X_data) > sample_size:
                sample_indices = np.random.choice(len(self.X_data), sample_size, replace=False)
                X_sample = self.X_data.iloc[sample_indices]
            else:
                X_sample = self.X_data
            
            # 计算SHAP值
            shap_values = self.explainer.shap_values(X_sample)
            
            # 如果是二分类，取正类的SHAP值
            if isinstance(shap_values, list) and len(shap_values) == 2:
                self.shap_values = shap_values[1]
            else:
                self.shap_values = shap_values
            
            self.X_sample = X_sample
            return True
            
        except Exception as e:
            _LOG.error(f"计算SHAP值失败: {e}")
            return False
    
    def plot_shap_summary(self):
        """绘制SHAP摘要图"""
        if self.shap_values is None:
            return
        
        try:
            _LOG.info("生成SHAP摘要图...")
            
            # 摘要图（蜂群图）
            plt.figure(figsize=(10, 8))
            shap.summary_plot(self.shap_values, self.X_sample, 
                            feature_names=self.feature_names, show=False)
            plt.tight_layout()
            plt.savefig(self.plot_dir / "shap_summary.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            # 条形图（特征重要性）
            plt.figure(figsize=(10, 8))
            shap.summary_plot(self.shap_values, self.X_sample, 
                            feature_names=self.feature_names, 
                            plot_type="bar", show=False)
            plt.tight_layout()
            plt.savefig(self.plot_dir / "shap_importance.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            _LOG.info("SHAP图表已保存")
            
        except Exception as e:
            _LOG.error(f"生成SHAP图表失败: {e}")
    
    def get_feature_importance_df(self):
        """获取基于SHAP的特征重要性DataFrame"""
        if self.shap_values is None:
            return None
        
        try:
            # 计算每个特征的平均绝对SHAP值
            mean_shap_values = np.abs(self.shap_values).mean(axis=0)
            
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'shap_importance': mean_shap_values
            }).sort_values('shap_importance', ascending=False)
            
            return importance_df
            
        except Exception as e:
            _LOG.error(f"计算SHAP特征重要性失败: {e}")
            return None


class AutoMLOptimizer:
    """AutoML自动化参数优化器"""
    
    def __init__(self):
        self.best_models = {}
        self.optimization_results = {}
        
    def optimize_hyperparameters(self, X_train, y_train, X_test, y_test, 
                                search_type='random', cv_folds=5, n_iter=30):
        """使用GridSearch或RandomizedSearch优化超参数"""
        _LOG.info(f"开始AutoML超参数优化 ({search_type})...")
        
        # 定义模型和参数空间
        models_params = {
            'RandomForest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'n_estimators': randint(50, 300) if search_type == 'random' else [100, 200, 300],
                    'max_depth': randint(5, 30) if search_type == 'random' else [10, 20, None],
                    'min_samples_split': randint(2, 20) if search_type == 'random' else [2, 5, 10],
                    'min_samples_leaf': randint(1, 10) if search_type == 'random' else [1, 2, 4],
                    'max_features': ['sqrt', 'log2', None]
                }
            },
            'GradientBoosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': randint(50, 200) if search_type == 'random' else [100, 150, 200],
                    'learning_rate': uniform(0.01, 0.29) if search_type == 'random' else [0.01, 0.1, 0.2],
                    'max_depth': randint(3, 8) if search_type == 'random' else [3, 5, 7],
                    'min_samples_split': randint(2, 20) if search_type == 'random' else [2, 5, 10]
                }
            },
            'LogisticRegression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {
                    'C': uniform(0.1, 99.9) if search_type == 'random' else [0.1, 1, 10, 100],
                    'solver': ['liblinear', 'lbfgs'],
                    'penalty': ['l1', 'l2'] if search_type == 'grid' else ['l2']
                }
            }
        }
        
        results = {}
        
        for model_name, config in models_params.items():
            try:
                _LOG.info(f"优化 {model_name}...")
                
                if search_type == 'grid':
                    search = GridSearchCV(
                        config['model'], 
                        config['params'],
                        cv=cv_folds,
                        scoring='f1',
                        n_jobs=-1
                    )
                else:  # random search
                    search = RandomizedSearchCV(
                        config['model'], 
                        config['params'],
                        n_iter=n_iter,
                        cv=cv_folds,
                        scoring='f1',
                        n_jobs=-1,
                        random_state=42
                    )
                
                # 训练
                search.fit(X_train, y_train)
                
                # 评估最佳模型
                best_model = search.best_estimator_
                train_score = search.best_score_
                
                # 预测测试集
                y_pred = best_model.predict(X_test)
                from sklearn.metrics import f1_score
                test_score = f1_score(y_test, y_pred)
                
                results[model_name] = {
                    'best_model': best_model,
                    'best_params': search.best_params_,
                    'best_cv_score': train_score,
                    'test_f1_score': test_score
                }
                
                _LOG.info(f"{model_name} - CV F1: {train_score:.4f}, 测试F1: {test_score:.4f}")
                
            except Exception as e:
                _LOG.error(f"优化 {model_name} 失败: {e}")
        
        self.optimization_results = results
        return results
    
    def compare_optimized_models(self):
        """比较优化后的模型性能"""
        if not self.optimization_results:
            return None
        
        comparison_data = []
        for model_name, results in self.optimization_results.items():
            comparison_data.append({
                'Model': model_name,
                'CV_F1_Score': results['best_cv_score'],
                'Test_F1_Score': results['test_f1_score'],
                'Best_Params': str(results['best_params'])
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('Test_F1_Score', ascending=False)
        
        # 保存结果
        save_dataframe(comparison_df, "automl_comparison")
        
        return comparison_df


class InteractiveVisualizer:
    """交互式可视化器（Plotly + Streamlit）"""
    
    def __init__(self, df, target_column='at_risk'):
        self.df = df
        self.target_column = target_column
        self.numeric_cols = get_numeric_columns(df)
        self.plot_dir = Path(PLOTS_PATH) / "interactive"
        self.plot_dir.mkdir(parents=True, exist_ok=True)
    
    def create_interactive_dashboard(self):
        """创建交互式仪表板HTML文件"""
        _LOG.info("创建交互式可视化...")
        
        # 1. 目标变量分布饼图
        target_counts = self.df[self.target_column].value_counts()
        fig_pie = px.pie(
            values=target_counts.values,
            names=target_counts.index,
            title=f'{self.target_column} 分布'
        )
        fig_pie.write_html(self.plot_dir / "target_distribution.html")
        
        # 2. 数值变量分布直方图
        for col in self.numeric_cols[:6]:  # 限制前6个变量
            fig_hist = px.histogram(
                self.df, 
                x=col, 
                color=self.target_column,
                title=f'{col} 分布（按{self.target_column}分组）',
                marginal="box"
            )
            fig_hist.write_html(self.plot_dir / f"hist_{col}.html")
        
        # 3. 相关性热力图
        if len(self.numeric_cols) > 1:
            corr_matrix = self.df[self.numeric_cols].corr()
            fig_heatmap = px.imshow(
                corr_matrix,
                title='变量相关性热力图',
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            fig_heatmap.write_html(self.plot_dir / "correlation_heatmap.html")
        
        # 4. 3D散点图
        if len(self.numeric_cols) >= 3:
            fig_3d = px.scatter_3d(
                self.df.sample(min(1000, len(self.df))),  # 采样以提高性能
                x=self.numeric_cols[0],
                y=self.numeric_cols[1],
                z=self.numeric_cols[2],
                color=self.target_column,
                title='3D特征空间分布'
            )
            fig_3d.write_html(self.plot_dir / "scatter_3d.html")
        
        # 5. 并行坐标图
        if len(self.numeric_cols) >= 4:
            fig_parallel = px.parallel_coordinates(
                self.df.sample(min(500, len(self.df))),
                dimensions=self.numeric_cols[:6],
                color=self.target_column,
                title='并行坐标图'
            )
            fig_parallel.write_html(self.plot_dir / "parallel_coordinates.html")
        
        # 6. 创建综合仪表板
        self._create_comprehensive_dashboard()
        
        _LOG.info(f"交互式可视化已保存到: {self.plot_dir}")
    
    def _create_comprehensive_dashboard(self):
        """创建综合仪表板"""
        # 创建子图布局
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['目标变量分布', '数值变量箱线图', '相关性分析', '特征重要性'],
            specs=[[{"type": "pie"}, {"type": "box"}],
                   [{"type": "heatmap"}, {"type": "bar"}]]
        )
        
        # 1. 目标变量分布
        target_counts = self.df[self.target_column].value_counts()
        fig.add_trace(
            go.Pie(labels=target_counts.index, values=target_counts.values),
            row=1, col=1
        )
        
        # 2. 箱线图（第一个数值变量）
        if self.numeric_cols:
            for i, target_val in enumerate(self.df[self.target_column].unique()):
                data = self.df[self.df[self.target_column] == target_val][self.numeric_cols[0]]
                fig.add_trace(
                    go.Box(y=data, name=f'{self.target_column}={target_val}'),
                    row=1, col=2
                )
        
        # 3. 相关性热力图
        if len(self.numeric_cols) > 1:
            corr_matrix = self.df[self.numeric_cols[:5]].corr()  # 限制大小
            fig.add_trace(
                go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu_r'
                ),
                row=2, col=1
            )
        
        # 4. 模拟特征重要性（如果有的话）
        if hasattr(self, 'feature_importance'):
            top_features = self.feature_importance.head(10)
            fig.add_trace(
                go.Bar(x=top_features['importance'], y=top_features['feature'], orientation='h'),
                row=2, col=2
            )
        
        fig.update_layout(height=800, title_text="OULAD数据分析综合仪表板")
        fig.write_html(self.plot_dir / "comprehensive_dashboard.html")
    
    def create_streamlit_app(self):
        """创建Streamlit应用代码"""
        streamlit_code = '''
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="OULAD数据分析", layout="wide")

st.title("🎓 OULAD学生学业风险分析仪表板")
st.markdown("---")

# 侧边栏
st.sidebar.header("📊 分析选项")

# 加载数据
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("outputs/dataframes/master_dataframe_cleaned.csv")
        return df
    except FileNotFoundError:
        st.error("数据文件未找到，请先运行分析流程")
        return None

df = load_data()

if df is not None:
    # 基本信息
    st.header("📈 数据概况")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("学生总数", f"{len(df):,}")
    with col2:
        if 'at_risk' in df.columns:
            at_risk_rate = df['at_risk'].mean()
            st.metric("学业困难率", f"{at_risk_rate:.1%}")
        else:
            st.metric("学业困难率", "未知")
    with col3:
        st.metric("特征数量", df.shape[1])
    with col4:
        complete_rate = (1 - df.isnull().any(axis=1).mean())
        st.metric("数据完整率", f"{complete_rate:.1%}")
    
    # 目标变量分布
    if 'at_risk' in df.columns:
        st.header("🎯 学业风险分布")
        col1, col2 = st.columns(2)
        
        with col1:
            risk_counts = df['at_risk'].value_counts()
            fig_pie = px.pie(
                values=risk_counts.values, 
                names=['成功', '困难'] if len(risk_counts) == 2 else risk_counts.index,
                title='学业风险分布'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                x=['成功', '困难'] if len(risk_counts) == 2 else risk_counts.index, 
                y=risk_counts.values,
                title='学业风险统计'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # 交互式分析
    st.header("🔍 交互式分析")
    
    # 选择变量进行分析
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if 'at_risk' in numeric_cols:
        numeric_cols.remove('at_risk')
    
    if numeric_cols:
        selected_var = st.selectbox("选择要分析的数值变量", numeric_cols)
        
        if selected_var and 'at_risk' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(
                    df, x=selected_var, color='at_risk',
                    title=f'{selected_var} 分布（按学业风险分组）',
                    nbins=30
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                fig_box = px.box(
                    df, x='at_risk', y=selected_var,
                    title=f'{selected_var} 箱线图'
                )
                st.plotly_chart(fig_box, use_container_width=True)
    
    # 相关性分析
    if len(numeric_cols) > 1:
        st.header("🔗 变量相关性")
        corr_cols = st.multiselect("选择要分析相关性的变量", numeric_cols, default=numeric_cols[:5])
        
        if len(corr_cols) > 1:
            corr_matrix = df[corr_cols].corr()
            fig_heatmap = px.imshow(
                corr_matrix, 
                title='相关性热力图',
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 数据统计
    st.header("📊 数据统计")
    if st.checkbox("显示描述性统计"):
        st.dataframe(df.describe())
    
    # 数据预览
    st.header("📋 数据预览")
    n_rows = st.slider("显示行数", 10, 100, 50)
    st.dataframe(df.head(n_rows))
    
    # 下载数据
    st.header("💾 数据下载")
    if st.button("下载清洗后的数据"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="下载CSV文件",
            data=csv,
            file_name="oulad_cleaned_data.csv",
            mime="text/csv"
        )

else:
    st.warning("请先运行数据分析流程生成数据文件")
    st.info("运行命令: `python run_analysis.py`")
'''
        
        # 保存Streamlit应用代码
        with open(self.plot_dir / "streamlit_app.py", 'w', encoding='utf-8') as f:
            f.write(streamlit_code)
        
        _LOG.info("Streamlit应用代码已保存")


def create_streamlit_app():
    """创建Streamlit应用代码"""
    streamlit_code = '''
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="OULAD数据分析", layout="wide")

st.title("🎓 OULAD学生学业风险分析仪表板")
st.markdown("---")

# 侧边栏
st.sidebar.header("📊 分析选项")

# 加载数据
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("outputs/dataframes/master_dataframe_cleaned.csv")
        return df
    except FileNotFoundError:
        st.error("数据文件未找到，请先运行分析流程")
        return None

df = load_data()

if df is not None:
    # 基本信息
    st.header("📈 数据概况")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("学生总数", f"{len(df):,}")
    with col2:
        if 'at_risk' in df.columns:
            at_risk_rate = df['at_risk'].mean()
            st.metric("学业困难率", f"{at_risk_rate:.1%}")
        else:
            st.metric("学业困难率", "未知")
    with col3:
        st.metric("特征数量", df.shape[1])
    with col4:
        complete_rate = (1 - df.isnull().any(axis=1).mean())
        st.metric("数据完整率", f"{complete_rate:.1%}")
    
    # 目标变量分布
    if 'at_risk' in df.columns:
        st.header("🎯 学业风险分布")
        col1, col2 = st.columns(2)
        
        with col1:
            risk_counts = df['at_risk'].value_counts()
            fig_pie = px.pie(
                values=risk_counts.values, 
                names=['成功', '困难'] if len(risk_counts) == 2 else risk_counts.index,
                title='学业风险分布'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                x=['成功', '困难'] if len(risk_counts) == 2 else risk_counts.index, 
                y=risk_counts.values,
                title='学业风险统计'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # 交互式分析
    st.header("🔍 交互式分析")
    
    # 选择变量进行分析
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if 'at_risk' in numeric_cols:
        numeric_cols.remove('at_risk')
    
    if numeric_cols:
        selected_var = st.selectbox("选择要分析的数值变量", numeric_cols)
        
        if selected_var and 'at_risk' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(
                    df, x=selected_var, color='at_risk',
                    title=f'{selected_var} 分布（按学业风险分组）',
                    nbins=30
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                fig_box = px.box(
                    df, x='at_risk', y=selected_var,
                    title=f'{selected_var} 箱线图'
                )
                st.plotly_chart(fig_box, use_container_width=True)
    
    # 相关性分析
    if len(numeric_cols) > 1:
        st.header("🔗 变量相关性")
        corr_cols = st.multiselect("选择要分析相关性的变量", numeric_cols, default=numeric_cols[:5])
        
        if len(corr_cols) > 1:
            corr_matrix = df[corr_cols].corr()
            fig_heatmap = px.imshow(
                corr_matrix, 
                title='相关性热力图',
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 数据统计
    st.header("📊 数据统计")
    if st.checkbox("显示描述性统计"):
        st.dataframe(df.describe())
    
    # 数据预览
    st.header("📋 数据预览")
    n_rows = st.slider("显示行数", 10, 100, 50)
    st.dataframe(df.head(n_rows))
    
    # 下载数据
    st.header("💾 数据下载")
    if st.button("下载清洗后的数据"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="下载CSV文件",
            data=csv,
            file_name="oulad_cleaned_data.csv",
            mime="text/csv"
        )

else:
    st.warning("请先运行数据分析流程生成数据文件")
    st.info("运行命令: `python run_analysis.py`")
'''
    
    # 保存Streamlit应用代码
    app_dir = Path(PLOTS_PATH) / "interactive"
    app_dir.mkdir(parents=True, exist_ok=True)
    
    with open(app_dir / "streamlit_app.py", 'w', encoding='utf-8') as f:
        f.write(streamlit_code)
    
    # 创建运行脚本
    run_script = '''#!/bin/bash
# 运行Streamlit应用
echo "启动OULAD数据分析仪表板..."
echo "请在浏览器中访问 http://localhost:8501"
streamlit run outputs/plots/interactive/streamlit_app.py
'''
    
    with open(app_dir / "run_dashboard.sh", 'w', encoding='utf-8') as f:
        f.write(run_script)
    
    # Windows版本
    run_script_win = '''@echo off
echo 启动OULAD数据分析仪表板...
echo 请在浏览器中访问 http://localhost:8501
streamlit run outputs/plots/interactive/streamlit_app.py
'''
    
    with open(app_dir / "run_dashboard.bat", 'w', encoding='utf-8') as f:
        f.write(run_script_win)
    
    _LOG.info("Streamlit应用和运行脚本已保存")


def run_advanced_analysis(df, models_dict, X_test, y_test, feature_cols):
    """
    运行完整的高级分析
    
    Args:
        df: 数据框
        models_dict: 训练好的模型字典
        X_test: 测试特征
        y_test: 测试标签
        feature_cols: 特征列名
    """
    _LOG.info("开始高级分析...")
    
    results = {}
    
    # 1. SHAP分析
    if SHAP_AVAILABLE and 'random_forest' in models_dict:
        _LOG.info("运行SHAP可解释性分析...")
        
        try:
            shap_analyzer = SHAPAnalyzer(
                models_dict['random_forest'], 
                X_test, 
                feature_cols
            )
            
            if shap_analyzer.create_explainer():
                if shap_analyzer.calculate_shap_values():
                    shap_analyzer.plot_shap_summary()
                    
                    # 获取SHAP特征重要性
                    shap_importance = shap_analyzer.get_feature_importance_df()
                    if shap_importance is not None:
                        save_dataframe(shap_importance, "shap_feature_importance")
                        results['shap_importance'] = shap_importance
                        _LOG.info("SHAP分析完成")
        except Exception as e:
            _LOG.error(f"SHAP分析失败: {e}")
    
    # 2. AutoML优化
    _LOG.info("运行AutoML参数优化...")
    
    try:
        # 准备数据
        exclude_cols = ['id_student', 'final_result', 'at_risk']
        X_train_auto = df[[col for col in df.columns if col not in exclude_cols]]
        y_train_auto = df['at_risk']
        
        # 处理分类变量
        from sklearn.preprocessing import LabelEncoder
        label_encoders = {}
        for col in X_train_auto.columns:
            if X_train_auto[col].dtype == 'object':
                label_encoders[col] = LabelEncoder()
                X_train_auto[col] = label_encoders[col].fit_transform(X_train_auto[col].astype(str))
        
        # 填充缺失值
        X_train_auto = X_train_auto.fillna(X_train_auto.median())
        
        # 分割数据
        from sklearn.model_selection import train_test_split
        X_train_split, X_test_split, y_train_split, y_test_split = train_test_split(
            X_train_auto, y_train_auto, test_size=0.2, random_state=42, stratify=y_train_auto
        )
        
        automl = AutoMLOptimizer()
        optimization_results = automl.optimize_hyperparameters(
            X_train_split, y_train_split, X_test_split, y_test_split,
            search_type='random', n_iter=20
        )
        
        if optimization_results:
            comparison_df = automl.compare_optimized_models()
            results['automl_results'] = optimization_results
            results['automl_comparison'] = comparison_df
            _LOG.info("AutoML优化完成")
            
    except Exception as e:
        _LOG.error(f"AutoML优化失败: {e}")
    
    # 3. 交互式可视化
    _LOG.info("生成交互式可视化...")
    
    try:
        create_streamlit_app()
        results['streamlit_app'] = "已生成Streamlit应用"
        _LOG.info("交互式可视化完成")
        
    except Exception as e:
        _LOG.error(f"生成交互式可视化失败: {e}")
    
    _LOG.info("高级分析完成")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("高级分析模块已加载") 
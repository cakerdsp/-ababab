from scipy import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from sklearn.preprocessing import StandardScaler
def load_data(path):

    x=io.loadmat(path)

    ins_perclass,class_number,train_test_split = 11,15,9

    input_dim=x['fea'].shape[1]

    feat=x['fea'].reshape(-1,ins_perclass,input_dim)

    label=x['gnd'].reshape(-1,ins_perclass)

    train_data,test_data = feat[:,:train_test_split,:].reshape(-1,input_dim),feat[:,train_test_split:,:].reshape(-1,input_dim)

    train_label,test_label = label[:,:train_test_split].reshape(-1),label[:,train_test_split:].reshape(-1)
    # test_data : (test_num, input_dim)
    # test_label : (test_num,)
    # train_data : (train_num, input_dim)
    # train_label : (train_num,)
    # 每一行是一个样本
    scaler = StandardScaler()
    train_data = scaler.fit_transform(train_data)
    test_data = scaler.transform(test_data)

    print("the number of train data is ",train_data.shape[0])
    print("the number of test data is ",test_data.shape[0])
    print("the input dimension is ",input_dim)
    print("the number of class is ",class_number)
    print("the number of instance per class is ",ins_perclass)
    print("the number of class is ",class_number)
    return train_data,train_label,test_data,test_label


# 可视化降维结果的函数
def visualize_2d_data(X, y, title, method_name, ax=None):
    """可视化二维数据
    
    参数：
    X (ndarray): 形状为 (n_samples, 2) 的数据矩阵
    y (ndarray): 形状为 (n_samples,) 的标签向量
    title (str): 图表标题
    method_name (str): 降维方法名称
    ax (matplotlib.axes.Axes, optional): 指定绘图的Axes对象，如果为None则创建新的figure
    """
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 中文黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正确显示负号
    matplotlib.rcParams['font.size'] = 12               # 设置全局字体大小
    
    # 如果没有提供ax，则创建新的figure
    if ax is None:
        plt.figure(figsize=(12, 10))
        ax = plt.gca()
    
    # 获取唯一的类别标签
    unique_labels = np.unique(y)
    
    # 为每个类别分配不同的颜色 - 使用对比度更高的颜色方案
    colors = plt.cm.viridis(np.linspace(0, 1, len(unique_labels)))
    # 如果类别较多，可以使用tab20提供更多颜色
    if len(unique_labels) > 10:
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
    
    # 绘制每个类别的样本点 - 调整点的大小和透明度
    for i, label in enumerate(unique_labels):
        ax.scatter(X[y == label, 0], X[y == label, 1], 
                  color=colors[i], alpha=0.8, s=70, 
                  edgecolors='w', linewidths=0.5,
                  label=f'类别 {label}')
    
    # 设置标题和标签 - 调整字体大小和间距
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_xlabel(f'{method_name} 成分 1', fontsize=11, labelpad=10)
    ax.set_ylabel(f'{method_name} 成分 2', fontsize=11, labelpad=10)
    
    # 调整图例位置和样式，避免遮挡 - 完全移到图表外部
    if len(unique_labels) <= 15:  # 如果类别数量合理，显示图例
        ax.legend(loc='center left', frameon=True, fontsize=8, 
                  fancybox=True, framealpha=0.7, 
                  borderpad=1, ncol=1,
                  bbox_to_anchor=(1.08, 0.5), # 将图例完全放在图表外部右侧中间位置
                  markerscale=0.6) # 减小图例中的标记大小
    else:  # 如果类别太多，不显示图例
        ax.legend().set_visible(False)
    
    # 设置网格线
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # 调整轴刻度
    ax.tick_params(axis='both', which='major', labelsize=10)
    
    # 添加边框
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

# 添加特征向量可视化函数
def visualize_eigenvectors(components, title, n_components=8, img_shape=(64, 64)):
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 中文黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正确显示负号
    matplotlib.rcParams['font.size'] = 12               # 设置全局字体大小
    
    # 确保不超过可用的特征向量数量
    n_components = min(n_components, components.shape[0])
    
    # 创建图像网格 - 增加图像大小
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    # 显示每个特征向量
    for i in range(n_components):
        # 将特征向量重塑为图像形状
        eigenvector = components[i].reshape(img_shape)
        
        # 归一化到[0,1]范围以便显示
        eigenvector = (eigenvector - eigenvector.min()) / (eigenvector.max() - eigenvector.min())
        
        # 显示图像 - 添加边框使图像更清晰
        axes[i].imshow(eigenvector, cmap='gray')
        axes[i].set_title(f'特征向量 {i+1}', fontsize=14, pad=8)
        axes[i].axis('off')
        # 添加边框
        for spine in axes[i].spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.5)
            spine.set_edgecolor('gray')
    
    # 设置总标题
    plt.suptitle(title, fontsize=15, y=0.98)
    
    # 调整子图之间的间距 - 增加间距确保图像完全显示
    plt.tight_layout(pad=4.0, h_pad=3.5, w_pad=3.5)
    plt.subplots_adjust(top=0.92, wspace=0.5, hspace=0.5)  # 为总标题留出空间，增加子图间距


# 添加可视化降维维度与准确率关系的函数
def visualize_accuracy_vs_dimensions(dimensions, accuracies, title="降维维度与准确率关系"):
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 中文黑体
    matplotlib.rcParams['axes.unicode_minus'] = False    # 正确显示负号
    matplotlib.rcParams['font.size'] = 12               # 设置全局字体大小
    
    # 创建图形和坐标轴
    plt.figure(figsize=(12, 8))
    
    # 设置线条样式和标记
    line_styles = ['-o', '-s', '-^', '-d']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # 绘制每种方法的准确率曲线
    for i, (method, accs) in enumerate(accuracies.items()):
        plt.plot(dimensions, accs, line_styles[i % len(line_styles)], 
                 linewidth=2, markersize=8, label=method,
                 color=colors[i % len(colors)])
    
    # 设置图表标题和标签
    plt.title(title, fontsize=16, pad=15)
    plt.xlabel('降维维度', fontsize=14, labelpad=10)
    plt.ylabel('准确率', fontsize=14, labelpad=10)
    
    # 设置x轴刻度为整数
    plt.xticks(dimensions)
    
    # 设置y轴范围，从0开始以显示完整的准确率范围
    plt.ylim([0, 1.05])
    
    # 添加网格线
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 添加图例
    plt.legend(loc='lower right', fontsize=12, frameon=True, 
               fancybox=True, framealpha=0.8, borderpad=1)
    
    # 为每个数据点添加数值标签
    for method, accs in accuracies.items():
        for i, acc in enumerate(accs):
            plt.text(dimensions[i], acc + 0.01, f'{acc:.2%}', 
                     ha='center', va='bottom', fontsize=9)
    
    # 调整布局
    plt.tight_layout()
    
    return plt.gcf()  # 返回当前图形对象
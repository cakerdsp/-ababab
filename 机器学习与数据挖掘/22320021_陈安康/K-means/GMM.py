import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal
from scipy.optimize import linear_sum_assignment
import matplotlib.pyplot as plt
import random
import time
# from sklearn.decomposition import PCA
from PCA import PCA
# from sklearn.cluster import KMeans
from K_means import Kmeans
# 数据路径
train_file_path = r'C:\Users\86135\Desktop\机器学习与数据挖掘\K-means\material\mnist_train.csv'
test_file_path = r'C:\Users\86135\Desktop\机器学习与数据挖掘\K-means\material\mnist_test.csv'


def Standard(X):
    # 计算均值和标准差
    mean = X.mean(axis=0)  # 按列计算均值
    std = X.std(axis=0)    # 按列计算标准差

    # Z-score 标准化
    return (X - mean) / std

# 读出来的数据是一行一个样本
def csv2array():
    train_label = pd.read_csv(train_file_path, usecols = ['label'])
    train_label_array = train_label.to_numpy()

    train_X = pd.read_csv(train_file_path, usecols = lambda column: column != 'label')
    train_X_array = train_X.to_numpy()


    test_label = pd.read_csv(test_file_path, usecols = ['label'])
    test_label_array = test_label.to_numpy()

    test_X = pd.read_csv(test_file_path, usecols = lambda column: column != 'label')
    test_X_array = test_X.to_numpy()

    return train_label_array, train_X_array, test_label_array, test_X_array

def initialize_parameters(X, K, covariance_type='full',init_type='random',pca = 30):
    n_samples, n_features = X.shape
    # 初始化均值, 随机选择的K个值
    if init_type == 'random':
        means = X[np.random.choice(n_samples, K, replace=False), :]
    elif init_type == 'kmeans':
        k_means = Kmeans(init_type='random',n_components=pca)
        _,means = k_means.kmeans()

        # kmeans = KMeans(n_clusters=2, random_state=0)

        # # 拟合数据
        # kmeans.fit(X)

        # # 获取簇的中心（均值）
        # means = kmeans.cluster_centers_
    elif init_type == 'k++':
        centers = []
        # 随机选择第一个中心点
        centers.append(X[np.random.randint(X.shape[0])])
        for _ in range(1, K):
            # 选取其余点到目前选出来的中心的距离的最小值，组成这个distances矩阵
            distances = np.array([min(np.linalg.norm(x - center)**2 for center in centers) for x in X])
            # 将距离矩阵转化成概率矩阵，然后使用按概率分布加权随机抽样的方法来找到下一个中心，生成的采样点是随机的，概率越大，占的“采样空间”越大，越容易被选中
            probabilities = distances / distances.sum()
            cumulative_probs = probabilities.cumsum()
            r = np.random.rand()
            
            # 根据概率选择下一个中心
            next_center_index = np.where(cumulative_probs >= r)[0][0]
            centers.append(X[next_center_index])
        means = np.array(centers)

    covariances = []
    # 初始化协方差矩阵，计算的全部的样本的协方差矩阵，然后复制了K份，每份是一样的
    if covariance_type == 'full':
        # 使用数据的协方差矩阵进行初始化
        for _ in range(K):
            cov_matrix = np.cov(X.T) + np.eye(n_features) * 1e-6  # 确保协方差矩阵正定
            covariances.append(cov_matrix)
    elif covariance_type == 'diag':
        # 使用每个簇的方差进行初始化
        for _ in range(K):
            cov_matrix = np.diag(np.var(X, axis=0))  # 对角协方差矩阵
            covariances.append(cov_matrix)
    elif covariance_type == 'spherical':
        # 使用全体样本的方差进行初始化
        for _ in range(K):
            sigma2 = np.var(X)  # 均匀方差初始化
            cov_matrix = np.eye(n_features) * sigma2  # 球形协方差矩阵
            covariances.append(cov_matrix)

    # covariances = []
    # for k in range(K):
    #     # 随机从数据集中选择与该簇相关的样本
    #     cluster_points = X[np.random.choice(n_samples, size=n_samples//K, replace=False), :]
    #     cov_matrix = np.cov(cluster_points, rowvar=False) + np.eye(n_features) * 1e-6
    #     covariances.append(cov_matrix)

    # 初始化混合系数，这里初始化为1/k
    pis = np.ones(K) / K
    return means, covariances, pis


# 主要是求责任矩阵，这里的责任矩阵是N * K的
def e_step(X, means, covariances, pis):
    n_samples = X.shape[0]
    # 初始化责任矩阵
    responsibilities = np.zeros((n_samples, len(means)))
    # 使用 logpdf 避免溢出
    for k in range(len(means)):
        # 计算每个高斯分布的概率密度
        responsibilities[:, k] = pis[k] * multivariate_normal.pdf(X, mean=means[k], cov=covariances[k],allow_singular=True)
    # 归一化责任矩阵
    # responsibilities = np.exp(responsibilities)  # 将对数概率转换回普通概率
    responsibilities_sum = responsibilities.sum(axis=1, keepdims=True)
    responsibilities_sum = np.maximum(responsibilities_sum, 1e-40)  # 防止除以零
    responsibilities /= responsibilities_sum
    
    return responsibilities

def m_step(X, responsibilities, K,covariance_type='full'):
    n_samples, n_features = X.shape
    # 更新混合系数
    pis = responsibilities.sum(axis=0) / n_samples
    # 更新均值
    means = np.array([responsibilities[:, k].dot(X) / responsibilities[:, k].sum() for k in range(K)])
    # 更新协方差矩阵
    epsilon = 1e-8
    covariances = []
    for k in range(K):
        # N_k
        N_k = responsibilities[:, k].sum()
        if N_k > 0:
            # 如果该簇的责任和大于零，计算协方差
            # cov_matrix = np.cov(X, rowvar=False, aweights=responsibilities[:, k]) 
            # 初始化协方差矩阵
            if covariance_type == 'full':
            # 完全协方差矩阵
                D = X.shape[1]  # 特征数
                cov_matrix = np.zeros((D, D))
                for n in range(X.shape[0]):
                    diff = (X[n] - means[k]).reshape(-1, 1)
                    cov_matrix += responsibilities[n][k] * diff @ diff.T  # (D, 1) @ (1, D) -> (D, D)
                cov_matrix /= N_k 
            elif covariance_type == 'diag':
            # 对角协方差矩阵
                diff = X - means[k]  # 计算每个样本与均值的差
                weighted_diff_square = (responsibilities[:, k][:, np.newaxis] * (diff ** 2)).sum(axis=0)
                cov_diag = weighted_diff_square / N_k
                cov_matrix = np.diag(cov_diag)  # 仅保留对角元素
            elif covariance_type == 'spherical':
            # 球形协方差矩阵
                diff = X - means[k]
                weighted_diff_square = (responsibilities[:, k][:, np.newaxis] * (diff ** 2)).sum()
                sigma2 = weighted_diff_square / (N_k * X.shape[1])  # 平均方差
                cov_matrix = np.eye(X.shape[1]) * sigma2  # 球形协方差矩阵

        else:
            # 如果该簇的责任和为零，使用默认的协方差矩阵（单位矩阵）
            cov_matrix = np.eye(X.shape[1]) * epsilon
        covariances.append(cov_matrix)
    return means, covariances, pis

# 这就相当于是一个损失函数
# log_likelihoods 是 N * 1的
def log_likelihood(X, means, covariances, pis):
    n_samples = X.shape[0]
    log_likelihoods = np.zeros(n_samples)
    for k in range(len(means)):
        log_likelihoods += pis[k] * multivariate_normal.pdf(X, mean=means[k], cov=covariances[k],allow_singular=True)
    # 防止为0
    log_likelihoods = np.log(log_likelihoods + 1e-40)
    return -log_likelihoods.sum()





def EM_GMM(X, K, test_X, labels, max_iter=200, tol=1e-6,init_type = 'random', cov_type = 'full'):
    means, covariances, pis = initialize_parameters(X, K,init_type=init_type,covariance_type=cov_type)
    log_likelihoods = []
    acc = []
    num_epochs = 0
    for _ in range(max_iter):
        responsibilities = e_step(X, means, covariances, pis)
        means, covariances, pis = m_step(X, responsibilities, K,covariance_type=cov_type)
        ll = log_likelihood(X, means, covariances, pis)
        log_likelihoods.append(ll)

        acc.append(predict(test_X, means, covariances, pis,labels))
        num_epochs += 1
        print(f'[{num_epochs}]: [acc]: {acc[-1]} [loss]: {log_likelihoods[-1]}')
        # 如果不再改变
        if len(log_likelihoods) > 1 and np.abs(log_likelihoods[-1] - log_likelihoods[-2]) < tol:
            break
    return means, covariances, pis, responsibilities, log_likelihoods, acc, num_epochs

def map_labels(true_labels, predicted_labels):
    n_clusters = len(np.unique(predicted_labels))
    cost_matrix = np.zeros((n_clusters, n_clusters))
    for i in range(n_clusters):
        for j in range(n_clusters):
            cost_matrix[i, j] = -np.sum((true_labels == i) & (predicted_labels == j))
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    label_mapping = dict(zip(col_ind, row_ind))
    return np.array([label_mapping.get(label, -1) for label in predicted_labels])


def predict(X_test, means, covariances, pis,labels):
    # 计算责任矩阵
    n_samples = X_test.shape[0]
    responsibilities = np.zeros((n_samples, len(means)))
    for k in range(len(means)):
        responsibilities[:, k] = pis[k] * multivariate_normal.pdf(X_test, mean=means[k], cov=covariances[k],allow_singular=True)
    
    # 归一化责任矩阵
    responsibilities /= responsibilities.sum(axis=1, keepdims=True)
    
    # 获取每个样本的簇标签
    cluster_labels = np.argmax(responsibilities, axis=1)
    labels = labels.reshape(1,-1)
    cluster_labels = map_labels(labels,cluster_labels)
    return (np.sum(np.where(cluster_labels == labels, 1, 0)) / labels.shape[1]) * 100


def show(acc,loss,num_epochs,init_type,cov_type):
    plt.figure(1)
    label = f'{init_type}_{cov_type}'
    color1 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    plt.plot(range(num_epochs), loss, color=color1, label=f'loss_{label}')
    # color2 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    # plt.plot(range(num_epochs), loss_train, color=color2, label=)
    plt.title('Loss')  # 标题
    plt.xlabel('num_epochs')  # 横轴标签
    plt.ylabel('Loss')  # 纵轴标签
    # 显示图例
    plt.legend()
    plt.grid(True)


    plt.figure(2)
    color3 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    plt.plot(range(num_epochs), acc, color=color3, label=f'acc_{label}')
    plt.title('Acc')  # 标题
    plt.xlabel('num_epochs')  # 横轴标签
    plt.ylabel('Acc')  # 纵轴标签
    # 显示图例
    plt.legend()
    plt.grid(True)

# 示例数据

label,X,test_label,test_X = csv2array()
# X = X / 255
# X = Standard(X)
# test_X = Standard(X)
# 运行EM算法
K = 10
X = X/255
test_X = test_X/255
# 创建PCA对象，设置降维后的维度
pca = PCA(n_components=30)

# 训练PCA模型
pca.fit(X)

# 转换数据
X = pca.transform(X)

# 转换数据
test_X = pca.transform(test_X)


# X = Standard(X)
# test_X = Standard(test_X)

def main(init_type,cov_type):
    init_type = init_type
    cov_type = cov_type
    start_time = time.time()
    means, covariances, pis, responsibilities, log_likelihoods,acc, num_epochs = EM_GMM(X, K,test_X,test_label,init_type=init_type,cov_type=cov_type,max_iter= 80)
    end_time = time.time()
    print(f'{init_type}_{cov_type}: ',end_time - start_time,'s')
    show(acc,log_likelihoods,num_epochs,init_type=init_type,cov_type=cov_type)



main('random','full')
k_means = Kmeans(init_type='K++')
start_time = time.time()
k_means.kmeans()
end_time = time.time()
print('K-means: ',end_time - start_time,'s')
k_means.show()
plt.show()

# print(log_likelihoods)
# print("Means:", means)
# print("Covariances:", covariances)
# print("Pis:", pis)
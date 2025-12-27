import numpy as np
import matplotlib.pyplot as plt

class PCA:
    def __init__(self, n_components=None):
        self.n_components = n_components  # 降维后的维度
    
    def fit(self, X):
        # 数据标准化（训练集）
        self.mean = np.mean(X, axis=0)  # 存储训练集的均值，用于变换时的去中心化
        X = self._standardize(X)  # 使用训练集均值和标准差进行标准化
        
        # # 删除全0特征
        # non_zero_features = np.std(X, axis=0) != 0
        # X = X[:, non_zero_features]
        
        # 计算协方差矩阵
        cov_matrix = np.cov(X.T)  # 计算协方差矩阵，X.T是样本特征矩阵
        
        # 计算特征值和特征向量
        eigvals, eigvecs = np.linalg.eigh(cov_matrix)
        
        # 将特征值从大到小排序
        eigvals_sorted_idx = np.argsort(eigvals)[::-1]
        eigvals_sorted = eigvals[eigvals_sorted_idx]
        eigvecs_sorted = eigvecs[:, eigvals_sorted_idx]
        
        # 选择前n个主成分
        if self.n_components is not None:
            eigvecs_sorted = eigvecs_sorted[:, :self.n_components]
        
        # 存储特征值和特征向量
        self.eigvals = eigvals_sorted
        self.eigvecs = eigvecs_sorted
    
    def transform(self, X):

        # 数据标准化（测试集），使用训练集的均值和标准差
        # X = self._standardize(X, fit=False)
        
        # # 删除全0特征
        # non_zero_features = np.std(X, axis=0) != 0
        # X = X[:, non_zero_features]
        
        # 将数据投影到主成分上
        return np.dot(X, self.eigvecs)
    
    def _standardize(self, X, fit=True):

        if fit:
            # 训练集的标准化
            self.mean = np.mean(X, axis=0)
            self.std = np.std(X, axis=0)
            self.std[self.std == 0] = 1  # 防止标准差为零的列
        else:
            # 测试集的标准化，使用训练集的均值和标准差
            pass
        
        # 均值归零
        X_centered = X - self.mean
        
        # 方差归一化
        # X_standardized = X_centered / self.std
        
        return X_centered
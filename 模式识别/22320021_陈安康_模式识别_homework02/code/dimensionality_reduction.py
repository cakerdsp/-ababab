import numpy as np

class PCA:
    def __init__(self, n_components=None):
        self.n_components = n_components
        self.components_ = None  # 主成分（特征向量）
        self.mean_ = None        # 均值
        self.explained_variance_ = None         # 特征值
        self.explained_variance_ratio_ = None   # 特征值比例

    def fit(self, X):
        # 1. 去中心化
        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_
        n_samples = X.shape[0]

        # 2. 计算协方差矩阵
        cov_matrix = np.dot(X_centered.T, X_centered) / (n_samples - 1)

        # 3. 使用 SVD 分解协方差矩阵
        U, S, Vt = np.linalg.svd(cov_matrix)

        # 4. 选择前 n_components 个主成分
        if self.n_components is None:
            self.n_components = X.shape[1]

        self.components_ = U[:, :self.n_components].T  # 每一行为一个主成分
        self.explained_variance_ = S[:self.n_components]
        self.explained_variance_ratio_ = self.explained_variance_ / np.sum(S)

        return self

    def transform(self, X):
        # 5. 投影到主成分上
        X_centered = X - self.mean_
        return np.dot(X_centered, self.components_.T)

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

class LDA: 
    def __init__(self, n_components=None):
        self.n_components = n_components
        self.means_ = None  # 每个类别的均值向量
        self.priors_ = None  # 每个类别的先验概率
        self.components_ = None  # 投影矩阵
        self.classes_ = None  # 类别标签
        
    def fit(self, X, y):
        n_samples, n_features = X.shape
        
        # 1. 获取唯一的类别标签
        self.classes_, y_indices = np.unique(y, return_inverse=True)
        n_classes = len(self.classes_)
        
        # 2. 计算每个类别的均值向量和先验概率
        self.means_ = np.zeros((n_classes, n_features))
        self.priors_ = np.zeros(n_classes)
        
        for i, c in enumerate(self.classes_):
            X_c = X[y == c]
            self.means_[i] = np.mean(X_c, axis=0)
            self.priors_[i] = X_c.shape[0] / n_samples
        
        # 3. 计算类内散度矩阵 Sw
        Sw = np.zeros((n_features, n_features))
        for i, c in enumerate(self.classes_):
            X_c = X[y == c]
            X_centered = X_c - self.means_[i]
            Sw += np.dot(X_centered.T, X_centered)
        
        # 4. 计算类间散度矩阵 Sb
        overall_mean = np.mean(X, axis=0)
        Sb = np.zeros((n_features, n_features))
        for i in range(n_classes):
            n_c = np.sum(y == self.classes_[i])
            mean_diff = self.means_[i] - overall_mean
            Sb += n_c * np.outer(mean_diff, mean_diff)
        
        # 5. 计算 Sw^-1 * Sb 的特征值和特征向量
        # 为避免奇异性问题，可以添加一个小的正则化项
        Sw_reg = Sw + np.eye(n_features) * 1e-4
        
        # 求解广义特征值问题
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(np.linalg.inv(Sw_reg).dot(Sb))
        except np.linalg.LinAlgError:
            # 如果矩阵不可逆，使用伪逆
            Sw_inv = np.linalg.pinv(Sw_reg)
            eigenvalues, eigenvectors = np.linalg.eigh(Sw_inv.dot(Sb))
        
        # 6. 特征值和特征向量按降序排序
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # 7. 选择前n_components个特征向量
        if self.n_components is None:
            self.n_components = min(n_features, n_classes - 1)
        else:
            self.n_components = min(self.n_components, n_classes - 1)
        
        self.components_ = eigenvectors[:, :self.n_components].T
        
        return self
    
    def transform(self, X):
        return np.dot(X, self.components_.T)
    
    def fit_transform(self, X, y):
        self.fit(X, y)
        return self.transform(X)
import numpy as np
from collections import Counter

class KNNClassifier:
    def __init__(self, n_neighbors=5, metric='euclidean'):
        self.n_neighbors = n_neighbors
        self.metric = metric
        
        # 训练数据
        self.X_train = None
        self.y_train = None

    def fit(self, X_train, y_train):
        self.X_train = np.asarray(X_train)
        self.y_train = np.asarray(y_train)
        
        if self.X_train.shape[0] != self.y_train.shape[0]:
            raise ValueError("特征和标签样本数量不一致")
        
        return self

    def _compute_distances(self, x):
        if self.metric == 'euclidean':
            return np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
        elif self.metric == 'manhattan':
            return np.sum(np.abs(self.X_train - x), axis=1)
        else:
            raise ValueError("不支持的度量方式")

    def predict(self, X_test):
        X_test = np.asarray(X_test)
        if X_test.ndim == 1:
            X_test = X_test.reshape(1, -1)
            
        predictions = []
        for x in X_test:
            distances = self._compute_distances(x)
            k_indices = np.argsort(distances)[:self.n_neighbors]
            k_nearest_labels = self.y_train[k_indices]
            most_common = Counter(k_nearest_labels).most_common(1)
            predictions.append(most_common[0][0])
        
        return np.array(predictions)
        
    def accuracy(self, y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        
        if y_true.shape != y_pred.shape:
            raise ValueError("真实标签和预测标签的形状不一致")
            
        # 计算准确率：正确预测的样本数 / 总样本数
        return np.mean(y_true == y_pred)


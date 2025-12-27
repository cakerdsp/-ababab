import numpy as np
from sklearn.svm import SVC

class SVMClassifier:
    def __init__(self, C=1.0, kernel='rbf', gamma='scale'):
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        
        # 创建SVM模型
        self.model = SVC(C=self.C, kernel=self.kernel, gamma=self.gamma)
        
    def fit(self, X_train, y_train):
        X_train = np.asarray(X_train)
        y_train = np.asarray(y_train)
        
        if X_train.shape[0] != y_train.shape[0]:
            raise ValueError("特征和标签样本数量不一致")
        
        self.model.fit(X_train, y_train)
        return self
    
    def predict(self, X_test):
        X_test = np.asarray(X_test)
        return self.model.predict(X_test)
    
    def accuracy(self, y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        
        if y_true.shape != y_pred.shape:
            raise ValueError("真实标签和预测标签的形状不一致")
            
        # 计算准确率：正确预测的样本数 / 总样本数
        return np.mean(y_true == y_pred)
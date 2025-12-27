import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
import random
import time
from scipy.optimize import linear_sum_assignment
# from sklearn.decomposition import PCA
from PCA import PCA
# 数据路径
train_file_path = r'C:\Users\86135\Desktop\机器学习与数据挖掘\K-means\material\mnist_train.csv'
test_file_path = r'C:\Users\86135\Desktop\机器学习与数据挖掘\K-means\material\mnist_test.csv'


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


def Standard(X):
    # 计算均值和标准差
    mean = X.mean(axis=0)  # 按列计算均值
    std = X.std(axis=0)    # 按列计算标准差

    # Z-score 标准化
    return (X - mean) / std

class Kmeans:
    def __init__(self,init_type,n_components = 30):
        self.train_label_array, self.train_X_array, self.test_label_array, self.test_X_array = csv2array()
        self.train_X_array = self.train_X_array / 255

        self.test_X_array = self.test_X_array / 255
        self.pca = PCA(n_components=n_components)
        self.pca.fit(self.train_X_array)
        self.init_type = init_type

        # 转换数据
        self.train_X_array = self.pca.transform(self.train_X_array)

        # 转换数据
        self.test_X_array = self.pca.transform(self.test_X_array)


        # self.train_X_array = Standard(self.train_X_array)
        # self.test_X_array = Standard(self.test_X_array)
        self.k = 10


    def distance_based_method(self):
 
        # Step 1: 随机选择第一个中心
        centers = [self.train_X_array[np.random.randint(self.train_X_array.shape[0])]]
        
        for _ in range(1, self.k):
            # Step 2: 计算每个点到当前已选中心的最小距离
            distances = np.array([min(np.linalg.norm(point - center)**2 for center in centers) for point in self.train_X_array])
            
            # Step 3: 选择距离最大的点
            next_center = self.train_X_array[np.argmax(distances)]
            centers.append(next_center)
            
        self.centroids = np.array(centers)

    def initialize_centroids(self):
        
        indices = np.random.choice(self.train_X_array.shape[0], self.k, replace=False)
        self.centroids = self.train_X_array[indices]


    def K_means_plus_plus(self):
        centers = []
        # 随机选择第一个中心点
        centers.append(self.train_X_array[np.random.randint(self.train_X_array.shape[0])])
        
        for _ in range(1, self.k):
            # 选取其余点到目前选出来的中心的距离的最小值，组成这个distances矩阵
            distances = np.array([min(np.linalg.norm(x - center)**2 for center in centers) for x in self.train_X_array])
            # 将距离矩阵转化成概率矩阵，然后使用按概率分布加权随机抽样的方法来找到下一个中心，生成的采样点是随机的，概率越大，占的“采样空间”越大，越容易被选中
            probabilities = distances / distances.sum()
            cumulative_probs = probabilities.cumsum()
            r = np.random.rand()
            
            # 根据概率选择下一个中心
            next_center_index = np.where(cumulative_probs >= r)[0][0]
            centers.append(self.train_X_array[next_center_index])
            
        self.centroids = np.array(centers)
    
    def compute_distances(self,X):
    
        distances = np.zeros((X.shape[0], len(self.centroids)))
        for i, centroid in enumerate(self.centroids):
            distances[:, i] = np.linalg.norm(X - centroid, axis=1)
        return distances
        
    
    def assign_clusters(self,distances):
      
        return np.argmin(distances, axis=1)
    
    def update_centroids(self):
        
        tmp = np.copy(self.centroids)
        for i in range(self.k):
            self.centroids[i, :] = self.train_X_array[self.labels == i].mean(axis=0)
        if np.all(tmp == self.centroids):
            return True
        else:
            return False

    def getloss(self):
        return np.min(self.distances,axis = 1).sum()

    
    def kmeans(self, max_iters=200):
       
        if self.init_type == 'random':
            self.initialize_centroids()
        elif self.init_type == 'distance_based':
            self.distance_based_method()
        elif self.init_type == 'K++':
            self.K_means_plus_plus()
        self.loss = []
        self.acc = []
        self.num_epochs = 0
        for _ in range(max_iters):
            self.distances = self.compute_distances(self.train_X_array)
            self.labels = self.assign_clusters(self.distances)
            self.loss.append(self.getloss())
            # 如果质心不再变化，则提前停止迭代
            self.acc.append(self.test())
            self.num_epochs += 1
            print(f'[{self.num_epochs}]: [acc]: {self.acc[-1]} [loss]: {self.loss[-1]}')
            if self.update_centroids():
                break
        return self.labels, self.centroids

    def test(self):
        distances = self.compute_distances(self.test_X_array)
        labels = self.assign_clusters(distances)
        self.test_label_array = self.test_label_array.reshape(1, -1)
        # self.labels = self.labels.reshape(self.labels.shape[0],1)
        labels = self.map_labels(self.test_label_array,labels)
        # self.labels = self.labels.reshape(self.labels.shape[0],1)
        return (np.sum(np.where(labels == self.test_label_array, 1, 0)) / self.test_label_array.shape[1]) * 100

    def map_labels(self,true_labels, predicted_labels):
        n_clusters = len(np.unique(predicted_labels))
        cost_matrix = np.zeros((n_clusters, n_clusters))
        for i in range(n_clusters):
            for j in range(n_clusters):
                cost_matrix[i, j] = -np.sum((true_labels == i) & (predicted_labels == j))
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        label_mapping = dict(zip(col_ind, row_ind))
        return np.array([label_mapping[label] for label in predicted_labels])


    def show(self):
        plt.figure(1)
        label = f'{self.init_type}'
        color1 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        plt.plot(range(self.num_epochs), self.loss, color=color1, label=label)
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
        plt.plot(range(self.num_epochs), self.acc, color=color3, label=label)
        plt.title('Acc')  # 标题
        plt.xlabel('num_epochs')  # 横轴标签
        plt.ylabel('Acc')  # 纵轴标签
        # 显示图例
        plt.legend()
        plt.grid(True)











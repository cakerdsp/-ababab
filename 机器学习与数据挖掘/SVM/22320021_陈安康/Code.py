import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.svm import SVC
import random
import time
# 数据路径
train_file_path = r'C:\Users\86135\Desktop\python\机器学习与数据挖掘\SVM\mnist_01_train.csv'
test_file_path = r'C:\Users\86135\Desktop\python\机器学习与数据挖掘\SVM\mnist_01_test.csv'

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

class SVM:
    def __init__(self,kernel_,iterations = 1050):
        # 将csv文件中的数据转换为矩阵
        self.train_label_array, self.train_X_array, self.test_label_array, self.test_X_array = csv2array()

        self.train_X_array = self.train_X_array / 255

        self.test_X_array = self.test_X_array / 255
        self.model = SVC(kernel = kernel_, C = 1.0,max_iter = iterations)

    def fit(self):
        self.model.fit(self.train_X_array,self.train_label_array.ravel())

    def predict(self):
        self.pred_label = self.model.predict(self.test_X_array)
        return self.pred_label, self.test_label_array.ravel()
    
    def show(self,start_time,end_time):
        print("错误率:", (np.sum(np.bitwise_xor(self.pred_label,self.test_label_array.ravel())) / self.test_label_array.ravel().shape[0]) * 100, "运行时间：", end_time - start_time)



class Hinge_Loss:
    def __init__(self,lr = 0.2, iterations = 30):
        self.train_label_array, self.train_X_array, self.test_label_array, self.test_X_array = csv2array()
        # # 计算每列的均值和标准差
        # mean = np.mean(self.train_X_array, axis=0)  # axis=0 表示按列计算
        # std = np.std(self.train_X_array, axis=0)
        # std = np.where(std == 0, 1, std)
        # self.train_X_array = ( self.train_X_array - mean) / std

        # mean = np.mean(self.test_X_array, axis=0)  # axis=0 表示按列计算
        # std = np.std(self.test_X_array, axis=0)
        # std = np.where(std == 0, 1, std)
        # self.test_X_array = ( self.test_X_array - mean) / std


        # X_min = self.train_X_array.min(axis=0)  # 每列的最小值
        # X_max = self.train_X_array.max(axis=0)  # 每列的最大值
        # # 按照 Min-Max 归一化公式进行转换
        # self.train_X_array = (self.train_X_array - X_min) / (X_max - X_min)


        # X_min = self.test_X_array.min(axis=0)  # 每列的最小值
        # X_max = self.test_X_array.max(axis=0)  # 每列的最大值
        # # 按照 Min-Max 归一化公式进行转换
        # self.test_X_array = (self.test_X_array - X_min) / (X_max - X_min)
        self.train_X_array = self.train_X_array / 255


        # X_min = self.test_X_array.min(axis=0)  # 每列的最小值
        # X_max = self.test_X_array.max(axis=0)  # 每列的最大值
        # # 按照 Min-Max 归一化公式进行转换
        self.test_X_array = self.test_X_array / 255
        
        self.learning_rate = lr
        self.iterations = iterations
        self.weights = np.random.normal(loc=0, scale=0.01, size=(self.train_X_array.shape[1],1))
        # self.weights = np.random.rand(self.train_X_array.shape[1],1)
        self.b = np.random.rand()
        self.m = self.train_X_array.shape[0]
        self.loss_list = []
        # 正则化超参
        self.lambd = 0.01

        # print(self.train_X_array.shape, self.weights.shape)


    def hinge_loss(self,Z):
        self.y = np.where(self.train_label_array == 0, -1,self.train_label_array)
        return np.maximum(0, 1- self.y * Z)
        

    
    def fit(self):
        for i in range(self.iterations):
            Z = np.dot(self.train_X_array, self.weights) + self.b 
            # print('Z:')
            # print(Z.shape)
            self.loss = self.hinge_loss(Z)
            self.loss_list.append((( 1 / self.m ) * np.sum(self.loss) + 0.5 * self.lambd * np.dot(self.weights.T,self.weights))[0])
            dw = ( 1 / self.m ) * np.sum(np.where(self.loss > 0, -self.y * self.train_X_array, 0),axis = 0)
            dw = dw.reshape(-1, 1)
            # print('dw:')
            # print(dw.shape)
            db = ( 1 / self.m ) * np.sum(np.where(self.loss > 0, -self.y, 0),axis = 0)
            # print('db:')
            # print(db.shape)
            # 这里单独加入正则化项
            self.weights = self.weights - self.learning_rate * (dw + self.lambd * self.weights)
            self.b = self.b - self.learning_rate * db

    def predict(self):
        Z = np.dot(self.test_X_array, self.weights) + self.b 
        self.y_ = np.where(self.test_label_array == 0, -1,self.test_label_array)
        self.y_pred = np.where(Z > 0, 1, -1)
        return self.y_pred , self.y_

    def show(self,start_time, end_time):
        res = (np.sum(np.where(self.y_pred == self.y_, 0, 1)) / self.test_label_array.shape[0]) * 100
        print("Hinge_Loss 错误率：", res, "运行时间：", end_time - start_time)
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        plt.plot(range(self.iterations), self.loss_list, color=color, label=f'Hinge_Loss lr = {self.learning_rate}')
        # 添加标题和标签
        plt.title('Hinge_Loss')  # 标题
        plt.xlabel('Iteration')  # 横轴标签
        plt.ylabel('Loss')  # 纵轴标签

        # 显示图例
        plt.legend()

        # 显示图形

class Cross_encropy_Loss:
    def __init__(self,lr = 0.59, iterations = 30):
        self.train_label_array, self.train_X_array, self.test_label_array, self.test_X_array = csv2array()

        self.train_X_array = self.train_X_array / 255


        
        self.test_X_array = self.test_X_array / 255


        self.learning_rate = lr
        self.iterations = iterations
        self.weights = np.random.normal(loc=0, scale=0.01, size=(self.train_X_array.shape[1],1))
        # self.weights = np.random.rand(self.train_X_array.shape[1],1)

        self.b = np.random.rand()
        self.m = self.train_X_array.shape[0]
        # 正则化超参
        self.lambd = 0.01
        self.loss_list = []

        # print(self.train_X_array.shape, self.weights.shape)

    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))

    def Cross_encropy_loss(self,H):
        epsilon = 1e-15
        H = np.clip(H, epsilon, 1 - epsilon)
        self.loss_list.append((-np.mean(self.train_label_array * np.log(H) + (1 - self.train_label_array) * np.log(1 - H)) + 0.5 * self.lambd * np.dot(self.weights.T,self.weights))[0])
        

    
    def fit(self):
        for i in range(self.iterations):
            Z = np.dot(self.train_X_array, self.weights) + self.b 
            H = self.sigmoid(Z)
            self.Cross_encropy_loss(H)
            dw = ( 1 / self.m ) * np.dot(self.train_X_array.T, (H - self.train_label_array))
            dw = dw.reshape(-1, 1)
 
            db = ( 1 / self.m ) * np.sum(H - self.train_label_array)

            # 这里单独加入正则化项
            self.weights = self.weights - self.learning_rate * (dw + self.lambd * self.weights)
            self.b = self.b - self.learning_rate * db

    def predict(self):
        Z = np.dot(self.test_X_array, self.weights) + self.b 
        H = self.sigmoid(Z)
        self.y_pred = np.round(H)
        return self.y_pred, self.test_label_array

    def show(self,start_time, end_time):
        res2 = (np.sum(np.where(self.y_pred == self.test_label_array, 0, 1)) / self.test_label_array.shape[0]) * 100
        print("Cross_encropy_Loss 错误率：", res2, "运行时间：", end_time - start_time)
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        plt.plot(range(self.iterations), self.loss_list, color=color, label=f'Cross_encropy_Loss lr = {self.learning_rate}')
        # 添加标题和标签
        plt.title('Cross_encropy_Loss')  # 标题
        plt.xlabel('Iteration')  # 横轴标签
        plt.ylabel('Loss')  # 纵轴标签

        # 显示图例
        plt.legend()



Linear_SVM = SVM('linear')
start_time = time.time()
Linear_SVM.fit()
end_time = time.time()
Linear_SVM.predict()
Linear_SVM.show(start_time, end_time)

Rbf_SVM = SVM('rbf')
start_time = time.time()
Rbf_SVM.fit()
end_time = time.time()
Rbf_SVM.predict()
Rbf_SVM.show(start_time, end_time)

Hinge_Loss = Hinge_Loss(lr = 0.2, iterations = 30)
start_time = time.time()
Hinge_Loss.fit()
end_time = time.time()
y_pred, y = Hinge_Loss.predict()
Hinge_Loss.show(start_time, end_time)


C_Loss = Cross_encropy_Loss(lr = 0.59, iterations = 30)
start_time = time.time()
C_Loss.fit()
end_time = time.time()
y_pred_, y_ = C_Loss.predict()
C_Loss.show(start_time, end_time)
plt.show()



# 下面的代码是用来进行超参调试的
# 用来训练学习率的
# for i in np.arange(0.2, 0.31, 0.01):
#     Hinge_Loss_ = Hinge_Loss(lr = i, iterations = 10)
#     start_time = time.time()
#     Hinge_Loss_.fit()
#     end_time = time.time()
#     y_pred, y = Hinge_Loss_.predict()
#     Hinge_Loss_.show(start_time, end_time)

# for i in np.arange(0.5, 0.61, 0.01):
#     C_Loss = Cross_encropy_Loss(lr = i, iterations = 10)
#     start_time = time.time()
#     C_Loss.fit()
#     end_time = time.time()
#     y_pred_, y_ = C_Loss.predict()
#     C_Loss.show(start_time, end_time)
# plt.show()


# 用来训练迭代次数超参的
# y = []
# for i in range(10,100,10):
#     Hinge_Loss_ = Hinge_Loss(lr = 0.2, iterations = i)
#     start_time = time.time()
#     Hinge_Loss_.fit()
#     end_time = time.time()
#     y_pred_, y_ = Hinge_Loss_.predict()
#     # C_Loss = Cross_encropy_Loss(lr = 0.59, iterations = i)
#     # start_time = time.time()
#     # C_Loss.fit()
#     # end_time = time.time()
#     # y_pred_, y_ = C_Loss.predict()
#     res2 = (np.sum(np.where(y_pred_ == y_, 0, 1)) / y_.shape[0]) * 100
#     y.append(res2)
# plt.plot(range(100,1000,100), y, color='r', label='error rate')
# # 添加标题和标签
# plt.title('error rate - Iteration')  # 标题
# plt.xlabel('Iteration')  # 横轴标签
# plt.ylabel('error rate')  # 纵轴标签
# plt.show()


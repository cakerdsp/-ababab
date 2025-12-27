import numpy as np
import matplotlib.pyplot as plt


class solution():
    def __init__(self,filename):
        with open(filename,'r') as f:
            lines = f.readlines()
            # 丢掉表头
            lines.pop(0)
            self.size = len(lines)
            # 特征矩阵
            self.data = np.zeros((self.size,2))
            # 结果矩阵
            self.result = np.zeros((self.size,1))
            # 权重，分别表示w_age、w_salary、b,是三行一列的矩阵
            self.param = np.array([[1.0],[1.0],[1.0]])
            # 迭代次数
            self.n = 5000
            # 学习率
            self.learn_rate = 0.46
            self.loss_val = []
            # self.predict = []
            for j in range(self.size):
                # 这里要求分隔符是','才行！！！！！！！！！！！
                line_list = lines[j].strip().split(',')
                for i in range(2):
                    self.data[j][i] = int(line_list[i])
                self.result[j] = int(line_list[2])
            
            # 标准化
            self.standardization()
            # 归一化
            self.normalization()
            # 添加偏置项
            self.add_bias()
            

    def normalization(self):
        for col in range(2): 
            col_list = self.data[:,col]
            maxval = max(col_list)
            minval = min(col_list)
            self.data[:,col] = (col_list - minval) / (maxval - minval)
            

    def standardization(self):
        for col in range(2):
            col_list = self.data[:,col]
            mean = np.mean(col_list)
            std_dev = np.std(col_list)
            self.data[:,col] = (col_list - mean) / std_dev


    # 添加偏置项
    def add_bias(self):
        self.data = np.hstack((self.data, np.ones((self.data.shape[0], 1))))     


    # 逻辑函数
    def sigmoid(self,x):
        return 1 / (1 + np.exp(-x))


    # 训练参数用的，采用批量梯度下降
    def train(self):
        for i in range(self.n):
            y = self.sigmoid(np.dot(self.data, self.param))
            self.loss(y)
            for j in range(3):
                grad = np.dot(self.data[:,j].T,(y - self.result))
                self.param[j][0] = self.param[j][0] - self.learn_rate * (1 / self.size) * grad

    # 用来预测的
    def predict(self):
        # self.predict = np.round(self.sigmoid(np.dot(self.data, self.param)))
        predict = np.round(self.sigmoid(np.dot(self.data, self.param)))
        count = 0
        count2 = 0
        for i in range(self.size):
            if predict[i][0] == self.result[i][0]:
                count += 1
                if predict[i][0] == 1:
                    count2 += 1
        percent = float(count) / self.size
        a = sum(self.result)
        recall = count2 / a
        return predict, percent, recall

    # 求损失函数平均值，绘图用的
    def loss(self,y):
        self.loss_val.append(-np.mean(self.result * np.log(y) + (1 - self.result) * np.log(1 - y)))

   # 绘制loss曲线图
    def diagram_loss(self):
        plt.rcParams['font.family'] = 'SimHei'
        x = range(self.n)
        y = self.loss_val
        plt.figure()
        plt.plot(x,y)
        plt.title('误差和迭代次数')
        plt.xlabel('迭代次数')
        plt.ylabel('代价')


    #绘制决策边界图
    def diagram_db(self):
        plt.rcParams['font.family'] = 'SimHei'
        plt.figure()
        #绘制散点图
        color_map = {0 : 'r', 1 : 'b'}
        colors = [color_map[it[0]] for it in self.result.tolist()]
        plt.scatter(self.data[:,0], self.data[:,1], c = colors)

        # # z = np.zeros((self.size,self.size))
        # # for i in range(self.size):
        # #     for j in  range(self.size):
        # z = [predict[i][0] for i in range(self.size)]
        # plt.tricontourf(self.data[:,0], self.data[:,1], z, colors = 'k', alpha=0.1)  # 绘制等高线
        # plt.show()
        y = (-self.param[0] / self.param[1]) * self.data[:,0] - (self.param[2] / self.param[1])
        plt.plot(self.data[:,0], y, c = 'g')
        plt.title('预测分类')

if __name__ == "__main__":
    # 这里是用来确定最合适学习率的
    # x = np.arange(0,1,0.01)
    # y = []
    # for it in x:
        # 训练用的
        test = solution("lab7\\train.csv")
        test.train()

        # test.diagram_loss()
        # 预测用的
        pre = solution("lab7\data_all.csv")
        pre.param = test.param
        pred,perc, recall = pre.predict()
        # y.append(perc)

    # 学习率与预测准确率画图
    # print(max(y))
    # xy = zip(x,y)
    # print(max(xy, key = lambda pair: pair[1])[0])
    # plt.rcParams['font.family'] = 'SimHei'
    # plt.plot(x, y, c = 'b')
    # plt.title(f'迭代次数为{pre.n}')
    # plt.xlabel('学习率')
    # plt.ylabel('预测准确率')
    # plt.show()


        test.diagram_loss()
        print(perc)
        print(recall)
        pre.diagram_db()
        plt.show()
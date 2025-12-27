
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from model.softmax import LinearClassifier
import matplotlib.pyplot as plt
from model.MLP import MLP
from model.CNN import CNN
import time
import random
# 超参数
num_epochs = 100
batch_size = 512
lr = 0.001
print(torch.__version__)
print(torch.cuda.is_available())

# 数据加载函数
def load_data(dir):
    import pickle
    X_train = []
    Y_train = []
    for i in range(1, 6):
        with open(dir + r'/data_batch_' + str(i), 'rb') as fo:
            dict = pickle.load(fo, encoding='bytes')
        X_train.append(dict[b'data'])
        Y_train += dict[b'labels']
    X_train = np.concatenate(X_train, axis=0)

    with open(dir + r'/test_batch', 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    X_test = dict[b'data']
    Y_test = dict[b'labels']
    return X_train, Y_train, X_test, Y_test

# 加载数据
data_dir = r"C:\Users\86135\Desktop\python\机器学习与数据挖掘\CNN_MLP_softmax\data"  # 替换为你的CIFAR-10数据目录
X_train, Y_train, X_test, Y_test = load_data(data_dir)

# 转换为Tensor
X_train = torch.tensor(X_train, dtype=torch.float32)
Y_train = torch.tensor(Y_train, dtype=torch.long)
X_test = torch.tensor(X_test, dtype=torch.float32)
Y_test = torch.tensor(Y_test, dtype=torch.long)

# 数据归一化
X_train /= 255.0
X_test /= 255.0

# 构建 DataLoader
train_dataset = TensorDataset(X_train, Y_train)
test_dataset = TensorDataset(X_test, Y_test)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# softmax
input_dim = 32 * 32 * 3  # CIFAR-10 每个图片是32x32x3
num_classes = 10
model1 = LinearClassifier(input_dim, num_classes)
optimizer1 = optim.Adam(model1.parameters(), lr=lr)
# criterion1 = nn.CrossEntropyLoss()
# optimizer1 = optim.SGD(model1.parameters(), lr=lr)



# model2 = LinearClassifier(input_dim, num_classes)

# criterion2 = nn.CrossEntropyLoss()
# optimizer2 = optim.SGD(model2.parameters(), lr=lr, momentum=0.9)


# model3 = LinearClassifier(input_dim, num_classes)

# criterion3 = nn.CrossEntropyLoss()
# optimizer3 = optim.Adam(model3.parameters(), lr=lr, betas=(0.9, 0.999))

# # MLP
# # 模型超参数
input_dim = 32 * 32 * 3  # 每张图像的像素值总数
# # 只是隐藏层的规模
hidden_dim_list = [1024,512,256,128]
output_dim = 10  # CIFAR-10 有 10 个类别
# # 初始化模型
model2 = MLP(input_dim, hidden_dim_list, output_dim)

# criterion1 = nn.CrossEntropyLoss()
optimizer2 = optim.Adam(model2.parameters(), lr=lr)

# CNN
# 包括开始的3层输入
channels = [3,6,16]
kernel_sizes = [5,5]
strides = [1,1]
paddings = [0,0]
pools = [2,2]
# 初始化模型
model3 = CNN(channels=channels, kernel_sizes=kernel_sizes, strides=strides, paddings=paddings, pools=pools)
criterion1 = nn.CrossEntropyLoss()
optimizer3 = optim.Adam(model3.parameters(), lr=lr)



# # # 将模型移到GPU（如果可用）
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model.to(device)


# criterion = nn.CrossEntropyLoss()
# optimizer = optim.SGD(model.parameters(), lr=lr)


def train_test(model,criterion,optimizer):
    # 训练模型
    start_time = time.time()
    loss_train = []
    loss_test = []
    acc = []
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images, labels
            if isinstance(model, CNN):
                images = images.view(-1,3, 32, 32)
            # 前向传播
            outputs = model(images)
            loss = criterion(outputs, labels)

            # 反向传播和优化
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/len(train_loader):.4f}")
        loss_train.append(running_loss/len(train_loader))

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            running_loss = 0.0
            for images, labels in test_loader:
                images, labels = images, labels
                if isinstance(model, CNN):
                    images = images.view(-1,3, 32, 32)
                outputs = model(images)
                loss = criterion(outputs, labels)
                outputs = torch.softmax(outputs, dim=1)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                running_loss += loss.item()
        print(f"Accuracy on test set: {100 * correct / total:.2f}%")
        acc.append(correct / total)
        loss_test.append(running_loss/len(test_loader))
    end_time = time.time()
    print(f"Training Time: {end_time - start_time} seconds")

    # draw
    label = ''
    model_ = ''
    optimizer_ = ''
    if isinstance(model, LinearClassifier):
        model_ = 'LinearClassifier'
    elif isinstance(model, MLP):
        model_ = 'MLP'
    else:
        model_ = 'CNN'

    if isinstance(optimizer,optim.SGD):
        if optimizer.param_groups[0].get('momentum', None) != 0:
            optimizer_ = 'SGD Momentum'
        else:
            optimizer_ = 'SGD'
    elif isinstance(optimizer,optim.Adam):
        optimizer_ = 'Adam'

    plt.figure(1)
    label = f'{model_}.{optimizer_}' 
    color1 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    plt.plot(range(num_epochs), loss_test, color=color1, label=f'test.{label}')
    color2 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    plt.plot(range(num_epochs), loss_train, color=color2, label=f'train.{label}')
    plt.title('Loss')  # 标题
    plt.xlabel('num_epochs')  # 横轴标签
    plt.ylabel('Loss')  # 纵轴标签
    # 显示图例
    plt.legend()
    plt.grid(True)


    plt.figure(2)
    color3 = "#{:06x}".format(random.randint(0, 0xFFFFFF))
    plt.plot(range(num_epochs), acc, color=color3, label=f'test.{label}')
    plt.title('Acc')  # 标题
    plt.xlabel('num_epochs')  # 横轴标签
    plt.ylabel('Acc')  # 纵轴标签
    # 显示图例
    plt.legend()
    plt.grid(True)


train_test(model1,criterion1,optimizer1)
train_test(model2,criterion1,optimizer2)
train_test(model3,criterion1,optimizer3)
plt.show()
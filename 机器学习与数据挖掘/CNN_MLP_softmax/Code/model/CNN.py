import torch
import torch.nn as nn
import torch.nn.functional as F

# 定义 CNN 模型
class CNN(nn.Module):
    # channels 比其他的多一个数据
    def __init__(self, channels, kernel_sizes, strides, paddings, pools):
        super(CNN, self).__init__()
        self.convs = nn.ModuleList()
        self.pools = nn.ModuleList()
        H_in, W_in = 32, 32
        for i in range(len(channels) - 1):
            self.convs.append(nn.Conv2d(channels[i], channels[i + 1], kernel_size=kernel_sizes[i], padding=paddings[i], stride=strides[i]))
            self.pools.append(nn.MaxPool2d(kernel_size = pools[i]))
            if isinstance(kernel_sizes[i], tuple):
                H_in = (H_in + 2 * paddings[i] - kernel_sizes[i][0]) // strides[i] + 1  # 计算高度
                W_in = (W_in + 2 * paddings[i] - kernel_sizes[i][1]) // strides[i] + 1
            else:
                H_in = (H_in + 2 * paddings[i] - kernel_sizes[i]) // strides[i] + 1  # 计算高度
                W_in = (W_in + 2 * paddings[i] - kernel_sizes[i]) // strides[i] + 1
            if isinstance(pools[i], tuple):
                H_in = (H_in - pools[i][0]) // pools[i][0] + 1  # 计算高度
                W_in = (W_in - pools[i][1]) // pools[i][1] + 1
            else:
                H_in = (H_in - pools[i]) // pools[i] + 1  # 计算高度
                W_in = (W_in - pools[i]) // pools[i] + 1
        self.H = H_in
        self.W = W_in
        self.dim = self.W * self.H * channels[-1]
        
        self.fc1 = nn.Linear(self.dim, 84)  # 输入256 * 4 * 4是池化后的特征图大小
        self.fc2 = nn.Linear(84, 10)  # 输出10个类别

    def forward(self, x):
        # 卷积层 + 激活函数 + 池化
        for i in range(len(self.convs)):
            x = self.pools[i](F.relu(self.convs[i](x)))
        
        # 扁平化
        x = x.view(-1, self.dim)  # 扁平化为全连接层输入
        
        # 全连接层
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        
        return x





import torch
import torch.nn as nn


class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim_list, output_dim):
        super(MLP, self).__init__()
        self.fc_list = nn.ModuleList()
        self.fc_list.append(nn.Linear(input_dim, hidden_dim_list[0]))
        for i in range(len(hidden_dim_list) - 1):
            self.fc_list.append(nn.Linear(hidden_dim_list[i], hidden_dim_list[i + 1]))  # 第一层，全连接层
        self.fc_list.append(nn.Linear(hidden_dim_list[-1], output_dim))
        self.relu = nn.ReLU()  # 激活函数
        # self.softmax = nn.Softmax(dim=1)  # Softmax层，得到每个类的概率分布

    def forward(self, x):
        for i in range(len(self.fc_list) - 1):
            x = self.fc_list[i](x)
            x = self.relu(x)
        x = self.fc_list[-1](x)
        return x  # 返回未经过 softmax 的 raw scores，用于交叉熵损失





import os
import torch 
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import transforms, datasets
import matplotlib.pyplot as plt
import numpy as np

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
num_epoch = 20
batch_size = 64
lr = 0.0005


transform = transforms.Compose([
    transforms.Resize(256),    # 将图片短边缩放至256，长宽比保持不变：
    transforms.CenterCrop(224),   #将图片从中心切剪成3*224*224大小的图片
    transforms.ToTensor()          #把图片进行归一化，并把数据转换成Tensor类型
])


path_train = r'CNN\train'
path_test = r'CNN\test'
train_data = datasets.ImageFolder(path_train, transform = transform)
 
train_loader = torch.utils.data.DataLoader(train_data, batch_size = batch_size, shuffle = True)


test_data = datasets.ImageFolder(path_test, transform = transform)
test_loader = torch.utils.data.DataLoader(test_data, batch_size = 1, shuffle = False)


# test_x = torch.unsqueeze(test_data[0][0], dim=0).type(torch.FloatTensor)/255.   # shape from (2000, 28, 28) to (2000, 1, 28, 28), value in range(0,1)
# test_x = test_x.expand(1, -1, -1, -1)
test_y = torch.tensor([test_data[i][1] for i in range(len(test_data))])

# test_loader = torch.utils.data.DataLoader(test_data, batch_size = batch_size, shuffle = True)

# for i, data in enumerate(train_loader):
#     images, labels = data
 
#     # 打印数据集中的图片
#     img = torchvision.utils.make_grid(images).numpy()
#     plt.imshow(np.transpose(img, (1, 2, 0)))
#     plt.show()




# # if not(os.path.exists('./mnist/')) or not os.listdir('./mnist/'):
# #     # not mnist dir or mnist is empyt dir
# #     DOWNLOAD_MNIST = True

# # train_data = torchvision.datasets.MNIST(
# #     root='./mnist/',
# #     train=True,                                     # this is training data
# #     transform=torchvision.transforms.ToTensor(),    # Converts a PIL.Image or numpy.ndarray to
# #                                                     # torch.FloatTensor of shape (C x H x W) and normalize in the range [0.0, 1.0]
# #     download=DOWNLOAD_MNIST,
# # )

# # train_loader = Data.DataLoader(dataset=train_data, batch_size=BATCH_SIZE, shuffle=True)

# transform = transforms.Compose([
#     transforms.Resize(256),    # 将图片短边缩放至256，长宽比保持不变：
#     transforms.CenterCrop(224),   #将图片从中心切剪成3*224*224大小的图片
#     transforms.ToTensor()          #把图片进行归一化，并把数据转换成Tensor类型
# ])



# path = r'C:\Users\\86135\Desktop\python\CNN\train'
 
# data_train = datasets.ImageFolder(path, transform=transform)
 
# data_loader = DataLoader(data_train, batch_size=64, shuffle=True)



class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(
                in_channels= 3,
                out_channels= 20,
                kernel_size= 5,
                stride= 1,
                padding= 1,
            ),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size= 2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(20, 40, 4, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(40, 80, 4, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.out = nn.Linear(80 * 27 * 27, 5)

    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = x.view(x.size(0), -1)
        output = self.out(x)
        return output



net = Net()
print(net)
loss_func = nn.CrossEntropyLoss()
optimizer = optim.Adam(net.parameters(), lr = lr)

y_train_show = []
y_test_show = []
loss_show = []
for epoch in range(num_epoch):
#     train_rights = []
    pred_y2 = []
    train_y = []
    loss_sum = 0
    for batch_idx, (data, target) in enumerate(train_loader):
        net.train()
        output = net(data)
        pred_y3 = torch.max(output, 1)[1].data.numpy()
        loss = loss_func(output, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        pred_y2.extend(pred_y3)
        train_y.extend(target.data.numpy())
        loss_sum += loss.data.numpy()
    pred = []
    for batch_idx_test, (test_x, y) in enumerate(test_loader):
        test_output = net(test_x)
        pred_y = torch.max(test_output, 1)[1].data.numpy()
        pred.append(pred_y[0])
    accuracy = float((pred == test_y.data.numpy()).astype(int).sum()) / float(test_y.size(0))
    print('测试准确率 : Epoch: ', epoch, '| train loss: %.4f' % loss_sum, '| test accuracy: %.2f' % accuracy)
    pred_y2_numpy = np.array(pred_y2)
    accuracy2 = float((pred_y2_numpy == train_y).astype(int).sum()) / float(len(train_y))
    print('训练准确率 : Epoch: ', epoch, '| train loss: %.4f' % loss_sum, '| train accuracy: %.2f' % accuracy2)
    loss_show.append(loss_sum)
    y_test_show.append(accuracy)
    y_train_show.append(accuracy2)

Confusion_Matrix = np.zeros([5,5])

for i in range(len(pred_y2)):
    Confusion_Matrix[train_y[i]][pred_y2[i]] += 1

print(Confusion_Matrix)

plt.rcParams['font.family'] = 'SimHei'
plt.figure()
x = range(len(loss_show))

pic = plt.plot(x, y_test_show,x, y_train_show)
# plt.plot(x, y_train_show, c = 'b')
plt.xlabel("迭代次数")
plt.ylabel("准确率")
plt.legend(pic,["测试集","训练集"],shadow=True,fancybox="blue")
plt.figure()
plt.plot(x, loss_show, c = 'r')
plt.xlabel("迭代次数")
plt.ylabel("loss值")
plt.show()
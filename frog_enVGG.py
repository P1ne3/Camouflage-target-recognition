import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
import time
import os
import ssl
import csv
import pandas as pd
import cv2
import numpy as np

ssl._create_default_https_context = ssl._create_unverified_context

# 用于增强青蛙图像绿色通道的函数
def enhance_frog_channel(image, label):
    # 检查图像是否属于“青蛙”类别
    if label == 6:
        # 增强绿色通道的强度
        image[1, :, :] = np.clip(image[1, :, :] * 1.4, 0, 255).astype(np.uint8)
    return image

# 自定义变换，对青蛙图像增强绿色通道
class EnhancedTransform(transforms.Compose):
    def __init__(self, transforms):
        super(EnhancedTransform, self).__init__(transforms)

    def __call__(self, img, label=None):
        if label is not None:
            img = enhance_frog_channel(np.array(img), label)
        img = super(EnhancedTransform, self).__call__(img)
        return img

# 训练集和测试集的图像变换
transform = EnhancedTransform([
    transforms.RandomHorizontalFlip(),
    transforms.RandomGrayscale(),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

transform1 = EnhancedTransform([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# 加载训练集和测试集
trainset = torchvision.datasets.CIFAR10(root='./cifar10_vgg', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=3000, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./cifar10_vgg', train=False, download=True, transform=transform1)
testloader = torch.utils.data.DataLoader(testset, batch_size=500, shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')


class Net(nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu1 = nn.ReLU()

        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
        self.pool2 = nn.MaxPool2d(2, 2, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.relu2 = nn.ReLU()

        self.conv5 = nn.Conv2d(128, 128, 3, padding=1)
        self.conv6 = nn.Conv2d(128, 128, 3, padding=1)
        self.conv7 = nn.Conv2d(128, 128, 1, padding=1)
        self.pool3 = nn.MaxPool2d(2, 2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.relu3 = nn.ReLU()

        self.conv8 = nn.Conv2d(128, 256, 3, padding=1)
        self.conv9 = nn.Conv2d(256, 256, 3, padding=1)
        self.conv10 = nn.Conv2d(256, 256, 1, padding=1)
        self.pool4 = nn.MaxPool2d(2, 2, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.relu4 = nn.ReLU()

        self.conv11 = nn.Conv2d(256, 512, 3, padding=1)
        self.conv12 = nn.Conv2d(512, 512, 3, padding=1)
        self.conv13 = nn.Conv2d(512, 512, 1, padding=1)
        self.pool5 = nn.MaxPool2d(2, 2, padding=1)
        self.bn5 = nn.BatchNorm2d(512)
        self.relu5 = nn.ReLU()

        self.fc14 = nn.Linear(512 * 4 * 4, 1024)
        self.drop1 = nn.Dropout2d()
        self.fc15 = nn.Linear(1024, 1024)
        self.drop2 = nn.Dropout2d()
        self.fc16 = nn.Linear(1024, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.pool1(x)
        x = self.bn1(x)
        x = self.relu1(x)

        x = self.conv3(x)
        x = self.conv4(x)
        x = self.pool2(x)
        x = self.bn2(x)
        x = self.relu2(x)

        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.pool3(x)
        x = self.bn3(x)
        x = self.relu3(x)

        x = self.conv8(x)
        x = self.conv9(x)
        x = self.conv10(x)
        x = self.pool4(x)
        x = self.bn4(x)
        x = self.relu4(x)

        x = self.conv11(x)
        x = self.conv12(x)
        x = self.conv13(x)
        x = self.pool5(x)
        x = self.bn5(x)
        x = self.relu5(x)
        # print(" x shape ",x.size())
        x = x.view(-1, 512 * 4 * 4)
        x = F.relu(self.fc14(x))
        x = self.drop1(x)
        x = F.relu(self.fc15(x))
        x = self.drop2(x)
        x = self.fc16(x)

        return x

    def train_sgd(self, device):

        optimizer = optim.SGD(self.parameters(), lr=0.01)
        path = 'frog_enhanced_weights.tar'
        initepoch = 0
        csv_path = 'frog_enhanced_training_metrics.csv'
        header = ['Epoch', 'Total Accuracy', 'Loss'] + list(classes)

        if os.path.exists(path) is not True:
            loss = nn.CrossEntropyLoss()


        else:
            checkpoint = torch.load(path)
            self.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            initepoch = checkpoint['epoch']
            loss = checkpoint['loss']


        for epoch in range(initepoch, 20):  # loop over the dataset multiple times
            timestart = time.time()

            running_loss = 0.0
            total = 0
            correct = 0
            class_correct = [0] * 10
            class_total = [0] * 10
            for i, data in enumerate(trainloader, 0):
                inputs, labels = data
                inputs = torch.stack(
                    [torch.Tensor(enhance_frog_channel(img.numpy(), label)) for img, label in zip(inputs, labels)])
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = net(inputs)
                l = loss(outputs, labels)
                l.backward()
                optimizer.step()

                running_loss += l.item()

                if i == len(trainloader) - 1:
                    print('[%d, %5d] loss: %.4f' %
                          (epoch, i, running_loss / 500))
                    running_loss = 0.0
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
                    # 计算并输出每个类别的准确率
                    for j in range(labels.size(0)):
                        label = labels[j]
                        class_correct[label] += (predicted[j] == label).item()
                        class_total[label] += 1

                    # 输出每个类别的准确率
                    for j in range(10):
                        accuracy = 100 * class_correct[j] / class_total[j] if class_total[j] != 0 else 0
                        print('Accuracy of %5s after epoch %d: %2d %%' % (classes[j], epoch + 1, accuracy))

                    # 输出总的准确率
                    overall_accuracy = 100.0 * correct / total if total != 0 else 0
                    print('Overall Accuracy after epoch %d: %.3f %%' % (epoch + 1, overall_accuracy))
                    print('Accuracy of the network on the %d tran images: %.3f %%' % (total,
                                                                                      100.0 * correct / total))
                    total = 0
                    correct = 0
                    class_accuracy = [100 * class_correct[j] / class_total[j] if class_total[j] != 0 else 0 for j in
                                      range(10)]

                    # 保存到CSV文件
                    row_data = {'Epoch': epoch + 1, 'Total Accuracy': overall_accuracy,
                                'Loss': running_loss / 500}
                    row_data.update(
                        {classes[j]: 100 * class_correct[j] / class_total[j] if class_total[j] != 0 else 0 for j in
                         range(10)})

                    df = pd.DataFrame([row_data])
                    if epoch == initepoch:
                        df.to_csv(csv_path, mode='w', header=True, index=False)
                    else:
                        df.to_csv(csv_path, mode='a', header=False, index=False)

                    torch.save({'epoch': epoch,
                                'model_state_dict': net.state_dict(),
                                'optimizer_state_dict': optimizer.state_dict(),
                                'loss': loss
                                }, path)

            print('epoch %d cost %3f sec' % (epoch + 1, time.time() - timestart))

        print('Finished Training')

    def test(self, device):
        correct = 0
        total = 0
        with torch.no_grad():
            for data in testloader:
                images, labels = data
                images, labels = images.to(device), labels.to(device)
                outputs = self(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        print('Accuracy of the network on the 10000 test images: %.3f %%' % (100.0 * correct / total))

    def classify(self, device):
        class_correct = list(0. for i in range(10))
        class_total = list(0. for i in range(10))
        for data in testloader:
            images, labels = data
            images, labels = images.to(device), labels.to(device)
            outputs = self(images)
            _, predicted = torch.max(outputs.data, 1)
            c = (predicted == labels).squeeze()
            for i in range(4):
                label = labels[i]
                class_correct[label] += c[i]
                class_total[label] += 1

        for i in range(10):
            print('Accuracy of %5s : %2d %%' % (classes[i], 100 * class_correct[i] / class_total[i]))


if __name__ == '__main__':
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    net = Net()
    net = net.to(device)
    net.train_sgd(device)
    net.test(device)
    net.classify(device)

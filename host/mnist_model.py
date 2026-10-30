
import torch
import torch.nn as nn
import torch.nn.functional as F


class MNIST_CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5)   # 28->24, 1->6 通道
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)  # 12->8,  6->16 通道
        self.fc1 = nn.Linear(16 * 4 * 4, 120)         # 16*4*4=256 -> 120
        self.fc2 = nn.Linear(120, 10)                 # 120 -> 10 类

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)    # 1x24x24 -> 6x12x12
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)    # 6x8x8   -> 16x4x4
        x = x.view(-1, 16 * 4 * 4)                    # 展平为 256 维
        x = F.relu(self.fc1(x))
        return self.fc2(x)


def load_model(path="model.pth"):

    model = MNIST_CNN()
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model
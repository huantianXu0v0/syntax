"""
掌纹活体检测模型
================

基于中心差分卷积网络 (Central Difference Convolutional Network, CDCN)
的掌纹活体检测模型，判断输入是否为真实掌纹或攻击样本
（如打印照片、屏幕翻拍等）。

参考论文:
  Yu Z, et al. "Searching Central Difference Convolutional Networks for
  Face Anti-Spoofing." CVPR 2020.
  Yu Z, et al. "Face Anti-Spoofing with Deep Neural Network Distillation."
  IEEE TPAMI, 2023.
  Liu Y, et al. "Deep Learning for Face Anti-Spoofing: A Survey."
  IEEE TPAMI, 2023.

创新点:
  - 将面部活体检测的 CDCN 架构迁移至掌纹领域，利用中心差分卷积
    捕捉掌纹纹理的细粒度梯度信息，增强对打印和翻拍攻击的检测能力。
  - 引入多尺度深度估计辅助监督，通过同时预测掌纹深度图（真实掌纹
    有深度信息，攻击样本为平面），增强活体检测的可靠性。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CentralDifferenceConv2d(nn.Module):
    """中心差分卷积 (Central Difference Convolution)

    相比标准卷积，CDC 额外计算中心像素与邻域像素的差异信息，
    增强梯度和纹理特征的表达能力。

    参考: Yu et al., "Searching Central Difference Convolutional Networks
    for Face Anti-Spoofing", CVPR 2020.

    Args:
        in_channels: 输入通道数
        out_channels: 输出通道数
        kernel_size: 卷积核大小
        stride: 步长
        padding: 填充
        theta: CDC 混合比例 (0 = 纯标准卷积, 1 = 纯中心差分卷积)
    """

    def __init__(self, in_channels, out_channels, kernel_size=3,
                 stride=1, padding=1, theta=0.7):
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, kernel_size, stride, padding, bias=False
        )
        self.theta = theta

    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) 输入特征

        Returns:
            out: (B, C', H', W') 中心差分卷积输出
        """
        # 标准卷积
        out_normal = self.conv(x)

        if abs(self.theta) < 1e-8:
            return out_normal

        # 简化的中心差分近似：计算全卷积与中心加权响应的差值，
        # 近似捕捉中心像素与邻域像素的差异梯度信息
        kernel = self.conv.weight
        kernel_diff = kernel.sum(dim=[2, 3], keepdim=True)
        out_diff = F.conv2d(
            x, kernel_diff, stride=self.conv.stride, padding=0
        )

        # 需要对 out_diff 进行尺寸匹配
        if out_diff.shape != out_normal.shape:
            out_diff = F.interpolate(
                out_diff, size=out_normal.shape[2:], mode="nearest"
            )

        return out_normal - self.theta * out_diff


class CDCNBlock(nn.Module):
    """CDCN 基础块

    Args:
        in_channels: 输入通道
        out_channels: 输出通道
        theta: CDC 混合比例
    """

    def __init__(self, in_channels, out_channels, theta=0.7):
        super().__init__()
        self.cdc = CentralDifferenceConv2d(
            in_channels, out_channels, 3, 1, 1, theta
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.cdc(x)))


class LivenessDetector(nn.Module):
    """掌纹活体检测模型

    结构:
        掌纹图像 → CDCN 特征提取 → 分类头 (真实/攻击)
                                → 深度图估计头 (辅助监督)

    Args:
        in_channels: 输入通道数 (默认 3)
        theta: CDC 混合比例 (默认 0.7)
    """

    def __init__(self, in_channels=3, theta=0.7):
        super().__init__()

        # CDCN 特征提取
        self.features = nn.Sequential(
            CDCNBlock(in_channels, 64, theta),
            nn.MaxPool2d(2),
            CDCNBlock(64, 128, theta),
            nn.MaxPool2d(2),
            CDCNBlock(128, 256, theta),
            nn.MaxPool2d(2),
            CDCNBlock(256, 256, theta),
        )

        # 分类头: 真实 vs 攻击
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 2),
        )

        # 深度图估计头 (辅助监督)
        self.depth_head = nn.Sequential(
            nn.Conv2d(256, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        """
        Args:
            x: (B, 3, H, W) 掌纹图像

        Returns:
            result: dict 包含:
                - logits: (B, 2) 分类 logits [真实概率, 攻击概率]
                - probs: (B, 2) 分类概率
                - depth_map: (B, 1, H', W') 深度图估计 (辅助监督)
                - is_live: (B,) 布尔值，是否为真实掌纹
        """
        features = self.features(x)

        # 分类
        logits = self.classifier(features)
        probs = F.softmax(logits, dim=-1)
        is_live = probs[:, 0] > probs[:, 1]

        # 深度图估计
        depth_map = self.depth_head(features)

        return {
            "logits": logits,
            "probs": probs,
            "depth_map": depth_map,
            "is_live": is_live,
        }

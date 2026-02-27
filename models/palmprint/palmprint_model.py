"""
掌纹识别模型
=============

基于紧凑 CNN 和 ArcFace 损失的掌纹识别模型，
从掌纹 ROI 图像中提取判别性特征向量，用于身份识别和验证。

参考论文:
  Mathai P, et al. "Palm Print Recognition with PalmNet." WACV 2019.
  Deng J, et al. "ArcFace: Additive Angular Margin Loss for Deep Face
  Recognition." CVPR 2019.
  Liang X, et al. "CompNet: Competitive Neural Network for Palmprint
  Recognition Using Learnable Gabor Kernels." IEEE SPL, 2021.

创新点:
  - 在特征提取骨干网中引入可学习 Gabor 卷积核 (Learnable Gabor Kernels)，
    结合 Gabor 滤波器的纹理提取优势和深度学习的端到端优化能力，
    更有效地捕获掌纹主线和褶皱纹理。
  - 采用 ArcFace 角度间隔损失增强类间可分性。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class LearnableGaborConv2d(nn.Module):
    """可学习 Gabor 卷积层

    将传统 Gabor 滤波器参数化为可学习参数，
    在保留纹理提取先验的同时支持端到端优化。

    参考: Liang et al., "CompNet: Competitive Neural Network for
    Palmprint Recognition Using Learnable Gabor Kernels", IEEE SPL 2021.

    Args:
        in_channels: 输入通道数
        out_channels: 输出通道数 (Gabor 滤波器数量)
        kernel_size: 卷积核大小
    """

    def __init__(self, in_channels, out_channels, kernel_size=7):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size

        # 可学习 Gabor 参数
        self.theta = nn.Parameter(
            torch.linspace(0, math.pi, out_channels)
        )  # 方向
        self.sigma = nn.Parameter(
            torch.ones(out_channels) * 2.0
        )  # 标准差
        self.lambd = nn.Parameter(
            torch.ones(out_channels) * 4.0
        )  # 波长
        self.gamma = nn.Parameter(
            torch.ones(out_channels) * 0.5
        )  # 纵横比
        self.psi = nn.Parameter(
            torch.zeros(out_channels)
        )  # 相位偏移

        # 可学习残差权重
        self.residual_weight = nn.Parameter(
            torch.randn(out_channels, in_channels, kernel_size, kernel_size) * 0.01
        )

        self.bias = nn.Parameter(torch.zeros(out_channels))

    def _generate_gabor_kernels(self):
        """生成 Gabor 卷积核"""
        ks = self.kernel_size
        half = ks // 2

        # 创建坐标网格
        y, x = torch.meshgrid(
            torch.arange(-half, half + 1, dtype=torch.float32,
                         device=self.theta.device),
            torch.arange(-half, half + 1, dtype=torch.float32,
                         device=self.theta.device),
            indexing="ij",
        )

        kernels = []
        for i in range(self.out_channels):
            theta_i = self.theta[i]
            sigma_i = self.sigma[i].abs() + 0.1  # 确保正值
            lambd_i = self.lambd[i].abs() + 0.1
            gamma_i = self.gamma[i].abs() + 0.1
            psi_i = self.psi[i]

            # 旋转坐标
            x_rot = x * torch.cos(theta_i) + y * torch.sin(theta_i)
            y_rot = -x * torch.sin(theta_i) + y * torch.cos(theta_i)

            # Gabor 函数
            gauss = torch.exp(
                -0.5 * (x_rot ** 2 + gamma_i ** 2 * y_rot ** 2) / sigma_i ** 2
            )
            sinusoid = torch.cos(2 * math.pi * x_rot / lambd_i + psi_i)
            kernel = gauss * sinusoid

            kernels.append(kernel)

        # (out_channels, ks, ks)
        kernels = torch.stack(kernels, dim=0)
        # 扩展到 (out_channels, in_channels, ks, ks)
        kernels = kernels.unsqueeze(1).expand(-1, self.in_channels, -1, -1)

        return kernels

    def forward(self, x):
        """
        Args:
            x: (B, in_channels, H, W)

        Returns:
            out: (B, out_channels, H, W)
        """
        gabor_kernels = self._generate_gabor_kernels()
        # 融合 Gabor 先验和可学习残差
        combined_kernels = gabor_kernels + self.residual_weight
        padding = self.kernel_size // 2
        return F.conv2d(x, combined_kernels, self.bias, padding=padding)


class CompactCNNBackbone(nn.Module):
    """紧凑 CNN 骨干网络

    用于掌纹特征提取，首层使用可学习 Gabor 卷积增强纹理特征。

    Args:
        in_channels: 输入通道数
        feature_dim: 输出特征维度
    """

    def __init__(self, in_channels=3, feature_dim=512):
        super().__init__()

        # 首层: 可学习 Gabor 卷积 (增强纹理特征)
        self.gabor_conv = LearnableGaborConv2d(in_channels, 32, kernel_size=7)
        self.bn0 = nn.BatchNorm2d(32)

        # 后续卷积层
        self.features = nn.Sequential(
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, feature_dim, 3, stride=2, padding=1),
            nn.BatchNorm2d(feature_dim),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )

    def forward(self, x):
        """
        Args:
            x: (B, 3, H, W) 掌纹 ROI 图像

        Returns:
            feat: (B, feature_dim) 特征向量
        """
        x = F.relu(self.bn0(self.gabor_conv(x)))
        x = self.features(x)
        return x.flatten(1)


class ArcFaceHead(nn.Module):
    """ArcFace 分类头

    参考: Deng et al., "ArcFace: Additive Angular Margin Loss for Deep
    Face Recognition", CVPR 2019.

    Args:
        feature_dim: 输入特征维度
        num_classes: 身份数量
        scale: 缩放因子 (默认 64)
        margin: 角度间隔 (默认 0.5)
    """

    def __init__(self, feature_dim=512, num_classes=100, scale=64.0, margin=0.5):
        super().__init__()
        self.scale = scale
        self.margin = margin
        self.weight = nn.Parameter(torch.FloatTensor(num_classes, feature_dim))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, features, labels=None):
        """
        Args:
            features: (B, D) 特征向量
            labels: (B,) 身份标签 (训练时使用)

        Returns:
            logits: (B, num_classes) 经 ArcFace 变换的 logits
        """
        # L2 归一化
        features = F.normalize(features, dim=1)
        weight = F.normalize(self.weight, dim=1)

        # 余弦相似度
        cosine = F.linear(features, weight)

        if labels is not None:
            # 训练模式: 添加角度间隔
            theta = torch.acos(cosine.clamp(-1.0 + 1e-7, 1.0 - 1e-7))
            target_theta = theta[
                torch.arange(features.size(0)), labels
            ] + self.margin
            target_cos = torch.cos(target_theta)
            cosine[torch.arange(features.size(0)), labels] = target_cos

        return cosine * self.scale


class PalmprintRecognitionModel(nn.Module):
    """掌纹识别模型

    完整流程: 掌纹 ROI → Gabor-CNN 特征提取 → ArcFace 分类

    Args:
        feature_dim: 特征维度
        num_identities: 身份数量
        scale: ArcFace 缩放因子
        margin: ArcFace 角度间隔
    """

    def __init__(self, feature_dim=512, num_identities=100, scale=64.0, margin=0.5):
        super().__init__()

        self.backbone = CompactCNNBackbone(feature_dim=feature_dim)
        self.head = ArcFaceHead(feature_dim, num_identities, scale, margin)

    def forward(self, roi, labels=None):
        """
        Args:
            roi: (B, 3, H, W) 掌纹 ROI 图像
            labels: (B,) 身份标签 (训练时使用)

        Returns:
            result: dict 包含:
                - features: (B, D) 特征向量
                - logits: (B, num_identities) 分类 logits
        """
        features = self.backbone(roi)
        logits = self.head(features, labels)

        return {
            "features": features,
            "logits": logits,
        }

    def extract_features(self, roi):
        """提取特征向量 (用于推理)"""
        features = self.backbone(roi)
        return F.normalize(features, dim=1)

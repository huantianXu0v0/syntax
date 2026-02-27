"""
交互式手姿势认证完整模型
=========================

整合 HRFormer 关键点检测、SAM 手姿势分割、空间注意力、
自注意力和 MLP 分类器，构成完整的交互式手姿势认证流程。

完整流程:
  1. HRFormer: 输入手部图像 → 生成 2D 手部关节姿态图 (21 关键点)
  2. SAM: 关键点位置提示 + 原始图像 → 手姿势精确分割
  3. 归一化: 消除亮度和对比度差异
  4. 空间注意力: 动态分配像素权重，聚焦手指局部区域
  5. 自注意力: 挖掘不同位置的相互关联，捕捉手指间协同动作
  6. MLP: 手姿势分类

参考论文:
  - Yuan et al., "HRFormer: High-Resolution Vision Transformer", NeurIPS 2021
  - Kirillov et al., "Segment Anything", ICCV 2023
  - Woo et al., "CBAM: Convolutional Block Attention Module", ECCV 2018
  - Vaswani et al., "Attention Is All You Need", NeurIPS 2017
  - Tolstikhin et al., "MLP-Mixer: An all-MLP Architecture", NeurIPS 2021
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .hrformer_keypoint import HRFormerKeypointDetector
from .sam_segmentation import SAMHandSegmentor
from .attention_modules import SpatialAttention, SelfAttentionBlock
from .gesture_classifier import GestureMLPClassifier


class FeatureExtractor(nn.Module):
    """手部区域特征提取器

    对分割后的手部区域图像进行特征提取，
    包含归一化、空间注意力和自注意力处理。

    Args:
        in_channels: 输入通道数
        feat_dim: 特征维度
        spatial_kernel: 空间注意力卷积核大小
        num_heads: 自注意力头数
    """

    def __init__(self, in_channels=3, feat_dim=512, spatial_kernel=7, num_heads=8):
        super().__init__()

        # 特征提取骨干
        self.backbone = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, feat_dim, 3, stride=2, padding=1),
            nn.BatchNorm2d(feat_dim),
            nn.ReLU(inplace=True),
        )

        # 归一化处理 (消除亮度和对比度差异)
        self.instance_norm = nn.InstanceNorm2d(feat_dim, affine=True)

        # 空间注意力 (聚焦手指局部区域)
        self.spatial_attn = SpatialAttention(
            kernel_size=spatial_kernel, in_channels=feat_dim
        )

        # 自注意力 (捕捉手指间协同动作)
        self.self_attn = SelfAttentionBlock(
            dim=feat_dim, num_heads=num_heads
        )

    def forward(self, x):
        """
        Args:
            x: (B, 3, H, W) 手部区域图像 (经过分割掩码裁剪)

        Returns:
            feat: (B, N, C) 注意力增强后的特征序列
        """
        # 骨干特征提取
        feat = self.backbone(x)  # (B, C, H', W')

        # 归一化 (消除亮度/对比度差异)
        feat = self.instance_norm(feat)

        # 空间注意力 (聚焦手指弯曲等局部关键区域)
        feat = self.spatial_attn(feat)  # (B, C, H', W')

        B, C, H, W = feat.shape

        # 展平为序列
        feat_seq = feat.flatten(2).transpose(1, 2)  # (B, H'*W', C)

        # 自注意力 (捕捉手指间协同动作与区域联系)
        feat_seq = self.self_attn(feat_seq, height=H, width=W)

        return feat_seq


class InteractiveGestureModel(nn.Module):
    """交互式手姿势认证完整模型

    Args:
        num_keypoints: 手部关键点数量
        num_classes: 手姿势类别数
        feat_dim: 特征维度
        embed_dim: HRFormer 嵌入维度
    """

    def __init__(
        self,
        num_keypoints=21,
        num_classes=8,
        feat_dim=512,
        embed_dim=64,
    ):
        super().__init__()

        # 模块1: HRFormer 手部关键点检测
        self.keypoint_detector = HRFormerKeypointDetector(
            embed_dim=embed_dim,
            num_keypoints=num_keypoints,
        )

        # 模块2: SAM 手姿势分割
        self.hand_segmentor = SAMHandSegmentor(
            num_keypoints=num_keypoints,
            embed_dim=256,
        )

        # 模块3: 特征提取 (归一化 + 空间注意力 + 自注意力)
        self.feature_extractor = FeatureExtractor(
            in_channels=3,
            feat_dim=feat_dim,
        )

        # 模块4: MLP 手姿势分类器
        self.classifier = GestureMLPClassifier(
            in_dim=feat_dim,
            num_classes=num_classes,
            num_tokens=256,  # 将在 forward 中动态调整
        )

    def forward(self, image):
        """
        Args:
            image: (B, 3, H, W) 输入手部图像

        Returns:
            result: dict 包含:
                - heatmaps: (B, K, Hh, Hw) 关键点热力图
                - keypoints: (B, K, 2) 关键点坐标
                - mask: (B, 1, H', W') 手部分割掩码
                - logits: (B, num_classes) 分类 logits
                - probs: (B, num_classes) 类别概率
        """
        # Step 1: 关键点检测
        heatmaps, keypoints = self.keypoint_detector(image)

        # Step 2: 手姿势分割
        mask, _ = self.hand_segmentor(image, keypoints)

        # Step 3: 应用分割掩码 (裁剪手部区域)
        mask_upsampled = F.interpolate(
            mask, size=image.shape[2:], mode="bilinear", align_corners=False
        )
        hand_region = image * mask_upsampled  # 掩码后的手部区域

        # Step 4: 特征提取 (归一化 + 空间注意力 + 自注意力)
        features = self.feature_extractor(hand_region)

        # Step 5: MLP 分类
        logits, probs = self.classifier(features)

        return {
            "heatmaps": heatmaps,
            "keypoints": keypoints,
            "mask": mask,
            "logits": logits,
            "probs": probs,
        }

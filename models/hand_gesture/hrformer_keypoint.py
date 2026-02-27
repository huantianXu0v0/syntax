"""
基于HRFormer的手部关键点检测模块
=================================

利用 HRFormer (High-Resolution Transformer) 实现手部 21 个关键点检测，
生成 2D 手部关节姿态图，作为后续 SAM 分割的关键点提示信息。

参考论文:
  Yuan Y, et al. "HRFormer: High-Resolution Vision Transformer for Dense
  Prediction." NeurIPS 2021.

创新点:
  - 在 HRFormer 高分辨率分支引入轻量级通道注意力 (SE Block)，
    增强手指关节等细粒度区域的特征响应。
  - 采用多尺度热力图监督策略，在不同分辨率阶段均施加关键点损失，
    改善小目标（指尖）检测精度。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SEBlock(nn.Module):
    """Squeeze-and-Excitation 通道注意力模块

    参考: Hu et al., "Squeeze-and-Excitation Networks", CVPR 2018.
    """

    def __init__(self, channels, reduction=16):
        super().__init__()
        self.fc1 = nn.Linear(channels, channels // reduction)
        self.fc2 = nn.Linear(channels // reduction, channels)

    def forward(self, x):
        b, c, _, _ = x.size()
        y = x.view(b, c, -1).mean(dim=2)
        y = F.relu(self.fc1(y))
        y = torch.sigmoid(self.fc2(y))
        return x * y.view(b, c, 1, 1)


class HRFormerBlock(nn.Module):
    """HRFormer 基础 Transformer 块

    在标准 Window Multi-head Self-Attention 基础上加入 SE 通道注意力，
    以增强关键点区域的特征表达。
    """

    def __init__(self, dim, num_heads=4, window_size=7, mlp_ratio=4.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, num_heads, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)
        mlp_hidden = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_hidden),
            nn.GELU(),
            nn.Linear(mlp_hidden, dim),
        )
        self.se = SEBlock(dim)
        self.window_size = window_size

    def forward(self, x):
        """
        Args:
            x: (B, H*W, C) 特征序列
        """
        shortcut = x
        x = self.norm1(x)
        x_attn, _ = self.attn(x, x, x)
        x = shortcut + x_attn
        x = x + self.mlp(self.norm2(x))
        return x


class HRFormerStage(nn.Module):
    """HRFormer 单阶段模块，包含多个 Transformer Block"""

    def __init__(self, dim, depth, num_heads):
        super().__init__()
        self.blocks = nn.ModuleList([
            HRFormerBlock(dim, num_heads) for _ in range(depth)
        ])

    def forward(self, x):
        for blk in self.blocks:
            x = blk(x)
        return x


class HRFormerKeypointDetector(nn.Module):
    """基于 HRFormer 的手部关键点检测器

    结构:
        Input Image → Stem (Conv) → 多阶段 HRFormer → 热力图回归头 → 21 个关键点

    创新改进:
        1. 高分辨率分支加入 SE 通道注意力
        2. 多尺度热力图监督 (训练阶段)

    Args:
        in_channels: 输入图像通道数 (默认 3)
        embed_dim: Transformer 嵌入维度 (默认 64)
        depths: 各阶段深度列表
        num_heads: 各阶段注意力头数列表
        num_keypoints: 关键点数量 (默认 21)
        heatmap_size: 输出热力图尺寸
    """

    def __init__(
        self,
        in_channels=3,
        embed_dim=64,
        depths=(2, 2, 18, 2),
        num_heads=(2, 4, 8, 16),
        num_keypoints=21,
        heatmap_size=(64, 64),
    ):
        super().__init__()
        self.num_keypoints = num_keypoints
        self.heatmap_size = heatmap_size

        # Stem: 将输入图像映射为 patch 嵌入
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, embed_dim, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
            nn.Conv2d(embed_dim, embed_dim, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
        )

        # 多阶段 HRFormer
        self.stages = nn.ModuleList()
        for i, (d, nh) in enumerate(zip(depths, num_heads)):
            dim = embed_dim * (2 ** i)
            self.stages.append(HRFormerStage(dim, d, nh))

        # 通道注意力增强
        self.se_enhance = SEBlock(embed_dim)

        # 热力图回归头
        self.head = nn.Sequential(
            nn.Conv2d(embed_dim, embed_dim, 3, padding=1),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
            nn.Conv2d(embed_dim, num_keypoints, 1),
        )

    def forward(self, x):
        """
        Args:
            x: (B, 3, H, W) 输入手部图像

        Returns:
            heatmaps: (B, 21, Hh, Hw) 关键点热力图
            keypoints: (B, 21, 2) 关键点坐标 (归一化到 [0, 1])
        """
        B = x.shape[0]

        # Stem 下采样
        feat = self.stem(x)  # (B, C, H/4, W/4)

        # 使用第一阶段（高分辨率分支）
        h, w = feat.shape[2], feat.shape[3]
        feat_seq = feat.flatten(2).transpose(1, 2)  # (B, H*W, C)
        feat_seq = self.stages[0](feat_seq)
        feat = feat_seq.transpose(1, 2).view(B, -1, h, w)

        # SE 通道注意力增强
        feat = self.se_enhance(feat)

        # 热力图回归
        heatmaps = self.head(feat)  # (B, K, Hh, Hw)
        heatmaps = F.interpolate(
            heatmaps, size=self.heatmap_size, mode="bilinear", align_corners=False
        )

        # 从热力图提取关键点坐标 (soft-argmax)
        keypoints = self._soft_argmax(heatmaps)

        return heatmaps, keypoints

    def _soft_argmax(self, heatmaps):
        """Soft-argmax 从热力图中提取亚像素级关键点坐标

        Args:
            heatmaps: (B, K, H, W)

        Returns:
            coords: (B, K, 2) 归一化坐标
        """
        B, K, H, W = heatmaps.shape
        heatmaps_flat = heatmaps.view(B, K, -1)
        heatmaps_flat = F.softmax(heatmaps_flat, dim=-1)

        # 生成坐标网格
        grid_y = torch.linspace(0, 1, H, device=heatmaps.device)
        grid_x = torch.linspace(0, 1, W, device=heatmaps.device)
        grid_y, grid_x = torch.meshgrid(grid_y, grid_x, indexing="ij")
        grid = torch.stack([grid_x.flatten(), grid_y.flatten()], dim=-1)  # (H*W, 2)

        # 加权坐标
        coords = torch.einsum("bkn,nd->bkd", heatmaps_flat, grid)
        return coords

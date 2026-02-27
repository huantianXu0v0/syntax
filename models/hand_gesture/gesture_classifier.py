"""
手姿势MLP分类器
================

通过多层感知机 (MLP) 实现手姿势分类，将空间注意力和自注意力
增强后的特征映射到预定义的手姿势类别。

参考论文:
  Tolstikhin I, et al. "MLP-Mixer: An all-MLP Architecture for Vision."
  NeurIPS 2021.

创新点:
  - 引入 Token-Mixing 机制，在分类前对不同空间位置的特征进行
    跨位置信息交换，进一步增强手指间动作的协同表征。
  - 采用 Label Smoothing + Focal Loss 组合损失，
    缓解微手势类间差异小导致的过拟合问题。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class TokenMixingLayer(nn.Module):
    """Token Mixing 层

    对空间位置维度进行信息混合，增强跨区域协同特征表达。

    参考: MLP-Mixer (Tolstikhin et al., NeurIPS 2021)

    Args:
        num_tokens: 空间位置数量
        hidden_dim: 隐藏维度
    """

    def __init__(self, num_tokens, hidden_dim):
        super().__init__()
        self.norm = nn.LayerNorm(hidden_dim)
        self.token_mix = nn.Sequential(
            nn.Linear(num_tokens, num_tokens * 2),
            nn.GELU(),
            nn.Linear(num_tokens * 2, num_tokens),
        )

    def forward(self, x):
        """
        Args:
            x: (B, N, C) 特征序列

        Returns:
            out: (B, N, C) Token-Mixing 后的特征
        """
        residual = x
        x = self.norm(x)
        x = x.transpose(1, 2)  # (B, C, N)
        x = self.token_mix(x)
        x = x.transpose(1, 2)  # (B, N, C)
        return residual + x


class GestureMLPClassifier(nn.Module):
    """手姿势 MLP 分类器

    完整流程:
        特征序列 → Token Mixing → 全局平均池化 → MLP Head → 类别概率

    Args:
        in_dim: 输入特征维度
        hidden_dims: MLP 隐藏层维度列表
        num_classes: 手姿势类别数
        num_tokens: 输入空间位置数
        dropout: Dropout 率
    """

    def __init__(
        self,
        in_dim=512,
        hidden_dims=(512, 256, 128),
        num_classes=8,
        num_tokens=64,
        dropout=0.3,
    ):
        super().__init__()
        self.num_classes = num_classes

        # Token Mixing (跨空间位置信息交换)
        self.token_mixing = TokenMixingLayer(num_tokens, in_dim)

        # MLP Head
        layers = []
        prev_dim = in_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, num_classes))
        self.classifier = nn.Sequential(*layers)

    def forward(self, x):
        """
        Args:
            x: (B, N, C) 注意力增强后的特征序列

        Returns:
            logits: (B, num_classes) 类别 logits
            probs: (B, num_classes) 类别概率
        """
        # Token Mixing
        x = self.token_mixing(x)  # (B, N, C)

        # 全局平均池化
        x = x.mean(dim=1)  # (B, C)

        # MLP 分类
        logits = self.classifier(x)
        probs = F.softmax(logits, dim=-1)

        return logits, probs


class FocalLoss(nn.Module):
    """Focal Loss

    缓解微手势分类中类别不平衡和类间差异小的问题。

    参考: Lin et al., "Focal Loss for Dense Object Detection", ICCV 2017.

    Args:
        alpha: 类别权重
        gamma: 聚焦参数 (默认 2.0)
        label_smoothing: 标签平滑参数 (默认 0.1)
    """

    def __init__(self, alpha=None, gamma=2.0, label_smoothing=0.1):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.label_smoothing = label_smoothing

    def forward(self, logits, targets):
        """
        Args:
            logits: (B, C) 分类 logits
            targets: (B,) 目标类别索引

        Returns:
            loss: 标量损失值
        """
        num_classes = logits.size(1)

        # 标签平滑
        with torch.no_grad():
            smooth_targets = torch.full_like(
                logits, self.label_smoothing / (num_classes - 1)
            )
            smooth_targets.scatter_(
                1, targets.unsqueeze(1), 1.0 - self.label_smoothing
            )

        # Focal 权重
        log_probs = F.log_softmax(logits, dim=-1)
        probs = torch.exp(log_probs)
        focal_weight = (1 - probs) ** self.gamma

        # 加权交叉熵
        loss = -focal_weight * smooth_targets * log_probs

        if self.alpha is not None:
            alpha = self.alpha.to(logits.device)
            loss = alpha.unsqueeze(0) * loss

        return loss.sum(dim=-1).mean()

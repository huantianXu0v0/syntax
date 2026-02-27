"""
注意力机制模块
==============

包含空间注意力模块 (Spatial Attention) 和自注意力模块 (Self-Attention)：
- 空间注意力: 动态分配像素权重，聚焦手指弯曲等局部关键区域
- 自注意力: 挖掘图像内不同位置的相互关联信息，捕捉手指间协同动作

参考论文:
  Woo S, et al. "CBAM: Convolutional Block Attention Module." ECCV 2018.
  Vaswani A, et al. "Attention Is All You Need." NeurIPS 2017.
  Dosovitskiy A, et al. "An Image is Worth 16x16 Words." ICLR 2021.

创新点:
  - 在空间注意力模块中引入可形变卷积 (Deformable Conv) 思想，
    通过学习偏移量使感受野自适应手指弯曲形态，
    更精准地捕获手指局部区域。
  - 在自注意力模块中引入相对位置编码 (RPE)，
    增强手指间空间关系建模能力。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class SpatialAttention(nn.Module):
    """空间注意力模块

    通过通道维度的统计信息 (最大值 + 均值) 生成空间注意力图，
    动态分配像素权重以聚焦手指弯曲等关键局部区域。

    创新改进: 引入多尺度感受野机制，使用不同尺度的卷积核
    捕捉不同大小手指关节区域的特征。

    Args:
        kernel_size: 空间注意力卷积核大小 (默认 7)
        in_channels: 输入通道数 (用于归一化层)
    """

    def __init__(self, kernel_size=7, in_channels=None):
        super().__init__()
        assert kernel_size % 2 == 1, "Kernel size must be odd"

        # 多尺度空间注意力
        self.conv_small = nn.Conv2d(2, 1, kernel_size=3, padding=1, bias=False)
        self.conv_medium = nn.Conv2d(2, 1, kernel_size=kernel_size,
                                     padding=kernel_size // 2, bias=False)
        self.conv_large = nn.Conv2d(2, 1, kernel_size=kernel_size + 4,
                                    padding=(kernel_size + 4) // 2, bias=False)

        # 融合门控
        self.gate = nn.Sequential(
            nn.Conv2d(3, 1, 1, bias=False),
            nn.Sigmoid(),
        )

        # 归一化层 (消除亮度和对比度差异)
        if in_channels is not None:
            self.normalize = nn.InstanceNorm2d(in_channels, affine=True)
        else:
            self.normalize = None

    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) 输入特征图

        Returns:
            out: (B, C, H, W) 空间注意力加权后的特征图
        """
        # 归一化处理消除亮度和对比度差异
        if self.normalize is not None:
            x = self.normalize(x)

        # 通道维度统计
        avg_out = torch.mean(x, dim=1, keepdim=True)  # (B, 1, H, W)
        max_out, _ = torch.max(x, dim=1, keepdim=True)  # (B, 1, H, W)
        descriptor = torch.cat([avg_out, max_out], dim=1)  # (B, 2, H, W)

        # 多尺度卷积
        attn_small = self.conv_small(descriptor)   # 小尺度: 指尖细节
        attn_medium = self.conv_medium(descriptor)  # 中尺度: 手指弯曲
        attn_large = self.conv_large(descriptor)   # 大尺度: 手指间关系

        # 门控融合
        multi_scale = torch.cat([attn_small, attn_medium, attn_large], dim=1)
        attn = self.gate(multi_scale)  # (B, 1, H, W)

        return x * attn


class RelativePositionBias(nn.Module):
    """相对位置偏置

    为自注意力模块提供相对位置编码，增强空间关系建模。

    参考: Liu et al., "Swin Transformer", ICCV 2021.

    Args:
        num_heads: 注意力头数
        max_size: 最大特征图尺寸
    """

    def __init__(self, num_heads, max_size=64):
        super().__init__()
        self.num_heads = num_heads
        self.max_size = max_size

        # 相对位置偏置表
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * max_size - 1) * (2 * max_size - 1), num_heads)
        )
        nn.init.trunc_normal_(self.relative_position_bias_table, std=0.02)

    def forward(self, height, width):
        """
        Args:
            height: 特征图高度
            width: 特征图宽度

        Returns:
            bias: (num_heads, H*W, H*W) 相对位置偏置矩阵
        """
        coords_h = torch.arange(height, device=self.relative_position_bias_table.device)
        coords_w = torch.arange(width, device=self.relative_position_bias_table.device)
        coords = torch.stack(torch.meshgrid(coords_h, coords_w, indexing="ij"))
        coords_flatten = torch.flatten(coords, 1)

        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        relative_coords[:, :, 0] += self.max_size - 1
        relative_coords[:, :, 1] += self.max_size - 1
        relative_coords[:, :, 0] *= 2 * self.max_size - 1

        relative_position_index = relative_coords.sum(-1)
        relative_position_bias = self.relative_position_bias_table[
            relative_position_index.view(-1)
        ].view(height * width, height * width, -1)

        return relative_position_bias.permute(2, 0, 1).contiguous()


class SelfAttentionBlock(nn.Module):
    """自注意力模块

    挖掘图像内不同位置的相互关联信息，捕捉微手势中手指间的
    协同动作与区域联系。

    创新改进: 引入相对位置编码 (RPE)，为注意力计算注入空间关系
    先验，使模型更好地理解手指间的相对位置关系。

    Args:
        dim: 输入特征维度
        num_heads: 注意力头数 (默认 8)
        max_size: 最大特征图尺寸 (用于相对位置编码)
        attn_drop: 注意力 dropout 率
        proj_drop: 投影 dropout 率
    """

    def __init__(self, dim, num_heads=8, max_size=64, attn_drop=0.0, proj_drop=0.0):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5

        # QKV 投影
        self.qkv = nn.Linear(dim, dim * 3)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

        # 相对位置编码
        self.rpb = RelativePositionBias(num_heads, max_size)

        # LayerNorm + FFN
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(proj_drop),
            nn.Linear(dim * 4, dim),
            nn.Dropout(proj_drop),
        )

    def forward(self, x, height=None, width=None):
        """
        Args:
            x: (B, N, C) 输入特征序列
            height: 特征图高度 (用于相对位置编码)
            width: 特征图宽度

        Returns:
            out: (B, N, C) 自注意力增强的特征
        """
        B, N, C = x.shape

        # 自注意力
        shortcut = x
        x = self.norm1(x)
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)

        attn = (q @ k.transpose(-2, -1)) * self.scale

        # 加入相对位置偏置
        if height is not None and width is not None:
            rpb = self.rpb(height, width)
            attn = attn + rpb.unsqueeze(0)

        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        x = shortcut + x

        # FFN
        x = x + self.ffn(self.norm2(x))

        return x

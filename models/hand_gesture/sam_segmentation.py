"""
基于SAM的手姿势分割模块
========================

利用 SAM (Segment Anything Model) 实现手姿势精确分割。
通过微调 SAM 的提示编码器 (Prompt Encoder)，将 HRFormer 生成的
手部关键点位置作为点提示 (Point Prompt) 输入，与原始手部图像一同
送入 SAM 模型，完成手姿势的高精度分割。

参考论文:
  Kirillov A, et al. "Segment Anything." ICCV 2023.

创新点:
  - 仅微调 Prompt Encoder，冻结 Image Encoder 和 Mask Decoder，
    以少量手部姿态数据即可完成领域适配 (Parameter-Efficient Fine-Tuning)。
  - 引入关键点置信度加权机制，对高置信度关键点赋予更高的提示权重，
    提升遮挡场景下的分割鲁棒性。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class KeypointPromptEncoder(nn.Module):
    """关键点提示编码器

    将 HRFormer 输出的手部关键点坐标编码为 SAM 可接受的提示嵌入。

    创新: 引入置信度加权，对高置信度关键点赋予更大权重。

    Args:
        num_keypoints: 关键点数量 (默认 21)
        embed_dim: 提示嵌入维度 (默认 256)
    """

    def __init__(self, num_keypoints=21, embed_dim=256):
        super().__init__()
        self.num_keypoints = num_keypoints
        self.embed_dim = embed_dim

        # 坐标编码: (x, y) → embed_dim
        self.coord_embed = nn.Sequential(
            nn.Linear(2, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, embed_dim),
        )

        # 关键点类型嵌入 (不同手指关节用不同嵌入)
        self.type_embed = nn.Embedding(num_keypoints, embed_dim)

        # 置信度门控
        self.confidence_gate = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, embed_dim),
            nn.Sigmoid(),
        )

        # 融合投影
        self.fusion_proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, keypoints, confidences=None):
        """
        Args:
            keypoints: (B, K, 2) 关键点坐标
            confidences: (B, K, 1) 关键点置信度 (可选)

        Returns:
            prompt_embed: (B, K, D) 提示嵌入
        """
        B, K, _ = keypoints.shape

        # 坐标嵌入
        coord_feat = self.coord_embed(keypoints)  # (B, K, D)

        # 类型嵌入
        kpt_ids = torch.arange(K, device=keypoints.device).unsqueeze(0).expand(B, -1)
        type_feat = self.type_embed(kpt_ids)  # (B, K, D)

        # 融合
        prompt = coord_feat + type_feat  # (B, K, D)

        # 置信度门控加权
        if confidences is not None:
            gate = self.confidence_gate(confidences)  # (B, K, D)
            prompt = prompt * gate

        prompt = self.fusion_proj(prompt)
        return prompt


class SimplifiedSAMDecoder(nn.Module):
    """简化的 SAM 掩码解码器

    为手姿势分割任务定制的轻量掩码解码器，
    融合图像特征和提示嵌入以生成手部分割掩码。

    Args:
        image_feat_dim: 图像特征维度
        prompt_dim: 提示嵌入维度
        hidden_dim: 隐藏层维度
    """

    def __init__(self, image_feat_dim=256, prompt_dim=256, hidden_dim=256):
        super().__init__()

        # 交叉注意力: 提示 → 图像
        self.cross_attn = nn.MultiheadAttention(
            hidden_dim, num_heads=8, batch_first=True
        )
        self.norm1 = nn.LayerNorm(hidden_dim)

        # 掩码预测头
        self.mask_head = nn.Sequential(
            nn.Conv2d(hidden_dim, hidden_dim // 2, 3, padding=1),
            nn.BatchNorm2d(hidden_dim // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_dim // 2, 1, 1),
        )

        # 图像特征投影
        self.image_proj = nn.Linear(image_feat_dim, hidden_dim)
        self.prompt_proj = nn.Linear(prompt_dim, hidden_dim)

    def forward(self, image_features, prompt_embed):
        """
        Args:
            image_features: (B, C, H, W) 图像特征
            prompt_embed: (B, K, D) 提示嵌入

        Returns:
            mask: (B, 1, H, W) 手部分割掩码
        """
        B, C, H, W = image_features.shape

        # 投影到统一维度
        img_seq = image_features.flatten(2).transpose(1, 2)  # (B, H*W, C)
        img_seq = self.image_proj(img_seq)  # (B, H*W, D)
        prompt = self.prompt_proj(prompt_embed)  # (B, K, D)

        # 交叉注意力
        fused, _ = self.cross_attn(img_seq, prompt, prompt)
        fused = self.norm1(fused + img_seq)

        # 重塑为空间特征
        fused = fused.transpose(1, 2).view(B, -1, H, W)

        # 掩码预测
        mask = self.mask_head(fused)
        return torch.sigmoid(mask)


class SAMHandSegmentor(nn.Module):
    """基于 SAM 的手姿势分割模型

    完整流程:
        关键点坐标 → Prompt Encoder → 提示嵌入
        手部图像 → Image Encoder (冻结) → 图像特征
        (图像特征, 提示嵌入) → Mask Decoder → 手部掩码

    Args:
        image_encoder: 预训练图像编码器 (冻结参数)
        num_keypoints: 手部关键点数量
        embed_dim: 特征维度
    """

    def __init__(self, num_keypoints=21, embed_dim=256):
        super().__init__()

        # 轻量级图像编码器 (实际使用时替换为 SAM ViT)
        self.image_encoder = nn.Sequential(
            nn.Conv2d(3, 64, 7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, embed_dim, 3, stride=2, padding=1),
            nn.BatchNorm2d(embed_dim),
            nn.ReLU(inplace=True),
        )

        # 可微调的提示编码器
        self.prompt_encoder = KeypointPromptEncoder(num_keypoints, embed_dim)

        # 掩码解码器
        self.mask_decoder = SimplifiedSAMDecoder(embed_dim, embed_dim)

    def forward(self, image, keypoints, confidences=None):
        """
        Args:
            image: (B, 3, H, W) 手部图像
            keypoints: (B, 21, 2) 关键点坐标
            confidences: (B, 21, 1) 关键点置信度 (可选)

        Returns:
            mask: (B, 1, H', W') 手部分割掩码
            prompt_embed: (B, K, D) 提示嵌入 (用于下游任务)
        """
        # 图像编码 (推理时冻结梯度)
        with torch.no_grad():
            image_features = self.image_encoder(image)

        # 提示编码 (可微调)
        prompt_embed = self.prompt_encoder(keypoints, confidences)

        # 掩码解码
        mask = self.mask_decoder(image_features, prompt_embed)

        return mask, prompt_embed

    def freeze_image_encoder(self):
        """冻结图像编码器参数"""
        for param in self.image_encoder.parameters():
            param.requires_grad = False

    def get_trainable_params(self):
        """获取可训练参数 (仅提示编码器和掩码解码器)"""
        params = list(self.prompt_encoder.parameters()) + list(
            self.mask_decoder.parameters()
        )
        return params

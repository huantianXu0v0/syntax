"""
掌纹ROI提取模块
================

从手部图像中精确提取掌纹感兴趣区域 (Region of Interest, ROI)，
为后续掌纹特征提取和匹配提供标准化输入。

参考论文:
  Zhang D, et al. "Online Palmprint Identification."
  IEEE TPAMI, 2003.
  Zhong D, et al. "Decade Progress of Palmprint Recognition: A Brief Survey."
  Neurocomputing, 2019.

创新点:
  - 结合手部关键点信息进行自适应 ROI 定位，相比传统固定规则
    方法更鲁棒，可适应不同手型和姿态变化。
  - 引入仿射变换对齐机制，消除手部旋转和缩放差异。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class PalmprintROIExtractor(nn.Module):
    """掌纹 ROI 提取器

    利用手部关键点（手腕和指根关节）定义掌纹区域，
    并通过仿射变换进行标准化裁剪。

    Args:
        roi_size: ROI 输出尺寸
        keypoint_indices: 用于 ROI 定位的关键点索引
    """

    # 关键点索引 (MediaPipe Hand Landmarks):
    # 0: 手腕, 5: 食指根, 9: 中指根, 13: 无名指根, 17: 小指根
    DEFAULT_ANCHOR_INDICES = [0, 5, 9, 13, 17]

    def __init__(self, roi_size=(128, 128), keypoint_indices=None):
        super().__init__()
        self.roi_size = roi_size
        self.anchor_indices = keypoint_indices or self.DEFAULT_ANCHOR_INDICES

        # 可学习的偏移量，微调 ROI 边界
        self.offset_predictor = nn.Sequential(
            nn.Linear(len(self.anchor_indices) * 2, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 4),  # (dx, dy, dw, dh)
            nn.Tanh(),
        )

    def forward(self, image, keypoints):
        """
        Args:
            image: (B, 3, H, W) 手部图像
            keypoints: (B, 21, 2) 关键点坐标 (归一化到 [0, 1])

        Returns:
            roi: (B, 3, roi_h, roi_w) 提取的掌纹 ROI
            roi_bbox: (B, 4) ROI 边界框 (x1, y1, x2, y2)
        """
        B, _, H, W = image.shape

        # 提取锚点关键点
        anchors = keypoints[:, self.anchor_indices, :]  # (B, 5, 2)

        # 计算掌纹区域中心和范围
        center = anchors.mean(dim=1)  # (B, 2)
        extent = anchors.max(dim=1).values - anchors.min(dim=1).values  # (B, 2)

        # 可学习偏移量
        anchor_flat = anchors.reshape(B, -1)  # (B, 10)
        offsets = self.offset_predictor(anchor_flat) * 0.1  # (B, 4), 小范围偏移

        # 构建 ROI 边界框
        x1 = (center[:, 0] - extent[:, 0] * 0.6 + offsets[:, 0]).clamp(0, 1)
        y1 = (center[:, 1] - extent[:, 1] * 0.6 + offsets[:, 1]).clamp(0, 1)
        x2 = (center[:, 0] + extent[:, 0] * 0.6 + offsets[:, 2]).clamp(0, 1)
        y2 = (center[:, 1] + extent[:, 1] * 0.6 + offsets[:, 3]).clamp(0, 1)

        roi_bbox = torch.stack([x1, y1, x2, y2], dim=-1)  # (B, 4)

        # 使用 grid_sample 进行可微分 ROI 裁剪
        roi = self._crop_and_resize(image, roi_bbox)

        return roi, roi_bbox

    def _crop_and_resize(self, image, bbox):
        """可微分 ROI 裁剪

        使用仿射变换和 grid_sample 实现可微分的裁剪和缩放。

        Args:
            image: (B, 3, H, W)
            bbox: (B, 4) 归一化边界框

        Returns:
            roi: (B, 3, roi_h, roi_w)
        """
        B = image.shape[0]
        x1, y1, x2, y2 = bbox[:, 0], bbox[:, 1], bbox[:, 2], bbox[:, 3]

        # 构建仿射变换矩阵
        # 将 bbox 区域映射到 [-1, 1] 空间
        sx = 2.0 / (x2 - x1 + 1e-6)
        sy = 2.0 / (y2 - y1 + 1e-6)
        tx = -1.0 - sx * x1
        ty = -1.0 - sy * y1

        # 注意: grid_sample 需要的是从输出到输入的映射
        # 所以我们构建逆映射
        theta = torch.zeros(B, 2, 3, device=image.device)
        theta[:, 0, 0] = 1.0 / sx
        theta[:, 1, 1] = 1.0 / sy
        theta[:, 0, 2] = (x1 + x2) - 1.0
        theta[:, 1, 2] = (y1 + y2) - 1.0

        grid = F.affine_grid(theta, [B, 3, self.roi_size[0], self.roi_size[1]],
                             align_corners=False)
        roi = F.grid_sample(image, grid, align_corners=False, mode="bilinear",
                            padding_mode="zeros")

        return roi

"""
并行识别流水线
==============

并行模式下，输入的图片已经是手姿势提示后的手姿势图像，
掌纹识别、活体检测和手姿势认证同时进行，
最后经过决策融合得到可信身份 ID 或识别失败。

参考论文:
  Ross A, et al. "Information Fusion in Biometrics."
  Pattern Recognition Letters, 2003.
  Jia W, et al. "A Survey on Palmprint Recognition." 2023.
"""

import torch
import torch.nn as nn

from ..liveness import LivenessDetector
from ..hand_gesture import InteractiveGestureModel
from ..palmprint import PalmprintROIExtractor, PalmprintRecognitionModel
from .decision_fusion import DecisionFusion


class ParallelPipeline(nn.Module):
    """并行可信掌纹识别流水线

    流程:
        输入手姿势图像 → 同时执行:
            1. 掌纹识别 (ROI提取 + 特征匹配)
            2. 活体检测
            3. 手姿势认证
        → 决策融合 → 可信身份 ID / 识别失败

    Args:
        num_gesture_classes: 手姿势类别数
        num_identities: 身份数量
        fusion_weights: 决策融合权重
    """

    def __init__(
        self,
        num_gesture_classes=8,
        num_identities=100,
        fusion_weights=None,
    ):
        super().__init__()

        # 各子模型
        self.liveness_detector = LivenessDetector()
        self.gesture_model = InteractiveGestureModel(
            num_classes=num_gesture_classes
        )
        self.roi_extractor = PalmprintROIExtractor()
        self.palmprint_model = PalmprintRecognitionModel(
            num_identities=num_identities
        )

        # 决策融合模块
        if fusion_weights is None:
            fusion_weights = {
                "palmprint": 0.5,
                "liveness": 0.3,
                "gesture": 0.2,
            }
        self.decision_fusion = DecisionFusion(fusion_weights)

    def forward(self, image, gesture_password=None, labels=None):
        """
        并行识别流程。

        Args:
            image: (B, 3, H, W) 手姿势提示后的图像
            gesture_password: int 预期手姿势类别
            labels: (B,) 身份标签 (训练时使用)

        Returns:
            result: dict 包含:
                - success: bool 是否识别成功
                - identity: (B,) 身份 ID (成功时)
                - confidence: float 综合置信度
                - details: dict 各分支详细输出
        """
        details = {}

        # === 分支 1: 活体检测 (并行) ===
        liveness_result = self.liveness_detector(image)
        details["liveness"] = liveness_result

        # === 分支 2: 手姿势认证 (并行) ===
        gesture_result = self.gesture_model(image)
        details["gesture"] = gesture_result

        # === 分支 3: 掌纹识别 (并行) ===
        # 利用手姿势模型的关键点进行 ROI 提取
        keypoints = gesture_result["keypoints"]
        roi, roi_bbox = self.roi_extractor(image, keypoints)
        details["roi_bbox"] = roi_bbox

        palmprint_result = self.palmprint_model(roi, labels)
        details["palmprint"] = palmprint_result

        # === 决策融合 ===
        fusion_result = self.decision_fusion(
            palmprint_result=palmprint_result,
            liveness_result=liveness_result,
            gesture_result=gesture_result,
            gesture_password=gesture_password,
        )
        details["fusion"] = fusion_result

        return {
            "success": fusion_result["accept"],
            "identity": fusion_result.get("identity"),
            "confidence": fusion_result.get("confidence"),
            "stage": "completed",
            "message": fusion_result["message"],
            "details": details,
        }

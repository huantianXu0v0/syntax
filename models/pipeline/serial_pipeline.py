"""
串行识别流水线
==============

串行模式下，识别流程按顺序执行：
  图像采集 → 掌纹活体检测 → 手姿势认证 (可多次) → ROI 提取 → 掌纹识别

任何环节失败或不匹配则立即中断，只有全部通过才得到可信身份 ID。

参考论文:
  Jia W, et al. "A Survey on Palmprint Recognition." 2023.
  Kumar A, et al. "Personal Verification Using Palmprint and Hand Geometry
  Biometric." AVBPA 2003.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..liveness import LivenessDetector
from ..hand_gesture import InteractiveGestureModel
from ..palmprint import PalmprintROIExtractor, PalmprintRecognitionModel


class SerialPipeline(nn.Module):
    """串行可信掌纹识别流水线

    流程:
        1. 活体检测 → 若检测为攻击，中断
        2. 手姿势认证 → 若不匹配预设密码，中断（可多次认证）
        3. ROI 提取 + 掌纹识别 → 输出身份 ID

    Args:
        num_gesture_classes: 手姿势类别数
        num_identities: 身份数量
        max_retry: 手姿势认证最大重试次数
        confidence_threshold: 置信度阈值
    """

    def __init__(
        self,
        num_gesture_classes=8,
        num_identities=100,
        max_retry=3,
        confidence_threshold=0.85,
    ):
        super().__init__()
        self.max_retry = max_retry
        self.confidence_threshold = confidence_threshold

        # 各子模型
        self.liveness_detector = LivenessDetector()
        self.gesture_model = InteractiveGestureModel(
            num_classes=num_gesture_classes
        )
        self.roi_extractor = PalmprintROIExtractor()
        self.palmprint_model = PalmprintRecognitionModel(
            num_identities=num_identities
        )

    def forward(self, images, gesture_password=None, labels=None):
        """
        串行识别流程。

        Args:
            images: list of (B, 3, H, W) 多次采集的手部图像
                    (至少 1 张，最多 max_retry 张)
            gesture_password: list[int] 预设手姿势密码序列
            labels: (B,) 身份标签 (训练时使用)

        Returns:
            result: dict 包含:
                - success: bool 是否识别成功
                - identity: (B,) 身份 ID (成功时)
                - stage: str 失败阶段 (失败时)
                - details: dict 各阶段详细输出
        """
        details = {}

        # === 阶段 1: 活体检测 ===
        liveness_result = self.liveness_detector(images[0])
        details["liveness"] = liveness_result

        if not liveness_result["is_live"].all():
            return {
                "success": False,
                "identity": None,
                "stage": "liveness_detection",
                "message": "活体检测失败: 检测到攻击样本",
                "details": details,
            }

        # === 阶段 2: 手姿势认证 (可多次) ===
        if gesture_password is not None:
            gesture_matched = False

            for attempt_idx, img in enumerate(images[: self.max_retry]):
                gesture_result = self.gesture_model(img)
                details[f"gesture_attempt_{attempt_idx}"] = gesture_result

                # 检查预测的手姿势是否匹配密码序列中对应位置
                predicted_class = gesture_result["probs"].argmax(dim=-1)
                max_confidence = gesture_result["probs"].max(dim=-1).values

                if attempt_idx < len(gesture_password):
                    expected = gesture_password[attempt_idx]
                    # 检查预测类别匹配且置信度达标
                    class_match = (predicted_class == expected).all()
                    conf_pass = (
                        max_confidence >= self.confidence_threshold
                    ).all()

                    if class_match and conf_pass:
                        if attempt_idx == len(gesture_password) - 1:
                            gesture_matched = True
                    else:
                        break

            details["gesture_matched"] = gesture_matched

            if not gesture_matched:
                return {
                    "success": False,
                    "identity": None,
                    "stage": "gesture_authentication",
                    "message": "手姿势认证失败: 手势不匹配或置信度不足",
                    "details": details,
                }

        # === 阶段 3: ROI 提取 + 掌纹识别 ===
        # 使用最后一张图像进行掌纹识别
        final_image = images[-1]

        # 先获取关键点用于 ROI 提取
        _, keypoints = self.gesture_model.keypoint_detector(final_image)
        roi, roi_bbox = self.roi_extractor(final_image, keypoints)
        details["roi_bbox"] = roi_bbox

        # 掌纹识别
        palmprint_result = self.palmprint_model(roi, labels)
        details["palmprint"] = palmprint_result

        # 获取身份
        identity = palmprint_result["logits"].argmax(dim=-1)
        identity_confidence = F.softmax(
            palmprint_result["logits"], dim=-1
        ).max(dim=-1).values

        if (identity_confidence < self.confidence_threshold).any():
            return {
                "success": False,
                "identity": None,
                "stage": "palmprint_recognition",
                "message": "掌纹识别失败: 置信度不足",
                "details": details,
            }

        return {
            "success": True,
            "identity": identity,
            "confidence": identity_confidence,
            "stage": "completed",
            "message": "可信身份识别成功",
            "details": details,
        }

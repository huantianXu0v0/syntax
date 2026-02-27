"""
决策融合模块
=============

在并行识别流水线中，将掌纹识别、活体检测和手姿势认证
三个分支的结果进行融合决策，综合判定最终的身份识别结果。

参考论文:
  Ross A, et al. "Information Fusion in Biometrics."
  Pattern Recognition Letters, 2003.
  Kittler J, et al. "On Combining Classifiers."
  IEEE TPAMI, 1998.
  Kumar A, et al. "Biometric Score Fusion Using Adaptive Neuro-Fuzzy
  Inference System." IJCB 2011.

创新点:
  - 采用自适应权重决策融合策略，根据各分支输出的置信度动态调整
    融合权重，而非使用固定权重，提升异常场景下的鲁棒性。
  - 引入门控机制，当某一分支置信度极低时自动触发拒绝判定，
    实现安全优先的决策策略。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DecisionFusion(nn.Module):
    """自适应决策融合模块

    融合策略:
        1. 各分支输出置信度分数
        2. 通过门控网络动态计算融合权重
        3. 加权融合得到综合置信度分数
        4. 与阈值比较，判定最终结果

    Args:
        base_weights: 基础融合权重 (dict)
        threshold: 接受阈值 (默认 0.85)
        reject_threshold: 单分支拒绝阈值 (默认 0.3)
    """

    def __init__(self, base_weights=None, threshold=0.85, reject_threshold=0.3):
        super().__init__()
        self.threshold = threshold
        self.reject_threshold = reject_threshold

        if base_weights is None:
            base_weights = {
                "palmprint": 0.5,
                "liveness": 0.3,
                "gesture": 0.2,
            }
        self.register_buffer(
            "base_weights",
            torch.tensor([
                base_weights["palmprint"],
                base_weights["liveness"],
                base_weights["gesture"],
            ]),
        )

        # 自适应门控网络
        self.gate_network = nn.Sequential(
            nn.Linear(3, 16),
            nn.ReLU(inplace=True),
            nn.Linear(16, 3),
            nn.Softmax(dim=-1),
        )

    def forward(
        self,
        palmprint_result,
        liveness_result,
        gesture_result,
        gesture_password=None,
    ):
        """
        决策融合。

        Args:
            palmprint_result: 掌纹识别结果 dict
            liveness_result: 活体检测结果 dict
            gesture_result: 手姿势认证结果 dict
            gesture_password: 预期手姿势类别

        Returns:
            result: dict 包含:
                - accept: bool 是否接受
                - identity: 身份 ID
                - confidence: 综合置信度
                - message: 结果信息
        """
        # 提取各分支置信度
        palmprint_conf = F.softmax(
            palmprint_result["logits"], dim=-1
        ).max(dim=-1).values  # (B,)

        liveness_conf = liveness_result["probs"][:, 0]  # (B,) 真实概率

        gesture_probs = gesture_result["probs"]
        if gesture_password is not None:
            gesture_conf = gesture_probs[:, gesture_password]  # (B,)
        else:
            gesture_conf = gesture_probs.max(dim=-1).values  # (B,)

        # 堆叠置信度
        confidences = torch.stack(
            [palmprint_conf, liveness_conf, gesture_conf], dim=-1
        )  # (B, 3)

        # === 门控机制: 单分支极低置信度触发拒绝 ===
        reject_mask = (confidences < self.reject_threshold).any(dim=-1)  # (B,)

        # === 自适应权重融合 ===
        adaptive_weights = self.gate_network(confidences)  # (B, 3)
        # 与基础权重混合
        final_weights = 0.5 * self.base_weights.unsqueeze(0) + 0.5 * adaptive_weights

        # 加权融合
        fused_confidence = (final_weights * confidences).sum(dim=-1)  # (B,)

        # === 判定 ===
        accept = (fused_confidence >= self.threshold) & (~reject_mask)

        # 获取身份
        identity = palmprint_result["logits"].argmax(dim=-1)

        # 构建消息
        if accept.all():
            message = "可信身份识别成功"
        elif reject_mask.any():
            message = "识别失败: 某分支置信度极低，触发安全拒绝"
        else:
            message = "识别失败: 综合置信度未达阈值"

        return {
            "accept": accept,
            "identity": identity if accept.all() else None,
            "confidence": fused_confidence,
            "adaptive_weights": adaptive_weights,
            "branch_confidences": confidences,
            "message": message,
        }

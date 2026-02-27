"""
全局配置模块 (Global Configuration)

定义模型参数、训练超参数和推理配置。
"""


class GestureConfig:
    """交互式手姿势认证模型配置"""

    # HRFormer 手部关键点检测
    NUM_KEYPOINTS = 21          # 手部关键点数量 (MediaPipe 标准)
    HRFORMER_EMBED_DIM = 64     # HRFormer 嵌入维度
    HRFORMER_DEPTHS = [2, 2, 18, 2]     # 各阶段 Transformer 层数
    HRFORMER_NUM_HEADS = [2, 4, 8, 16]  # 各阶段注意力头数
    HEATMAP_SIZE = (64, 64)     # 热力图输出尺寸

    # SAM 分割配置
    SAM_MODEL_TYPE = "vit_b"        # SAM 模型类型: vit_b / vit_l / vit_h
    SAM_PROMPT_EMBED_DIM = 256      # 提示编码器嵌入维度
    SAM_FINETUNE_PROMPT_ONLY = True  # 仅微调提示编码器

    # 注意力模块
    SPATIAL_ATTN_KERNEL = 7     # 空间注意力卷积核大小
    SELF_ATTN_HEADS = 8         # 自注意力头数
    SELF_ATTN_DIM = 512         # 自注意力特征维度

    # MLP 分类器
    MLP_HIDDEN_DIMS = [512, 256, 128]  # MLP 隐藏层维度
    MLP_DROPOUT = 0.3                   # Dropout 率
    NUM_GESTURE_CLASSES = 8    # 手姿势类别数

    # 输入图像
    INPUT_SIZE = (256, 256)     # 输入图像尺寸


class PalmprintConfig:
    """掌纹识别模型配置"""

    ROI_SIZE = (128, 128)       # ROI 区域尺寸
    FEATURE_DIM = 512           # 特征向量维度
    BACKBONE = "CompactCNN"     # 骨干网络类型
    MARGIN = 0.5                # ArcFace 间隔
    SCALE = 64                  # ArcFace 缩放因子


class LivenessConfig:
    """活体检测模型配置"""

    INPUT_SIZE = (256, 256)     # 输入图像尺寸
    FEATURE_DIM = 256           # 特征维度
    NUM_CLASSES = 2             # 类别数 (真实 / 攻击)
    BACKBONE = "CDCN"           # 骨干网络: Central Difference CNN


class PipelineConfig:
    """流水线配置"""

    MODE = "serial"             # 流水线模式: serial / parallel
    MAX_RETRY = 3               # 最大重试次数 (串行模式手姿势认证)
    CONFIDENCE_THRESHOLD = 0.85  # 置信度阈值
    FUSION_WEIGHTS = {          # 并行模式决策融合权重
        "palmprint": 0.5,
        "liveness": 0.3,
        "gesture": 0.2,
    }

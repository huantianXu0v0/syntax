# 可信掌纹识别框架 — 模型设计文档

## 1. 概述

本项目设计并实现了一种**基于可交互式手姿势的可信掌纹识别框架**，通过融合掌纹识别、活体检测和交互式手姿势认证三重验证机制，构建完整的可信身份识别系统。

**核心创新点**：利用**微手姿势（大拇指和食指的伸直-弯曲、并拢-张开等动作组合）**作为动态行为密码，判定掌纹识别的主观意愿性，防止非自愿情况下的身份冒用。

---

## 2. 系统架构

### 2.1 三大核心模块

| 模块 | 功能 | 核心技术 |
|------|------|----------|
| **掌纹识别** | 身份识别 | Learnable Gabor + CompactCNN + ArcFace |
| **活体检测** | 防攻击检测 | CDCN (中心差分卷积) + 深度图估计 |
| **手姿势认证** | 主观意愿判定 | HRFormer → SAM → Spatial Attn → Self-Attn → MLP |

### 2.2 识别流程

**串行模式**：
```
图像采集 → 活体检测 → 手姿势认证(可多次) → ROI提取 + 掌纹识别 → 可信身份ID
                ↓ 失败          ↓ 失败                    ↓ 失败
              中断            中断                       中断
```

**并行模式**：
```
手姿势图像 → ┬─ 掌纹识别  ─┐
             ├─ 活体检测  ─┤→ 决策融合 → 可信身份ID / 识别失败
             └─ 手姿势认证 ─┘
```

---

## 3. 交互式手姿势认证模型

### 3.1 HRFormer 手部关键点检测

**基础方法**：使用 HRFormer (High-Resolution Transformer) 检测手部 21 个关键点，生成 2D 手部关节姿态图。

**论文依据**：
> Yuan Y, Fu R, Huang L, et al. "**HRFormer: High-Resolution Vision Transformer for Dense Prediction.**" *NeurIPS 2021*.

**创新改进**：
- 在高分辨率分支引入 **SE (Squeeze-and-Excitation) 通道注意力**，增强手指关节等细粒度区域的特征响应
- 采用**多尺度热力图监督策略**，在不同分辨率阶段均施加关键点损失，改善指尖等小目标检测精度
- 使用 **Soft-Argmax** 从热力图中提取亚像素级关键点坐标

**补充参考**：
> Hu J, Shen L, Sun G. "**Squeeze-and-Excitation Networks.**" *CVPR 2018*.
> Sun K, Xiao B, Liu D, et al. "**Deep High-Resolution Representation Learning for Visual Recognition.**" *CVPR 2019*.

### 3.2 SAM 手姿势分割

**基础方法**：利用 SAM (Segment Anything Model) 进行手姿势精确分割，将关键点位置作为点提示输入。

**论文依据**：
> Kirillov A, Mintun E, Ravi N, et al. "**Segment Anything.**" *ICCV 2023*.

**创新改进**：
- **仅微调 Prompt Encoder**（冻结 Image Encoder 和 Mask Decoder），实现参数高效微调 (Parameter-Efficient Fine-Tuning)
- 引入**关键点置信度加权机制**：对高置信度关键点赋予更高的提示权重，提升遮挡场景下的分割鲁棒性
- 设计**专用 KeypointPromptEncoder**：融合坐标嵌入、关键点类型嵌入和置信度门控

**补充参考**：
> Ma J, He Y, Li F, et al. "**Segment Anything in Medical Images.**" *Nature Communications, 2024*.

### 3.3 空间注意力模块

**基础方法**：基于 CBAM (Convolutional Block Attention Module) 的空间注意力机制，动态分配像素权重。

**论文依据**：
> Woo S, Park J, Lee J Y, et al. "**CBAM: Convolutional Block Attention Module.**" *ECCV 2018*.

**创新改进**：
- **多尺度感受野机制**：使用 3×3、7×7、11×11 三种尺度的卷积核分别捕捉指尖细节、手指弯曲和手指间关系
- **门控融合**：通过 1×1 卷积 + Sigmoid 学习各尺度的最优融合权重
- **InstanceNorm 归一化**：消除亮度和对比度差异，增强跨环境适应性

### 3.4 自注意力模块

**基础方法**：标准多头自注意力机制 (Multi-Head Self-Attention)。

**论文依据**：
> Vaswani A, Shazeer N, Parmar N, et al. "**Attention Is All You Need.**" *NeurIPS 2017*.
> Dosovitskiy A, Beyer L, Kolesnikov A, et al. "**An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale.**" *ICLR 2021*.

**创新改进**：
- 引入**相对位置编码 (Relative Position Bias, RPB)**，为注意力计算注入空间关系先验，增强手指间相对位置关系建模
- 采用 Pre-Norm 结构 (LayerNorm → Attention → Residual) 提高训练稳定性

**补充参考**：
> Liu Z, Lin Y, Cao Y, et al. "**Swin Transformer: Hierarchical Vision Transformer using Shifted Windows.**" *ICCV 2021*.

### 3.5 MLP 手姿势分类器

**基础方法**：多层感知机分类器。

**论文依据**：
> Tolstikhin I, Houlsby N, Kolesnikov A, et al. "**MLP-Mixer: An all-MLP Architecture for Vision.**" *NeurIPS 2021*.

**创新改进**：
- 引入 **Token-Mixing 层**：在分类前对不同空间位置的特征进行跨位置信息交换，增强手指间动作协同表征
- **组合损失函数**：Focal Loss + Label Smoothing，缓解微手势类间差异小导致的过拟合
- 使用 BatchNorm + GELU 激活 + Dropout 正则化

**补充参考**：
> Lin T Y, Goyal P, Girshick R, et al. "**Focal Loss for Dense Object Detection.**" *ICCV 2017*.

---

## 4. 掌纹识别模型

### 4.1 可学习 Gabor 卷积

**论文依据**：
> Liang X, Li Z, Fan Z, et al. "**CompNet: Competitive Neural Network for Palmprint Recognition Using Learnable Gabor Kernels.**" *IEEE Signal Processing Letters, 2021*.

**创新改进**：
- 将传统 Gabor 滤波器的 5 个参数（θ, σ, λ, γ, ψ）设为**可学习参数**，支持端到端优化
- 引入**可学习残差权重**：Gabor 先验 + 自由权重，融合传统纹理提取能力与数据驱动学习能力

### 4.2 ArcFace 损失

**论文依据**：
> Deng J, Guo J, Xue N, et al. "**ArcFace: Additive Angular Margin Loss for Deep Face Recognition.**" *CVPR 2019*.

### 4.3 ROI 提取

**论文依据**：
> Zhang D, Kong W K, You J, et al. "**Online Palmprint Identification.**" *IEEE TPAMI, 2003*.
> Zhong D, Du X, Zhong K. "**Decade Progress of Palmprint Recognition: A Brief Survey.**" *Neurocomputing, 2019*.

**创新改进**：
- 结合手部关键点信息进行**自适应 ROI 定位**，替代传统固定规则方法
- 引入**可学习偏移量**微调 ROI 边界
- 使用 **grid_sample** 实现可微分裁剪，支持端到端训练

---

## 5. 活体检测模型

### 5.1 中心差分卷积网络 (CDCN)

**论文依据**：
> Yu Z, Zhao C, Wang Z, et al. "**Searching Central Difference Convolutional Networks for Face Anti-Spoofing.**" *CVPR 2020*.
> Yu Z, Wan J, Qin Y, et al. "**Face Anti-Spoofing with Deep Neural Network Distillation.**" *IEEE TPAMI, 2023*.

**创新改进**：
- 将面部活体检测的 CDCN 架构**迁移至掌纹领域**
- 中心差分卷积 (CDC) 额外计算中心像素与邻域像素的差异信息，增强纹理梯度特征
- **多尺度深度估计辅助监督**：真实掌纹有深度信息，攻击样本（打印/翻拍）为平面

**补充参考**：
> Liu Y, Jourabloo A, Liu X. "**Deep Learning for Face Anti-Spoofing: A Survey.**" *IEEE TPAMI, 2023*.

---

## 6. 决策融合模块

### 6.1 自适应权重融合

**论文依据**：
> Ross A, Nandakumar K, Jain A K. "**Information Fusion in Biometrics.**" *Pattern Recognition Letters, 2003*.
> Kittler J, Hatef M, Duin R P W, et al. "**On Combining Classifiers.**" *IEEE TPAMI, 1998*.

**创新改进**：
- **自适应门控网络**：根据各分支输出的置信度**动态调整融合权重**（非固定权重），提升异常场景下的鲁棒性
- **安全门控拒绝机制**：当任一分支置信度极低（< reject_threshold）时，自动触发拒绝判定，实现安全优先策略
- 基础权重与自适应权重 50/50 混合，兼顾先验知识和数据驱动

---

## 7. 微手姿势定义

| 类别 | 手姿势 | 描述 |
|------|--------|------|
| 0 | 食指伸直 | 大拇指弯曲，食指伸直 |
| 1 | 大拇指伸直 | 大拇指伸直，食指弯曲 |
| 2 | 双指伸直 | 大拇指和食指均伸直 |
| 3 | 双指并拢 | 大拇指和食指并拢接触 |
| 4 | OK 手势 | 大拇指和食指形成圆环 |
| 5 | 双指弯曲 | 大拇指和食指均弯曲 |
| 6 | 拇指张开 | 大拇指张开，食指弯曲 |
| 7 | 交叉手势 | 食指和中指交叉 |

用户可设置由上述微手姿势组成的**动态行为密码序列**（如：[2, 3, 0] = 双指伸直 → 双指并拢 → 食指伸直），作为交互式认证的凭证。

---

## 8. 代码结构

```
models/
├── __init__.py              # 包初始化
├── config.py                # 全局配置
├── hand_gesture/            # 交互式手姿势认证模型
│   ├── __init__.py
│   ├── hrformer_keypoint.py # HRFormer 手部关键点检测 (+ SE 注意力)
│   ├── sam_segmentation.py  # SAM 手姿势分割 (+ 置信度加权提示编码)
│   ├── attention_modules.py # 空间注意力 (多尺度) + 自注意力 (RPE)
│   ├── gesture_classifier.py# MLP 分类器 (+ Token Mixing + Focal Loss)
│   └── gesture_model.py     # 完整手姿势认证模型
├── palmprint/               # 掌纹识别模型
│   ├── __init__.py
│   ├── roi_extraction.py    # 自适应 ROI 提取
│   └── palmprint_model.py   # Gabor-CNN + ArcFace 掌纹识别
├── liveness/                # 活体检测模型
│   ├── __init__.py
│   └── liveness_model.py    # CDCN + 深度图估计
└── pipeline/                # 识别流水线
    ├── __init__.py
    ├── serial_pipeline.py   # 串行流水线
    ├── parallel_pipeline.py # 并行流水线
    └── decision_fusion.py   # 自适应决策融合
```

---

## 9. 参考文献汇总

1. Yuan Y, et al. "HRFormer: High-Resolution Vision Transformer for Dense Prediction." *NeurIPS 2021*.
2. Kirillov A, et al. "Segment Anything." *ICCV 2023*.
3. Woo S, et al. "CBAM: Convolutional Block Attention Module." *ECCV 2018*.
4. Vaswani A, et al. "Attention Is All You Need." *NeurIPS 2017*.
5. Dosovitskiy A, et al. "An Image is Worth 16x16 Words." *ICLR 2021*.
6. Liu Z, et al. "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows." *ICCV 2021*.
7. Tolstikhin I, et al. "MLP-Mixer: An all-MLP Architecture for Vision." *NeurIPS 2021*.
8. Lin T Y, et al. "Focal Loss for Dense Object Detection." *ICCV 2017*.
9. Hu J, et al. "Squeeze-and-Excitation Networks." *CVPR 2018*.
10. Deng J, et al. "ArcFace: Additive Angular Margin Loss for Deep Face Recognition." *CVPR 2019*.
11. Liang X, et al. "CompNet: Competitive Neural Network for Palmprint Recognition Using Learnable Gabor Kernels." *IEEE SPL, 2021*.
12. Mathai P, et al. "Palm Print Recognition with PalmNet." *WACV 2019*.
13. Zhang D, et al. "Online Palmprint Identification." *IEEE TPAMI, 2003*.
14. Zhong D, et al. "Decade Progress of Palmprint Recognition: A Brief Survey." *Neurocomputing, 2019*.
15. Yu Z, et al. "Searching Central Difference Convolutional Networks for Face Anti-Spoofing." *CVPR 2020*.
16. Yu Z, et al. "Face Anti-Spoofing with Deep Neural Network Distillation." *IEEE TPAMI, 2023*.
17. Ross A, et al. "Information Fusion in Biometrics." *Pattern Recognition Letters, 2003*.
18. Kittler J, et al. "On Combining Classifiers." *IEEE TPAMI, 1998*.
19. Sun K, et al. "Deep High-Resolution Representation Learning for Visual Recognition." *CVPR 2019*.
20. Ma J, et al. "Segment Anything in Medical Images." *Nature Communications, 2024*.
21. Jia W, et al. "A Survey on Palmprint Recognition." *Pattern Recognition, 2023*.

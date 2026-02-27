<template>
  <view class="page-wrapper">
    <!-- 背景装饰层 -->
    <view class="bg-layer">
      <view class="bg-pattern"></view>
      <view class="bg-orb orb-1"></view>
      <view class="bg-orb orb-2"></view>
    </view>

    <!-- 顶部导航 -->
    <PcNavbar />

    <!-- 主内容区 -->
    <view class="container-xl main-content">

      <!-- Hero Section -->
      <view class="hero-section">
        <view class="hero-left">
          <view class="badge-capsule">
            <text class="dot"></text>
            <text>Trusted Palmprint Recognition</text>
          </view>

          <text class="hero-title">Interactive</text>
          <text class="hero-title gradient-text">Palmprint Auth.</text>

          <text class="hero-desc">
            基于可交互式手姿势的可信掌纹识别框架，融合
            <text class="highlight">掌纹识别</text>、
            <text class="highlight">活体检测</text> 和
            <text class="highlight">手姿势认证</text>
            三重验证，确保身份认证的安全性与主观意愿性。
          </text>

          <view class="hero-actions">
            <button class="btn-primary" @click="switchMode('serial')">
              串行模式
              <text class="btn-icon">→</text>
            </button>
            <button class="btn-secondary" @click="switchMode('parallel')">
              并行模式
              <text class="btn-icon">⇉</text>
            </button>
          </view>
        </view>

        <!-- 右侧: 流程架构图 -->
        <view class="hero-right">
          <view class="glow-bg"></view>
          <view class="arch-diagram">
            <view class="arch-title">{{ mode === 'serial' ? '串行流水线' : '并行流水线' }}</view>

            <!-- 串行模式 -->
            <view v-if="mode === 'serial'" class="pipeline-flow serial">
              <view class="step" :class="{ active: currentStep >= 0, done: currentStep > 0 }">
                <view class="step-icon">📷</view>
                <text class="step-label">图像采集</text>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
                <view class="step-icon">🛡️</view>
                <text class="step-label">活体检测</text>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
                <view class="step-icon">🤚</view>
                <text class="step-label">手姿势认证</text>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: currentStep >= 3, done: currentStep > 3 }">
                <view class="step-icon">🔍</view>
                <text class="step-label">ROI + 掌纹识别</text>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: currentStep >= 4 }">
                <view class="step-icon">✅</view>
                <text class="step-label">可信身份ID</text>
              </view>
            </view>

            <!-- 并行模式 -->
            <view v-else class="pipeline-flow parallel">
              <view class="step active">
                <view class="step-icon">📷</view>
                <text class="step-label">手姿势图像</text>
              </view>
              <view class="arrow">→</view>
              <view class="parallel-branches">
                <view class="branch" :class="{ done: branchStatus.palmprint }">
                  <view class="step-icon">🔍</view>
                  <text class="step-label">掌纹识别</text>
                </view>
                <view class="branch" :class="{ done: branchStatus.liveness }">
                  <view class="step-icon">🛡️</view>
                  <text class="step-label">活体检测</text>
                </view>
                <view class="branch" :class="{ done: branchStatus.gesture }">
                  <view class="step-icon">🤚</view>
                  <text class="step-label">手姿势认证</text>
                </view>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: fusionDone }">
                <view class="step-icon">⚖️</view>
                <text class="step-label">决策融合</text>
              </view>
              <view class="arrow">→</view>
              <view class="step" :class="{ active: fusionDone }">
                <view class="step-icon">✅</view>
                <text class="step-label">可信身份ID</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 模块介绍 -->
      <view class="modules-section">
        <text class="section-title">核心模块</text>
        <view class="modules-grid">
          <view v-for="(mod, idx) in modules" :key="idx" class="module-card">
            <view class="module-icon">{{ mod.icon }}</view>
            <text class="module-title">{{ mod.title }}</text>
            <text class="module-desc">{{ mod.desc }}</text>
            <view class="module-tags">
              <text v-for="(tag, ti) in mod.tags" :key="ti" class="tag">{{ tag }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 手姿势示例 -->
      <view class="gesture-section">
        <text class="section-title">微手姿势密码示例</text>
        <text class="section-desc">
          利用大拇指和食指的伸直-弯曲、并拢-张开等动作组合，设置动态行为密码序列
        </text>
        <view class="gesture-grid">
          <view v-for="(g, gi) in gestures" :key="gi" class="gesture-card"
                :class="{ selected: selectedGestures.includes(gi) }"
                @click="toggleGesture(gi)">
            <text class="gesture-emoji">{{ g.emoji }}</text>
            <text class="gesture-name">{{ g.name }}</text>
            <text class="gesture-detail">{{ g.detail }}</text>
          </view>
        </view>
        <view v-if="selectedGestures.length > 0" class="password-preview">
          <text class="password-label">当前密码序列:</text>
          <view class="password-sequence">
            <view v-for="(gi, si) in selectedGestures" :key="si" class="password-step">
              <text class="pw-num">{{ si + 1 }}</text>
              <text class="pw-emoji">{{ gestures[gi].emoji }}</text>
            </view>
          </view>
        </view>
      </view>

    </view>

    <!-- 底部页脚 -->
    <PcFooter />
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';

// 流水线模式
const mode = ref('serial');
const currentStep = ref(-1);
const fusionDone = ref(false);
const branchStatus = reactive({
  palmprint: false,
  liveness: false,
  gesture: false,
});

// 模块数据
const modules = ref([
  {
    icon: '🤚',
    title: '手姿势认证模型',
    desc: '基于 HRFormer 手部关键点检测 → SAM 手姿势分割 → 空间注意力 + 自注意力 → MLP 分类',
    tags: ['HRFormer', 'SAM', 'Spatial Attention', 'Self-Attention', 'MLP-Mixer'],
  },
  {
    icon: '🔍',
    title: '掌纹识别模型',
    desc: '可学习 Gabor 卷积核 + 紧凑 CNN 特征提取 + ArcFace 角度间隔损失，精确识别身份',
    tags: ['Learnable Gabor', 'CompactCNN', 'ArcFace'],
  },
  {
    icon: '🛡️',
    title: '活体检测模型',
    desc: '中心差分卷积网络 (CDCN) 捕捉掌纹纹理梯度信息，辅以深度图估计抵御攻击',
    tags: ['CDCN', 'Depth Estimation', 'Anti-Spoofing'],
  },
  {
    icon: '⚖️',
    title: '决策融合模块',
    desc: '自适应权重融合策略 + 门控安全拒绝机制，综合多模态结果输出可信身份',
    tags: ['Adaptive Fusion', 'Gated Rejection', 'Multi-modal'],
  },
]);

// 微手姿势数据
const gestures = ref([
  { emoji: '☝️', name: '食指伸直', detail: '大拇指弯曲，食指伸直' },
  { emoji: '👍', name: '大拇指伸直', detail: '大拇指伸直，食指弯曲' },
  { emoji: '✌️', name: '双指伸直', detail: '大拇指和食指均伸直' },
  { emoji: '🤏', name: '双指并拢', detail: '大拇指和食指并拢接触' },
  { emoji: '👌', name: 'OK手势', detail: '大拇指和食指形成圆环' },
  { emoji: '✊', name: '双指弯曲', detail: '大拇指和食指均弯曲' },
  { emoji: '🤙', name: '拇指张开', detail: '大拇指张开，食指弯曲' },
  { emoji: '🤞', name: '交叉手势', detail: '食指和中指交叉' },
]);
const selectedGestures = ref([]);

const switchMode = (m) => {
  mode.value = m;
  currentStep.value = -1;
  fusionDone.value = false;
  branchStatus.palmprint = false;
  branchStatus.liveness = false;
  branchStatus.gesture = false;

  // 模拟流程动画
  if (m === 'serial') {
    simulateSerial();
  } else {
    simulateParallel();
  }
};

const simulateSerial = () => {
  const steps = [0, 1, 2, 3, 4];
  steps.forEach((s, i) => {
    setTimeout(() => { currentStep.value = s; }, (i + 1) * 800);
  });
};

const simulateParallel = () => {
  setTimeout(() => { branchStatus.liveness = true; }, 600);
  setTimeout(() => { branchStatus.gesture = true; }, 900);
  setTimeout(() => { branchStatus.palmprint = true; }, 1200);
  setTimeout(() => { fusionDone.value = true; }, 1800);
};

const toggleGesture = (idx) => {
  const pos = selectedGestures.value.indexOf(idx);
  if (pos >= 0) {
    selectedGestures.value.splice(pos, 1);
  } else {
    selectedGestures.value.push(idx);
  }
};
</script>

<style lang="scss">
page { background-color: #F8FAFC; }

.bg-layer {
  position: fixed; top: 0; left: 0; width: 100%; height: 100vh;
  z-index: 0; pointer-events: none; overflow: hidden;
}
.bg-pattern {
  position: absolute; width: 100%; height: 100%;
  background-image: radial-gradient(#CBD5E1 1px, transparent 1px);
  background-size: 32px 32px; opacity: 0.4;
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
}
.bg-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; animation: float 10s ease-in-out infinite; }
.orb-1 { top: -100px; left: -100px; width: 600px; height: 600px; background: radial-gradient(circle, #a5f3fc 0%, #818cf8 100%); }
.orb-2 { top: 40%; right: -200px; width: 500px; height: 500px; background: radial-gradient(circle, #c4b5fd 0%, #f0abfc 100%); animation-delay: -5s; }
@keyframes float { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(20px, 30px); } }

.page-wrapper { position: relative; z-index: 1; }
.main-content { padding: 0 40px; max-width: 1280px; margin: 0 auto; }

/* Hero */
.hero-section {
  min-height: calc(100vh - 70px);
  display: flex; align-items: center; justify-content: space-between;
  gap: 60px;

  .hero-left {
    max-width: 500px; z-index: 2;
    .badge-capsule {
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(255,255,255,0.8); border: 1px solid #E2E8F0;
      padding: 6px 12px; border-radius: 100px;
      font-size: 13px; font-weight: 600; color: #475569;
      margin-bottom: 24px;
      .dot { width: 8px; height: 8px; background: #10B981; border-radius: 50%; }
    }
    .hero-title {
      display: block; font-size: 56px; font-weight: 800; line-height: 1.1;
      letter-spacing: -2px; color: #0F172A;
      &.gradient-text {
        background: linear-gradient(135deg, #6366F1 0%, #06B6D4 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      }
    }
    .hero-desc {
      font-size: 16px; color: #64748B; margin: 28px 0 36px; line-height: 1.7;
      .highlight { color: #0F172A; font-weight: 600; border-bottom: 2px solid #E2E8F0; }
    }
    .hero-actions {
      display: flex; gap: 16px;
      .btn-primary, .btn-secondary {
        height: 50px; padding: 0 28px; border-radius: 12px;
        font-size: 15px; font-weight: 600; border: none; cursor: pointer;
        display: flex; align-items: center; gap: 8px;
        transition: all 0.3s ease;
      }
      .btn-primary {
        background: #0F172A; color: #fff;
        box-shadow: 0 10px 25px -8px rgba(15,23,42,0.3);
        &:hover { transform: translateY(-2px); }
      }
      .btn-secondary {
        background: #fff; color: #334155; border: 1px solid #E2E8F0;
        &:hover { background: #F1F5F9; }
      }
    }
  }

  .hero-right {
    flex: 1; display: flex; justify-content: center; position: relative;
    .glow-bg { position: absolute; width: 100%; height: 100%; background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%); filter: blur(40px); }
  }
}

/* 架构图 */
.arch-diagram {
  background: rgba(30,41,59,0.95); backdrop-filter: blur(20px);
  border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);
  padding: 28px; min-width: 500px;
  box-shadow: 0 30px 60px -12px rgba(0,0,0,0.25);

  .arch-title {
    color: #94A3B8; font-size: 13px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 24px; text-align: center;
  }
}

.pipeline-flow {
  display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap;

  .step {
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08); transition: all 0.5s ease;
    min-width: 80px;

    &.active { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.3); }
    &.done { background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.3); }
    .step-icon { font-size: 24px; }
    .step-label { color: #E2E8F0; font-size: 11px; text-align: center; white-space: nowrap; }
  }
  .arrow { color: #64748B; font-size: 20px; }
}

.parallel-branches {
  display: flex; flex-direction: column; gap: 8px;
  .branch {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-radius: 10px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
    transition: all 0.5s ease;
    &.done { background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.3); }
    .step-icon { font-size: 18px; }
    .step-label { color: #E2E8F0; font-size: 12px; }
  }
}

/* 模块介绍 */
.modules-section {
  padding: 100px 0 80px;

  .section-title {
    display: block; font-size: 36px; font-weight: 800; color: #0F172A;
    text-align: center; margin-bottom: 50px; letter-spacing: -1px;
  }
}

.modules-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;

  .module-card {
    background: rgba(255,255,255,0.7); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.9); padding: 30px;
    border-radius: 16px; transition: all 0.3s ease;
    &:hover { transform: translateY(-4px); box-shadow: 0 20px 40px -12px rgba(0,0,0,0.08); }

    .module-icon { font-size: 32px; margin-bottom: 16px; }
    .module-title { display: block; font-size: 18px; font-weight: 700; color: #1E293B; margin-bottom: 10px; }
    .module-desc { display: block; font-size: 14px; color: #64748B; line-height: 1.6; margin-bottom: 16px; }
    .module-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .tag {
      background: #EEF2FF; color: #4F46E5; padding: 3px 10px;
      border-radius: 100px; font-size: 12px; font-weight: 500;
    }
  }
}

/* 手姿势 */
.gesture-section {
  padding: 60px 0 100px;

  .section-title {
    display: block; font-size: 36px; font-weight: 800; color: #0F172A;
    text-align: center; margin-bottom: 12px; letter-spacing: -1px;
  }
  .section-desc {
    display: block; font-size: 16px; color: #64748B; text-align: center;
    margin-bottom: 40px; max-width: 600px; margin-left: auto; margin-right: auto;
  }
}

.gesture-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;

  .gesture-card {
    background: rgba(255,255,255,0.7); border: 2px solid #E2E8F0;
    border-radius: 16px; padding: 24px; text-align: center;
    cursor: pointer; transition: all 0.3s ease;
    &:hover { transform: translateY(-3px); border-color: #A5B4FC; }
    &.selected { border-color: #6366F1; background: #EEF2FF; }
    .gesture-emoji { font-size: 40px; display: block; margin-bottom: 8px; }
    .gesture-name { display: block; font-size: 15px; font-weight: 600; color: #1E293B; margin-bottom: 4px; }
    .gesture-detail { display: block; font-size: 12px; color: #94A3B8; }
  }
}

.password-preview {
  margin-top: 30px; text-align: center;
  .password-label { display: block; font-size: 14px; color: #64748B; margin-bottom: 12px; }
  .password-sequence { display: flex; justify-content: center; gap: 12px; }
  .password-step {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    background: #0F172A; color: #fff; padding: 12px 18px; border-radius: 12px;
    .pw-num { font-size: 11px; color: #94A3B8; }
    .pw-emoji { font-size: 28px; }
  }
}

/* 响应式 */
@media screen and (max-width: 900px) {
  .hero-section { flex-direction: column; text-align: center; padding-top: 40px; }
  .hero-left { .hero-actions { justify-content: center; } }
  .hero-title { font-size: 42px !important; }
  .arch-diagram { min-width: auto; width: 100%; }
  .modules-grid { grid-template-columns: 1fr; }
  .gesture-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>

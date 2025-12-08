<template>
  <view class="quiz-workspace">
    
    <!-- 1. 沉浸式 Header -->
    <view class="quiz-header">
      <view class="header-left" @click="handleExit">
		<view class="header-right">
         <!-- 增加退出按钮 -->
         <view class="btn-close" @click="handleExit">Exit</view>
       </view>
        <text class="chapter-title">{{ title || 'Practice' }}</text>
      </view>
      
      <!-- 进度指示器 -->
      <view class="header-center">
        <text class="progress-text">Question {{ currentIndex + 1 }} / {{ questionList.length }}</text>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
        </view>
      </view>
      
      <view class="header-right">
        <view class="timer-badge">
          <text>⏱ {{ formatTime(duration) }}</text>
        </view>
      </view>
    </view>

    <!-- Loading 状态 -->
    <view class="loading-container" v-if="loading">
      <view class="spinner"></view>
      <text>Preparing your workspace...</text>
    </view>

    <!-- 2. 主工作区 (Split View) -->
    <view class="quiz-body" v-else-if="currentQ">
          
          <!-- 左侧：题目描述 -->
          <view class="panel-context">
            <scroll-view scroll-y class="scroll-inner">
              <view class="context-content">
                <view class="tags-row">
                  <view class="tag difficulty" :class="'lv-'+currentQ.difficulty">{{ getDifficultyLabel(currentQ.difficulty) }}</view>
                  <view class="tag type">{{ currentQ.type === 'code_gap' ? 'Code' : 'Choice' }}</view>
                </view>
                <text class="q-title">{{ currentQ.title }}</text>
                <!-- 这里可以增加 Markdown 渲染器，目前先用 Text -->
              </view>
            </scroll-view>
          </view>
    
          <!-- 右侧：交互区 -->
          <view class="panel-interaction">
            <scroll-view scroll-y class="scroll-inner">
              <view class="interaction-content">
                
                <!-- 1. 选择题组件 -->
                <QuizChoice 
                  v-if="currentQ.type === 'choice'"
                  :options="currentQ.content.options"
                  v-model="userAnswers[currentIndex]"
                  :show-result="hasSubmitted"
                  :correct-answer="currentQ.answer.correct_val"
                />
    
                <!-- 2. 代码填空组件 -->
                <QuizCodeGap 
                  v-else-if="currentQ.type === 'code_gap'"
                  :code="currentQ.content.code_snippet"
                  :lang="currentQ.content.language"
                  :gap-mode="currentQ.content.gap_mode"
                  :gap-options="currentQ.content.gap_options"
                  v-model="userAnswers[currentIndex]"
                  :show-result="hasSubmitted"
                  :correct-answer="currentQ.answer.correct_val"
                />
    
                <!-- 3. 结果解析卡片 (提交后显示) -->
                <view class="feedback-card" v-if="hasSubmitted" :class="isCurrentCorrect ? 'success' : 'error'">
                  <view class="fb-header">
                    <text class="fb-icon">{{ isCurrentCorrect ? '🎉' : '🤔' }}</text>
                    <text class="fb-title">{{ isCurrentCorrect ? 'Correct!' : 'Incorrect' }}</text>
                  </view>
                  <text class="fb-desc">{{ currentQ.answer.analysis || 'No analysis provided.' }}</text>
                </view>
    
              </view>
            </scroll-view>
          </view>
    
        </view>
    
        <!-- 底部 Action Bar -->
        <view class="action-bar">
          <view class="bar-inner">
            <view class="btn-group">
              <!-- 只有在未提交时才允许切题，或者你可以设计成随时切题 -->
              <button class="btn-secondary" @click="prevQuestion" :disabled="currentIndex === 0">Prev</button>
              
              <!-- 核心按钮逻辑 -->
              <button class="btn-primary" @click="handleMainAction" :class="btnStatusClass">
                {{ mainBtnText }}
              </button>
            </view>
          </view>
        </view>
    
      </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import QuizChoice from '@/components/Quiz/QuizChoice.vue';
import QuizCodeGap from '@/components/Quiz/QuizCodeGap.vue';

const quizCo = uniCloud.importObject('quiz-co', { customUI: true });

// 数据状态
const loading = ref(true);
const questionList = ref([]);
const currentIndex = ref(0);
const userAnswers = ref([]); // 二维数组：索引对应题号，值是该题的答案数组
const submitStatus = ref([]); // 记录每一题是否已提交

// 计算属性
const currentQ = computed(() => questionList.value[currentIndex.value]);
const currentAns = computed(() => userAnswers.value[currentIndex.value] || []);
const hasSubmitted = computed(() => submitStatus.value[currentIndex.value] === true);

// 判断当前题是否正确
const isCurrentCorrect = computed(() => {
  if (!currentQ.value) return false;
  // 简单的数组全等比较
  const correct = currentQ.value.answer.correct_val;
  const user = currentAns.value;
  if (!user || user.length !== correct.length) return false;
  // 注意：如果是填空题，顺序必须一致；选择题如果是多选，可能需要 sort
  return JSON.stringify(user) === JSON.stringify(correct);
});

// 按钮文本动态变化
const mainBtnText = computed(() => {
  if (!hasSubmitted.value) return 'Check Answer';
  if (currentIndex.value === questionList.value.length - 1) return 'Finish';
  return 'Next Question';
});

const btnStatusClass = computed(() => {
  if (!hasSubmitted.value) return '';
  return isCurrentCorrect.value ? 'btn-success' : 'btn-retry';
});

// 加载数据
onLoad((opt) => {
  if (opt.categoryId) {
    fetchQuestions(opt.categoryId);
  }
});

const fetchQuestions = async (id) => {
  try {
    const res = await quizCo.getQuestionsByChapter(id);
    if (res.errCode === 0) {
      questionList.value = res.data;
      // 初始化答案数组结构
      userAnswers.value = new Array(res.data.length).fill().map(() => []); 
      submitStatus.value = new Array(res.data.length).fill(false);
    }
  } finally {
    loading.value = false;
  }
};

// 核心：按钮点击逻辑
const handleMainAction = () => {
  // 1. 如果还没提交 -> 提交并校验
  if (!hasSubmitted.value) {
    if (currentAns.value.length === 0) {
      return uni.showToast({ title: 'Please answer first', icon: 'none' });
    }
    
    // 标记为已提交，界面会自动显示结果卡片
    submitStatus.value[currentIndex.value] = true;
    
    // 这里可以加震动反馈
    // if (!isCurrentCorrect.value) uni.vibrateShort();
    return;
  }

  // 2. 如果已提交 -> 进入下一题
  if (currentIndex.value < questionList.value.length - 1) {
    currentIndex.value++;
  } else {
    // 3. 最后一题 -> 退出或显示总分
    uni.showToast({ title: 'All Done!', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 1000);
  }
};

const prevQuestion = () => {
  if (currentIndex.value > 0) currentIndex.value--;
};

const handleExit = () => uni.navigateBack();

// 工具函数
const getDifficultyLabel = (diff) => {
  const map = { 1: 'Easy', 2: 'Medium', 3: 'Hard' };
  return map[diff] || 'Easy';
};

const startTimer = () => {
  timer = setInterval(() => { duration.value++; }, 1000);
};

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const handleKeydown = (e) => {
  if (e.key === 'ArrowRight') nextQuestion();
  if (e.key === 'ArrowLeft') prevQuestion();
};
</script>

<style lang="scss" scoped>
/* 沉浸式容器 */
.quiz-workspace {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #FFFFFF;
  color: #1E293B;
  overflow: hidden; /* 禁止整页滚动 */
}

/* 1. Header */
.quiz-header {
  height: 60px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #E2E8F0;
  background: #fff;
  flex-shrink: 0;
  
  .header-left {
    display: flex; align-items: center; gap: 12px; cursor: pointer;
    .back-icon { font-size: 18px; color: #64748B; transition: color 0.2s; &:hover { color: #0F172A; } }
    .chapter-title { font-weight: 600; font-size: 14px; max-width: 200px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  }
  
  .header-center {
    flex: 1; max-width: 400px; display: flex; flex-direction: column; align-items: center; gap: 4px;
    .progress-text { font-size: 12px; color: #94A3B8; font-weight: 500; }
    .progress-track {
      width: 100%; height: 4px; background: #F1F5F9; border-radius: 4px; overflow: hidden;
      .progress-fill { height: 100%; background: #0F172A; border-radius: 4px; transition: width 0.3s ease; }
    }
  }
  
  .header-right {
    .timer-badge {
      background: #F8FAFC; padding: 4px 10px; border-radius: 6px; font-size: 13px; color: #64748B; font-family: monospace; font-weight: 600; border: 1px solid #E2E8F0;
    }
  }
}

/* 2. Body (Split View) */
.quiz-body {
  flex: 1;
  display: flex;
  overflow: hidden; /* 内部滚动 */
  
  /* 左侧 */
  .panel-context {
    width: 40%; /* PC端占比 */
    background: #F8FAFC;
    border-right: 1px solid #E2E8F0;
    display: flex; flex-direction: column;
  }
  
  /* 右侧 */
  .panel-interaction {
    width: 60%;
    background: #FFFFFF;
    display: flex; flex-direction: column;
  }
  
  .scroll-inner { height: 100%; }
}

/* Context 内容样式 */
.context-content {
  padding: 40px;
  
  .tags-row {
    display: flex; gap: 8px; margin-bottom: 16px;
    .tag {
      font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 100px; text-transform: uppercase; letter-spacing: 0.5px;
      &.lv-1 { background: #DCFCE7; color: #166534; } /* Green */
      &.lv-2 { background: #FEF3C7; color: #92400E; } /* Yellow */
      &.lv-3 { background: #FEE2E2; color: #991B1B; } /* Red */
      &.type { background: #E0F2FE; color: #075985; } /* Blue */
    }
  }
  
  .q-title { font-size: 24px; font-weight: 800; line-height: 1.4; color: #0F172A; margin-bottom: 24px; display: block; }
  .q-desc-box { font-size: 16px; line-height: 1.8; color: #475569; }
}

/* Interaction 内容样式 */
.interaction-content {
  padding: 40px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80%;
  
  .component-placeholder {
    width: 100%; height: 300px; border: 2px dashed #E2E8F0; border-radius: 16px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    background: #F8FAFC;
    
    .ph-text { font-size: 18px; font-weight: 700; color: #94A3B8; margin-bottom: 8px; }
    .ph-sub { font-size: 14px; color: #CBD5E1; }
  }
}

/* 3. Footer Action Bar */
.action-bar {
  height: 80px;
  background: #fff;
  border-top: 1px solid #E2E8F0;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  z-index: 10;
  
  .bar-inner {
    width: 100%; max-width: 1200px; padding: 0 24px;
    display: flex; justify-content: flex-end; /* 按钮靠右 */
    
    .btn-group { display: flex; gap: 16px; }
    
    button {
      height: 48px; padding: 0 32px; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none;
      
      &.btn-primary { 
        background: #0F172A; color: #fff; 
        &:hover { background: #334155; transform: translateY(-1px); }
        &:active { transform: scale(0.98); }
      }
      &.btn-secondary {
        background: #fff; color: #475569; border: 1px solid #CBD5E1;
        &:hover { background: #F1F5F9; border-color: #94A3B8; }
        &:disabled { opacity: 0.5; cursor: not-allowed; }
      }
    }
  }
}

.loading-container, .empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: #64748B;
}

/* 📱 移动端适配 (Stack View) */
@media (max-width: 900px) {
  .quiz-body { flex-direction: column; overflow-y: auto; } /* 上下堆叠，且允许整体滚动 */
  
  .panel-context { 
    width: 100%; min-height: auto; border-right: none; border-bottom: 1px solid #E2E8F0; 
    .scroll-inner { height: auto; } /* 移动端取消内部滚动，改用整体滚动 */
  }
  .context-content { padding: 24px; }
  
  .panel-interaction { 
    width: 100%; min-height: 400px; 
    .scroll-inner { height: auto; }
  }
  .interaction-content { padding: 24px; }
  
  /* 隐藏 Header 中不重要的信息 */
  .header-center { display: none; } 
}
/* 结果反馈卡片 (Glassmorphism) */
.feedback-card {
  margin-top: 30px; padding: 20px; border-radius: 12px;
  width: 100%; max-width: 680px;
  animation: slideUp 0.3s ease;
  
  &.success { background: #ECFDF5; border: 1px solid #10B981; color: #065F46; }
  &.error { background: #FEF2F2; border: 1px solid #EF4444; color: #991B1B; }
  
  .fb-header { display: flex; align-items: center; margin-bottom: 8px; font-weight: 800; font-size: 18px; }
  .fb-icon { margin-right: 10px; }
  .fb-desc { font-size: 15px; line-height: 1.6; opacity: 0.9; }
}

/* 按钮状态变化 */
.btn-primary {
  transition: all 0.3s !important;
  &.btn-success { background: #10B981 !important; } /* 答对变绿 */
  &.btn-retry { background: #0F172A !important; } /* 答错保持深色 (Next) */
}

.btn-close { font-size: 14px; font-weight: 600; cursor: pointer; color: #64748B; &:hover{color:#000} }

@keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>
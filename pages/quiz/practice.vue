<template>
  <view class="quiz-workspace">
    
    <!-- 1. Header (增加题目列表入口) -->
    <view class="quiz-header">
      <view class="header-left" @click="handleExit">
        <view class="btn-close">Exit</view>
      </view>
      
      <!-- 进度条 -->
      <view class="header-center">
        <text class="progress-text">Question {{ currentIndex + 1 }} / {{ questionList.length }}</text>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
        </view>
      </view>
      
      <view class="header-right">
        <!-- 题目列表开关 (新增) -->
        <view class="list-toggle" @click="toggleDrawer">
          <text class="icon-list">☰</text>
          <text class="list-text">{{ answeredCount }}/{{ questionList.length }}</text>
        </view>

        <!-- 计时器 -->
        <view class="timer-wrapper">
          <view class="reset-btn" v-if="duration > 0" @click.stop="resetTimer">↺</view>
          <view class="timer-badge" :class="{ 'is-running': isTimerRunning }" @click="toggleTimer">
            <text class="timer-icon">{{ isTimerRunning ? '⏸' : '▶️' }}</text>
            <text>{{ formatTime(duration) }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Loading -->
    <view class="loading-container" v-if="loading">
      <view class="spinner"></view>
      <text>Preparing your workspace...</text>
    </view>

    <!-- 2. 主工作区 -->
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
          </view>
        </scroll-view>
      </view>

      <!-- 右侧：交互区 -->
      <view class="panel-interaction">
        <scroll-view scroll-y class="scroll-inner">
          <view class="interaction-content">
            <!-- 组件 -->
            <QuizChoice 
              v-if="currentQ.type === 'choice'"
              :options="currentQ.content.options"
              v-model="userAnswers[currentIndex]"
              :show-result="hasSubmitted"
              :correct-answer="currentResult?.correct_val || []" 
            />
            <QuizCodeGap 
              v-else-if="currentQ.type === 'code_gap'"
              :code="currentQ.content.code_snippet"
              :lang="currentQ.content.language"
              :gap-mode="currentQ.content.gap_mode"
              :gap-options="currentQ.content.gap_options"
              v-model="userAnswers[currentIndex]"
              :show-result="hasSubmitted"
              :correct-answer="currentResult?.correct_val || []"
            />

            <!-- 结果解析 -->
            <view class="feedback-card" v-if="hasSubmitted && currentResult" :class="isCurrentCorrect ? 'success' : 'error'">
              <view class="fb-header">
                <text class="fb-icon">{{ isCurrentCorrect ? '🎉' : '🤔' }}</text>
                <text class="fb-title">{{ isCurrentCorrect ? 'Correct!' : 'Incorrect' }}</text>
              </view>
              <text class="fb-desc">{{ currentResult.analysis || 'No analysis provided.' }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 3. 底部 Action Bar (按钮逻辑升级) -->
    <view class="action-bar">
      <view class="bar-inner">
        <view class="btn-group">
          <button class="btn-secondary" @click="prevQuestion" :disabled="currentIndex === 0">Prev</button>
          
          <!-- Skip 按钮：未提交且不是最后一题时显示 -->
          <button 
            class="btn-secondary" 
            v-if="!hasSubmitted && currentIndex < questionList.length - 1" 
            @click="skipQuestion"
          >
            Skip
          </button>

          <!-- 主按钮：Check / Next / Finish -->
          <button class="btn-primary" @click="handleMainAction" :class="btnStatusClass">
            {{ mainBtnText }}
          </button>
        </view>
      </view>
    </view>

    <!-- 4. 题目导览抽屉 (Drawer) -->
    <view class="drawer-overlay" v-if="showDrawer" @click="toggleDrawer">
      <view class="drawer-panel" @click.stop>
        <view class="drawer-header">
          <text class="dh-title">Question List</text>
          <view class="dh-stats">
            <text class="ds-item"><text class="dot green"></text> Correct</text>
            <text class="ds-item"><text class="dot red"></text> Wrong</text>
            <text class="ds-item"><text class="dot gray"></text> Todo</text>
          </view>
        </view>
        
        <scroll-view scroll-y class="drawer-body">
          <view class="q-grid">
            <view 
              class="q-cell" 
              v-for="(item, index) in questionList" 
              :key="item._id"
              :class="getQCellClass(index)"
              @click="jumpToQuestion(index)"
            >
              {{ index + 1 }}
              <!-- 右上角小标记：当前题 -->
              <view class="current-indicator" v-if="index === currentIndex"></view>
            </view>
          </view>
        </scroll-view>

        <!-- 未完成提示 -->
        <view class="drawer-footer" v-if="unansweredCount > 0">
          <text class="warn-text">⚠️ You have {{ unansweredCount }} unanswered questions.</text>
        </view>
      </view>
    </view>

    <!-- 结算弹窗 (保持不变) -->
    <view class="result-modal" v-if="showSummary">
      <!-- ... 这里复用之前的结算弹窗代码 ... -->
      <view class="modal-backdrop"></view>
      <view class="modal-content">
        <view class="modal-icon">🏆</view>
        <text class="modal-title">Session Complete!</text>
        <view class="stats-grid">
          <view class="stat-box highlight">
            <text class="val">{{ correctCount }} / {{ questionList.length }}</text>
            <text class="label">Correct Answers</text>
          </view>
          <view class="stat-box">
            <text class="val">{{ formatTime(duration) }}</text>
            <text class="label">Time Spent</text>
          </view>
        </view>
        <view class="modal-actions">
          <button class="btn-outline" @click="handleRetry">Try Again</button>
          <button class="btn-fill" @click="handleExit">Back to Library</button>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { onLoad, onUnload } from '@dcloudio/uni-app';
import QuizChoice from '@/components/Quiz/QuizChoice.vue';
import QuizCodeGap from '@/components/Quiz/QuizCodeGap.vue';
import { getCloudObject } from '@/utils/cloud.js';

const quizCo = getCloudObject('quiz-co');

// 状态
const loading = ref(true);
const questionList = ref([]);
const currentIndex = ref(0);
const userAnswers = ref([]); 
const submitStatus = ref([]); 
// 存储题目解析记录结构: { 0: { is_correct: true, analysis: '...', correct_val: [...] }, ... }
const resultsLog = ref({}); 
const currentResult = ref(null);
const showDrawer = ref(false); // 抽屉开关
const showSummary = ref(false); // 结算开关

// 计时器状态
const duration = ref(0);
const isTimerRunning = ref(false);
let timerInterval = null;

// --- 计算属性 ---
const currentQ = computed(() => questionList.value[currentIndex.value]);
const currentAns = computed(() => userAnswers.value[currentIndex.value] || []);
const hasSubmitted = computed(() => submitStatus.value[currentIndex.value] === true);
const progressPercent = computed(() => ((currentIndex.value + 1) / questionList.value.length) * 100);

const isCurrentCorrect = computed(() => currentResult.value?.is_correct || false);

// 统计逻辑
const correctCount = computed(() => {
  return Object.values(resultsLog.value).filter(res => res && res.is_correct).length;
});
const answeredCount = computed(() => submitStatus.value.filter(v => v).length);
const unansweredCount = computed(() => questionList.value.length - answeredCount.value);

// --- 监听切题 (核心修复逻辑) ---
// 每次 currentIndex 变化时，自动检查是否有缓存的结果
watch(currentIndex, (newIndex) => {
  if (submitStatus.value[newIndex] && resultsLog.value[newIndex]) {
    // 如果这道题做过，且有缓存结果 -> 恢复显示
    currentResult.value = resultsLog.value[newIndex];
  } else {
    // 没做过 -> 清空结果
    currentResult.value = null;
  }
});

// 按钮文字逻辑
const mainBtnText = computed(() => {
  if (!hasSubmitted.value) return 'Check Answer';
  if (currentIndex.value === questionList.value.length - 1) return 'Finish';
  return 'Next Question';
});

const btnStatusClass = computed(() => {
  if (!hasSubmitted.value) return '';
  return isCurrentCorrect.value ? 'btn-success' : 'btn-retry';
});

// --- 初始化 ---
onLoad((opt) => {
  if (opt.categoryId) fetchQuestions(opt.categoryId);
  if (opt.startIndex) currentIndex.value = parseInt(opt.startIndex);
  // 自动开始计时 (可选)
  // toggleTimer();
});

const fetchQuestions = async (id) => {
  try {
    const res = await quizCo.getQuestionsByChapter(id);
    if (res.errCode === 0) {
      questionList.value = res.data;
      userAnswers.value = new Array(res.data.length).fill().map(() => []); 
      submitStatus.value = new Array(res.data.length).fill(false);
    }
  } finally {
    loading.value = false;
  }
};

// --- 核心操作 ---

// 1. 跳过
// --- 修改 Skip 逻辑 ---
const skipQuestion = () => {
  if (currentIndex.value < questionList.value.length - 1) {
    currentIndex.value++;
    // 🔴 同样交由 watch 处理状态重置
  }
};

// 2. 主按钮动作
// --- 修改 handleMainAction (存入缓存) ---
const handleMainAction = async () => {
  // A. 提交校验
  if (!hasSubmitted.value) {
    if (currentAns.value.length === 0) return uni.showToast({ title: 'Please enter answer', icon: 'none' });
    
    uni.showLoading({ title: 'Checking...' });
    try {
      const res = await quizCo.checkAnswer(
        currentQ.value._id, 
        currentAns.value, 
        duration.value,
        'practice'
      );
      
      if (res.errCode === 0) {
        // 1. 设置当前显示结果
        currentResult.value = res.data;
        // 2. 标记已提交
        submitStatus.value[currentIndex.value] = true;
        // 3. 🔴 核心：将完整结果存入缓存池，供回头查看使用
        resultsLog.value[currentIndex.value] = res.data;
        
        if (!isTimerRunning.value) toggleTimer();
      } else {
        uni.showToast({ title: 'Check failed', icon: 'none' });
      }
    } finally {
      uni.hideLoading();
    }
    return;
  }

  // B. 下一题 (Next)
  if (currentIndex.value < questionList.value.length - 1) {
    currentIndex.value++;
    // 🔴 不需要手动设置 currentResult = null 了，watch 会自动处理
  } else {
    // C. 结算
    handleFinish();
  }
};

// 3. 完成检查
const handleFinish = () => {
  // 检查是否有未完成的题目
  if (unansweredCount.value > 0) {
    uni.showToast({ title: `You have ${unansweredCount.value} unfinished questions`, icon: 'none' });
    // 自动打开抽屉，让用户去选
    showDrawer.value = true;
  } else {
    // 全部完成，显示结算
    if (isTimerRunning.value) toggleTimer();
    showSummary.value = true;
  }
};

// --- 抽屉相关 ---
const toggleDrawer = () => showDrawer.value = !showDrawer.value;

const jumpToQuestion = (index) => {
  currentIndex.value = index;

  showDrawer.value = false;
};

// --- 修改 Drawer 样式判断逻辑 ---
const getQCellClass = (index) => {
  const classes = [];
  if (index === currentIndex.value) classes.push('active-border');
  
  if (submitStatus.value[index]) {
     // 🔴 核心修复：判断 resultsLog[index]?.is_correct
        const log = resultsLog.value[index];
        // 安全判断：log 必须存在且 is_correct 为 true 才算对
        const isRight = log && log.is_correct === true;
        
        classes.push(isRight ? 'correct' : 'wrong');
  } else {
    classes.push('todo');
  }
  
  return classes.join(' ');
};

// --- 计时器与通用 ---
const toggleTimer = () => {
  if (isTimerRunning.value) {
    clearInterval(timerInterval);
    isTimerRunning.value = false;
  } else {
    isTimerRunning.value = true;
    timerInterval = setInterval(() => { duration.value++; }, 1000);
  }
};

const resetTimer = () => {
  uni.vibrateShort();
  if (timerInterval) clearInterval(timerInterval);
  isTimerRunning.value = false;
  duration.value = 0;
};

const prevQuestion = () => {
  if (currentIndex.value > 0) {
      currentIndex.value--;
      currentResult.value = null;
  }
};

const handleExit = () => uni.navigateBack();
const handleRetry = () => {
    // 重置所有状态
    currentIndex.value = 0;
    userAnswers.value = userAnswers.value.map(() => []);
    submitStatus.value = submitStatus.value.map(() => false);
    resultsLog.value = {};
    currentResult.value = null;
    duration.value = 0;
    showSummary.value = false;
    showDrawer.value = false;
};

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const getDifficultyLabel = (d) => ({1:'Easy',2:'Medium',3:'Hard'}[d] || 'Easy');

onUnload(() => { if (timerInterval) clearInterval(timerInterval); });
</script>

<style lang="scss" scoped>
/* 继承之前的全局布局 */
.quiz-workspace {
  height: 100vh; display: flex; flex-direction: column; background: #FFF; color: #1E293B; overflow: hidden;
}

/* Header 优化 */
.quiz-header {
  height: 60px; padding: 0 24px; border-bottom: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between;
  
  .header-left .btn-close { font-weight: 600; color: #64748B; cursor: pointer; &:hover{color:#0F172A} }
  
  .header-center { flex: 1; max-width: 300px; display: flex; flex-direction: column; align-items: center; }
  .progress-text { font-size: 12px; color: #94A3B8; margin-bottom: 4px; }
  .progress-track { width: 100%; height: 4px; background: #F1F5F9; border-radius: 4px; overflow: hidden; }
  .progress-fill { height: 100%; background: #0F172A; transition: width 0.3s; }

  .header-right { display: flex; align-items: center; gap: 16px; }
  
  /* 列表开关 */
  .list-toggle {
    display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 10px; border-radius: 8px; transition: background 0.2s;
    &:hover { background: #F1F5F9; }
    .icon-list { font-size: 16px; }
    .list-text { font-size: 13px; font-weight: 600; color: #475569; }
  }

  .timer-wrapper { display: flex; align-items: center; gap: 8px; }
  .reset-btn { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: #F1F5F9; border-radius: 50%; color: #64748B; font-size: 14px; cursor: pointer; &:hover { transform: rotate(-90deg); color: #0F172A; } }
  .timer-badge { 
    background: #F1F5F9; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; color: #64748B; display: flex; gap: 6px; cursor: pointer; border: 1px solid transparent;
    &.is-running { background: #ECFDF5; color: #059669; border-color: #10B981; }
  }
}

/* 抽屉样式 (Drawer) */
.drawer-overlay {
  position: fixed; top: 60px; bottom: 0; left: 0; right: 0; 
  background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(2px); z-index: 50;
  display: flex; justify-content: flex-end; /* 右侧滑出 */
}

.drawer-panel {
  width: 320px; background: #fff; height: 100%; border-left: 1px solid #E2E8F0;
  display: flex; flex-direction: column; animation: slideLeft 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: -10px 0 30px rgba(0,0,0,0.1);
  overflow-y: auto;
  
  .drawer-header {
    padding: 20px; border-bottom: 1px solid #E2E8F0;
    .dh-title { font-size: 18px; font-weight: 800; display: block; margin-bottom: 12px; }
	/* --- 修复抽屉中的圆点颜色 --- */
	.dh-stats, .dh-legend {
		/* 确保父容器布局正确 */
		display: flex; gap: 16px; 
		.ds-item, .legend-item { 
			font-size: 12px; color: #64748B; 
			display: flex; align-items: center; gap: 6px; 
		}
	}

	/* 定义圆点基础样式 */
	.dot {
		width: 8px; 
		height: 8px; 
		border-radius: 50%;
		display: inline-block;
		/* 默认灰色 */
		background: #E2E8F0; 
  
		/* 状态颜色 */
		&.green { background: #10B981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }
		&.red   { background: #EF4444; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2); }
		&.gray  { background: #E2E8F0; }
	}
  }

  .drawer-body { flex: 1; padding: 20px; width: 80%;}
  
  /* 题目网格 */
  .q-grid {
    display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px;
	padding: 10px;
  }
  
  .q-cell {
    aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
    border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; position: relative;
    background: #F8FAFC; color: #64748B; border: 1px solid transparent; transition: all 0.2s;
    
    &:hover { transform: scale(1.05); }
    
    &.correct { background: #ECFDF5; color: #059669; border-color: #10B981; }
    &.wrong { background: #FEF2F2; color: #EF4444; border-color: #EF4444; }
    &.todo { background: #F1F5F9; }
    
    &.active-border { border: 2px solid #0F172A; color: #0F172A; } /* 当前题 */
    
    .current-indicator {
      position: absolute; top: 4px; right: 4px; width: 6px; height: 6px; background: #0F172A; border-radius: 50%;
    }
  }

  .drawer-footer {
    padding: 16px; background: #FFF7ED; border-top: 1px solid #FFEDD5; text-align: center;
    .warn-text { font-size: 13px; color: #C2410C; font-weight: 500; }
  }
}

@keyframes slideLeft { from { transform: translateX(100%); } to { transform: translateX(0); } }

/* Body & Footer 样式复用之前的 */
.quiz-body { flex: 1; display: flex; overflow: hidden; }
.panel-context { width: 40%; background: #F8FAFC; border-right: 1px solid #E2E8F0; display: flex; flex-direction: column; }
.panel-interaction { width: 60%; display: flex; flex-direction: column; }
.scroll-inner { height: 100%; }
.context-content, .interaction-content { padding: 40px; }

.action-bar {
  height: 80px; border-top: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: center;
  .bar-inner { width: 100%; max-width: 1200px; padding: 0 24px; display: flex; justify-content: flex-end; }
  .btn-group { display: flex; gap: 12px; }
  
  button {
    height: 48px; padding: 0 24px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; border: none;
    &.btn-primary { background: #0F172A; color: #fff; &.btn-success{background:#10B981} &.btn-retry{background:#0F172A} }
    &.btn-secondary { background: #fff; border: 1px solid #CBD5E1; color: #475569; &:hover{background:#F1F5F9} }
  }
}

.tags-row { display: flex; gap: 8px; margin-bottom: 16px; .tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: 700; text-transform: uppercase; &.type{background:#E0F2FE;color:#0284C7} &.lv-1{background:#DCFCE7;color:#166534} } }
.q-title { font-size: 24px; font-weight: 800; color: #0F172A; line-height: 1.4; }

/* 结算弹窗复用之前的样式... */
.result-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal-backdrop { position: absolute; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); }
.modal-content { position: relative; z-index: 2; background: #fff; width: 400px; border-radius: 24px; padding: 40px 30px; text-align: center; }
.modal-icon { font-size: 48px; margin-bottom: 16px; }
.modal-title { font-size: 24px; font-weight: 800; display: block; margin-bottom: 24px; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 30px; }
.stat-box { background: #F8FAFC; padding: 16px; border-radius: 12px; .val{font-size:20px;font-weight:700} .label{font-size:12px;color:#64748B} &.highlight{background:#ECFDF5; .val{color:#059669}} }
.modal-actions { display: flex; gap: 12px; button{flex:1;height:44px;border-radius:10px;font-weight:600;cursor:pointer} .btn-outline{background:#fff;border:1px solid #E2E8F0} .btn-fill{background:#0F172A;color:#fff;border:none} }

/* 反馈卡片 */
.feedback-card { margin-top: 30px; padding: 20px; border-radius: 12px; &.success{background:#ECFDF5;border:1px solid #10B981;color:#065F46} &.error{background:#FEF2F2;border:1px solid #EF4444;color:#991B1B} .fb-header{display:flex;align-items:center;font-weight:800;margin-bottom:8px; gap:8px} .fb-desc{line-height:1.6} }

@media(max-width: 900px) {
  .quiz-body { flex-direction: column; overflow-y: auto; }
  .panel-context, .panel-interaction { width: 100%; min-height: auto; }
  .drawer-panel { width: 80%; }
}
</style>
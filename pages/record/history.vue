<template>
  <view class="history-page">
    <PcNavbar />

    <view class="container-xl content-wrapper">
      
      <!-- 1. 页面头部 (Header & Stats) -->
      <view class="page-header">
        <view class="title-group">
          <text class="main-title">Learning History</text>
          <text class="sub-title">Track your progress and review past challenges.</text>
        </view>
        
        <!-- 顶部迷你仪表盘 -->
        <view class="stats-mini">
          <view class="stat-pill">
            <text class="label">Total</text>
            <text class="val">{{ totalCount }}</text>
          </view>
          <view class="stat-pill">
            <text class="label">Accuracy</text>
            <text class="val highlight">{{ accuracy }}%</text>
          </view>
        </view>
      </view>

      <!-- 2. 时光轴列表 (Timeline) -->
      <view class="timeline-container" v-if="historyList.length > 0">
        <!-- 贯穿线 -->
        <view class="timeline-line"></view>

        <view 
          class="timeline-item animate-up" 
          v-for="(item, index) in historyList" 
          :key="item._id"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          
          <!-- 左侧：时间节点 -->
          <view class="time-node">
            <text class="time-date">{{ formatDate(item.create_date, 'date') }}</text>
            <text class="time-clock">{{ formatDate(item.create_date, 'time') }}</text>
          </view>

          <!-- 中间：状态圆点 -->
          <view class="status-dot-wrapper">
            <view class="dot" :class="item.is_correct ? 'success' : 'error'">
              <text class="dot-icon">{{ item.is_correct ? '✓' : '✕' }}</text>
            </view>
          </view>

          <!-- 右侧：记录卡片 -->
          <view class="record-card" @click="reviewQuestion(item)">
            <view class="card-header">
              <view class="tags">
                <text class="tag category">{{ item.category_name || 'General' }}</text>
                <text class="tag type">{{ item.question_type === 'code_gap' ? 'Code' : 'Choice' }}</text>
              </view>
              <text class="duration">⏱ {{ formatDuration(item.duration) }}</text>
            </view>
            
            <text class="q-title">{{ item.question_title || 'Untitled Question' }}</text>
            
            <view class="card-footer">
              <text class="score">Score: <text :class="item.is_correct ? 's-high' : 's-low'">{{ item.score }}</text></text>
              <text class="review-link">Review Answer →</text>
            </view>
          </view>
        </view>

        <!-- 加载更多按钮 -->
        <view class="load-more-wrapper">
          <button 
            v-if="hasMore" 
            class="btn-load-more" 
            :loading="loading" 
            @click="loadMore"
          >
            {{ loading ? 'Loading...' : 'Load More History' }}
          </button>
          <text v-else class="no-more-text">End of the journey.</text>
        </view>

      </view>

      <!-- 3. 空状态 (Empty State) -->
      <view class="empty-state" v-else-if="!loading">
        <view class="empty-icon">📂</view>
        <text class="empty-text">No records found yet.</text>
        <button class="btn-go" @click="goStudy">Start Practicing</button>
      </view>
      
      <!-- 初始加载中 -->
      <view class="loading-state" v-else>
        <view class="spinner"></view>
      </view>

    </view>
	
    <PcFooter />
	
	<!-- 4. 复习弹窗 (Review Modal) -->
	    <view class="review-modal" v-if="showReviewModal" @click.self="closeReview">
	      <view class="modal-body">
	        
	        <!-- Loading 态 -->
	        <view class="modal-loading" v-if="reviewLoading">
	          <view class="spinner"></view>
	        </view>
	
	        <!-- 内容态 -->
	        <template v-else-if="reviewData">
	          <!-- 弹窗 Header -->
	          <view class="m-header">
	            <view class="m-title-group">
	              <text class="tag" :class="reviewData.record.is_correct ? 'success' : 'error'">
	                {{ reviewData.record.is_correct ? 'Correct' : 'Mistake' }}
	              </text>
	              <text class="title">Review Challenge</text>
	            </view>
	            <view class="btn-close" @click="closeReview">✕</view>
	          </view>
	
	          <scroll-view scroll-y class="m-scroll-content">
	            <view class="m-content">
	              
	              <!-- 题目区域 -->
	              <text class="q-title">{{ reviewData.question.title }}</text>
	              
	              <!-- 组件复用区：强制开启 showResult=true -->
	              <view class="component-wrapper">
	                
	                <!-- 选择题 -->
	                <QuizChoice 
	                  v-if="reviewData.question.type === 'choice'"
	                  :options="reviewData.question.content.options"
	                  :modelValue="reviewData.record.user_answer"
	                  :show-result="true"
	                  :correct-answer="reviewData.question.answer.correct_val"
	                />
	
	                <!-- 代码填空 -->
	                <QuizCodeGap 
	                  v-else
	                  :code="reviewData.question.content.code_snippet"
	                  :lang="reviewData.question.content.language"
	                  :gap-mode="reviewData.question.content.gap_mode"
	                  :gap-options="reviewData.question.content.gap_options"
	                  :modelValue="reviewData.record.user_answer"
	                  :show-result="true"
	                  :correct-answer="reviewData.question.answer.correct_val"
	                />
	              </view>
	
	              <!-- 解析卡片 (始终显示) -->
	              <view class="analysis-card">
	                <view class="an-header">
	                  <text class="icon">💡</text>
	                  <text class="label">Analysis</text>
	                </view>
	                <text class="an-text">{{ reviewData.question.answer.analysis || 'No analysis provided.' }}</text>
	              </view>
	
	            </view>
	          </scroll-view>
	        </template>
	      </view>
	    </view>
		
  </view>
    <FeedbackFab />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import FeedbackFab from '@/components/FeedbackFab/FeedbackFab.vue';
import { getCloudObject } from '@/utils/cloud.js';
import QuizChoice from '@/components/Quiz/QuizChoice.vue';
import QuizCodeGap from '@/components/Quiz/QuizCodeGap.vue';


const quizCo = getCloudObject('quiz-co');

const historyList = ref([]);
const totalCount = ref(0);
const loading = ref(true);
const page = ref(1);
const hasMore = ref(true);

//对应题目的弹窗
const showReviewModal = ref(false);
const reviewLoading = ref(false);
const reviewData = ref(null); // { record: ..., question: ... }

// 获取历史数据
const fetchHistory = async (isLoadMore = false) => {
  if (isLoadMore) loading.value = true;
  
  try {
    // 调用之前写的 getUserHistory
    const res = await quizCo.getUserHistory(page.value, 10);
    
    if (res.errCode === 0) {
      if (isLoadMore) {
        historyList.value.push(...res.data.list);
      } else {
        historyList.value = res.data.list;
      }
      
      totalCount.value = res.data.total;
      hasMore.value = res.data.has_more;
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const loadMore = () => {
  if (!hasMore.value) return;
  page.value++;
  fetchHistory(true);
};

// 计算正确率
const accuracy = computed(() => {
  if (historyList.value.length === 0) return 0;
  const correct = historyList.value.filter(i => i.is_correct).length;
  return ((correct / historyList.value.length) * 100).toFixed(0);
});

// 跳转去学习
const goStudy = () => uni.navigateTo({ url: '/pages/study/index' });

// reviewQuestion 方法
const reviewQuestion = async (item) => {
  showReviewModal.value = true;
  reviewLoading.value = true;
  reviewData.value = null; // 清空旧数据

  try {
    const res = await quizCo.getRecordDetail(item._id);
    if (res.errCode === 0) {
      reviewData.value = res.data;
    } else {
      uni.showToast({ title: 'Fetch failed', icon: 'none' });
      showReviewModal.value = false;
    }
  } catch (e) {
    console.error(e);
  } finally {
    reviewLoading.value = false;
  }
};

const closeReview = () => {
  showReviewModal.value = false;
};

// --- 工具函数 ---
const formatDate = (ts, type) => {
  if (!ts) return '-';
  const d = new Date(ts);
  if (type === 'date') {
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return 'Today';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
};

const formatDuration = (sec) => {
  if (!sec) return '0s';
  return sec < 60 ? `${sec}s` : `${Math.floor(sec/60)}m ${sec%60}s`;
};

onMounted(() => {
  fetchHistory();
});
</script>

<style lang="scss" scoped>
/* 全局背景 */
page { background-color: #F8FAFC; }
.history-page { min-height: 100vh; padding-top: 20px; }

.content-wrapper { max-width: 900px; margin: 0 auto; padding: 40px 24px; min-height: 80vh; }

/* 1. Header */
.page-header {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 60px;
  
  .main-title { font-size: 32px; font-weight: 800; color: #0F172A; display: block; margin-bottom: 8px; }
  .sub-title { font-size: 16px; color: #64748B; }
  
  .stats-mini {
    display: flex; gap: 12px;
    .stat-pill {
      background: #fff; padding: 8px 16px; border-radius: 12px; border: 1px solid #E2E8F0;
      display: flex; flex-direction: column; align-items: center; min-width: 80px;
      .label { font-size: 11px; color: #94A3B8; text-transform: uppercase; font-weight: 600; }
      .val { font-size: 18px; font-weight: 700; color: #0F172A; }
      .highlight { color: #10B981; }
    }
  }
}

/* 2. Timeline Core Style */
.timeline-container { position: relative; padding-bottom: 40px; }

/* 贯穿线 */
.timeline-line {
  position: absolute; top: 20px; bottom: 0; left: 100px; width: 2px; background: #E2E8F0; z-index: 0;
}

/* 单个条目 */
.timeline-item {
  display: flex; gap: 24px; margin-bottom: 40px; position: relative; z-index: 1;
  opacity: 0; animation: slideUp 0.5s ease forwards;
}

/* 左侧时间 */
.time-node {
  width: 80px; text-align: right; display: flex; flex-direction: column;
  .time-date { font-weight: 700; color: #0F172A; font-size: 14px; }
  .time-clock { color: #94A3B8; font-size: 12px; }
}

/* 中间圆点 */
.status-dot-wrapper {
  width: 40px; display: flex; justify-content: center;
  .dot {
    width: 32px; height: 32px; border-radius: 50%; background: #fff; border: 2px solid #E2E8F0;
    display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    
    &.success { border-color: #10B981; color: #10B981; background: #ECFDF5; }
    &.error { border-color: #EF4444; color: #EF4444; background: #FEF2F2; }
  }
}

/* 右侧卡片 */
.record-card {
  flex: 1; background: #fff; border-radius: 16px; padding: 20px;
  border: 1px solid #F1F5F9; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
  cursor: pointer; transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    border-color: #E2E8F0;
    .review-link { color: #4F46E5; transform: translateX(0); }
  }

  .card-header {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
    .tags { display: flex; gap: 8px; }
    .tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }
    .tag.category { background: #F1F5F9; color: #64748B; }
    .tag.type { background: #E0F2FE; color: #0284C7; }
    
    .duration { font-size: 12px; color: #94A3B8; font-family: monospace; }
  }

  .q-title { font-size: 16px; font-weight: 600; color: #1E293B; line-height: 1.5; display: block; margin-bottom: 16px; }

  .card-footer {
    display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #F8FAFC; padding-top: 12px;
    .score { font-size: 13px; color: #64748B; }
    .s-high { color: #10B981; font-weight: 700; }
    .s-low { color: #EF4444; font-weight: 700; }
    
    .review-link { font-size: 13px; color: #94A3B8; font-weight: 500; transition: all 0.2s; transform: translateX(-5px); }
  }
}

/* 底部按钮 */
.load-more-wrapper { padding-left: 104px; margin-top: 20px; }
.btn-load-more {
  background: #fff; border: 1px solid #E2E8F0; color: #475569; font-size: 14px; border-radius: 100px;
  &:hover { background: #F8FAFC; border-color: #CBD5E1; }
  &::after { border: none; }
}
.no-more-text { color: #CBD5E1; font-size: 13px; display: block; text-align: center; }

/* 空状态 */
.empty-state { text-align: center; padding: 80px 0;
  .empty-icon { font-size: 48px; margin-bottom: 16px; }
  .empty-text { color: #94A3B8; margin-bottom: 24px; display: block; }
  .btn-go { background: #0F172A; color: #fff; font-size: 14px; padding: 0 24px; border-radius: 8px; display: inline-block; }
}

.loading-state { text-align: center; padding: 50px; color: #94A3B8; }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .timeline-line { left: 24px; }
  .time-node { display: none; } /* 移动端隐藏左侧时间，改在卡片内显示 */
  .status-dot-wrapper { width: 50px; }
  .load-more-wrapper { padding-left: 0; }
}

/* --- 复习弹窗样式 --- */
.review-modal {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(15, 23, 42, 0.7); /* 深色遮罩 */
  backdrop-filter: blur(8px);
  z-index: 999;
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.2s ease;

  .modal-body {
    width: 90%; max-width: 700px; max-height: 85vh;
    background: #fff; border-radius: 20px;
    display: flex; flex-direction: column;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
    overflow: hidden;
    animation: zoomIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }

  /* Loading */
  .modal-loading {
    height: 300px; display: flex; align-items: center; justify-content: center;
  }

  /* Header */
  .m-header {
    padding: 20px 24px; border-bottom: 1px solid #E2E8F0;
    display: flex; justify-content: space-between; align-items: center;
    background: #fff;
    
    .m-title-group {
      display: flex; align-items: center; gap: 12px;
      .tag { 
        font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 6px; text-transform: uppercase;
        &.success { background: #ECFDF5; color: #059669; }
        &.error { background: #FEF2F2; color: #DC2626; }
      }
      .title { font-size: 16px; font-weight: 700; color: #0F172A; }
    }
    
    .btn-close {
      width: 32px; height: 32px; border-radius: 50%; background: #F1F5F9;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; color: #64748B; transition: all 0.2s;
      &:hover { background: #E2E8F0; color: #0F172A; }
    }
  }

  /* Content Scroll */
  .m-scroll-content { flex: 1; overflow-y: auto; }
  .m-content { padding: 30px; }

  .q-title { font-size: 18px; font-weight: 700; color: #1E293B; margin-bottom: 24px; display: block; line-height: 1.5; }

  .component-wrapper { margin-bottom: 30px; }

  /* 解析卡片 */
  .analysis-card {
    background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;
    
    .an-header {
      display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
      .icon { font-size: 18px; }
      .label { font-size: 14px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
    }
    .an-text { font-size: 15px; line-height: 1.7; color: #334155; }
  }
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes zoomIn { from { opacity: 0; transform: scale(0.95) translateY(20px); } to { opacity: 1; transform: scale(1) translateY(0); } }
</style>
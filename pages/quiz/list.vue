<!-- 题目索引页面 -->
<template>
  <view class="list-page">
    <PcNavbar />

    <view class="container-xl content">
      <!-- Header -->
      <view class="list-header">
        <view class="header-left">
          <text class="back-link" @click="goBack">← Back</text>
          <text class="title">Select a Challenge Q</text>
		  <text class="back-link">We will keep track of the questions you have completed...</text>
        </view>
        
        <!-- 统计胶囊 -->
        <view class="stats-capsule">
          <view class="stat-item">
            <text class="dot green"></text> {{ countStatus('correct') }} Done
          </view>
          <view class="stat-item">
            <text class="dot gray"></text> {{ questions.length - countStatus('correct') }} Left
          </view>
        </view>
      </view>

      <!-- Loading -->
      <view class="loading-box" v-if="loading">
        <view class="spinner"></view>
      </view>

      <!-- 题目列表 -->
      <view class="question-grid" v-else>
        <view 
          class="q-card" 
          v-for="(item, index) in questions" 
          :key="item._id"
          @click="startPractice(index)"
          :class="item.user_status"
        >
          <!-- 难度条 -->
          <view class="difficulty-bar" :class="'lv-' + item.difficulty"></view>
          
          <view class="q-info">
            <view class="q-meta">
              <text class="q-idx">#{{ index + 1 }}</text>
              <text class="q-tag">{{ item.type === 'code_gap' ? 'Code' : 'Choice' }}</text>
            </view>
            <text class="q-title">{{ item.title }}</text>
          </view>

          <!-- 状态图标 -->
          <view class="q-status">
            <text v-if="item.user_status === 'correct'" class="icon-ok">✓</text>
            <text v-else-if="item.user_status === 'wrong'" class="icon-err">✕</text>
            <text v-else class="icon-todo">➜</text>
          </view>
        </view>
      </view>

    </view>
    <PcFooter />
  </view>
  <FeedbackFab />
</template>

<script setup>
import { ref } from 'vue';
import { onLoad, onShow } from '@dcloudio/uni-app';
import { getCloudObject } from '@/utils/cloud.js';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import FeedbackFab from '@/components/FeedbackFab/FeedbackFab.vue';

const quizCo = getCloudObject('quiz-co');
const categoryId = ref('');
const questions = ref([]);
const loading = ref(true);

onLoad((opt) => {
  if (opt.id) {
    categoryId.value = opt.id;
  }
});

onShow(() => {
  if (categoryId.value) fetchList();
});

const fetchList = async () => {
  // 不显示全局 loading 遮罩，只显示局部
  try {
    const res = await quizCo.getQuestionListMeta(categoryId.value);
    if (res.errCode === 0) {
      questions.value = res.data;
	  console.log(res.data)
    }
  } finally {
    loading.value = false;
  }
};

const countStatus = (status) => {
  return questions.value.filter(q => q.user_status === status).length;
};

const goBack = () => uni.navigateBack();

// 核心跳转：带上 index 参数，告诉练习页从第几题开始
const startPractice = (index) => {
  uni.navigateTo({
    url: `/pages/quiz/practice?categoryId=${categoryId.value}&startIndex=${index}`
  });
};
</script>

<style lang="scss" scoped>
page { background-color: #F8FAFC; }
.content { padding-top: 40px; min-height: 80vh; }

.list-header {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px;
  .back-link { font-size: 14px; color: #64748B; cursor: pointer; margin-bottom: 8px; display: block; &:hover{color:#0F172A} }
  .title { font-size: 32px; font-weight: 800; color: #0F172A; }
  
  .stats-capsule {
    display: flex; gap: 16px; background: #fff; padding: 8px 16px; border-radius: 100px; border: 1px solid #E2E8F0;
    .stat-item { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: #475569; }
    .dot { width: 8px; height: 8px; border-radius: 50%; 
      &.green { background: #10B981; } &.gray { background: #CBD5E1; }
    }
  }
}

.question-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;
}

.q-card {
  background: #fff; border-radius: 16px; padding: 20px; position: relative; overflow: hidden;
  border: 1px solid #F1F5F9; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
  cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: space-between;
  
  &:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); border-color: #E2E8F0; }
  
  /* 完成状态样式微调 */
  &.correct { background: #F0FDF4; border-color: #DCFCE7; }
  
  .difficulty-bar {
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    &.lv-1 { background: #10B981; } /* 简单 */
    &.lv-2 { background: #F59E0B; } /* 中等 */
    &.lv-3 { background: #EF4444; } /* 困难 */
  }
  
  .q-info { flex: 1; padding-left: 12px; }
  .q-meta { display: flex; gap: 8px; margin-bottom: 6px; font-size: 12px; color: #94A3B8; font-weight: 600; }
  .q-tag { background: #F1F5F9; padding: 1px 6px; border-radius: 4px; }
  
  .q-title { 
    font-size: 15px; font-weight: 600; color: #1E293B; line-height: 1.4;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  }
  
  .q-status {
    width: 32px; height: 32px; border-radius: 50%; background: #F8FAFC; 
    display: flex; align-items: center; justify-content: center; margin-left: 12px; font-size: 14px;
    
    .icon-ok { color: #10B981; font-weight: bold; }
    .icon-err { color: #EF4444; font-weight: bold; }
    .icon-todo { color: #CBD5E1; }
  }
  &.correct .q-status { background: #DCFCE7; }
}

.loading-box { text-align: center; padding: 50px; }
</style>
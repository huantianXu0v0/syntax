<template>
  <view class="path-page">
    <PcNavbar />

    <!-- Loading 状态 -->
    <view class="loading-state" v-if="loading">
      <view class="spinner"></view>
      <text>Mapping your journey...</text>
    </view>

    <view class="container-xl" v-else>
      
      <!-- 1. 顶部面包屑 (Breadcrumb) -->
      <view class="breadcrumb">
        <text class="bc-link" @click="goBack">Library</text>
        <text class="bc-sep">/</text>
        <text class="bc-current">{{ parentInfo.name }}</text>
      </view>

      <!-- 2. Hero Header -->
      <view class="path-header">
        <view class="header-bg"></view> <!-- 弥散背景 -->
        <view class="header-content">
          <view class="icon-box">
            <!-- 模拟图标，实际请用 image -->
            <text class="t-icon">{{ parentInfo.name ? parentInfo.name.charAt(0) : 'C' }}</text>
          </view>
          <view class="info-box">
            <text class="track-title">{{ parentInfo.name }} Path</text>
            <text class="track-desc">{{ parentInfo.description || 'Master the core concepts and advanced techniques.' }}</text>
            
            <!-- 总进度 -->
            <view class="meta-row">
              <view class="progress-badge">
                <text class="label">Total Progress</text>
                <!-- 绑定后端返回的 info.total_progress -->
                <text class="val">{{ parentInfo.total_progress || 0 }}%</text>
              </view>
              <view class="stat-badge">
                <text>🎓 {{ parentInfo.total_chapters || 0 }} Chapters</text>
              </view>
            </view>
          </view>
          
          <button class="btn-resume">Continue Learning</button>
        </view>
      </view>

      <!-- 3. 路线图列表 (Timeline Layout) -->
      <view class="timeline-container">
        
        <block v-for="(item, index) in chapters" :key="item._id">
          <!-- 连接线 -->
          <view class="timeline-connector" v-if="index !== chapters.length - 1"></view>
          
          <view 
            class="chapter-card" 
            :class="{ 'locked': item.status === 'coming_soon' }"
            @click="enterChapter(item)"
          >
            <!-- 左侧序号/状态 -->
            <view class="chapter-status">
              <view class="status-dot" :class="getDotClass(item)">
                {{ index + 1 }}
              </view>
            </view>

            <!-- 右侧卡片内容 -->
            <view class="card-body">
              <view class="card-main">
                <view class="card-header">
                  <text class="ch-title">{{ item.name }}</text>
                  <text class="ch-tag" v-if="item.status === 'coming_soon'">Coming Soon</text>
                  <text class="ch-tag difficulty" v-else>Easy</text>
                </view>
                <text class="ch-desc">{{ item.description || 'Start your journey here.' }}</text>
                
                <!-- 底部元数据 -->
                <view class="card-footer" v-if="item.status !== 'coming_soon'">
                  <view class="progress-mini">
                    <view class="bar" :style="{ width: (item.progress_percent || 0) + '%' }"></view>
                  </view>
                  <text class="footer-text">{{ item.finished_questions }} / {{ item.total_questions }} Questions</text>
                </view>
              </view>
              
              <!-- 悬浮箭头 -->
              <view class="enter-icon">→</view>
            </view>
          </view>
        </block>

      </view>

    </view>
    
    <PcFooter />
  </view>
    <FeedbackFab />
</template>

<script setup>
import { ref} from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import FeedbackFab from '@/components/FeedbackFab/FeedbackFab.vue';
const quizCo = uniCloud.importObject('quiz-co', { customUI: true });

const parentId = ref('');
const parentInfo = ref({});
const chapters = ref([]);
const loading = ref(true);

onLoad((options) => {
  if (options.id) {
    parentId.value = options.id;
    fetchData();
  }
});

const fetchData = async () => {
  try {
    const res = await quizCo.getCourseDetail(parentId.value);
    if (res.errCode === 0) {
      parentInfo.value = res.data.info;
      chapters.value = res.data.chapters;
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  uni.navigateBack();
};

const getDotClass = (item) => {
  if (item.status === 'coming_soon') return 'is-locked';
  if (item.finished_questions > 0) return 'is-active';
  return 'is-todo';
};

const enterChapter = (item) => {
  if (item.status === 'coming_soon') {
    uni.showToast({ title: 'This chapter is under construction', icon: 'none' });
    return;
  }
  
  // 核心跳转：进入答题页，带上子分类ID
  // 这里的 'practice' 是我们之前写的答题页，你可以根据是否是考试模式跳转不同页面
  uni.navigateTo({
	// url: `/pages/quiz/practice?categoryId=${item._id}&title=${item.name}`
	url: `/pages/quiz/list?id=${item._id}`
  });
};
</script>

<style lang="scss" scoped>
page { background-color: #F8FAFC; }

.path-page {
  min-height: 100vh;
  padding-top: 20px;
}

/* 面包屑 */
.breadcrumb {
  margin-bottom: 30px; font-size: 14px; color: #64748B;
  .bc-link { cursor: pointer; &:hover { color: #0F172A; text-decoration: underline; } }
  .bc-sep { margin: 0 8px; color: #CBD5E1; }
  .bc-current { color: #0F172A; font-weight: 500; }
}

/* Header */
.path-header {
  position: relative;
  background: #fff;
  border-radius: 24px;
  padding: 40px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  border: 1px solid #E2E8F0;
  margin-bottom: 60px;
  
  .header-bg {
    position: absolute; top: 0; right: 0; width: 300px; height: 100%;
    background: linear-gradient(135deg, rgba(224, 195, 252, 0.3) 0%, rgba(142, 197, 252, 0.1) 100%);
    filter: blur(40px);
    z-index: 0;
  }
  
  .header-content {
    position: relative; z-index: 1; display: flex; align-items: center; gap: 30px;
    
    .icon-box {
      width: 80px; height: 80px; background: #0F172A; border-radius: 20px;
      display: flex; align-items: center; justify-content: center;
      color: #fff; font-size: 36px; font-weight: 800;
      box-shadow: 0 10px 20px rgba(15, 23, 42, 0.2);
    }
    
    .info-box { flex: 1; }
    .track-title { font-size: 32px; font-weight: 800; color: #0F172A; display: block; margin-bottom: 8px; }
    .track-desc { font-size: 16px; color: #64748B; margin-bottom: 20px; display: block; }
    
    .meta-row { display: flex; gap: 16px; }
    .progress-badge, .stat-badge {
      display: flex; align-items: center; gap: 8px;
      background: #F1F5F9; padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; color: #475569;
      .val { color: #000; }
    }
    
    .btn-resume {
      background: #000; color: #fff; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 600; border: none; cursor: pointer;
      transition: transform 0.2s;
      &:hover { transform: translateY(-2px); }
    }
  }
}

/* Timeline 列表 */
.timeline-container {
  max-width: 900px; margin: 0 auto; position: relative; padding-bottom: 100px;
}

.timeline-connector {
  position: absolute; left: 24px; top: 50px; bottom: -60px; width: 2px; background: #E2E8F0; z-index: 0;
}

.chapter-card {
  position: relative; z-index: 1;
  display: flex; gap: 30px; margin-bottom: 30px;
  cursor: pointer;
  
  &:hover .card-body {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    border-color: #CBD5E1;
    .enter-icon { opacity: 1; transform: translateX(0); }
  }
  
  &.locked { 
    opacity: 0.6; cursor: not-allowed; 
    .status-dot { background: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; }
  }

  /* 左侧圆点 */
  .chapter-status {
    padding-top: 24px;
    .status-dot {
      width: 48px; height: 48px; border-radius: 50%; background: #fff;
      border: 4px solid #E2E8F0;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; color: #64748B; font-size: 18px;
      position: relative; z-index: 2;
      
      &.is-active { border-color: #8EC5FC; color: #007AFF; }
      &.is-todo { border-color: #CBD5E1; }
    }
  }

  /* 右侧卡片 */
  .card-body {
    flex: 1; background: #fff; border-radius: 16px; padding: 24px;
    border: 1px solid #F1F5F9; transition: all 0.3s ease;
    display: flex; align-items: center;
    
    .card-main { flex: 1; }
    .card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
    .ch-title { font-size: 18px; font-weight: 700; color: #1E293B; }
    .ch-tag { font-size: 11px; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; color: #64748B; font-weight: 600; text-transform: uppercase;
      &.difficulty { background: #ECFDF5; color: #059669; }
    }
    .ch-desc { font-size: 14px; color: #64748B; line-height: 1.5; margin-bottom: 16px; display: block; }
    
    .progress-mini {
      height: 4px; background: #F1F5F9; border-radius: 10px; width: 100px; display: inline-block; vertical-align: middle; margin-right: 12px;
      .bar { height: 100%; background: #10B981; border-radius: 10px; }
    }
    .footer-text { font-size: 12px; color: #94A3B8; }
    
    .enter-icon { font-size: 24px; color: #0F172A; opacity: 0; transform: translateX(-10px); transition: all 0.3s ease; }
  }
}

.loading-state { text-align: center; padding: 100px; color: #94A3B8; }

/* 移动端适配 */
@media (max-width: 768px) {
  .path-header { flex-direction: column; align-items: flex-start; }
  .chapter-card { gap: 16px; }
  .timeline-connector { left: 23px; } /* 微调对齐 */
}
</style>
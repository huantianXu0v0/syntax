<template>
  <view class="study-hub">
    <!-- 复用导航栏 -->
    <PcNavbar />

    <view class="container-xl hub-content">
      
      <!-- 1. 个性化 Header -->
      <view class="hub-header">
        <view class="header-text">
          <text class="greeting">Welcome back, {{ nickname }}</text>
          <text class="subtitle">Select a track to start your journey.</text>
        </view>
        <!-- 右侧数据概览 (静态模拟，后期接数据库) -->
        <view class="stats-row">
          <view class="stat-item">
            <text class="val">12</text>
            <text class="label">Solved</text>
          </view>
          <view class="stat-item">
            <text class="val">🔥 3</text>
            <text class="label">Day Streak</text>
          </view>
        </view>
      </view>

      <!-- 2. 知识矩阵 (Grid 布局) -->
      <view class="category-grid" v-if="!loading">
        <view 
          class="cat-card" 
          v-for="(item, index) in categories" 
          :key="item._id"
          @click="enterCategory(item)"
        >
          <!-- 图标区 -->
          <view class="card-icon" :style="{ backgroundColor: getIconBg(index) }">
            <!-- 这里用首字母模拟图标，实际可用 item.icon -->
            {{ item.name.charAt(0) }}
          </view>
          
          <!-- 信息区 -->
          <view class="card-info">
            <text class="cat-name">{{ item.name }}</text>
            <text class="cat-desc">{{ item.description || 'No description available.' }}</text>
            
            <!-- 进度条 -->
            <view class="progress-track">
              <view class="progress-bar" style="width: 0%"></view> <!-- 暂时 0% -->
            </view>
            <text class="progress-text">0% Completed</text>
          </view>

          <!-- Hover 时的箭头 -->
          <view class="hover-arrow">→</view>
        </view>
      </view>
      
      <!-- Loading 骨架屏占位 -->
      <view class="loading-box" v-else>
        Loading Knowledge Matrix...
      </view>

    </view>
    
    <PcFooter />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { store } from '@/uni_modules/uni-id-pages/common/store.js';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
//引入云对象
const quizCo = uniCloud.importObject('quiz-co', {
    customUI: true // 报错时不自动弹窗，我们自己处理
});
const categories = ref([]);
const loading = ref(true);

const nickname = computed(() => store.userInfo.nickname || store.userInfo.username || 'Developer');

// 获取分类数据
const fetchCategories = async () => {
	loading.value = true;
  try {
    const res = await quizCo.getCategoryList();
	if(res.errCode === 0){
		categories.value = res.data;
	}else{
		uni.showToast({
			title:'res.errMsg',
			icon:'none'
		})
	}
      
  } catch (e) {
    console.error(e);
    uni.showToast({ title: 'Load failed', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

// 随机生成图标背景色，增加视觉丰富度
const getIconBg = (index) => {
  const colors = ['#E0C3FC', '#8EC5FC', '#FFD6A5', '#FFADAD', '#CAFFBF'];
  return colors[index % colors.length];
};

// 点击卡片进入答题页
const enterCategory = (item) => {
  // 跳转到练习页，并传递分类ID
  uni.navigateTo({
    url: `/pages/study/learning-path?id=${item._id}`
  });
};

onMounted(() => {
  fetchCategories();
});
</script>

<style lang="scss">
page { background-color: #F8FAFC; }

.hub-content {
  padding-top: 60px;
  min-height: 80vh;
}

/* Header */
.hub-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 50px;
  
  .greeting { font-size: 32px; font-weight: 800; color: #0F172A; display: block; margin-bottom: 8px; }
  .subtitle { font-size: 16px; color: #64748B; }
  
  .stats-row {
    display: flex; gap: 24px;
    .stat-item {
      display: flex; flex-direction: column; align-items: flex-end;
      .val { font-size: 24px; font-weight: 700; color: #0F172A; }
      .label { font-size: 12px; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
    }
  }
}

/* Grid Matrix */
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 3列布局 */
  gap: 24px;
  margin-bottom: 100px;
}

/* Card Design (Glassmorphism + Hover Effect) */
.cat-card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 30px;
  border: 1px solid #F1F5F9;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  cursor: pointer;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    border-color: #E2E8F0;
    
    .hover-arrow { opacity: 1; transform: translateX(0); }
  }

  .card-icon {
    width: 56px; height: 56px;
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; font-weight: 700; color: #333;
    margin-bottom: 24px;
  }

  .cat-name { font-size: 20px; font-weight: 700; color: #1E293B; display: block; margin-bottom: 8px; }
  .cat-desc { font-size: 14px; color: #64748B; line-height: 1.5; margin-bottom: 24px; display: block; height: 42px; overflow: hidden; }

  /* 进度条 */
  .progress-track {
    height: 6px; background: #F1F5F9; border-radius: 100px; overflow: hidden; margin-bottom: 8px;
    .progress-bar { height: 100%; background: #4F46E5; border-radius: 100px; }
  }
  .progress-text { font-size: 12px; color: #94A3B8; font-weight: 500; }

  /* 悬浮箭头 */
  .hover-arrow {
    position: absolute; top: 30px; right: 30px;
    font-size: 24px; color: #4F46E5;
    opacity: 0; transform: translateX(-10px);
    transition: all 0.3s ease;
  }
}

.loading-box { text-align: center; color: #999; padding: 50px; }

@media screen and (max-width: 900px) {
  .category-grid { grid-template-columns: 1fr; }
  .hub-header { flex-direction: column; align-items: flex-start; gap: 20px; }
}
</style>
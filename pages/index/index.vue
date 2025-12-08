<template>
  <view class="page-wrapper">
    
    <!-- === ✨ 新增：高级背景装饰层 ✨ === -->
    <view class="bg-layer">
      <!-- 1. 科技感点阵纹理 -->
      <view class="bg-pattern"></view>
      <!-- 2. 顶部弥散光球 (左上) -->
      <view class="bg-orb orb-1"></view>
      <!-- 3. 底部弥散光球 (右下) -->
      <view class="bg-orb orb-2"></view>
    </view>

    <!-- 1. 顶部导航 -->
    <PcNavbar />

    <!-- 2. 主内容区 -->
    <view class="container-xl main-content">
      
      <!-- Hero Section -->
      <PcReveal>
        <view class="hero-section">
          <view class="hero-content">
            <view class="badge">UniCloud & Vue3 Ready</view>
            <text class="hero-title">Build faster with</text>
            <text class="hero-title gradient-text">Serverless Power.</text>
            <text class="hero-desc">
              Experience the next generation of full-stack development. 
              Designed for high-performance PC web applications.
            </text>
            
            <view class="hero-actions">
              <button class="btn-primary">Get Started</button>
              <button class="btn-secondary">Documentation</button>
            </view>
          </view>

          <!-- 滚动提示 -->
          <view class="scroll-hint" @click="scrollToContent">
            <text class="mouse-icon">↓</text>
            <text class="scroll-text">Scroll to explore</text>
          </view>
        </view>
      </PcReveal>

      <!-- Grid Section -->
      <view id="feature-grid" class="grid-section">
        <block v-for="(item, index) in features" :key="index">
          <PcReveal :delay="index * 100">
            <view class="feature-card">
              <view class="card-icon">{{ item.icon }}</view>
              <text class="card-title">{{ item.title }}</text>
              <text class="card-desc">{{ item.desc }}</text>
            </view>
          </PcReveal>
        </block>
      </view>

      <!-- Showcase Section -->
      <view class="showcase-section">
        <view class="showcase-row">
          <PcReveal>
            <view class="text-col">
              <text class="sc-title">Global Edge Network</text>
              <text class="sc-desc">Your application is deployed to hundreds of edge nodes worldwide.</text>
            </view>
          </PcReveal>
          <PcReveal :delay="200">
            <view class="img-col blue-gradient"></view>
          </PcReveal>
        </view>

        <view class="showcase-row reverse">
          <PcReveal>
            <view class="text-col">
              <text class="sc-title">Real-time Database</text>
              <text class="sc-desc">Sync data across clients in milliseconds. Perfect for chat apps.</text>
            </view>
          </PcReveal>
          <PcReveal :delay="200">
            <view class="img-col purple-gradient"></view>
          </PcReveal>
        </view>
      </view>

    </view>

    <!-- 3. 底部页脚 -->
    <PcFooter />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import PcReveal from '@/components/PcReveal/PcReveal.vue';

//如果是调用云函数，返回的数据结构是res.result.data
//如果是调用云对象，返回的数据结构是res 
//2、使用云对象来获取homeData
const homeDataCo = uniCloud.importObject('getHomeDataByCloudObj');

const features = ref([]);

const scrollToContent = () => {
  const el = document.getElementById('feature-grid');
  if (el) el.scrollIntoView({ behavior: 'smooth' });
};

const fetchHomeData = async () => {
    //1、云函数调用方式
	try{
		// const res = await uniCloud.callFunction({
		// 	name:'getHomeData'
		// });
		const res = await homeDataCo.getHomedata()
		console.log(res)

		if(res && res.code === 0){
			features.value = res.data;
		}
		
	}
	catch(e){
		console.warn(e)
		uni.showToast({
			icon:'error',
			title:e.message
		})
	}
	
};

//页面最开始
onMounted(() => {
  fetchHomeData();
});

</script>

<style lang="scss">
/* --- 0. 全局背景优化 --- */
page {
  /* 不再是纯白，而是极其微弱的灰蓝调，更有质感 */
  background-color: #F8FAFC; 
}

/* --- 1. 背景装饰层 (核心代码) --- */
.bg-layer {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100vh;
  z-index: 0; /* 在最底层 */
  pointer-events: none; /* 确保不影响点击 */
  overflow: hidden;
}

/* 点阵纹理 */
.bg-pattern {
  position: absolute; width: 100%; height: 100%;
  /* 制作点阵效果：径向渐变 */
  background-image: radial-gradient(#CBD5E1 1px, transparent 1px);
  background-size: 32px 32px; /* 点间距 */
  opacity: 0.4; /* 淡淡的 */
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%); /* 底部渐隐，融合自然 */
  -webkit-mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
}

/* 弥散光球 */
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px); /* 强高斯模糊，制造光晕感 */
  opacity: 0.4;
  animation: float 10s ease-in-out infinite;
}

.orb-1 {
  top: -100px; left: -100px;
  width: 600px; height: 600px;
  background: radial-gradient(circle, #E0C3FC 0%, #8EC5FC 100%); /* 蓝紫调，呼应 Logo */
}

.orb-2 {
  top: 40%; right: -200px;
  width: 500px; height: 500px;
  background: radial-gradient(circle, #ffd1ff 0%, #fad0c4 100%); /* 暖色调，增加层次 */
  animation-delay: -5s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(20px, 30px); }
}

/* --- 2. 主内容与布局调整 --- */
.page-wrapper {
  position: relative;
  z-index: 1; /* 确保内容在背景之上 */
}

.main-content {
  padding-top: 0;
}

/* Hero Section */
.hero-section {
  min-height: calc(100vh - 70px);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; position: relative;
  
  .hero-content {
    display: flex; flex-direction: column; align-items: center;
    transform: translateY(-20px);
    z-index: 2; /* 确保文字清晰 */
  }

  .badge { 
    background: rgba(255,255,255,0.8); /* 半透明背景，适应底色 */
    backdrop-filter: blur(5px);
    border: 1px solid rgba(0,0,0,0.05);
    color: #4F46E5; 
    padding: 6px 16px; border-radius: 100px; 
    font-size: 13px; font-weight: 600; margin-bottom: 24px; 
  }
  
  .hero-title {
    font-size: 72px; font-weight: 800; line-height: 1.1; letter-spacing: -2px;
    color: #0F172A; /* 深蓝黑，比纯黑柔和 */
    
    &.gradient-text {
      background: linear-gradient(135deg, #4F46E5 0%, #EC4899 100%); /* 靛蓝到粉红 */
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
  
  .hero-desc { 
    font-size: 20px; color: #475569; max-width: 680px; 
    margin: 32px 0 40px; line-height: 1.6; font-weight: 400;
  }
  
  .hero-actions {
    display: flex; gap: 16px;
    button { 
      font-size: 16px; height: 52px; padding: 0 36px; 
      border-radius: 12px; border: none; cursor: pointer; font-weight: 600;
      display: flex; align-items: center; justify-content: center;
      transition: all 0.2s;
    }
    .btn-primary { 
      background: #0F172A; color: #fff; 
      box-shadow: 0 10px 25px -10px rgba(15, 23, 42, 0.6); /* 投影增加立体感 */
    }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 20px 30px -10px rgba(15, 23, 42, 0.7); }
    
    .btn-secondary { background: #fff; color: #333; border: 1px solid #E2E8F0; }
    .btn-secondary:hover { background: #F8FAFC; border-color: #CBD5E1; }
  }

  /* 滚动提示 */
  .scroll-hint {
    position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%);
    display: flex; flex-direction: column; align-items: center;
    opacity: 0.5; cursor: pointer; transition: opacity 0.3s;
    animation: bounce 2s infinite;
    &:hover { opacity: 1; }
    .mouse-icon { font-size: 20px; margin-bottom: 4px; }
    .scroll-text { font-size: 12px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; }
  }
}

/* Grid Section - 增加玻璃质感 */
.grid-section {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px;
  margin-bottom: 140px; padding-top: 100px;
  
  .feature-card {
    /* 卡片背景不再是纯色，而是微透明，透出背景的光晕 */
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    padding: 32px; border-radius: 20px; 
    transition: all 0.3s ease;
    
    &:hover { 
      transform: translateY(-5px); 
      background: rgba(255, 255, 255, 0.9);
      box-shadow: 0 20px 40px -10px rgba(0,0,0,0.08); 
      border-color: #fff;
    }
    .card-icon { font-size: 32px; margin-bottom: 20px; }
    .card-title { font-size: 18px; font-weight: 700; margin-bottom: 10px; color: #1E293B; display: block; }
    .card-desc { font-size: 15px; color: #64748B; line-height: 1.6; }
  }
}

/* Showcase Section */
.showcase-section {
  display: flex; flex-direction: column; gap: 120px;
  .showcase-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center;
    &.reverse { direction: rtl; .text-col { direction: ltr; } }
    .text-col {
      .sc-title { font-size: 42px; font-weight: 800; margin-bottom: 20px; letter-spacing: -1px; color: #1E293B; display: block; }
      .sc-desc { font-size: 18px; color: #64748B; line-height: 1.7; display: block; }
    }
    .img-col {
      height: 420px; border-radius: 24px;
      /* 给图片框也加一点高级投影 */
      box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.12);
      transition: transform 0.5s ease;
      
      &:hover { transform: scale(1.02); }
      &.blue-gradient { background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%); }
      &.purple-gradient { background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%); }
    }
  }
}

.loading-state { grid-column: span 3; text-align: center; color: #94A3B8; padding: 40px; }

@media screen and (max-width: 900px) {
  .hero-title { font-size: 48px; }
  .grid-section { grid-template-columns: 1fr; gap: 20px; }
  .showcase-row { grid-template-columns: 1fr !important; gap: 40px !important; direction: ltr !important; }
  .img-col { height: 300px; }
  .orb-1, .orb-2 { opacity: 0.2; } /* 移动端减弱背景干扰 */
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0) translateX(-50%); }
  40% { transform: translateY(-10px) translateX(-50%); }
  60% { transform: translateY(-5px) translateX(-50%); }
}
</style>
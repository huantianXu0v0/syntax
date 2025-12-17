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

      <!-- Hero Section (编程答题专属版) -->
            <PcReveal>
              <view class="hero-section">
                
                <!-- 左侧：文案与行动 -->
                <view class="hero-left">
                  <view class="badge-capsule">
                    <text class="dot"></text>
                    <text>New Challenges Added</text>
                  </view>
                  
                  <text class="hero-title">Master Coding through</text>
                  <text class="hero-title gradient-text">Practice.</text>
                  
                  <text class="hero-desc">
                    Level up your programming skills with interactive quizzes. 
                    From <text class="highlight">Python</text> basics to advanced <text class="highlight">Algorithms</text>.
                  </text>
                  
                  <view class="hero-actions">
                    <button class="btn-primary" @click="handleGetStarted">
                      Start Practicing
                      <text class="btn-icon">→</text>
                    </button>
                    
                    <view class="stats-mini">
                      <view class="avatars">
                        <!-- 模拟用户头像堆叠 -->
                        <view class="av" style="background:#ffadad"></view>
                        <view class="av" style="background:#ffd6a5"></view>
                        <view class="av" style="background:#caffbf"></view>
                      </view>
                      <text class="stats-text">Joined by 10k+ devs</text>
                    </view>
                  </view>
                </view>
      
                <!-- 右侧：悬浮代码演示区 (视觉核心) -->
                <view class="hero-right">
                  <!-- 背景光晕 -->
                  <view class="glow-bg"></view>
                  
                  <!-- 模拟 IDE 窗口 -->
                  <view class="code-window">
                    <view class="window-header">
                      <view class="dots">
                        <view class="d red"></view><view class="d yellow"></view><view class="d green"></view>
                      </view>
                      <text class="filename">solution.py</text>
                    </view>
                    <view class="window-body">
                      <view class="code-line"><text class="kwd">def</text> <text class="func">solve_puzzle</text>(data):</view>
                      <view class="code-line indent1"><text class="comment"># Find the hidden pattern</text></view>
                      <view class="code-line indent1"><text class="kwd">if</text> <text class="var">data</text>.is_empty():</view>
                      <view class="code-line indent2"><text class="kwd">return</text> <text class="bool">False</text></view>
                      <view class="code-line indent1"><text class="kwd">return</text> <text class="obj">True</text></view>
                      <view class="code-line cursor-line">
                        <text class="kwd">print</text>(<text class="str">"You did it!"</text>)<view class="cursor"></view>
                      </view>
                    </view>
                    
                    <!-- 悬浮标签 (Floating Tags) -->
                    <view class="float-tag tag-python">🐍 Python</view>
                    <view class="float-tag tag-score">💯 Score: 100</view>
                  </view>
                </view>
				
      
                <!-- 底部滚动提示 -->
				<view class="scroll-hint">
					<text class="mouse-icon">↑快点击'Start Practing'看看吧！</text>
					 <p class="mouse-icon" @click="scrollToContent">↓下方内容待开发中</p>
				</view>
				
<!--                <view class="scroll-hint" @click="scrollToContent">
                  <text class="mouse-icon">↓下方内容待开发中</text>
                </view> -->
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
  <FeedbackFab />
  <aichat />
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import PcReveal from '@/components/PcReveal/PcReveal.vue';
import FeedbackFab from '@/components/FeedbackFab/FeedbackFab.vue';
import aichat from'@/components/AiChatWidget/ai-chat-widget.vue'
//引入登录状态检测
import { store, mutations } from '@/uni_modules/uni-id-pages/common/store.js';

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
		// console.log(res)

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
const handleGetStarted = () => {
  // 1. 检查登录状态
  if (store.hasLogin) {
    // 2. 已登录 -> 跳转到学习中心 (新页面)
    uni.navigateTo({
      url: '/pages/study/index',
      animationType: 'fade-in' // 大厂喜欢淡入淡出，比较优雅
    });
  } else {
    // 3. 未登录 -> 跳转登录页
    uni.navigateTo({
      url: '/pages/login/login'
    });
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

// /* Hero Section */
// .hero-section {
//   min-height: calc(100vh - 70px);
//   display: flex; flex-direction: column; align-items: center; justify-content: center;
//   text-align: center; position: relative;
  
//   .hero-content {
//     display: flex; flex-direction: column; align-items: center;
//     transform: translateY(-20px);
//     z-index: 2; /* 确保文字清晰 */
//   }

//   .badge { 
//     background: rgba(255,255,255,0.8); /* 半透明背景，适应底色 */
//     backdrop-filter: blur(5px);
//     border: 1px solid rgba(0,0,0,0.05);
//     color: #4F46E5; 
//     padding: 6px 16px; border-radius: 100px; 
//     font-size: 13px; font-weight: 600; margin-bottom: 24px; 
//   }
  
//   .hero-title {
//     font-size: 72px; font-weight: 800; line-height: 1.1; letter-spacing: -2px;
//     color: #0F172A; /* 深蓝黑，比纯黑柔和 */
    
//     &.gradient-text {
//       background: linear-gradient(135deg, #4F46E5 0%, #EC4899 100%); /* 靛蓝到粉红 */
//       -webkit-background-clip: text;
//       -webkit-text-fill-color: transparent;
//     }
//   }
  
//   .hero-desc { 
//     font-size: 20px; color: #475569; max-width: 680px; 
//     margin: 32px 0 40px; line-height: 1.6; font-weight: 400;
//   }
  
//   .hero-actions {
//     display: flex; gap: 16px;
//     button { 
//       font-size: 16px; height: 52px; padding: 0 36px; 
//       border-radius: 12px; border: none; cursor: pointer; font-weight: 600;
//       display: flex; align-items: center; justify-content: center;
//       transition: all 0.2s;
//     }
//     .btn-primary { 
//       background: #0F172A; color: #fff; 
//       box-shadow: 0 10px 25px -10px rgba(15, 23, 42, 0.6); /* 投影增加立体感 */
//     }
//     .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 20px 30px -10px rgba(15, 23, 42, 0.7); }
    
//     .btn-secondary { background: #fff; color: #333; border: 1px solid #E2E8F0; }
//     .btn-secondary:hover { background: #F8FAFC; border-color: #CBD5E1; }
//   }

//   /* 滚动提示 */
//   .scroll-hint {
//     position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%);
//     display: flex; flex-direction: column; align-items: center;
//     opacity: 0.5; cursor: pointer; transition: opacity 0.3s;
//     animation: bounce 2s infinite;
//     &:hover { opacity: 1; }
//     .mouse-icon { font-size: 20px; margin-bottom: 4px; }
//     .scroll-text { font-size: 12px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; }
//   }
// }

/* --- Hero Section (New Design) --- */
.hero-section {
  min-height: calc(100vh - 70px);
  display: flex;
  align-items: center;
  justify-content: space-between; /* 左右分布 */
  position: relative;
  padding: 0 20px; /* 两侧留白 */
  
  /* 左侧文案 */
  .hero-left {
    max-width: 600px;
    z-index: 2;
    
    .badge-capsule {
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(255,255,255,0.8); border: 1px solid #E2E8F0;
      padding: 6px 12px; border-radius: 100px;
      font-size: 13px; font-weight: 600; color: #475569;
      margin-bottom: 24px;
      .dot { width: 8px; height: 8px; background: #10B981; border-radius: 50%; }
    }

    .hero-title {
      display: block;
      font-size: 64px; font-weight: 800; line-height: 1.1; letter-spacing: -2px;
      color: #0F172A;
      
      &.gradient-text {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }
    }

    .hero-desc {
      font-size: 18px; color: #64748B; margin: 32px 0 40px; line-height: 1.6; max-width: 500px;
      .highlight { color: #0F172A; font-weight: 600; border-bottom: 2px solid #E2E8F0; }
    }

    .hero-actions {
      display: flex; align-items: center; gap: 30px;
	  margin: 30px;
      
      .btn-primary {
        background: #0F172A; color: #fff; height: 56px; padding: 0 40px;
        border-radius: 14px; font-size: 16px; font-weight: 600; border: none; cursor: pointer;
        display: flex; align-items: center; gap: 8px;
        box-shadow: 0 20px 40px -10px rgba(15, 23, 42, 0.3);
        transition: all 0.3s ease;
        
        .btn-icon { transition: transform 0.2s; }
        &:hover { 
          transform: translateY(-2px); 
          box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
          .btn-icon { transform: translateX(4px); }
        }
      }

      .stats-mini {
        display: flex; align-items: center; gap: 12px;
        .avatars {
          display: flex;
          .av { width: 32px; height: 32px; border-radius: 50%; border: 2px solid #fff; margin-left: -10px; first-child { margin-left: 0; } }
        }
        .stats-text { font-size: 13px; color: #64748B; font-weight: 500; }
      }
    }
  }

  /* 右侧视觉图 */
  .hero-right {
    flex: 1;
    display: flex; justify-content: center; align-items: center;
    position: relative;
    z-index: 1;
    
    .glow-bg {
      position: absolute; width: 100%; height: 100%;
      background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
      filter: blur(40px); z-index: -1;
    }

    /* 代码窗口样式 */
    .code-window {
      background: rgba(30, 41, 59, 0.95); /* 深色背景 */
      backdrop-filter: blur(20px);
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.1);
      width: 480px;
      padding-bottom: 30px;
      box-shadow: 0 30px 60px -12px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.05);
      position: relative;
      animation: floatCode 6s ease-in-out infinite; /* 悬浮动画 */
      
      .window-header {
        padding: 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.05);
        display: flex; align-items: center;
        .dots { display: flex; gap: 6px; margin-right: 16px; .d { width: 10px; height: 10px; border-radius: 50%; } .red{background:#EF4444} .yellow{background:#F59E0B} .green{background:#10B981} }
        .filename { color: #94A3B8; font-size: 12px; font-family: monospace; }
      }

      .window-body {
        padding: 20px; font-family: 'Menlo', monospace; font-size: 14px; line-height: 1.8; color: #E2E8F0;
        
        .code-line { display: flex; }
        .indent1 { padding-left: 20px; }
        .indent2 { padding-left: 40px; }
        
        /* 语法高亮 */
        .kwd { color: #C084FC; } /* 紫色 */
        .func { color: #60A5FA; } /* 蓝色 */
        .str { color: #34D399; } /* 绿色 */
        .comment { color: #64748B; font-style: italic; }
        .var { color: #F472B6; }
        .obj { color: #FBBF24; }
        
        /* 光标闪烁 */
        .cursor {
          width: 8px; height: 18px; background: #60A5FA; display: inline-block; margin-left: 4px; vertical-align: middle;
          animation: blink 1s infinite;
        }
      }

      /* 悬浮标签 */
      .float-tag {
        position: absolute; padding: 8px 16px; background: #fff; border-radius: 12px;
        font-size: 13px; font-weight: 700; color: #0F172A;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        animation: floatTag 4s ease-in-out infinite;
      }
      .tag-python { top: -20px; right: -20px; transform: rotate(10deg); animation-delay: 0.5s; }
      .tag-score { bottom: 20px; left: -30px; transform: rotate(-5deg); animation-delay: 1s; }
    }
  }

  /* 滚动提示箭头 */
  .scroll-hint {
    position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
    opacity: 0.4; cursor: pointer; animation: bounce 2s infinite;
    .mouse-icon { font-size: 24px; color: #0F172A; }
  }
}

/* 动画定义 */
@keyframes floatCode {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}
@keyframes floatTag {
  0%, 100% { transform: translateY(0) rotate(var(--r, 0deg)); }
  50% { transform: translateY(-8px) rotate(var(--r, 0deg)); }
}
@keyframes blink { 50% { opacity: 0; } }

/* 📱 移动端适配 */
@media screen and (max-width: 900px) {
  .hero-section {
    flex-direction: column; justify-content: center; text-align: center;
    padding-top: 40px;
    
    .hero-left { margin-bottom: 60px; .hero-actions { justify-content: center; } }
    .hero-title { font-size: 48px; }
    .code-window { width: 90%; transform: scale(0.9); }
    /* 移动端隐藏部分装饰以提升性能 */
    .float-tag { display: none; }
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
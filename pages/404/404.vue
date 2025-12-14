<template>
  <view class="container">
    <!-- 1. 视觉区域：带有轻微浮动动画的插画 -->
    <view class="graphic-area">
      <!-- 这里的图片建议去 undraw.co 下载一个 SVG 或 PNG，放入 static 目录 -->
      <!-- 暂时用一个在线的占位图演示，请替换为你本地的 /static/404.png -->
      <image 
        src="@/static/img/404/404.jpg" 
        mode="widthFix" 
        class="illustration"
      ></image>
      <view class="shadow"></view>
    </view>

    <!-- 2. 文本区域：层次分明 -->
    <view class="text-area">
      <text class="title">404</text>
      <text class="subtitle">抱歉，您访问的页面已走失</text>
      <text class="description">可能是刚才的链接输入错误，或者该页面已被删除。</text>
    </view>

    <!-- 3. 操作区域：主次按钮 -->
    <view class="action-area">
      <button class="btn btn-primary" hover-class="btn-hover" @click="goHome">
        返回首页
      </button>
      <button class="btn btn-secondary" hover-class="btn-secondary-hover" @click="goBack">
        返回上一页
      </button>
    </view>
    
    <!-- 4. 底部版权（可选，增加专业感） -->
    <view class="footer">
      <text>© 2024 Your App Name</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {};
  },
  methods: {
    goHome() {
      // 尝试跳转到 TabBar 页面，如果不是 TabBar 页面会自动失败，需捕获异常
      uni.switchTab({
        url: '/pages/index/index', // 请修改为你项目的首页路径
        fail: () => {
          // 如果首页不是 TabBar 页面，则使用 reLaunch
          uni.reLaunch({
            url: '/pages/index/index'
          });
        }
      });
    },
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack({ delta: 1 });
      } else {
        // 如果没有上一页（比如直接扫码进来的404），就回首页
        this.goHome();
      }
    }
  }
};
</script>

<style lang="scss" scoped>
/* 定义大厂常用的配色变量 */
$primary-color: #007AFF; /* 科技蓝，可改为你的品牌色 */
$text-main: #333333;
$text-sub: #999999;
$bg-color: #ffffff;

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: $bg-color;
  padding: 0 40rpx;
  box-sizing: border-box;
}

/* 1. 插画动画区 */
.graphic-area {
  margin-top: -100rpx; /* 视觉上稍微向上偏移 */
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;

  .illustration {
    width: 400rpx;
    height: 400rpx;
    /* 浮动动画：增加灵动感 */
    animation: float 3s ease-in-out infinite;
  }
  
  .shadow {
    width: 200rpx;
    height: 20rpx;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 50%;
    margin-top: 20rpx;
    animation: scale 3s ease-in-out infinite;
  }
}

/* 2. 文本区 */
.text-area {
  text-align: center;
  margin-bottom: 80rpx;
  
  .title {
    font-size: 80rpx;
    font-weight: 900;
    color: #f0f2f5; /* 超浅灰色，作为背景字 */
    line-height: 1;
    display: block;
    margin-bottom: -40rpx; /* 叠加效果 */
    position: relative;
    z-index: 0;
  }

  .subtitle {
    font-size: 36rpx;
    font-weight: bold;
    color: $text-main;
    display: block;
    margin-bottom: 16rpx;
    position: relative;
    z-index: 1;
  }

  .description {
    font-size: 26rpx;
    color: $text-sub;
    line-height: 1.6;
    display: block;
    max-width: 500rpx;
    margin: 0 auto;
  }
}

/* 3. 按钮区 */
.action-area {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30rpx;

  .btn {
    width: 400rpx;
    height: 88rpx;
    line-height: 88rpx;
    border-radius: 44rpx; /* 圆角按钮 */
    font-size: 30rpx;
    font-weight: 500;
    border: none;
    outline: none;
    
    &::after {
      border: none;
    }
  }

  .btn-primary {
    background: linear-gradient(135deg, $primary-color, adjust-hue($primary-color, 36deg));
    color: #ffffff;
    box-shadow: 0 10rpx 20rpx rgba($primary-color, 0.2);
  }
  
  .btn-hover {
    opacity: 0.9;
    transform: scale(0.98);
  }

  .btn-secondary {
    background-color: transparent;
    color: $text-sub;
    border: 2rpx solid #eeeeee;
    
    &::after {
      border: none;
    }
  }
  
  .btn-secondary-hover {
    background-color: #f8f8f8;
  }
}

.footer {
  position: absolute;
  bottom: 40rpx;
  font-size: 20rpx;
  color: #dddddd;
}

/* 动画关键帧 */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20rpx); }
}

@keyframes scale {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(0.8); opacity: 0.1; }
}
</style>
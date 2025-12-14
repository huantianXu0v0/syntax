<template>
  <view class="fab-container" @click="goFeedback">
    <view class="fab-content">
      <text class="fab-icon">?</text>
      <view class="tooltip">Feedback</view>
    </view>
  </view>
</template>

<script setup>
const goFeedback = () => {
  uni.navigateTo({
    url: '/pages/feedback/index',
    animationType: 'pop-in'
  });
};
</script>

<style lang="scss" scoped>
/* 默认隐藏 (移动端不显示) */
.fab-container {
  display: none;
}

/* PC 端 / 大屏显示 */
@media screen and (min-width: 900px) {
  .fab-container {
    display: block;
    position: fixed;
    bottom: 40px;
    right: 40px;
    z-index: 999;
  }

  .fab-content {
    width: 56px;
    height: 56px;
    background: #0F172A; /* 深色品牌色 */
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.4);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性动画 */
    position: relative;

    &:hover {
      transform: scale(1.1) translateY(-2px);
      background: #1E293B;
      box-shadow: 0 15px 30px -5px rgba(15, 23, 42, 0.5);
      
      /* 显示 Tooltip */
      .tooltip {
        opacity: 1;
        transform: translateX(0);
        visibility: visible;
      }
    }
  }

  .fab-icon {
    font-size: 24px;
    color: #fff;
    font-weight: 700;
    font-family: serif; /* 问号用衬线体更有质感 */
  }

  /* 左侧提示气泡 */
  .tooltip {
    position: absolute;
    right: 70px;
    background: #fff;
    color: #0F172A;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    opacity: 0;
    visibility: hidden;
    transform: translateX(10px);
    transition: all 0.2s ease;
    
    /* 小三角 */
    &::after {
      content: '';
      position: absolute;
      right: -4px;
      top: 50%;
      transform: translateY(-50%);
      border-width: 4px 0 4px 4px;
      border-style: solid;
      border-color: transparent transparent transparent #fff;
    }
  }
}
</style>
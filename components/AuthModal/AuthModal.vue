<template>
  <!-- 遮罩层：使用 v-if 控制显隐，fade 动画 -->
  <view class="modal-overlay" v-if="isVisible" @click.self="close">
    <view class="modal-card" :class="{ 'shake-anim': shake }">
      
      <!-- 顶部关闭按钮 -->
      <view class="close-btn" @click="close">✕</view>

      <!-- 头部：Logo与标题 -->
      <view class="modal-header">
        <text class="m-logo">UNI-ID</text>
        <text class="m-title">{{ isLoginMode ? 'Welcome back' : 'Create an account' }}</text>
        <text class="m-sub">{{ isLoginMode ? 'Enter your details to sign in.' : 'Start your free 30-day trial.' }}</text>
      </view>

      <!-- 表单内容 -->
      <view class="modal-body">
        <!-- 注册模式下多一个 Name 输入框 -->
        <view class="input-item" v-if="!isLoginMode">
          <input type="text" placeholder="Full Name" class="m-input" />
        </view>
        
        <view class="input-item">
          <input type="text" placeholder="Email address" class="m-input" />
        </view>
        
        <view class="input-item">
          <input type="password" placeholder="Password" class="m-input" />
        </view>

        <button class="m-btn-primary" @click="handleSubmit">
          {{ isLoginMode ? 'Sign In' : 'Sign Up' }}
        </button>

        <view class="divider">or continue with</view>

        <view class="social-row">
          <view class="social-btn">G</view> <!-- 模拟 Google 图标 -->
          <view class="social-btn"></view> <!-- 模拟 Apple 图标 -->
        </view>
      </view>

      <!-- 底部切换 -->
      <view class="modal-footer">
        <text>{{ isLoginMode ? "No account?" : "Already have an account?" }}</text>
        <text class="switch-link" @click="toggleMode">
          {{ isLoginMode ? "Sign up" : "Log in" }}
        </text>
      </view>

    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const isVisible = ref(false);
const isLoginMode = ref(true); // true=登录, false=注册
const shake = ref(false); // 错误时的抖动动画

// 暴露给父组件调用的方法
const open = (mode = 'login') => {
  isLoginMode.value = mode === 'login';
  isVisible.value = true;
};

const close = () => {
  isVisible.value = false;
};

const toggleMode = () => {
  // 简单的切换动画逻辑可以是淡入淡出，这里直接切换
  isLoginMode.value = !isLoginMode.value;
};

const handleSubmit = () => {
  // 模拟提交
  console.log('Submit', isLoginMode.value ? 'Login' : 'Register');
  // 关闭弹窗
  // close();
};

// 暴露方法
defineExpose({ open, close });
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0,0,0,0.4); /* 深色遮罩 */
  backdrop-filter: blur(8px);   /* 核心：毛玻璃背景 */
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.3s ease;
}

.modal-card {
  width: 400px;
  background: #fff;
  border-radius: 24px;
  padding: 40px;
  position: relative;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.close-btn {
  position: absolute; top: 20px; right: 20px;
  font-size: 18px; color: #999; cursor: pointer; padding: 10px;
  &:hover { color: #333; }
}

.modal-header {
  text-align: center; margin-bottom: 30px;
  .m-logo { font-size: 16px; font-weight: 800; display: block; margin-bottom: 16px; letter-spacing: 1px; }
  .m-title { font-size: 28px; font-weight: 700; color: #111; display: block; margin-bottom: 8px; }
  .m-sub { font-size: 15px; color: #666; }
}

.m-input {
  width: 100%; height: 50px; background: #F9FAFB; border: 1px solid #E5E7EB;
  border-radius: 12px; padding: 0 16px; font-size: 15px; margin-bottom: 16px; box-sizing: border-box;
  &:focus { background: #fff; border-color: #111; outline: none; }
}

.m-btn-primary {
  width: 100%; height: 50px; line-height: 50px; background: #111; color: #fff;
  border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 10px;
  &:hover { transform: translateY(-1px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
}

.divider {
  text-align: center; font-size: 12px; color: #999; margin: 24px 0; position: relative;
  &::before, &::after {
    content: ''; position: absolute; top: 50%; width: 35%; height: 1px; background: #eee;
  }
  &::before { left: 0; } &::after { right: 0; }
}

.social-row {
  display: flex; gap: 16px;
  .social-btn {
    flex: 1; height: 44px; border: 1px solid #eee; border-radius: 12px;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
    font-weight: 600; font-size: 18px;
    &:hover { background: #f9f9f9; }
  }
}

.modal-footer {
  margin-top: 30px; text-align: center; font-size: 14px; color: #666;
  .switch-link { color: #111; font-weight: 600; margin-left: 5px; cursor: pointer; text-decoration: underline; }
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(20px) scale(0.95); } to { transform: translateY(0) scale(1); } }
</style>
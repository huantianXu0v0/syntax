<template>
  <view class="auth-page">
    <!-- 左侧品牌区 (保持不变) -->
    <view class="brand-side">
      <view class="brand-text">
        <text class="brand-logo">UNI-CLOUD</text>
        <text class="brand-slogan">Join the<br>revolution.</text>
        <text class="brand-desc">Join 10,000+ developers building the future of web applications with our platform.</text>
      </view>
      <view class="glass-decoration blue-theme"></view>
    </view>

    <!-- 右侧表单区 -->
    <view class="form-side">
      <view class="form-container">
        <view class="back-home" @click="goHome">← Back to Home</view>

        <text class="form-title">Create an account</text>
        <text class="form-sub">Start your 30-day free trial. No credit card required.</text>

        <!-- 1. 手机号 (作为 Username 传递) -->
        <view class="input-group">
          <text class="label">Mobile Number</text>
          <input class="input" type="number" maxlength="11" v-model="formData.username" placeholder="13800138000" placeholder-class="ph-style" />
        </view>

        <!-- 2. 昵称 -->
        <view class="input-group">
          <text class="label">Nickname</text>
          <input class="input" type="text" v-model="formData.nickname" placeholder="Your display name" placeholder-class="ph-style" />
        </view>

        <!-- 3. 密码 -->
        <view class="input-group">
          <text class="label">Password</text>
          <input class="input" type="password" v-model="formData.password" placeholder="Min. 6 characters" placeholder-class="ph-style" />
        </view>

        <!-- 4. 确认密码 (新增) -->
        <view class="input-group">
          <text class="label">Confirm Password</text>
          <input class="input" type="password" v-model="formData.passwordConfirm" placeholder="Re-enter your password" placeholder-class="ph-style" />
        </view>
        
        <!-- 5. 图形验证码 (新增) -->
        <view class="input-group">
          <text class="label">Captcha</text>
          <view class="captcha-box">
             <!-- <input class="input captcha-input" type="text" v-model="formData.captcha" placeholder="Enter code" placeholder-class="ph-style" /> -->
             <!-- 引入 uni-captcha 组件 -->
             <view class="captcha-img-wrapper" @click="refreshCaptcha">
                <uni-captcha ref="captchaRef" scene="register" v-model="formData.captcha" :focus="false" />
             </view>
          </view>
        </view>

        <!-- 协议勾选 -->
        <view class="terms-check">
          <view class="checkbox-label" @click="toggleAgree">
            <checkbox :checked="isAgree" style="transform:scale(0.7); pointer-events: none" color="#000" />
            <text class="terms-text">I agree to the <text class="link" @click.stop>Terms</text> and <text class="link" @click.stop>Privacy Policy</text>.</text>
          </view>
        </view>

        <button class="btn-submit" :disabled="isLoading" @click="handleRegister">
          {{ isLoading ? 'Creating...' : 'Get Started' }}
        </button>
        
        <view class="footer-link">
          <text>Already have an account? </text>
          <text class="link-bold" @click="goLogin">Log in</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
//引入 mutations
import { mutations } from '@/uni_modules/uni-id-pages/common/store.js';

const uniIdCo = uniCloud.importObject('uni-id-co');

const isLoading = ref(false);
const isAgree = ref(false);
const captchaRef = ref(null); // 获取验证码组件实例

const formData = reactive({
  username: '', // 对应手机号
  nickname: '',
  password: '',
  passwordConfirm: '',
  captcha: ''
});

const toggleAgree = () => { isAgree.value = !isAgree.value; };
const goHome = () => uni.reLaunch({ url: '/pages/index/index' });
const goLogin = () => uni.redirectTo({ url: '/pages/login/login' });

// 刷新验证码
const refreshCaptcha = () => {
  if(captchaRef.value) {
    captchaRef.value.getImageCaptcha();
  }
};

const handleRegister = async () => {
  // --- 1. 前端校验 ---
  if (!isAgree.value) return uni.showToast({ title: 'Please agree to terms', icon: 'none' });
  
  // 校验手机号
  if (!/^1\d{10}$/.test(formData.username)) {
    return uni.showToast({ title: 'Invalid mobile number', icon: 'none' });
  }
  
  // 校验昵称
  if (!formData.nickname) return uni.showToast({ title: 'Nickname required', icon: 'none' });

  // 校验密码
  if (formData.password.length < 6) return uni.showToast({ title: 'Password too short (min 6)', icon: 'none' });
  if (formData.password !== formData.passwordConfirm) {
    return uni.showToast({ title: 'Passwords do not match', icon: 'none' });
  }

  // 校验验证码
  if (formData.captcha.length !== 4) return uni.showToast({ title: 'Enter 4-digit captcha', icon: 'none' });

  isLoading.value = true;

  try {
    // --- 2. 调用 uni-id-co 注册 ---
    // 官方方法: registerUser
    // 参数说明: 即使是手机号，只要不是通过短信验证码注册，通常都传给 username 字段
    const res = await uniIdCo.registerUser({
	  mobile: formData.username,
      username: 'u' + formData.username, 
      password: formData.password,
      nickname: formData.nickname,
      captcha: formData.captcha
    });

    // --- 3. 注册成功 ---
    uni.showToast({ title: 'Register Success!', icon: 'success' });
    
    // 检查是否有 newToken (部分版本注册成功直接返回 token)
        if (res.errCode === 0 && res.newToken) {
          
          // 1. 存 Token
          uni.setStorageSync('uni_id_token', res.newToken.token);
          uni.setStorageSync('uni_id_token_expired', res.newToken.tokenExpired);
          uni.setStorageSync('uni_id_uid', res.uid);
          
          // 2. 构造用户信息 (注册时我们知道昵称，直接存进去！)
          const savedUserInfo = {
            _id: res.uid,
            username: formData.username, // 手机号
            nickname: formData.nickname, // 刚才输入的昵称
            avatar: '' 
          };
          
          uni.setStorageSync('uni_id_userInfo', savedUserInfo);
          
          // 3. 通知并跳转
          uni.$emit('login-success', savedUserInfo);
          
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/index/index' });
          }, 1500);
          
        } else {
          // 如果注册后没有返回 token，则跳转登录页
          setTimeout(goLogin, 1500);
        }

  } catch (e) {
    // --- 4. 错误处理 ---
    console.error(e);
    uni.showToast({ title: e.errMsg || 'Register failed', icon: 'none' });
    
    // 注册失败通常需要刷新验证码
    refreshCaptcha();
    formData.captcha = ''; 
  } finally {
    isLoading.value = false;
  }
};
</script>

<style lang="scss" scoped>
@import '@/static/css/auth.scss';


</style>
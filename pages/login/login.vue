<template>
  <view class="auth-page">
    <!-- 左侧品牌区 -->
    <view class="brand-side">
      <view class="brand-text">
        <text class="brand-logo">UNI-CLOUD</text>
        <text class="brand-slogan">Build your future,<br>line by line.</text>
      </view>
      <view class="glass-decoration"></view>
    </view>

    <!-- 右侧表单区 -->
    <view class="form-side">
      <view class="form-container">
        <view class="back-home" @click="goHome">← Back to Home</view>

        <text class="form-title">Welcome back</text>
        <text class="form-sub">Please enter your details to sign in.</text>
		<text class="form-sub">你的登录账号是 u+手机号，如u158xxxxxxxx</text>

        <!-- 1. 账号输入框 (支持手机号/邮箱/用户名) -->
        <view class="input-group">
          <text class="label">Account</text>
          <input class="input" type="text" v-model="loginData.username" placeholder="Mobile / Username / Email" placeholder-class="ph-style" />
        </view>

        <!-- 2. 密码输入框 -->
        <view class="input-group">
          <text class="label">Password</text>
          <input class="input" type="password" v-model="loginData.password" placeholder="••••••••" placeholder-class="ph-style" />
        </view>

        <!-- 3. 图形验证码 (新增模块) -->
        <view class="input-group">
          <text class="label">Captcha</text>
          <view class="captcha-box">
             <!-- <input class="input captcha-input" type="text" v-model="loginData.captcha" placeholder="Enter code" placeholder-class="ph-style" /> -->
             <!-- 引入 uni-captcha 组件，场景设为 login -->
             <view class="captcha-img-wrapper" @click="refreshCaptcha">
                <uni-captcha ref="captchaRef" scene="login" v-model="loginData.captcha" :focus="false" />
             </view>
          </view>
        </view>

        <button class="btn-submit" :disabled="isLoading" @click="handleLogin">
          {{ isLoading ? 'Signing in...' : 'Sign In' }}
        </button>

        <view class="footer-link">
          <text>Don't have an account? </text>
          <text class="link" @click="goRegister">Sign up for free</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
//引入 mutations
import { mutations } from '@/uni_modules/uni-id-pages/common/store.js';
import { onLoad } from '@dcloudio/uni-app'; // 引入 onLoad

const uniIdCo = uniCloud.importObject('uni-id-co');
const isLoading = ref(false);
const captchaRef = ref(null); // 验证码组件实例

// 1. 定义变量存跳转地址
const redirectUrl = ref('');

// 2. 在 onLoad 中接收参数
onLoad((options) => {
    if (options.uniIdRedirectUrl) {
        // 解码参数
        redirectUrl.value = decodeURIComponent(options.uniIdRedirectUrl);
        // console.log('登录后将跳转至:', redirectUrl.value);
    }
});

const loginData = reactive({
  username: '',
  password: '',
  captcha: ''   // 新增验证码字段
});

const goHome = () => uni.reLaunch({ url: '/pages/index/index' });
const goRegister = () => uni.redirectTo({ url: '/pages/register/register' });

// 刷新验证码方法
const refreshCaptcha = () => {
  if (captchaRef.value) {
    captchaRef.value.getImageCaptcha();
  }
};

// --- 核心登录逻辑 ---
const handleLogin = async () => {
  if (!loginData.username || !loginData.password) {
    return uni.showToast({ title: 'Please fill in all fields', icon: 'none' });
  }
  
  // 校验验证码长度
  if (loginData.captcha.length !== 4) {
    return uni.showToast({ title: 'Invalid Captcha', icon: 'none' });
  }

  isLoading.value = true;

  try {
    // 1. 智能识别参数 (保留之前的逻辑)
    let params = {
      password: loginData.password,
      captcha: loginData.captcha // 传入验证码
    };

    const inputValue = loginData.username;

    if (/^1\d{10}$/.test(inputValue)) {
      params.username = 'u' + inputValue;
	  
    } else if (/@/.test(inputValue)) {
      params.email = inputValue;  // 邮箱
    } else {
      params.username = inputValue; // 用户名
    }

    // 2. 调用登录接口
    const res = await uniIdCo.login(params);
	// console.log("res:",res);
    // 判断 errCode === 0 代表成功
        if (res.errCode === 0) {
          
			// 调用 store.js 提供的标准登录成功方法
			// 它会自动保存 token，自动获取用户信息，自动更新 store.userInfo
			mutations.loginSuccess({
				...res,
				showToast: true,
				autoBack: false // 我们自己控制跳转，所以设为 false
			});
          
          setTimeout(() => {
			if (redirectUrl.value) {
			    // A. 如果有回跳地址 -> 比如回到答题页
			    // 使用 redirectTo 或 reLaunch 均可，看你是否想保留登录页在栈里(通常不想)
			    uni.redirectTo({ url: redirectUrl.value });
			} else {
			    // B. 默认 -> 回首页
			    uni.reLaunch({ url: '/pages/index/index' });
			}  
            
          }, 800);
        } 
        
        else {
            // 处理 errCode 不为 0 的情况
            throw new Error(res.errMsg || 'Login failed');
        }

  } catch (e) {
    console.error(e);
    
    // 4. 错误处理
    let msg = e.errMsg || e.message || 'Login failed';
    
    // 特殊错误码处理：如果提示需要验证码，或者验证码错误，自动刷新
    if (e.errCode === 'uni-id-captcha-required' || e.errCode === 'uni-id-captcha-error') {
       msg = e.errCode === 'uni-id-captcha-required' ? '请输入验证码' : '验证码错误';
       refreshCaptcha(); // 刷新图片
       loginData.captcha = ''; // 清空输入
    } else if(msg.includes('User not exists')){
        msg = '账号不存在';
    } else if (msg.includes('password')){
        msg = '密码错误';
        refreshCaptcha(); // 密码错误也刷新一下验证码，防止暴力破解
        loginData.captcha = '';
    }
    
    uni.showToast({ title: msg+'111', icon: 'none' });
  } finally {
    isLoading.value = false;
  }
};
</script>

<style lang="scss" scoped>
@import '@/static/css/auth.scss';

/* --- 验证码专属样式 (复用注册页的样式) --- */
// .captcha-box {
//   display: flex;
//   align-items: center;
//   gap: 12px;
  
//   .captcha-input {
//     flex: 1; 
//   }
  
//   .captcha-img-wrapper {
//     width: 120px;
//     height: 50px;
//     border-radius: 10px;
//     overflow: hidden;
//     cursor: pointer;
//     background: #f0f0f0;
//     flex-shrink: 0;
//     display: flex;
    
//     /* 强制填满容器 */
//     ::v-deep .uni-captcha {
//       width: 100% !important;
//       height: 100% !important;
//       margin: 0 !important;
//       padding: 0 !important;
//       background-color: transparent !important;
//       display: flex !important;
//     }

//     ::v-deep .uni-captcha > view, 
//     ::v-deep .uni-captcha image {
//       width: 100% !important;
//       height: 100% !important;
//       object-fit: cover !important;
//       display: block !important;
//     }
//   }
// }
</style>
<template>
  <view class="navbar-wrapper">
    <view class="container-xl navbar-inner">
      <text class="logo" @click="goHome">SYNTAX</text>
      
      <view class="nav-menu">
        <text class="nav-item">Products-xu</text>
        <text class="nav-item">Solutions-huan</text>
        <text class="nav-item">Pricing-tian</text>
        <text class="nav-item">Docs-King</text>
      </view>
      
      <view class="nav-actions">
        <!-- 核心改变：直接使用 store.hasLogin 判断登录状态 -->
        <template v-if="!store.hasLogin">
          <text class="login-link" @click="handleAuth('login')">Sign In</text>
          <view class="nav-btn" @click="handleAuth('register')">Start Free</view>
        </template>

        <template v-else>
          <view class="user-profile-area">
            <view class="avatar-wrapper">
              <!-- 核心改变：直接使用 store.userInfo 读取数据 -->
			  <!-- store.userInfo.avatar_file.url -->
				<image v-if="store.userInfo?.avatar_file?.url" 
					:src="realAvatarUrl"  
					class="avatar-img" mode="aspectFill">
				</image>
              <view v-else class="avatar-placeholder">{{ userInitial }}</view>
            </view>

            <view class="dropdown-menu">
              <view class="menu-header">
                <text class="u-name">{{ store.userInfo.nickname || store.userInfo.username || 'User' }}</text>
                <text class="u-sub">{{ store.userInfo.email || store.userInfo.mobile || 'No contact info' }}</text>
              </view>
              
              <view class="menu-divider"></view>
              <view class="menu-item" @click="goProfile">
				  <text class="icon">👤</text> Profile Settings
			  </view>
			  
			  <view class="menu-item" @click="goHistory">
			      <text class="icon">🕒</text> Learning Activity
			  </view>
			  
			  <view class="menu-item" @click="goFeedback">
				  <text class="icon">💬</text> Help & Feedback
			  </view>
              <!-- <view class="menu-item"><text class="icon">📊</text> Dashboard</view> -->
              
			  <view class="menu-divider"></view>
              
			  <!-- 管理员可见 -->
			  <template v-if="isAdmin">
				<view class="menu-item admin-item" @click="goAdminFeedback">
			      <text class="icon">🛠️</text> Admin Console
			    </view>
			  </template>
			  
              <view class="menu-item logout" @click="handleLogout">
                <text class="icon">🚪</text> Log Out
              </view>  
            </view>
			
          </view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref,computed ,watch ,onMounted} from 'vue';
// 1. 引入官方 store
import { store, mutations } from '@/uni_modules/uni-id-pages/common/store.js';

const IS_MODAL_MODE = false; 
const emit = defineEmits(['openAuth']);
const realAvatarUrl = ref('');

//计算是否 是管理员
const isAdmin = computed(()=>{
	// console.log(",",store.userInfo)
	if (!store.hasLogin || !store.userInfo.role) return false;
	  return store.userInfo.role.includes('admin');
})

// 计算首字母
const userInitial = computed(() => {
  // store.userInfo 默认为空对象 {}，所以要判断一下 keys
  if (!store.hasLogin) return '?';
  const u = store.userInfo;
  const name = u.nickname || u.username || u.mobile || 'U';
  return String(name).charAt(0).toUpperCase();
});

const goHome = () => uni.reLaunch({ url: '/pages/index/index' });
const goFeedback = () => {uni.navigateTo({ url: '/pages/feedback/index' });};
const goProfile = () => {uni.navigateTo({ url: '/pages/profile/index' });};
// 跳转管理页
const goAdminFeedback = () => {uni.navigateTo({ url: '/pages/feedback/admin' });};


const handleAuth = (type) => {
  if (IS_MODAL_MODE) {
    emit('openAuth', type);
  } else {
    uni.navigateTo({ url: type === 'login' ? '/pages/login/login' : '/pages/register/register' });
  }
};

const getRealUrl = async (fileId) => {
  if (!fileId) {
    realAvatarUrl.value = '';
    return;
  }
  if (fileId.startsWith('http') || fileId.startsWith('blob')) {
    realAvatarUrl.value = fileId;
    return;
  }
  try {
    const res = await uniCloud.getTempFileURL({ fileList: [fileId] });
    if (res.fileList && res.fileList.length > 0) {
      realAvatarUrl.value = res.fileList[0].tempFileURL;
    }
  } catch (e) {
    console.error('Navbar头像转换失败', e);
  }
};
// 2. 退出登录逻辑
const handleLogout = () => {
  uni.showModal({
    title: 'Log out',
    content: 'Are you sure?',
    success: async (res) => {
      if (res.confirm) {
        // 方案 A: 使用官方 mutations.logout()
        // 注意：官方方法强制跳转到登录页，如果你希望这样，直接取消下面注释即可
        // mutations.logout(); 

        // 方案 B: (推荐) 自定义优雅退出，停留在当前页或首页
        try {
            const uniIdCo = uniCloud.importObject("uni-id-co", { customUI: true });
            await uniIdCo.logout();
        } catch(e){}

        // 核心：调用 store 的方法清空状态，Navbar 会自动响应变化！
        mutations.setUserInfo({}, { cover: true });
        
        // 清理一下其他可能残留的 token
        uni.removeStorageSync('uni_id_token');
        uni.removeStorageSync('uni_id_token_expired');

        uni.showToast({ title: 'Logged out', icon: 'none' });
        
        // 优雅跳转回首页
        uni.reLaunch({ url: '/pages/index/index' });
      }
    }
  });
};

//跳转到历史答题页面
const goHistory = ()=> {
	uni.navigateTo({
		url:'/pages/record/history',
		animationType:'fade-in'
	})
	
}


//监听用户信息变化 
// 只要 store 里的头像 ID 变了（比如上传成功后），立刻重新获取 https 链接
watch(() => store.userInfo, (newUserInfo) => {
  // 1. 安全获取 file 对象
  const avatarFile = newUserInfo?.avatar_file;
  
  // 2. 优先取 avatar_file.url，如果没有，再尝试取旧版字段 avatar
  // 注意这里加了 ?. 防止报错
  const fileId = avatarFile?.url || newUserInfo?.avatar;
  
  // 3. 只有当 fileId 存在时才去请求
  if (fileId) {
    getRealUrl(fileId);
  } else {
    realAvatarUrl.value = ''; // 如果没有头像，清空 url
  }
}, { immediate: true, deep: true });

</script>

<style lang="scss" scoped>
.navbar-wrapper {
  position: sticky; top: 0; z-index: 999; height: 70px;
  background: rgba(255,255,255,0.85); backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.navbar-inner { height: 100%; display: flex; align-items: center; justify-content: space-between; }
.logo { font-size: 20px; font-weight: 800; cursor: pointer; letter-spacing: -0.5px; }

/* 菜单项 */
.nav-menu { display: flex; gap: 32px; }
.nav-item { font-size: 14px; font-weight: 500; color: #666; cursor: pointer; transition: color 0.2s; &:hover { color: #000; } }

/* 右侧操作区 */
.nav-actions { display: flex; align-items: center; gap: 20px; }

/* 未登录时的按钮 */
.login-link { font-size: 14px; font-weight: 500; color: #666; cursor: pointer; &:hover { color: #000; } }
.nav-btn { font-size: 14px; background: #000; color: #fff; padding: 8px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; &:hover { opacity: 0.8; } }

/* =================================
   大厂风格：用户头像与下拉菜单
   ================================= */
.user-profile-area {
  position: relative; /* 关键：作为下拉菜单的定位基准 */
  padding: 10px 0;    /* 增加上下热区，防止鼠标移出头像时菜单瞬间消失 */
  
  /* 鼠标移入整个区域时，显示下拉菜单 */
  &:hover .dropdown-menu {
    opacity: 1;
    transform: translateY(0) scale(1);
    visibility: visible;
    pointer-events: auto;
  }
}

/* 头像容器 */
.avatar-wrapper {
  width: 36px; height: 36px;
  cursor: pointer;
  border-radius: 50%;
  transition: box-shadow 0.2s;
  
  &:hover {
    box-shadow: 0 0 0 2px rgba(0,0,0,0.1); /* 悬浮时的微光圈 */
  }
}

.avatar-img {
  width: 100%; height: 100%; border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.1);
}

/* 默认头像占位 (彩色圆点) */
.avatar-placeholder {
  width: 100%; height: 100%; border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 漂亮的蓝紫渐变 */
  color: #fff; font-size: 16px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: 100%; right: 0;
  width: 240px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px); /* 强毛玻璃 */
  border-radius: 16px;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.05);
  padding: 8px;
  
  /* 动画初始状态：隐藏、下移、微缩 */
  opacity: 0;
  transform: translateY(10px) scale(0.98);
  visibility: hidden;
  pointer-events: none;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top right;
}

.menu-header {
  padding: 12px 16px;
  .u-name { display: block; font-size: 15px; font-weight: 600; color: #111; margin-bottom: 2px; }
  .u-sub { display: block; font-size: 12px; color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}

.menu-divider {
  height: 1px; background: #f0f0f0; margin: 4px 8px;
}

.menu-item {
  display: flex; align-items: center;
  padding: 10px 16px;
  margin: 2px 0;
  border-radius: 8px;
  font-size: 14px; color: #333;
  cursor: pointer;
  transition: background 0.15s;
  
  .icon { margin-right: 10px; font-size: 16px; }
  
  &:hover { background: #F5F5F7; }
  
  &.logout {
    color: #FF4D4F;
    &:hover { background: #FFF1F0; }
  }
}
.admin-item {
  color: #1677FF; /* 品牌蓝，区别于普通菜单 */
  font-weight: 600;
  &:hover { background: #E6F7FF; }
}

/* 响应式 */
@media screen and (max-width: 768px) {
  .nav-menu { display: none; }
}
</style>
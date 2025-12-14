<template>
  <view class="profile-page">
    <PcNavbar />
    
    <!-- 顶部背景装饰 -->
    <view class="profile-bg"></view>

    <view class="container-xl content-wrapper">
      
      <!-- 页面标题 -->
      <view class="page-header">
        <text class="title">Account Settings</text>
        <text class="subtitle">Manage your profile details and security preferences.</text>
      </view>

      <view class="settings-grid">
        
        <!-- 左侧：导航/概览 (可选，此处做成用户信息概览) -->
        <view class="profile-sidebar">
          <view class="user-card">
            <view class="avatar-group" @click="uploadAvatar">
              <image 
                :src="realAvatarUrl" 
                class="avatar-lg" 
                mode="aspectFill"
                v-if="store.userInfo.avatar_file.url"
              ></image>
              <view class="avatar-placeholder" v-else>{{ userInitial }}</view>
              
              <!-- 上传遮罩 -->
              <view class="avatar-overlay">
                <text class="icon-camera">📷</text>
              </view>
            </view>
            
            <text class="u-name">{{ userInfo.nickname || 'User' }}</text>
            <text class="u-role">Developer</text>
            
            <view class="stat-row">
                <!-- 简单 -->
                <view class="s-item">
                    <text class="n easy">{{ userStats.easy }}</text>
                    <text class="l">Easy</text>
                </view>
                <view class="s-sep"></view>
                          
                <!-- 中等 -->
                <view class="s-item">
                    <text class="n medium">{{ userStats.medium }}</text>
                    <text class="l">Med</text>
                </view>
                <view class="s-sep"></view>
                          
                <!-- 困难 -->
                <view class="s-item">
                    <text class="n hard">{{ userStats.hard }}</text>
                    <text class="l">Hard</text>
                </view>
                          
                <!-- 分割线 (区分数量与正确率) -->
                <view class="s-divider-vertical"></view>
                          
                <!-- 正确率 -->
                <view class="s-item">
                    <text class="n rate">{{ userStats.accuracy }}%</text>
                    <text class="l">Rate</text>
                </view>
            </view>
			
          </view>
        </view>

        <!-- 右侧：设置表单 -->
        <view class="settings-main">
          
          <!-- 1. 基本信息卡片 -->
          <view class="setting-card">
            <view class="card-header">
              <text class="c-title">General Information</text>
            </view>
            <view class="card-body">
              
              <view class="form-item">
                <text class="label">Nickname</text>
                <input class="input" v-model="formData.nickname" placeholder="Enter your nickname" />
              </view>
              
              <view class="form-item">
                <text class="label">Mobile Number</text>
                <view class="input disabled">
                  <text>{{ userInfo.mobile || 'Not bound' }}</text>
                  <text class="tag-verified" v-if="userInfo.mobile_confirmed">Verified</text>
                </view>
                <text class="helper-text">Contact support to change your mobile number.</text>
              </view>

            </view>
            <view class="card-footer">
              <button class="btn-save" @click="saveProfile" :loading="loading">Save Changes</button>
            </view>
          </view>

          <!-- 2. 安全设置卡片 -->
          <view class="setting-card">
            <view class="card-header">
              <text class="c-title">Security</text>
            </view>
            <view class="card-body">
              <view class="security-row">
                <view class="sec-info">
                  <text class="sec-label">Password</text>
                  <text class="sec-desc">Last changed 3 months ago</text>
                </view>
                <button class="btn-outline" @click="toSetPwd">Change Password</button>
              </view>
            </view>
          </view>

        </view>
      </view>

    </view>
    
    <PcFooter />
    <!-- 引入刚刚写的悬浮按钮 -->
    <FeedbackFab />
  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted ,watch} from 'vue';
import { store, mutations } from '@/uni_modules/uni-id-pages/common/store.js';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import FeedbackFab from '@/components/FeedbackFab/FeedbackFab.vue';
import { getCloudObject } from '@/utils/cloud.js';

const uniIdCo = getCloudObject('uni-id-co');
const quizCo = getCloudObject('quiz-co');

const loading = ref(false);
//用于记录用户已经答题的数量，并且拆分为难 - 中 - 易三个部分
const userStats = ref({
  easy: 0,
  medium: 0,
  hard: 0,
  total: 0,
  accuracy: 0
});

// 直接使用 store 中的用户信息
const userInfo = computed(() => store.userInfo);

// 表单数据
const formData = reactive({
  nickname: ''
});

const userInitial = computed(() => {
  const name = userInfo.value.nickname || userInfo.value.username || 'U';
  return String(name).charAt(0).toUpperCase();
});

// 获取统计数据
const fetchUserStats = async () => {
  try {
    const res = await quizCo.getUserStatsToProfit(); 

    if (res.errCode === 0) {
      userStats.value = res.data;
    }
  } catch (e) {
    console.error(e);
  }
};

// 初始化数据
onMounted(() => {
  if (store.hasLogin) {
    formData.nickname = userInfo.value.nickname || '';
	fetchUserStats(); // 调用统计接口
  }
});

// 1. 新增一个响应式变量，用于存储转换后的真实 https 链接
const realAvatarUrl = ref('');

// 2. 封装一个转换函数
const getRealUrl = async (fileId) => {
  if (!fileId) {
    realAvatarUrl.value = '';
    return;
  }
  
  // 如果已经是 http 开头，说明已经是直链，直接用
  if (fileId.startsWith('http') || fileId.startsWith('blob')) {
    realAvatarUrl.value = fileId;
    return;
  }

  // 如果是 cloud:// 开头，需要转换
  try {
    const res = await uniCloud.getTempFileURL({
      fileList: [fileId]
    });
    if (res.fileList && res.fileList.length > 0) {
      realAvatarUrl.value = res.fileList[0].tempFileURL;
    }
  } catch (e) {
    console.error('头像链接转换失败', e);
  }
};

// 3. 监听用户信息变化 (核心修复)
// 只要 store 里的头像 ID 变了（比如上传成功后），立刻重新获取 https 链接
watch(() => store.userInfo.avatar_file, (newVal) => {
  const fileId = newVal?.url || store.userInfo.avatar;
  getRealUrl(fileId);
}, { immediate: true, deep: true });

// --- 上传头像 ---
const uploadAvatar = () => {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      const filePath = res.tempFilePaths[0];
      uni.showLoading({ title: 'Uploading...' });
      
      try {
        // 1. 上传到云存储
        const result = await uniCloud.uploadFile({
          filePath: filePath,
          cloudPath: `${store.userInfo.username}/avatar/${store.userInfo._id}_${Date.now()}.jpg`
        });
        
        // 2. 调用官方 mutations 更新头像
        // 注意：uni-id 默认使用 avatar_file 字段存储图片对象
        await mutations.updateUserInfo({
          avatar_file: {
            url: result.fileID
          }
        });
        
        uni.hideLoading();
        uni.showToast({ title: 'Avatar updated', icon: 'success' });
      } catch (e) {
        uni.hideLoading();
        console.error(e);
        uni.showToast({ title: 'Upload failed', icon: 'none' });
      }
    }
  });
};

// --- 保存资料 ---
const saveProfile = async () => {
  if(!formData.nickname.trim()) return;

  loading.value = true;
  try {
    // 它会自动：1.请求数据库更新 2.更新本地Store 3.触发界面刷新
    await mutations.updateUserInfo({
      nickname: formData.nickname
    });
    
    // 这里的提示其实 mutations 内部也有，可以保留或去掉
    // mutations 内部已经弹了 "更新成功"，这里就不弹了，或者根据需求定制
  } catch (e) {
    // 错误处理交给 mutations 内部打印，或者在这里补充
    console.error(e);
  } finally {
    loading.value = false;
  }
};

// 跳转修改密码 (复用 uni-id-pages 的页面，减少重复造轮子)
const toSetPwd = () => {
  uni.navigateTo({
    url: '/uni_modules/uni-id-pages/pages/userinfo/change_pwd/change_pwd'
  });
};
</script>

<style lang="scss" scoped>
page { background-color: #F8FAFC; }
.profile-page { min-height: 100vh; position: relative; }

/* 顶部装饰背景 */
.profile-bg {
  position: absolute; top: 0; left: 0; width: 100%; height: 240px;
  background: linear-gradient(180deg, #E2E8F0 0%, #F8FAFC 100%);
  z-index: 0;
}

.content-wrapper { position: relative; z-index: 1; padding-top: 40px; padding-bottom: 60px; }

/* 页面标题 */
.page-header {
  margin-bottom: 40px;
  .title { font-size: 32px; font-weight: 800; color: #0F172A; display: block; }
  .subtitle { font-size: 16px; color: #64748B; }
}

/* 栅格布局 */
.settings-grid {
  display: grid;
  grid-template-columns: 280px 1fr; /* 左窄右宽 */
  gap: 32px;
}

/* 左侧：用户卡片 */
.user-card {
  background: #fff; border-radius: 20px; padding: 40px 20px;
  display: flex; flex-direction: column; align-items: center; text-align: center;
  border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);

  /* pages/profile/index.vue -> style */
  
    .avatar-group {
      position: relative; 
      margin-bottom: 16px; 
      cursor: pointer;
      width: 100px; 
      height: 100px;
      /* 🔴 核心修复：边框和圆角加在父容器上 */
      border-radius: 50%;
      border: 4px solid #fff; 
      box-shadow: 0 4px 10px rgba(0,0,0,0.1);
      /* 🔴 核心修复：超出部分隐藏，保证图片和遮罩不出界 */
      overflow: hidden; 
      
      .avatar-lg { 
        width: 100%; 
        height: 100%; 
        /* 移除图片自身的边框和圆角，由父容器控制 */
        border-radius: 0; 
        border: none; 
        display: block;
      }
      
      .avatar-placeholder { 
        width: 100%; 
        height: 100%; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: #fff; 
        font-size: 36px; 
        font-weight: 700; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        /* 移除边框 */
        border: none; 
      }
      
      /* 悬浮显示的遮罩 */
      .avatar-overlay {
        position: absolute; 
        top: 0; 
        left: 0; 
        width: 100%; 
        height: 100%;
        background: rgba(0,0,0,0.5); 
        /* 这里的圆角其实被父容器裁切了，写不写都行，写上保险 */
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        opacity: 0; 
        transition: opacity 0.2s;
        z-index: 2; /* 确保在最上层 */
      }
      
      &:hover .avatar-overlay { opacity: 1; }
      .icon-camera { font-size: 24px; }
    
  }

  .u-name { font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 4px; }
  .u-role { font-size: 13px; color: #64748B; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 24px; }

  .stat-row {
      display: flex; 
      align-items: center; 
      justify-content: center; /* 居中对齐 */
      gap: 16px; 
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid #F1F5F9; /* 顶部分割线 */
      width: 100%;
  
      .s-item { 
        display: flex; 
        flex-direction: column; 
        align-items: center;
        min-width: 40px; 
      }
      
      /* 数字样式：大字号 + 颜色编码 */
      .n { 
        font-size: 20px; 
        font-weight: 800; 
        line-height: 1.2;
        
        &.easy   { color: #10B981; } /* 绿色 */
        &.medium { color: #F59E0B; } /* 橙色 */
        &.hard   { color: #EF4444; } /* 红色 */
        &.rate   { color: #0F172A; } /* 深色 */
      }
      
      /* 标签样式 */
      .l { 
        font-size: 11px; 
        color: #94A3B8; 
        text-transform: uppercase; 
        font-weight: 600; 
        margin-top: 4px;
      }
      
      /* 小分割线 */
      .s-sep { 
        width: 1px; 
        height: 16px; 
        background: #E2E8F0; 
      }
      
      /* 大分割线 (区分难度和正确率) */
      .s-divider-vertical {
        width: 1px;
        height: 32px;
        background: #CBD5E1;
        margin: 0 8px;
      }
    }
}

/* 右侧：设置卡片 */
.setting-card {
  background: #fff; border-radius: 16px; border: 1px solid #E2E8F0;
  margin-bottom: 24px; overflow: hidden;
  
  .card-header {
    padding: 20px 32px; border-bottom: 1px solid #F1F5F9;
    .c-title { font-size: 18px; font-weight: 700; color: #0F172A; }
  }
  
  .card-body { padding: 32px; }
  .card-footer { padding: 20px 32px; background: #F8FAFC; border-top: 1px solid #F1F5F9; display: flex; justify-content: flex-end; }
}

/* 表单样式 */
.form-item {
  margin-bottom: 24px;
  &:last-child { margin-bottom: 0; }
  
  .label { display: block; font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 8px; }
  
  .input {
    width: 100%; height: 48px; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0 16px; font-size: 15px; color: #1E293B; box-sizing: border-box; transition: all 0.2s;
    &:focus { border-color: #0F172A; outline: none; }
    
    &.disabled {
      background: #F1F5F9; color: #94A3B8; border-color: #F1F5F9; display: flex; align-items: center; justify-content: space-between;
      .tag-verified { font-size: 12px; color: #10B981; background: #ECFDF5; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
    }
  }
  .helper-text { font-size: 13px; color: #94A3B8; margin-top: 6px; display: block; }
}

/* 按钮样式 */
.btn-save {
  background: #0F172A; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer;
  &:hover { background: #334155; }
}

.security-row {
  display: flex; justify-content: space-between; align-items: center;
  .sec-label { font-size: 15px; font-weight: 600; color: #1E293B; display: block; margin-bottom: 4px; }
  .sec-desc { font-size: 13px; color: #94A3B8; }
  
  .btn-outline {
    background: #fff; border: 1px solid #E2E8F0; color: #475569; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer;
    &:hover { background: #F8FAFC; border-color: #CBD5E1; }
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .settings-grid { grid-template-columns: 1fr; }
  .profile-sidebar { margin-bottom: 20px; }
}
</style>
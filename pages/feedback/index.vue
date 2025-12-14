<template>
  <view class="feedback-page">
    <PcNavbar />
    
    <view class="container-xl">
      <view class="feedback-layout">
        
        <!-- 左侧：头部与切换 -->
        <view class="layout-header">
          <text class="page-title">Help & Feedback</text>
          <text class="page-sub">We value your voice. Help us improve.</text>
          
          <view class="tab-switch">
            <view 
              class="tab-item" 
              :class="{ active: currentTab === 'submit' }"
              @click="currentTab = 'submit'"
            >
              ✍️ Submit
            </view>
            <view 
              class="tab-item" 
              :class="{ active: currentTab === 'list' }"
              @click="currentTab = 'list'; fetchList()"
            >
              🗂️ My Records
            </view>
            <view class="tab-bg" :style="{ transform: currentTab === 'submit' ? 'translateX(0)' : 'translateX(100%)' }"></view>
          </view>
        </view>

        <!-- 右侧内容区：动态切换 -->
        <view class="layout-content">
          
          <!-- 1. 提交表单 -->
          <view class="form-panel animate-fade" v-if="currentTab === 'submit'">
            <view class="panel-title">What's on your mind?</view>
            
            <!-- 分类选择 -->
            <view class="form-label">Feedback Type</view>
            <view class="type-grid">
              <view 
                v-for="t in types" :key="t.value"
                class="type-chip"
                :class="{ active: formData.type === t.value }"
                @click="formData.type = t.value"
              >
                {{ t.label }}
              </view>
            </view>
            
            <!-- 内容输入 -->
            <view class="form-label">Details & Attachments</view>
            <view class="rich-input-wrapper">
                <textarea 
                    class="custom-textarea" 
                    v-model="formData.content" 
                    placeholder="在此输入文字，或直接 Ctrl+V 粘贴截图...[Describe your issue... (You can paste screenshots here directly)]" 
                    maxlength="500"
                    @paste="handlePaste"
                ></textarea>
                          
                <!-- 图片预览区 -->
                <view class="image-preview-list" v-if="tempImages.length > 0">
                    <view class="img-item" v-for="(img, index) in tempImages" :key="index">
                        <!-- 加载中遮罩 -->
                        <view class="uploading-mask" v-if="img.status === 'uploading'">
                            <view class="spinner-sm"></view>
                        </view>
                        <!-- 图片显示 -->
                        <image :src="img.localPath" mode="aspectFill" class="thumb" @click="previewImage(img.localPath)"></image>
                        <!-- 删除按钮 -->
                        <view class="btn-remove" @click.stop="removeImage(index)">✕</view>
                    </view>
                </view>
            
                <!-- 工具栏 -->
                <view class="input-toolbar">
                    <view class="tool-btn" @click="chooseImage">
                        <text class="icon">📷</text>
                        <text>Add Image</text>
                    </view>
                    <text class="count">{{ formData.content.length }}/500</text>
                </view>
            </view>
            
            <!-- 联系方式 -->
            <view class="form-label">Contact (Optional)</view>
            <input 
              class="custom-input" 
              v-model="formData.contact" 
              placeholder="Email or phone number"
            />
            
            <button class="btn-submit" @click="handleSubmit" :loading="submitting">
              Send Feedback
            </button>
          </view>

          <!-- 2. 反馈列表 -->
          <view class="list-panel animate-fade" v-else>
            <view v-if="loading" class="loading-state"><view class="spinner"></view></view>
            
            <view v-else-if="list.length === 0" class="empty-state">
              <text class="empty-icon">🍃</text>
              <text>No feedback yet.</text>
            </view>
            
            <scroll-view scroll-y class="list-scroll" v-else>
              <view class="record-card" v-for="item in list" :key="item._id">
                <view class="card-top">
                  <view class="tags">
                    <text class="tag-type">{{ getTypeLabel(item.type) }}</text>
                    <text class="date">{{ formatDate(item.create_date) }}</text>
                  </view>
                  <!-- 状态徽章 -->
                  <view class="status-badge" :class="getStatusClass(item.status)">
                    {{ getStatusLabel(item.status) }}
                  </view>
                </view>
                
                <text class="user-content">{{ item.content }}</text>
				
				 <!-- [新增] 列表显示图片 -->
				<view class="record-images" v-if="item.images && item.images.length">
				    <image 
				        v-for="(img, idx) in item.images" 
							:key="idx" 
				            :src="img" 
				            mode="aspectFill" 
				            class="record-thumb"
				            @click="previewRecordImage(item.images, idx)"
				    ></image>
				</view>
                
                <!-- 管理员回复区域 (如果有) -->
                <view class="admin-reply" v-if="item.reply_content">
                  <view class="reply-header">
                    <text class="icon">👩‍💻</text>
                    <text class="name">Support Team</text>
                    <text class="time">{{ formatDate(item.reply_date) }}</text>
                  </view>
                  <text class="reply-text">{{ item.reply_content }}</text>
                </view>
              </view>
            </scroll-view>
          </view>

        </view>
      </view>
    </view>

    <PcFooter />
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import PcFooter from '@/components/PcFooter/PcFooter.vue';
import { getCloudObject } from '@/utils/cloud.js';
import { store, mutations } from '@/uni_modules/uni-id-pages/common/store.js';

const feedbackCo = getCloudObject('feedback-co');

const currentTab = ref('submit');
const submitting = ref(false);
const loading = ref(false);
const list = ref([]);

const types = [
  { label: '💡 Suggestion', value: 'suggestion' },
  { label: '🐛 Bug Report', value: 'bug' },
  { label: '📚 Content Error', value: 'content' },
  { label: '💬 Other', value: 'other' }
];

const formData = reactive({
  type: 'suggestion',
  content: '',
  contact: '',
  images:[]
});
// [新增] 临时图片列表，包含上传状态
/**
 * tempImages 结构定义:
 * {
 *   localPath: 'blob:http://...', // 用于前端展示，绝对不会报错
 *   cloudId: 'cloud://...',       // 上传后的原始ID，存数据库用
 *   status: 'uploading' | 'success' | 'error'
 * }
 */
const tempImages = ref([]); 

// 1. 选择图片
const chooseImage = () => {
  uni.chooseImage({
    count: 3 - tempImages.value.length, // 限制最多3张
    success: (res) => {
      res.tempFilePaths.forEach(path => {
        uploadToCloud(path);
      });
    }
  });
};

// 2. 粘贴事件处理 (终极兼容版)
const handlePaste = (event) => {
  // 1. 尝试直接从参数获取
  let clipboardData = event.clipboardData;

  // 2. 如果没有，尝试从 uni-app 的封装层 originalEvent 获取
  if (!clipboardData && event.originalEvent) {
    clipboardData = event.originalEvent.clipboardData;
  }

  // 3. [最关键一步] 如果还是没有，直接读取浏览器全局事件对象 (解决 H5 很多兼容问题)
  if (!clipboardData && window.event) {
    clipboardData = window.event.clipboardData;
  }

  // console.log('剪贴板对象:', clipboardData); // 调试看这里是否还有值

  if (!clipboardData || !clipboardData.items) {
    // console.warn('未检测到剪贴板数据，可能是浏览器权限限制或非图片内容');
    return;
  }

  const items = clipboardData.items;
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    
    // 只处理图片
    if (item.type.indexOf('image') !== -1) {
      // 这里的 event 需要使用 window.event 或者传入的 event 来阻止默认行为
      // 为了保险，两个都调用一下
      if (event.preventDefault) event.preventDefault();
      if (window.event && window.event.preventDefault) window.event.preventDefault();
      
      const file = item.getAsFile();
      if (file) {
        const blobUrl = URL.createObjectURL(file);
        // console.log('捕获到图片，准备上传:', blobUrl);
        
        // 调用上传函数
        uploadToCloud(blobUrl, file);
      }
    }
  }
};

// 3. 上传逻辑 (核心修复：解决 cloud:// 报错)
const uploadToCloud = async (path, fileObj = null) => {
  if (tempImages.value.length >= 3) return uni.showToast({title: 'Max 3 images', icon:'none'});

  // 创建响应式对象
  const imgItem = reactive({ 
    localPath: path, // 关键：界面只显示这个，避免报错
    cloudId: '',
    status: 'uploading' 
  });
  tempImages.value.push(imgItem);

  try {
    const cloudPath = `${store.userInfo.username}/feedback/${Date.now()}_${Math.random().toString(36).slice(2)}.jpg`;
    
    // Web端上传
    const result = await uniCloud.uploadFile({
        filePath: path, 
        cloudPath: cloudPath,
        fileType: 'image'
    });

    // console.log('上传成功，原始结果:', result);
    
    // 获取 cloudID (阿里云通常是 fileID)
    const fileID = result.fileID || result.url;
    imgItem.cloudId = fileID; // 存起来，提交表单用

    // 【关键步骤】如果是 Web 端，cloud:// 无法直接显示
    // 如果你想在“提交后”或者“列表中”能看到图，通常需要换取 http 链接
    // 但在当前编辑界面，我们继续使用 localPath (Blob) 即可，不需要换成 http
    // 状态更新为成功
    imgItem.status = 'success';

  } catch (err) {
    console.error('上传失败:', err);
    imgItem.status = 'error';
    uni.showToast({ title: 'Upload failed', icon: 'none' });
    // 移除失败项
    setTimeout(() => {
        const idx = tempImages.value.indexOf(imgItem);
        if (idx !== -1) tempImages.value.splice(idx, 1);
    }, 1000);
  }
};

const removeImage = (index) => {
  tempImages.value.splice(index, 1);
};

const previewImage = (url) => {
  // 预览时如果是在上传中，可能还是 blob 地址，也能预览
  uni.previewImage({ urls: [url] });
};

// 列表图片预览
const previewRecordImage = (urls, current) => {
    uni.previewImage({ urls, current });
}

// 4. 提交表单
const handleSubmit = async () => {
  if (!formData.content.trim()) return uni.showToast({ title: '内容不能为空', icon: 'none' });
  
  if (tempImages.value.some(img => img.status === 'uploading')) {
    return uni.showToast({ title: '图片正在上传...', icon: 'none' });
  }

  submitting.value = true;
  
  // 提取上传成功的 Cloud ID 发送给数据库
  formData.images = tempImages.value
    .filter(img => img.status === 'success')
    .map(img => img.cloudId);

  try {
    const res = await feedbackCo.submitFeedback(formData);
    if (res.errCode === 0) {
      uni.showToast({ title: '反馈成功!', icon: 'success' });
      // 清空
      formData.content = '';
      formData.contact = '';
      formData.images = [];
      tempImages.value = [];
      
      setTimeout(() => {
        currentTab.value = 'list';
        fetchList();
      }, 1000);
    }
  } catch(e) {
    console.error(e);
    uni.showToast({ title: '提交失败', icon: 'none' });
  } finally {
    submitting.value = false;
  }
};

// 5. 获取列表 (修复：列表显示 cloud:// 也会报错的问题)
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await feedbackCo.getMyFeedbacks();
    if (res.errCode === 0) {
      const rawList = res.data;
      
      // 【关键】列表中的 cloud:// 必须转成 http 才能在 Web 端显示
      // 提取所有涉及的图片 ID
      let allImageIds = [];
      rawList.forEach(item => {
        if(item.images && item.images.length) {
          allImageIds = allImageIds.concat(item.images);
        }
      });
      
      if (allImageIds.length > 0) {
        // 批量转换 ID 为 HTTP 链接
        const tempFilesRes = await uniCloud.getTempFileURL({
            fileList: allImageIds
        });
        
        // 建立映射表: id -> https://...
        const urlMap = {};
        tempFilesRes.fileList.forEach(f => {
            urlMap[f.fileID] = f.tempFileURL;
        });
        
        // 替换列表数据中的链接
        rawList.forEach(item => {
            if(item.images && item.images.length) {
                item.images = item.images.map(id => urlMap[id] || id);
            }
        });
      }

      list.value = rawList;
    }
  } catch (e) {
      console.error(e);
  } finally {
    loading.value = false;
  }
};

// 工具函数
const getTypeLabel = (val) => types.find(t => t.value === val)?.label || 'Feedback';
const formatDate = (ts) => new Date(ts).toLocaleDateString();

const getStatusLabel = (s) => {
  const map = { 0: 'Pending', 1: 'Processing', 2: 'Resolved', 3: 'Closed' };
  return map[s] || 'Pending';
};
const getStatusClass = (s) => {
  const map = { 0: 's-gray', 1: 's-blue', 2: 's-green', 3: 's-red' };
  return map[s] || 's-gray';
};
</script>

<style lang="scss" scoped>
page { background-color: #F8FAFC; }
.feedback-page { min-height: 100vh; padding-top: 20px; }

/* 核心布局：两栏式或居中式，这里采用居中卡片式 */
.feedback-layout {
  max-width: 800px; margin: 40px auto;
}

/* Header */
.layout-header {
  text-align: center; margin-bottom: 40px;
  .page-title { font-size: 36px; font-weight: 800; color: #0F172A; display: block; margin-bottom: 8px; }
  .page-sub { font-size: 16px; color: #64748B; }
}

/* Tab Switcher (iOS Segment Control Style) */
.tab-switch {
  display: inline-flex; position: relative;
  background: #E2E8F0; padding: 4px; border-radius: 12px; margin-top: 24px;
  
  .tab-item {
    width: 140px; text-align: center; padding: 8px 0; z-index: 2;
    font-size: 14px; font-weight: 600; color: #64748B; cursor: pointer; transition: color 0.3s;
    &.active { color: #0F172A; }
  }
  
  .tab-bg {
    position: absolute; left: 4px; top: 4px; bottom: 4px; width: 140px;
    background: #fff; border-radius: 8px; z-index: 1;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
}

/* Content Area */
.layout-content {
  background: #fff; border-radius: 24px; padding: 40px;
  box-shadow: 0 10px 30px -5px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;
  min-height: 500px;
}

/* Form Styles */
.panel-title { font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 24px; }
.form-label { font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 12px; display: block; }

.type-grid {
  display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px;
  .type-chip {
    padding: 8px 16px; border-radius: 100px; border: 1px solid #E2E8F0;
    font-size: 13px; color: #475569; cursor: pointer; transition: all 0.2s;
    &:hover { background: #F8FAFC; border-color: #CBD5E1; }
    &.active { background: #0F172A; color: #fff; border-color: #0F172A; }
  }
}

/* [核心修改] 增强型输入框容器 */
.rich-input-wrapper {
  background: #F8FAFC; 
  border: 1px solid #E2E8F0;
  border-radius: 12px; 
  padding: 0; /* 内部控制 padding */
  margin-bottom: 24px;
  transition: all 0.2s;
  overflow: hidden;
  
  /* 聚焦时的样式：模拟整体聚焦 */
  &:focus-within {
    border-color: #0F172A;
    background: #fff;
    box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.1);
  }

  .custom-textarea {
    width: 100%; 
    height: 100px; /* 高度减小，因为有图片区 */
    background: transparent; 
    border: none;
    padding: 16px; 
    font-size: 15px; 
    margin-bottom: 0;
    resize: none;
    &:focus { outline: none; border: none; background: transparent; }
  }

  /* 图片预览列表 */
  .image-preview-list {
    padding: 0 16px 12px 16px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;

    .img-item {
      position: relative;
      width: 64px; height: 64px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #E2E8F0;
      
      .thumb { width: 100%; height: 100%; }
      
      /* 上传中遮罩 */
      .uploading-mask {
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(255,255,255,0.8);
        display: flex; align-items: center; justify-content: center;
        z-index: 2;
      }

      /* 删除按钮 */
      .btn-remove {
        position: absolute; top: 2px; right: 2px;
        width: 16px; height: 16px;
        background: rgba(0,0,0,0.6);
        color: #fff;
        border-radius: 50%;
        font-size: 10px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer;
        z-index: 3;
        &:hover { background: #EF4444; }
      }
    }
  }

  /* 工具栏 */
  .input-toolbar {
    border-top: 1px solid #F1F5F9;
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #F8FAFC;

    .tool-btn {
      display: flex; align-items: center; gap: 6px;
      cursor: pointer;
      padding: 6px 10px;
      border-radius: 6px;
      transition: background 0.2s;
      
      .icon { font-size: 16px; }
      text { font-size: 13px; font-weight: 600; color: #64748B; }
      
      &:hover {
        background: #E2E8F0;
        text { color: #0F172A; }
      }
    }
    
    .count { font-size: 12px; color: #94A3B8; }
  }
}

/* 列表中的图片展示 */
.record-images {
  display: flex; gap: 8px; margin-bottom: 16px;
  .record-thumb {
    width: 80px; height: 80px;
    border-radius: 8px;
    border: 1px solid #F1F5F9;
    cursor: zoom-in;
  }
}

/* Spinner 动画 */
.spinner-sm {
  width: 20px; height: 20px;
  border: 2px solid #CBD5E1;
  border-top-color: #0F172A;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.custom-input {
  width: 100%; height: 48px; background: #F8FAFC; border: 1px solid #E2E8F0;
  border-radius: 12px; padding: 0 16px; font-size: 15px; margin-bottom: 32px; box-sizing: border-box;
  &:focus { outline: none; border-color: #0F172A; background: #fff; }
}

.btn-submit {
  width: 100%; height: 50px; background: #0F172A; color: #fff;
  border-radius: 12px; font-weight: 600; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  &:active { transform: scale(0.98); }
}

/* List Styles */
.list-scroll { max-height: 600px; }

.record-card {
  border: 1px solid #F1F5F9; border-radius: 16px; padding: 20px; margin-bottom: 20px;
  
  .card-top {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
    .tags { display: flex; align-items: center; gap: 8px; }
    .tag-type { font-size: 12px; font-weight: 700; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; }
    .date { font-size: 12px; color: #94A3B8; }
    
    .status-badge {
      font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 100px; text-transform: uppercase;
      &.s-gray { background: #F1F5F9; color: #64748B; } /* Pending */
      &.s-blue { background: #E0F2FE; color: #0284C7; } /* Processing */
      &.s-green { background: #DCFCE7; color: #166534; } /* Resolved */
      &.s-red { background: #FEF2F2; color: #991B1B; } /* Closed */
    }
  }
  
  .user-content { font-size: 15px; color: #334155; line-height: 1.6; display: block; margin-bottom: 16px; }
  
  .admin-reply {
    background: #F8FAFC; border-radius: 12px; padding: 16px; border-left: 3px solid #0F172A;
    .reply-header {
      display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
      .name { font-size: 13px; font-weight: 700; color: #0F172A; }
      .time { font-size: 11px; color: #94A3B8; margin-left: auto; }
    }
    .reply-text { font-size: 14px; color: #475569; line-height: 1.5; }
  }
}

.empty-state { text-align: center; padding: 60px 0; color: #94A3B8; .empty-icon { font-size: 40px; margin-bottom: 16px; display: block; } }
.loading-state { text-align: center; padding: 40px; }

.animate-fade { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Mobile */
@media (max-width: 768px) {
  .feedback-layout { margin: 20px; }
  .layout-content { padding: 24px; }
}
</style>
<template>
  <view class="admin-page">
    <PcNavbar />
    
    <view class="container-xl content">
      <view class="page-header">
        <text class="title">Feedback Console</text>
        
        <!-- 筛选器 -->
        <view class="filter-tabs">
          <view class="tab" :class="{active: filter===''}" @click="switchFilter('')">All</view>
          <view class="tab" :class="{active: filter===0}" @click="switchFilter(0)">Pending</view>
          <view class="tab" :class="{active: filter===2}" @click="switchFilter(2)">Replied</view>
        </view>
      </view>

      <!-- 列表区 -->
      <view class="ticket-list" v-if="!loading">
        <view 
          class="ticket-card" 
          v-for="item in list" 
          :key="item._id"
        >
          <view class="t-header">
            <view class="user-info">
              <text class="u-name">{{ item.nickname || item.username || item.mobile ||'Anonymous' }}</text>
              <text class="u-contact" v-if="item.contact">(contact-way：{{ item.contact }})</text>
            </view>
            <view class="t-meta">
              <text class="tag-type">{{ item.type }}</text>
              <text class="time">{{ formatDate(item.create_date) }}</text>
            </view>
          </view>
          
          <text class="t-content">{{ item.content }}</text>
		  
		   <!-- [新增] 图片展示区域 -->
		  <view class="ticket-imgs" v-if="item.images && item.images.length">
		    <image 
				v-for="(img, idx) in item.images" 
		        :key="idx"
		        :src="img" 
		        mode="aspectFill" 
		        class="t-thumb"
		        @click.stop="previewImage(item.images, idx)"
		    ></image>
		   </view>
          
          <!-- 底部操作栏 -->
          <view class="t-footer">
            <view class="status-indicator">
              <view class="dot" :class="item.status === 2 ? 'green' : 'orange'"></view>
              <text>{{ item.status === 2 ? 'Replied' : 'Pending' }}</text>
            </view>
            
            <button 
              v-if="item.status !== 2" 
              class="btn-reply" 
              @click="openReply(item)"
            >Reply</button>
            <view v-else class="reply-preview">
              <text class="r-label">You replied:</text> {{ item.reply_content }}
            </view>
          </view>
        </view>
        
        <!-- 空状态 -->
        <view v-if="list.length === 0" class="empty">No feedbacks found.</view>
      </view>
      
      <view v-else class="loading"><view class="spinner"></view></view>
    </view>

    <!-- 回复弹窗 -->
    <view class="modal-overlay" v-if="showModal" @click="showModal = false">
      <view class="modal-box" @click.stop>
        <text class="m-title">Reply to User</text>
        <!-- [新增] 快捷回复区域 -->
        <view class="quick-tags">
              <view class="q-label">Quick Reply:</view>
              <view class="tag-list">
                <view 
                  class="tag-item" 
                  v-for="(text, index) in replyTemplates" 
                  :key="index"
                  @click="applyTemplate(text)"
                >
                  {{ text }}
                </view>
              </view>
        </view>
			
		<textarea 
          class="m-input" 
          v-model="replyText" 
          placeholder="Type your response here..."
          maxlength="200"
        ></textarea>
        <view class="m-actions">
          <button class="btn-cancel" @click="showModal = false">Cancel</button>
          <button class="btn-send" @click="sendReply" :loading="sending">Send</button>
        </view>
      </view>
    </view>
    
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PcNavbar from '@/components/PcNavbar/PcNavbar.vue';
import { getCloudObject } from '@/utils/cloud.js';

const feedbackCo = getCloudObject('feedback-co');
const list = ref([]);
const loading = ref(true);
const filter = ref(''); // '' | 0 | 2

// 弹窗状态
const showModal = ref(false);
const replyText = ref('');
const currentItem = ref(null);
const sending = ref(false);
// 定义常用话术 (快捷回复模板)
const replyTemplates = [
  "bug已经修复，您的反馈是我们前进的动力--欢迎━(*｀∀´*)ノ亻! 你能够有一个良好的体验！",
  "✅ Thank you for your feedback! We will look into it.",
  "🐛 We have confirmed this bug and will fix it in the next version.",
  "👌 Suggestion noted. Thanks for helping us improve!",
  "🤔 Could you please provide more details or screenshots?",
  "🎉 This issue has been resolved. Please update to the latest version."
];

// [新增] 应用模板函数
const applyTemplate = (text) => {
  // 交互优化：如果框里已经有字了，为了防止误触覆盖，可以加个简单判断
  // 这里为了效率，直接覆盖或者追加，这里采用“直接赋值”最快
  replyText.value = text;
};

// [核心] 获取数据并处理图片链接
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await feedbackCo.getAdminFeedbacks({ status: filter.value });
    
    if (res.errCode === 0) {
      const rawList = res.data;
      
      // --- 图片链接转换逻辑 Start ---
      
      // 1. 收集所有记录中的所有图片ID
      let allImageIds = [];
      rawList.forEach(item => {
        if (item.images && Array.isArray(item.images) && item.images.length > 0) {
          allImageIds = allImageIds.concat(item.images);
        }
      });

      // 2. 如果有图片，批量向云端换取 HTTP 链接
      if (allImageIds.length > 0) {
        // uniCloud 批量换取临时链接 (不需要每次渲染都请求，一次搞定)
        const tempFilesRes = await uniCloud.getTempFileURL({
          fileList: allImageIds
        });
        
        // 3. 建立映射表: CloudID -> HTTP URL
        const urlMap = {};
        tempFilesRes.fileList.forEach(f => {
          // 如果转换成功，用 tempFileURL，否则保留原值
          urlMap[f.fileID] = f.tempFileURL; 
        });
        
        // 4. 将 HTTP 链接回填到列表中
        rawList.forEach(item => {
          if (item.images && item.images.length > 0) {
            item.images = item.images.map(id => urlMap[id] || id);
          }
        });
      }
      // --- 图片链接转换逻辑 End ---

      list.value = rawList;
    } else {
      uni.showToast({ title: res.errMsg, icon: 'none' });
    }
  } catch(e) {
     console.error('Fetch error:', e);
     uni.showToast({ title: 'Fetch failed', icon: 'none' });
  } finally {
    loading.value = false;
  }
};

// [新增] 预览图片
const previewImage = (urls, current) => {
  uni.previewImage({
    urls: urls,
    current: current
  });
};

const switchFilter = (val) => {
  filter.value = val;
  fetchData();
};

const openReply = (item) => {
  currentItem.value = item;
  replyText.value = '';
  showModal.value = true;
};

const sendReply = async () => {
  if (!replyText.value.trim()) return;
  sending.value = true;
  
  try {
    const res = await feedbackCo.replyFeedback({
      id: currentItem.value._id,
      replyContent: replyText.value
    });
    
    if (res.errCode === 0) {
      uni.showToast({ title: 'Sent!', icon: 'success' });
      showModal.value = false;
      fetchData(); // 刷新列表
    }
  } finally {
    sending.value = false;
  }
};

const formatDate = (ts) => new Date(ts).toLocaleString();

onMounted(() => {
  fetchData();
  // console.log(list)
});
</script>

<style lang="scss" scoped>
page { background-color: #F8FAFC; }
.content { padding-top: 40px; min-height: 80vh; }

.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
  .title { font-size: 28px; font-weight: 800; color: #0F172A; }
}

.filter-tabs {
  display: flex; background: #E2E8F0; padding: 4px; border-radius: 8px;
  .tab {
    padding: 6px 16px; font-size: 13px; color: #64748B; cursor: pointer; border-radius: 6px; font-weight: 600;
    &.active { background: #fff; color: #0F172A; shadow: 0 2px 4px rgba(0,0,0,0.05); }
  }
}

.ticket-card {
  background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 16px;
  
  .t-header {
    display: flex; justify-content: space-between; margin-bottom: 12px;
    .u-name { font-weight: 700; color: #0F172A; font-size: 15px; }
    .u-contact { color: #64748B; font-size: 13px; margin-left: 8px; }
    .tag-type { background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-right: 8px; }
    .time { color: #94A3B8; font-size: 12px; }
  }
  
  .t-content { font-size: 15px; color: #334155; line-height: 1.6; display: block; margin-bottom: 16px; }
  
  .t-footer {
    display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #F8FAFC; padding-top: 12px;
    .status-indicator { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #64748B; }
    .dot { width: 8px; height: 8px; border-radius: 50%; &.green{background:#10B981} &.orange{background:#F59E0B} }
  }
}

.btn-reply {
  font-size: 13px; background: #0F172A; color: #fff; padding: 6px 16px; border-radius: 6px; cursor: pointer;
}

.reply-preview { font-size: 13px; color: #64748B; background: #F8FAFC; padding: 8px; border-radius: 6px; width: 100%; }
.r-label { font-weight: 700; color: #0F172A; }

/* 弹窗 */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100;
  display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);
}
.modal-box {
  background: #fff; width: 500px; padding: 30px; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.2);
  .m-title { font-size: 20px; font-weight: 700; margin-bottom: 20px; display: block; }
  /* [新增] 快捷回复样式 */
    .quick-tags {
      margin-bottom: 16px;
      .q-label { font-size: 12px; font-weight: 700; color: #64748B; margin-bottom: 8px; text-transform: uppercase; }
      
      .tag-list {
        display: flex; flex-wrap: wrap; gap: 8px;
        
        .tag-item {
          font-size: 12px; color: #475569;
          background: #F1F5F9; border: 1px solid #E2E8F0;
          padding: 6px 12px; border-radius: 100px;
          cursor: pointer; transition: all 0.2s;
          max-width: 100%;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; /* 防止太长 */
          
          &:hover {
            background: #E2E8F0; color: #0F172A; border-color: #CBD5E1;
          }
          &:active {
            transform: scale(0.96); background: #CBD5E1;
          }
        }
      }
    }
  
    /* 输入框稍微调高一点，适应更多内容 */
    .m-input { 
      width: 100%; height: 120px; 
      background: #F8FAFC; border: 1px solid #E2E8F0; 
      border-radius: 8px; padding: 12px; 
      font-size: 14px; box-sizing: border-box; 
      color: #334155;
      margin-bottom: 20px;
      
      &:focus { outline: none; border-color: #0F172A; background: #fff; }
    }
  
    .m-actions { display: flex; justify-content: flex-end; gap: 12px; }
  
  .m-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 20px; }
  button { font-size: 14px; padding: 8px 20px; border-radius: 8px; cursor: pointer; }
  .btn-cancel { background: #fff; border: 1px solid #E2E8F0; color: #475569; }
  .btn-send { background: #0F172A; color: #fff; border: none; }
}
/* 移动端适配：如果是手机看后台，标签可以改为横向滚动 */
@media (max-width: 600px) {
  .modal-box { width: 90%; padding: 20px; }
  .tag-list {
    flex-wrap: nowrap !important;
    overflow-x: auto;
    padding-bottom: 5px; /* 留出滚动条空间 */
    
    .tag-item { flex-shrink: 0; }
  }
}
.loading { text-align: center; padding: 40px; color: #94A3B8; }
.empty { text-align: center; padding: 60px; color: #94A3B8; }
</style>
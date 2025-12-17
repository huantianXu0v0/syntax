<template>
  <view class="ai-widget-container">
    
    <!-- 1. 聊天窗口 (当 isOpen 为 true 时显示) -->
    <!-- 使用 transition 实现简单的淡入淡出动画 -->
    <view class="chat-window" :class="{ 'window-open': isOpen }">
      
      <!-- 顶部标题栏 -->
      <view class="chat-header">
        <text class="title">🤖 智能助手-Ayu</text>
        <view class="close-btn" @click="toggleChat">×</view>
      </view>

      <!-- 消息内容区 (可滚动) -->
      <scroll-view 
        class="chat-body" 
        scroll-y="true" 
        :scroll-top="scrollTop"
        scroll-with-animation="true"
      >
        <view class="msg-list">
          <view 
            v-for="(item, index) in chatList" 
            :key="index" 
            class="msg-item"
            :class="item.role === 'user' ? 'msg-right' : 'msg-left'"
          >
            <!-- 头像 -->
            <view class="avatar">
              {{ item.role === 'user' ? '👤' : '🤖' }}
            </view>
            <!-- 气泡 -->
            <view class="bubble">
              <text>{{ item.content }}</text>
            </view>
          </view>
          
          <!-- 加载中提示 -->
         <view v-if="loading" class="msg-item msg-left">
            <view class="avatar">🤖</view>
            <view class="bubble loading-bubble">
              <text>正在思考...</text>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- 底部输入区 -->
      <view class="chat-footer">
        <input 
          class="input-box" 
          v-model="inputText" 
          placeholder="请输入问题..." 
          confirm-type="send"
          @confirm="sendMessage" 
        />
        <button 
          class="send-btn" 
          :disabled="loading || !inputText" 
          @click="sendMessage"
        >发送</button>
      </view>
    </view>

    <!-- 2. 悬浮按钮 (始终显示) -->
    <view class="float-btn" @click="toggleChat" :class="{ 'btn-active': isOpen }">
      <!-- 这里可以用 image 标签换成你的机器人图片 -->
      <text class="icon">🤖</text> 
    </view>

  </view>
</template>

<script>
export default {
  data() {
    return {
      isOpen: false,      // 控制窗口开关
      inputText: '',      // 输入框内容
      loading: false,     // 是否正在请求接口
      scrollTop: 0,       // 滚动条位置
      chatList: [         // 初始欢迎语
        { role: 'bot', content: '你好！我是你的AI助手，有什么可以帮你的吗？' }
      ]
    }
  },
  methods: {
    // 切换聊天框显示/隐藏
    toggleChat() {
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.scrollToBottom();
      }
    },

    // 滚动到底部
    scrollToBottom() {
      setTimeout(() => {
        // 设置一个足够大的值，确保滚到底部
        this.scrollTop = 99999; 
      }, 100);
    },

    // 发送消息逻辑
    async sendMessage() {
      if (!this.inputText.trim() || this.loading) return;

      const msg = this.inputText;
      
      // 1. UI更新：显示用户消息
      this.chatList.push({ role: 'user', content: msg });
      this.inputText = '';
      this.loading = true;
      this.scrollToBottom();

      try {
        // 2. 调用云对象 (请确保你已经上传了之前写的 chat-bot 云对象)
        const chatBot = uniCloud.importObject('chatBot-co');
        const res = await chatBot.ask(msg);

        // 3. UI更新：显示机器人回复
        if (res.errCode === 0) {
          this.chatList.push({ role: 'bot', content: res.reply });
        } else {
          this.chatList.push({ role: 'bot', content: `出错啦: ${res.errMsg}` });
        }
      } catch (e) {
        this.chatList.push({ role: 'bot', content: '网络开小差了，请稍后再试。' });
      } finally {
        this.loading = false;
        this.scrollToBottom();
      }
    }
  }
}
</script>

<style scoped>
/* ================= 悬浮按钮样式 ================= */
.float-btn {
  position: fixed;
  left: 20px;   /* 左下角定位 */
  bottom: 30px; /* 距离底部距离 */
  width: 50px;
  height: 50px;
  background-color: #007AFF; /* 按钮颜色 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0, 122, 255, 0.3);
  z-index: 999;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.float-btn:active {
  transform: scale(0.9);
}

/* 按钮打开时的状态（可选效果） */
.btn-active {
  transform: rotate(360deg); 
}

.icon {
  font-size: 24px;
  color: white;
}

/* ================= 聊天窗口样式 ================= */
.chat-window {
  position: fixed;
  left: 20px;         /* 对齐按钮左侧 */
  bottom: 90px;       /* 在按钮上方显示 */
  width: 300px;       /* 窗口宽度 */
  height: 400px;      /* 窗口高度 */
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 998;
  overflow: hidden;
  
  /* 动画初始状态：隐藏 + 缩小 + 移位 */
  transform: scale(0.8) translateY(20px);
  opacity: 0;
  pointer-events: none; /* 隐藏时不可点击 */
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* 窗口打开时的状态 */
.window-open {
  transform: scale(1) translateY(0);
  opacity: 1;
  pointer-events: auto;
}

/* 1. 头部 */
.chat-header {
  height: 45px;
  background-color: #f8f8f8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  border-bottom: 1px solid #eee;
}
.chat-header .title {
  font-size: 14px;
  font-weight: bold;
  color: #333;
}
.chat-header .close-btn {
  font-size: 20px;
  color: #999;
  padding: 5px;
  cursor: pointer;
}

/* 2. 内容区 */
.chat-body {
  flex: 1;
  background-color: #f5f5f5;
  padding: 10px;
  box-sizing: border-box;
  /* 确保 scroll-view 有高度 */
  height: 0; 
}

.msg-list {
  display: flex;
  flex-direction: column;
  padding-bottom: 10px;
}

.msg-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.msg-left { flex-direction: row; }
.msg-right { flex-direction: row-reverse; }

.avatar {
  width: 32px;
  height: 32px;
  background: #fff;
  border-radius: 50%;
  text-align: center;
  line-height: 32px;
  font-size: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin: 0 8px;
}

.bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
  word-break: break-all;
}

.msg-left .bubble {
  background-color: #fff;
  color: #333;
  border-top-left-radius: 2px;
}

.msg-right .bubble {
  background-color: #007AFF;
  color: #fff;
  border-top-right-radius: 2px;
}

.loading-bubble {
  color: #999 !important;
  font-style: italic;
  font-size: 12px;
}

/* 3. 底部 */
.chat-footer {
  height: 50px;
  background-color: #fff;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  padding: 0 10px;
}

.input-box {
  flex: 1;
  background: #f0f0f0;
  height: 32px;
  border-radius: 16px;
  padding: 0 12px;
  font-size: 14px;
}

.send-btn {
  margin-left: 10px;
  height: 32px;
  line-height: 32px;
  font-size: 13px;
  background-color: #007AFF;
  color: white;
  border-radius: 16px;
  padding: 0 15px;
}
.send-btn[disabled] {
  background-color: #ccc;
  color: #fff;
}
</style>
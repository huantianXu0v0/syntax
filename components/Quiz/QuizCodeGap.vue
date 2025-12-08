<template>
  <view class="ide-window">
    <!-- IDE 头部 -->
    <view class="ide-header">
      <view class="dots">
        <view class="dot red"></view><view class="dot yellow"></view><view class="dot green"></view>
      </view>
      <text class="filename">Main.{{ lang }}</text>
    </view>

    <!-- 代码区域 -->
    <view class="ide-body">
      <view class="code-line" v-for="(segment, index) in segments" :key="index">
        
        <!-- 普通文本 -->
        <text class="code-text" v-if="!segment.isGap">{{ segment.text }}</text>
        
        <!-- 填空坑位 -->
        <view v-else class="gap-slot" :class="getGapClass(segment.gapIndex)">
          
          <!-- 模式A: 选词 (Picker) -->
          <picker 
            v-if="gapMode === 'select' && !showResult" 
            :range="gapOptions" 
            @change="(e) => handlePickerChange(e, segment.gapIndex)"
          >
            <view class="gap-value select-mode">
              {{ modelValue[segment.gapIndex] || '???' }}
            </view>
          </picker>

          <!-- 模式B: 手写 (Input) -->
          <input 
            v-else-if="gapMode === 'input' && !showResult"
            class="gap-input"
            type="text"
            :value="modelValue[segment.gapIndex]"
            @input="(e) => handleInput(e, segment.gapIndex)"
            placeholder="..." 
            :maxlength="20"
          />

          <!-- 结果展示模式 (不可编辑) -->
          <view v-else class="gap-value result-mode">
            {{ modelValue[segment.gapIndex] || '___' }}
          </view>

        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  code: { type: String, default: '' }, // 原始代码字符串
  lang: { type: String, default: 'java' },
  gapMode: { type: String, default: 'input' }, // input | select
  gapOptions: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }, // 用户填写的答案数组
  showResult: { type: Boolean, default: false },
  correctAnswer: { type: Array, default: () => [] }
});

const emit = defineEmits(['update:modelValue']);

// 解析代码片段，生成渲染数组
const segments = computed(() => {
  if (!props.code) return [];
  // 使用正则根据 {{gap}} 切割，保留分隔符
  const parts = props.code.split(/({{gap}})/g);
  let gapCounter = 0;
  
  return parts.map(part => {
    if (part === '{{gap}}') {
      return { isGap: true, gapIndex: gapCounter++ };
    }
    // 处理换行符，确保样式显示换行
    return { isGap: false, text: part };
  });
});

const handleInput = (e, index) => {
  const newVal = [...props.modelValue];
  newVal[index] = e.detail.value.trim();
  emit('update:modelValue', newVal);
};

const handlePickerChange = (e, index) => {
  const newVal = [...props.modelValue];
  newVal[index] = props.gapOptions[e.detail.value];
  emit('update:modelValue', newVal);
};

const getGapClass = (index) => {
  if (!props.showResult) {
    return props.modelValue[index] ? 'filled' : 'empty';
  }
  // 简单比对逻辑 (实际可能需要忽略大小写等)
  const isCorrect = props.modelValue[index] === props.correctAnswer[index];
  return isCorrect ? 'correct' : 'wrong';
};
</script>

<style lang="scss" scoped>
.ide-window {
  background: #1E1E1E; border-radius: 12px; overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
  width: 100%; max-width: 800px; margin: 0 auto;
  font-family: 'Fira Code', 'Consolas', monospace;
}

.ide-header {
  background: #252526; padding: 10px 16px; display: flex; align-items: center;
  .dots { display: flex; gap: 6px; margin-right: 16px; .dot { width: 10px; height: 10px; border-radius: 50%; } .red{background:#FF5F56} .yellow{background:#FFBD2E} .green{background:#27C93F} }
  .filename { color: #9CA3AF; font-size: 12px; opacity: 0.8; }
}

.ide-body {
  padding: 24px; color: #D4D4D4; font-size: 15px; line-height: 2.2;
  white-space: pre-wrap; /* 保留换行和空格 */
  word-break: break-all;
}

.code-line { display: inline; /* 让文本和输入框混排 */ }

.gap-slot {
  display: inline-block; margin: 0 4px; vertical-align: middle;
  border-bottom: 2px solid #4F46E5; transition: all 0.3s;
  
  &.empty { border-color: #64748B; }
  &.filled { border-color: #4F46E5; }
  &.correct { border-color: #10B981; color: #10B981; }
  &.wrong { border-color: #EF4444; color: #EF4444; text-decoration: line-through; }
  
  .gap-input {
    background: rgba(255,255,255,0.1); border: none; border-radius: 4px;
    color: #fff; height: 28px; min-width: 60px; padding: 0 8px; text-align: center;
    font-family: inherit; font-size: inherit;
    &:focus { background: rgba(255,255,255,0.15); outline: none; }
  }
  
  .gap-value {
    padding: 2px 10px; background: rgba(255,255,255,0.1); border-radius: 4px; min-width: 40px; text-align: center; cursor: pointer;
    &.select-mode { color: #60A5FA; font-weight: bold; }
  }
}
</style>
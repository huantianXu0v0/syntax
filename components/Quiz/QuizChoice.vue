<template>
  <view class="choice-group">
    <view 
      class="option-card" 
      v-for="(opt, index) in options" 
      :key="opt.id"
      :class="getOptionClass(opt.id)"
      @click="handleSelect(opt.id)"
    >
      <!-- 序号/图标 -->
      <view class="opt-prefix">
        <text v-if="!showResult">{{ String.fromCharCode(65 + index) }}</text>
        <text v-else-if="isCorrect(opt.id)" class="icon-yes">✓</text>
        <text v-else-if="isWrong(opt.id)" class="icon-no">✕</text>
        <text v-else>{{ String.fromCharCode(65 + index) }}</text>
      </view>

      <!-- 内容 -->
      <view class="opt-content">
        <text class="opt-text">{{ opt.text }}</text>
      </view>

      <!-- 选中标记 (仅答题时显示) -->
      <view class="check-circle" v-if="isSelected(opt.id) && !showResult"></view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  options: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }, // 用户选中的 ID 数组
  showResult: { type: Boolean, default: false }, // 是否展示结果
  correctAnswer: { type: Array, default: () => [] } // 正确答案 ID 数组
});

const emit = defineEmits(['update:modelValue']);

const isSelected = (id) => props.modelValue.includes(id);
const isCorrect = (id) => props.correctAnswer.includes(id);
const isWrong = (id) => isSelected(id) && !isCorrect(id);

const handleSelect = (id) => {
  if (props.showResult) return; // 提交后不可修改
  // 单选逻辑 (如果要支持多选，这里改成 push/filter)
  emit('update:modelValue', [id]);
};

// 计算样式类名
const getOptionClass = (id) => {
  if (!props.showResult) {
    return isSelected(id) ? 'active' : '';
  }
  // 结果展示模式
  if (isCorrect(id)) return 'result-correct'; // 正确答案(绿色)
  if (isWrong(id)) return 'result-wrong';     // 用户选错的(红色)
  return 'result-dim'; // 其他未选选项(淡化)
};
</script>

<style lang="scss" scoped>
.choice-group { display: flex; flex-direction: column; gap: 16px; width: 100%; max-width: 680px; margin: 0 auto; }

.option-card {
  display: flex; align-items: center; padding: 20px 24px;
  background: #fff; border: 2px solid transparent; border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
  cursor: pointer; transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  
  &:hover:not(.result-correct):not(.result-wrong) {
    transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); border-color: #E2E8F0;
  }

  /* 选中状态 */
  &.active { border-color: #0F172A; background: #F8FAFC; }
  
  /* 结果状态 */
  &.result-correct { border-color: #10B981; background: #ECFDF5; color: #065F46; }
  &.result-wrong { border-color: #EF4444; background: #FEF2F2; opacity: 1; }
  &.result-dim { opacity: 0.5; }

  .opt-prefix {
    width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
    background: #F1F5F9; border-radius: 8px; margin-right: 16px; font-weight: 700; color: #64748B; font-size: 14px;
    .icon-yes { color: #10B981; font-size: 18px; }
    .icon-no { color: #EF4444; font-size: 16px; }
  }
  
  /* 适配状态下的前缀背景 */
  &.active .opt-prefix { background: #0F172A; color: #fff; }
  &.result-correct .opt-prefix { background: #fff; }
  &.result-wrong .opt-prefix { background: #fff; }

  .opt-content { flex: 1; font-size: 16px; font-weight: 500; line-height: 1.5; }

  .check-circle {
    width: 10px; height: 10px; border-radius: 50%; background: #0F172A; margin-left: 12px;
  }
}
</style>
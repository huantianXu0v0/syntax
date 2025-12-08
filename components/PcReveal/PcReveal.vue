<!-- 滚动动画核心组件 -->
<template>
  <view 
    class="pc-reveal" 
    :class="{ 'is-active': isActive }"
    :style="{ transitionDelay: delay + 'ms' }"
  >
    <slot></slot>
  </view>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue';

const props = defineProps({
  delay: { type: Number, default: 0 }
});

const isActive = ref(false);
const instance = getCurrentInstance();

onMounted(() => {
  const observer = uni.createIntersectionObserver(instance);
  observer.relativeToViewport({ bottom: -50 }).observe('.pc-reveal', (res) => {
    if (res.intersectionRatio > 0) {
      isActive.value = true;
      observer.disconnect();
    }
  });
});
</script>

<style scoped>
.pc-reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.8s ease, transform 1s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform, opacity;
}
.pc-reveal.is-active {
  opacity: 1;
  transform: translateY(0);
}
</style>
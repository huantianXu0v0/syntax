<!-- 底部页脚 -->
<template>
  <view class="footer-wrapper">
    <view class="container-xl footer-content">
      <view class="footer-col">
        <text class="f-title">Product</text>
        <text class="f-link">Features</text>
        <text class="f-link">Security</text>
        <text class="f-link">Enterprise</text>
      </view>
      <view class="footer-col">
        <text class="f-title">Company</text>
        <text class="f-link">About</text>
        <text class="f-link">Blog</text>
        <text class="f-link">Careers</text>
      </view>
      <view class="footer-col">
        <text class="f-title">Legal</text>
        <text class="f-link">Privacy</text>
        <text class="f-link">Terms</text>
      </view>
      <view class="footer-col brand-col">
        <text class="logo">UNI-CLOUD</text>
        <text class="copyright">© 2026  Huantian Xu reserves all rights.</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.footer-wrapper {
  background: #F9FAFB;
  border-top: 1px solid #eee;
  padding: 80px 0 40px;
  margin-top: 120px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 150px;
  
  .f-title { font-size: 14px; font-weight: 700; color: #111; margin-bottom: 8px; }
  .f-link { font-size: 14px; color: #666; cursor: pointer; &:hover { color: #111; } }
}

.brand-col {
  text-align: right;
  .logo { font-size: 18px; font-weight: 800; display: block; margin-bottom: 10px; }
  .copyright { font-size: 12px; color: #999; }
}

@media screen and (max-width: 768px) {
  .footer-content { gap: 40px; }
  .brand-col { text-align: left; width: 100%; margin-top: 20px; }
}
</style>
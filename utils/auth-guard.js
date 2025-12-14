// utils/auth-guard.js

// 防抖锁：防止并发请求导致多次弹出提示或多次跳转
let isRedirecting = false;

export function handleLoginExpired() {
  if (isRedirecting) return;
  isRedirecting = true;

  // console.log('[AuthGuard] 监测到登录失效，开始处理...');

  // 1. 清理本地脏数据 (Token, UserInfo)
  uni.removeStorageSync('uni_id_token');
  uni.removeStorageSync('uni_id_token_expired');
  uni.removeStorageSync('uni_id_userInfo');
  uni.removeStorageSync('uni_id_uid');
  
  // 通知 UI 更新（如 Navbar 变为未登录态）
  uni.$emit('login-success', null); 

  // 2. 获取当前页面栈，为了拿到“案发现场”
  const pages = getCurrentPages();
  const currentPage = pages[pages.length - 1];
  
  // 3. 构造完整的回跳地址
  // 注意：如果是 TabBar 页面，route 前面不加 /，普通页面通常也不加，uni-app 会自动处理
  // 但为了保险，我们构建一个标准路径
  let fullPath = '/' + (currentPage ? currentPage.route : 'pages/index/index');
  
  // 拼接参数 (例如: ?id=123&type=code)
  if (currentPage && currentPage.options && Object.keys(currentPage.options).length > 0) {
    const query = Object.keys(currentPage.options)
      .map(key => `${key}=${currentPage.options[key]}`)
      .join('&');
    fullPath += `?${query}`;
  }

  // 4. 提示用户
  uni.showToast({ title: '登录已过期，请重新登录', icon: 'none', duration: 2000 });

  // 5. 延迟跳转 (编码 URL 防止参数丢失)
  setTimeout(() => {
    const redirectUrl = encodeURIComponent(fullPath);
    
    uni.redirectTo({
      url: `/pages/login/login?uniIdRedirectUrl=${redirectUrl}`,
      complete: () => {
        // 跳转完成后解锁，允许下一次拦截
        isRedirecting = false;
      },
      fail: () => {
        // 如果 redirectTo 失败（比如当前就在登录页），也要解锁
        isRedirecting = false;
      }
    });
  }, 1500);
}
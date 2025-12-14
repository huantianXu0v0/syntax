// interceptor.js

export function initInterceptor() {
  // 需要拦截的路由API列表
  const routeApis = ['navigateTo', 'redirectTo', 'reLaunch', 'switchTab'];

  routeApis.forEach((api) => {
    uni.addInterceptor(api, {
      fail: (err) => {
        console.log(`[拦截器] ${api} 失败:`, err);
        
        // 核心逻辑：判断错误信息中是否包含页面未找到的提示
        // 不同平台报错信息可能略有不同，但通常都包含 'not found'
        if (err.errMsg && err.errMsg.indexOf('not found') !== -1) {
          // 防止无限循环：如果跳转 404 页面本身失败，就不要再跳了
          if (err.errMsg.indexOf('pages/404/404') !== -1) {
             console.error('404页面不存在，请在pages.json中配置');
             return;
          }

          // 跳转到自定义的 404 页面
          // 使用 reLaunch 比较保险，可以清除路由栈，防止用户点返回又回到错误页
          uni.reLaunch({
            url: '/pages/404/404'
          });
        }
      }
    });
  });
}
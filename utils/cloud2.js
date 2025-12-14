// utils/cloud.js - 封装的云对象调用工具
class CloudObjectManager {
  constructor() {
    this.needLoginMethods = {}; // 需要登录的方法名
  }
  
  // 创建云对象代理
  createProxy(cloudObjectName, options = {}) {
    const cloudObj = uniCloud.importObject(cloudObjectName, options);
    
    return new Proxy(cloudObj, {
      get: (target, method) => {
        // 如果是云对象方法
        if (typeof target[method] === 'function') {
          return async (...args) => {
            try {
              const res = await target[method](...args);
              
              // 检查是否返回401错误
              if (res && res.errCode === 401) {
                this.handleTokenExpired();
                // 返回一个特殊标记，表示已跳转登录
                return Promise.reject({
                  errCode: 401,
                  errMsg: '登录已过期，请重新登录',
                  redirected: true
                });
              }
              
              return res;
            } catch (error) {
              // 如果云对象抛出了401错误（通过throw方式）
              if (error.errCode === 401) {
                this.handleTokenExpired();
                return Promise.reject({
                  ...error,
                  redirected: true
                });
              }
              throw error;
            }
          };
        }
        return target[method];
      }
    });
  }
  
  // 处理token过期
  handleTokenExpired() {
    // 清除本地存储的token
	uni.removeStorageSync('uni_id_token');
	uni.removeStorageSync('uni_id_token_expired');
	uni.removeStorageSync('uni_id_userInfo');
	uni.removeStorageSync('uni_id_uid');
    
    // 跳转到登录页面
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];
    const currentRoute = currentPage.route || currentPage.__route__;
    
    // 排除登录页面本身
    if (currentRoute && !currentRoute.includes('login')) {
      // 可以存储当前页面路径，登录后返回
      uni.setStorageSync('login_redirect_url', currentPage.$page.fullPath);
      
      uni.showModal({
        title: '提示',
        content: '登录已过期，请重新登录',
        showCancel: false,
        success: () => {
          uni.reLaunch({
            url: '/pages/login/login' // 你的登录页面路径
          });
        }
      });
    }
  }
}

// 全局实例
export const cloudManager = new CloudObjectManager();

// 使用示例
export const quizCo = cloudManager.createProxy('quiz-co');
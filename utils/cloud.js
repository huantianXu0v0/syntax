// utils/cloud.js
import { handleLoginExpired } from '@/utils/auth-guard.js'; // 复用之前的卫士

/**
 * 获取增强版云对象 (支持自动拦截 401)
 * @param {String} name 云对象名称
 * @param {Object} options 配置项
 */
export function getCloudObject(name, options = {}) {
  // 1. 获取原始云对象
  // 强制开启 customUI，防止官方自动弹窗干扰我们的逻辑
  const cloudObj = uniCloud.importObject(name, { 
    ...options, 
    customUI: true 
  });

  // 2. 创建代理
  return new Proxy(cloudObj, {
    get(target, propKey) {
      const originalMethod = target[propKey];

      // 如果调用的是函数，则进行劫持
      if (typeof originalMethod === 'function') {
        return async (...args) => {
          try {
            // A. 执行原始请求
            const res = await originalMethod(...args);

            // B. 检查业务层面的 401 (return { errCode: 401 })
            if (res && typeof res === 'object') {
              if (
                res.errCode === 401 || 
                res.errCode === 'uni-id-token-expired' ||
                res.errCode === 'uni-id-check-token-failed'
              ) {
                // console.log(`[CloudProxy] 捕获到业务层 401 (${name}.${String(propKey)})`);
                handleLoginExpired(); // 调用统一的跳转逻辑
                return Promise.reject('LOGIN_EXPIRED'); // 中断业务流
              }
            }
            return res;

          } catch (err) {
            // C. 检查网络/系统层面的 401 (throw { errCode: 401 })
            const code = err.errCode || err.code;
            const msg = err.message || err.errMsg || '';

            if (
              code === 401 || 
              code === 'uni-id-token-expired' || 
              msg.includes('Unauthorized')
            ) {
              // console.log(`[CloudProxy] 捕获到异常层 401 (${name}.${String(propKey)})`);
              handleLoginExpired();
              return Promise.reject('LOGIN_EXPIRED');
            }
            
            // 其他错误照常抛出
            throw err;
          }
        };
      }

      // 如果不是函数（属性），直接返回
      return originalMethod;
    }
  });
}
<script>
	// 1. 引入刚才写的卫士
	import { handleLoginExpired } from '/utils/auth-guard.js';	
	export default {
		onLaunch: function() {
		    console.log('App Launch');
		    
		    // 初始化拦截器
		    uniCloud.addInterceptor('importObject', {
		      
		      // 1. 【核心】拦截业务逻辑返回 (处理 return { errCode: 401 })
		      returnValue(result) {
				  console.log('我正在拦截所有请求',result)
		        // 检查 result 是否存在且包含 errCode
		        if (result && typeof result === 'object') {
		          // 判断 Token 过期或无效
		          if (
		            result.errCode === 401 || 
		            result.errCode === 'uni-id-token-expired' || 
		            result.errCode === 'uni-id-check-token-failed'
		          ) {
		            console.log('拦截器捕获到业务层 401，跳转登录...');
		            handleLoginExpired();
		            
		            // 返回一个拒绝的 Promise，中断页面原本的 .then() 逻辑
		            // 这样页面的 try...catch 就会捕获到 error，停止执行后续代码
		            return Promise.reject('LOGIN_EXPIRED'); 
		          }
		        }
		        // 如果没问题，原样返回结果
		        return result;
		      },
		
		      // 2. 拦截系统级/网络级错误 (处理 throw 出来的错误)
		      fail(err) {
		        console.error('[Global Interceptor] Network/System Error:', err);
		        
		        // 提取错误信息
		        const errMsg = err.message || err.errMsg || '';
		        const errCode = err.errCode || err.code;
		
		        // 判断是否包含鉴权相关关键词
		        if (
		          errMsg.includes('Unauthorized') || 
		          errMsg.includes('Token expired') ||
		          errCode === 401 ||
		          errCode === 'uni-id-token-expired'
		        ) {
		          console.log('拦截器捕获到网络层 401，跳转登录...');
		          handleLoginExpired();
		        }
		      }
		    });
		  
			
		  
		  },
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style lang="scss">
	/*每个页面公共css */
	/* 全局样式 Reset */
	body {
	  margin: 0;
	  padding: 0;
	  background-color: #ffffff;
	  /* 大厂标准字体栈 */
	  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
	  -webkit-font-smoothing: antialiased;
	  color: #111;
	}
	
	/* 隐藏 H5 默认的滚动条但保留功能 (可选) */
	::-webkit-scrollbar {
	  width: 8px;
	  height: 8px;
	}
	::-webkit-scrollbar-track {
	  background: #fff;
	}
	::-webkit-scrollbar-thumb {
	  background: #ccc;
	  border-radius: 4px;
	}
	::-webkit-scrollbar-thumb:hover {
	  background: #999;
	}
	
	/* 核心版心容器类 - 供所有页面公用 */
	.container-xl {
	  max-width: 1200px;
	  margin: 0 auto;
	  padding: 0 24px;
	}
</style>

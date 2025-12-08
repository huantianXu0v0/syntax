<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
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

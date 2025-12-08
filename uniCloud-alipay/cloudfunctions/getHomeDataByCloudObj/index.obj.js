const db = uniCloud.database();

module.exports = {
	_before: function(){
		//可以增加权限校验，比如后台管理员方法只允许管理员调用
	},
	
	/**
	 * 获取首页数据
	 */
	async getHomedata(){
		try{
			const res = await db.collection('homeData')
			.where({
				status: 1
			})
			.field({
				'_id':1,
				'title':1,
				'desc':1,
				'icon':1,
				'sort':1
			})
			.orderBy('sort','asc')
			.limit(10)
			.get()
			
			return {
				code : 0,
				data : res.data,
				msg : 'success'
			}
			
		}
		catch(e){
			//前端会在catch中捕获
			throw new Error(e.message)
		}
	}
}


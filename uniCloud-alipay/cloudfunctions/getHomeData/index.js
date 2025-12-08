'use strict';

const db = uniCloud.database();

exports.main = async (event, context) => {
   //定义集合引用
   const collection = db.collection('homeData');
   try{
	   //查询数据库
	   const res = await collection
	   .where({
		   status: 1 //只查询status为1（上线）的数据
		   })
			.field({
				'_id':1,
				'title':1,
				'desc':1,
				'icon':1,
				'sort':1
			})
			.orderBy('sort','asc') //数字越小越在前面
			.limit(20)
			.get()
		
		//返回数据
		return {
			code : 0,
			msg : 'success',
			data : res.data
		}
   
   }
   catch(e){
	   console.warn(e);
	   return {
			code : 500,
			msg : 'Server error',
			error : e.message
	   }
   }
   
};
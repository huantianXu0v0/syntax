// 云对象教程: https://uniapp.dcloud.net.cn/uniCloud/cloud-obj
// jsdoc语法提示教程：https://ask.dcloud.net.cn/docs/#//ask.dcloud.net.cn/article/129
const db = uniCloud.database();
const cmd = db.command;
const uniIdCommon = require('uni-id-common');

// async function verifyLogin(ctx) {
// 	// 通过传入的 ctx 获取客户端信息
// 	const clientInfo = ctx.getClientInfo();
// 	const token = clientInfo.uniIdToken;

// 	if (!token) {
// 		throw { errCode: 401, errMsg: 'Unauthorized: No token provided' };
// 	}

// 	// 使用 ctx 上的 uniIdCommon 实例校验
// 	const payload = await ctx.uniIdCommon.checkToken(token);
// 	if (payload.errCode) {
// 		throw { errCode: 401, errMsg: 'Unauthorized: Token expired or invalid' };
// 	}
// 	// console.log(payload.uid)
// 	return payload.uid;
// }

/**
 * 🔒 独立鉴权函数 (返回完整的 payload)
 * @returns {Promise<{uid: string, role: string[], permission: string[]}>}
 */
async function verifyLogin(ctx) {
	const clientInfo = ctx.getClientInfo();
	const token = clientInfo.uniIdToken;

	if (!token) {
		throw { errCode: 401, errMsg: 'Unauthorized: No token provided' };
	}

	// 校验 Token
	const payload = await ctx.uniIdCommon.checkToken(token);
	if (payload.errCode) {
		throw { errCode: 401, errMsg: 'Unauthorized: Token expired or invalid' };
	}

	// 返回完整的 payload，而不仅仅是 uid
	// payload 结构通常为: { uid: '...', role: ['admin'], permission: [], exp: ... }
	return payload;
}

module.exports = {
	_before: function () {
		this.startTime = Date.now();
		this.uniIdCommon = uniIdCommon.createInstance({
			clientInfo: this.getClientInfo()
		});
	},
	
	_after: function(error, result) {
		if (error) {
			throw error;
		}
		// 避免 result 为空时报错
		if(result) {
			result.costMs = Date.now() - this.startTime;
		}
		return result;
	},
	
	
	/**
		 * 提交反馈
		 */
	async submitFeedback(params) {
			try {
				const payload = await verifyLogin(this);
				const uid = payload.uid
				if (!params.content) return { errCode: 400, errMsg: 'Content is required' };
	
				const res = await db.collection('feedback-records').add({
					user_id: uid,
					type: params.type || 'other',
					content: params.content,
					contact: params.contact || '',
					images: params.images || [],
					status: 0, // 默认待处理
					create_date: Date.now()
				});
	
				return { errCode: 0, msg: 'Submitted successfully' };
			} catch (e) {
				if (e.errCode === 401) return e;
				return { errCode: 500, errMsg: e.message };
			}
	},
	
		/**
		 * 获取我的反馈列表
		 */
	async getMyFeedbacks() {
			try {
				const payload = await verifyLogin(this);
				const uid = payload.uid;
				const res = await db.collection('feedback-records')
					.where({ user_id: uid })
					.orderBy('create_date', 'desc')
					.limit(20) // 暂时只取最近20条
					.get();
	
				return { errCode: 0, data: res.data };
			} catch (e) {
				if (e.errCode === 401) return e;
				return { errCode: 500, errMsg: e.message };
			}
	},

	/**
	 * [管理员] 获取所有反馈列表 (分步查询版)
	 */
	async getAdminFeedbacks(params = {}) {
	    try {
	        const dbCmd = db.command; // 引入查询指令
	
	        // 1. 鉴权
	        const auth = await verifyLogin(this);
	        const roles = auth.role || [];
	        if (!roles.includes('admin')) {
	            return { errCode: 403, errMsg: 'Permission Denied' };
	        }
	
	        // 2. 构建反馈表查询条件
	        let where = {};
	        if (params.status !== undefined && params.status !== '') {
	            where.status = parseInt(params.status);
	        }
	
	        // 3. 第一步：查询反馈列表
	        const feedbackRes = await db.collection('feedback-records')
	            .where(where)
	            .orderBy('create_date', 'desc')
	            .limit(100)
	            .get();
	        
	        const list = feedbackRes.data;
	        if (list.length === 0) {
	            return { errCode: 0, data: [] };
	        }
	
	        // 4. 第二步：提取所有 user_id (去重)
	        // 过滤掉没有 user_id 的脏数据
	        const userIds = list
	            .map(item => item.user_id)
	            .filter(id => id && typeof id === 'string');
	            
	        // 使用 Set 去重
	        const uniqueUserIds = [...new Set(userIds)];
	
	        // 5. 第三步：批量查询用户表
	        let userMap = {};
	        if (uniqueUserIds.length > 0) {
	            const userRes = await db.collection('uni-id-users')
	                .where({
	                    _id: dbCmd.in(uniqueUserIds) // 查询 ID 在列表中的用户
	                })
	                .field({ 
	                    '_id': 1, 
	                    'nickname': 1, 
	                    'username': 1, 
	                    'mobile': 1, 
	                    'email': 1 
	                })
	                .get();
	
	            // 转化为 Map 结构方便查找: { 'user_id_A': { nickname: '...' }, ... }
	            userRes.data.forEach(u => {
	                userMap[u._id] = u;
	            });
	        }
	
	        // 6. 第四步：在内存中合并数据
	        const result = list.map(item => {
	            const user = userMap[item.user_id] || {}; // 找不到用户就给空对象
	            
	            return {
	                ...item, // 保留反馈原有的 content, images, status 等
	                nickname: user.nickname || '',
	                username: user.username || '',
	                mobile: user.mobile || '',
	                email: user.email || ''
	            };
	        });
	
	        return { errCode: 0, data: result };
	
	    } catch (e) {
	        console.error(e);
	        return { errCode: 500, errMsg: e.message };
	    }
	},
	
		/**
		 * [管理员] 回复反馈
		 */
	async replyFeedback(params) {
			const { id, replyContent } = params;
			if (!id || !replyContent) return { errCode: 400, errMsg: 'Missing replyContent!!!---不能无回复，请宠爱你的用户哦~' };
	
			try {
				// 1. 获取鉴权信息
				const auth = await verifyLogin(this);
				const uid = auth.uid;
				const roles = auth.role || []; // 从 Token 中直接获取角色
					
				// 2. 鉴权：检查是否有 admin 角色
				if (!roles.includes('admin')) {
					return { errCode: 403, errMsg: 'Permission Denied: Admins only' };
				}
	
				await db.collection('feedback-records').doc(id).update({
					reply_content: replyContent,
					status: 2, // 标记为已回复
					reply_date: Date.now(),
					admin_id: uid // 记录是谁回复的
				});
	
				return { errCode: 0, msg: 'Replied' };
			} catch (e) {
				return { errCode: 500, errMsg: e.message };
			}
	},
}

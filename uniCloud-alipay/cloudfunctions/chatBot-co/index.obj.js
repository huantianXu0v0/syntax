// cloudfunctions/chat-bot/index.obj.js
const db = uniCloud.database();
const cmd = db.command;
const uniIdCommon = require('uni-id-common');

async function verifyLogin(ctx) {
	// 通过传入的 ctx 获取客户端信息
	const clientInfo = ctx.getClientInfo();
	const token = clientInfo.uniIdToken;

	if (!token) {
		throw { errCode: 401, errMsg: 'Unauthorized: No token provided' };
	}

	// 使用 ctx 上的 uniIdCommon 实例校验
	const payload = await ctx.uniIdCommon.checkToken(token);
	if (payload.errCode) {
		throw { errCode: 401, errMsg: 'Unauthorized: Token expired or invalid' };
	}
	// console.log(payload.uid)
	return payload.uid;
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
	 * 向青云客发送消息并获取回复
	 * {String} msg 用户发送的消息内容
	 */
	async ask(msg) {
		if (!msg) {
			return {
				errCode: 400,
				errMsg: '消息内容不能为空'
			}
		}

		// 1. 准备 API 地址
		// 注意：必须对中文进行 URL 编码，否则请求会乱码
		const apiUrl = "http://api.qingyunke.com/api.php";
		const payload = {
			key: 'free',
			appid: '0',
			msg: msg
		};

		try {
			// 2. 使用 uniCloud 内置的 httpclient 发起请求
			// 这一步运行在云端服务器，所以可以请求 HTTP 接口，不会有跨域和安全报错
			const res = await uniCloud.httpclient.request(apiUrl, {
				method: 'GET',
				data: payload,
				dataType: 'json', // 自动解析 JSON
				timeout: 5000 // 5秒超时
			});

			// 3. 处理返回结果
			// uniCloud.httpclient 返回的结构是 { status, data, headers }
			const apiData = res.data;

			if (apiData && apiData.result === 0) {
				// 成功获取回复
				// 处理换行符：青云客把换行符写成了 {br}，我们要换成真正的换行
				let replyContent = apiData.content.replace(/{br}/g, '\n');
				
				return {
					errCode: 0,
					reply: replyContent
				};
			} else {
				// API 返回错误
				return {
					errCode: 500,
					errMsg: '机器人开小差了'
				};
			}

		} catch (e) {
			return {
				errCode: 500,
				errMsg: '网络请求失败: ' + e.message
			};
		}
	}
};
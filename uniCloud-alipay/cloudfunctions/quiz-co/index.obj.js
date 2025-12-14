// uniCloud/cloudfunctions/quiz-co/index.obj.js

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
	 * 获取知识矩阵（分类列表）
	 */
	async getCategoryList() {
		try {
			let uid = null;
			try {
				// 使用 this._checkLogin 调用上面定义的私有方法
				uid = await verifyLogin(this);
			} catch (e) {
				// 未登录不报错，uid 为 null
			}

			const res = await db.collection('quiz-categories')
				.where({ status: true, parent_id: null })
				.orderBy('sort', 'desc')
				.get();
			
			const categories = res.data;

			// 统计进度
			const tasks = categories.map(async (cat) => {
				if (!uid) return { ...cat, progress_percent: 0 };

				const childrenRes = await db.collection('quiz-categories')
					.where({ parent_id: cat._id })
					.field({ _id: true })
					.get();
				
				const childIds = childrenRes.data.map(c => c._id);
				if (childIds.length === 0) return { ...cat, progress_percent: 0 };

				const totalRes = await db.collection('quiz-questions')
					.where({ category_id: db.command.in(childIds) })
					.count();
				
				const doneRes = await db.collection('quiz-records')
					.aggregate()
					.match({
						user_id: uid,
						category_id: db.command.in(childIds),
						is_correct: true
					})
					.group({ _id: '$question_id' })
					.count('total')
					.end();
				
				const finished = doneRes.data.length > 0 ? doneRes.data[0].total : 0;
				const total = totalRes.total;

				return {
					...cat,
					progress_percent: total > 0 ? Math.floor((finished / total) * 100) : 0
				};
			});

			const listWithProgress = await Promise.all(tasks);

			return { errCode: 0, errMsg: 'success', data: listWithProgress };
		} catch (e) {
			console.error(e);
			return { errCode: 500, errMsg: e.message };
		}
	},
	
	/**
	 * 获取课程详情
	 */
	async getCourseDetail(parentId) {
		if (!parentId) return { errCode: 400, errMsg: 'Missing parentId' };

		try {
			let uid = null;
			try {
				uid = await verifyLogin(this);
			} catch (e) {}

			const [parentRes, chaptersRes] = await Promise.all([
				db.collection('quiz-categories').doc(parentId).get(),
				db.collection('quiz-categories').where({ parent_id: parentId, status: true }).orderBy('sort', 'asc').get()
			]);

			if (parentRes.data.length === 0) return { errCode: 404, errMsg: 'Course not found' };

			const parentInfo = parentRes.data[0];
			const chapters = chaptersRes.data;

			const tasks = chapters.map(async (chapter) => {
				const qCount = await db.collection('quiz-questions')
					.where({ category_id: chapter._id })
					.count();
				const total = qCount.total;

				let finished = 0;
				if (uid && total > 0) {
					const aggRes = await db.collection('quiz-records')
						.aggregate()
						.match({
							user_id: uid,
							category_id: chapter._id,
							is_correct: true
						})
						.group({ _id: '$question_id' })
						.count('total')
						.end();
					
					if (aggRes.data.length > 0) {
						finished = aggRes.data[0].total;
					}
				}

				return {
					...chapter,
					total_questions: total,
					finished_questions: finished,
					progress_percent: total > 0 ? Math.floor((finished / total) * 100) : 0,
					status: total === 0 ? 'coming_soon' : 'active'
				};
			});

			const chaptersWithStats = await Promise.all(tasks);

			const totalQs = chaptersWithStats.reduce((sum, ch) => sum + ch.total_questions, 0);
			const totalDone = chaptersWithStats.reduce((sum, ch) => sum + ch.finished_questions, 0);
			const totalPercent = totalQs > 0 ? Math.floor((totalDone / totalQs) * 100) : 0;

			return {
				errCode: 0,
				errMsg: 'success',
				data: {
					info: {
						...parentInfo,
						total_progress: totalPercent,
						total_chapters: chapters.length
					},
					chapters: chaptersWithStats
				}
			};

		} catch (e) {
			console.error(e);
			return { errCode: 500, errMsg: e.message };
		}
	},
	
	/**
	 * 获取题目
	 */
	async getQuestionsByChapter(chapterId) {
		if (!chapterId) return { errCode: 400, errMsg: 'Missing chapterId' };

		try {
			const res = await db.collection('quiz-questions')
				.where({ category_id: chapterId })
				.field({
					'answer': false, 
					'create_date': false,
					'last_modify_date': false
				})
				.limit(50)
				.get();

			return {
				errCode: 0,
				errMsg: 'success',
				data: res.data
			};
		} catch (e) {
			return { errCode: 500, errMsg: 'Failed to load questions' };
		}
	},

	/**
	 * 提交答案
	 */
	async checkAnswer(questionId, userAnswer, duration = 0, mode = 'practice') {
		if (!questionId || !Array.isArray(userAnswer)) {
			return { errCode: 400, errMsg: 'Invalid params' };
		}

		try {
			// 这里的 this._checkLogin 必须能被访问到
			const uid = await verifyLogin(this);

			const res = await db.collection('quiz-questions')
				.doc(questionId)
				.field({
					'answer': true,
					'category_id': true,
					'difficulty': true
				})
				.get();

			if (res.data.length === 0) return { errCode: 404, errMsg: 'Question not found' };
			
			const question = res.data[0];
			const correctVal = question.answer.correct_val;

			// 比对 (这里简化处理，复杂情况需先 sort)
			const isCorrect = JSON.stringify(userAnswer) === JSON.stringify(correctVal);

			let score = 0;
			if (isCorrect) {
				const scoreMap = { 1: 10, 2: 20, 3: 30 };
				score = scoreMap[question.difficulty] || 10;
			}

			await db.collection('quiz-records').add({
				user_id: uid,
				question_id: questionId,
				category_id: question.category_id,
				user_answer: userAnswer,
				is_correct: isCorrect,
				score: score,
				duration: duration,
				mode: mode,
				create_date: Date.now()
			});

			return {
				errCode: 0,
				data: {
					is_correct: isCorrect,
					analysis: mode === 'practice' ? question.answer.analysis : null,
					correct_val: mode === 'practice' ? correctVal : null,
					score_gained: score
				}
			};

		} catch (e) {
			if (e.errCode === 401) return e;
			console.error(e);
			return { errCode: 500, errMsg: e.message };
		}
	},

	/**
		 * 获取用户答题概览 (用于 Header Dashboard)
		 *{ total_answered, correct_rate, streak_days }
		 */
	async getUserStats() {
			try {
				const uid = await verifyLogin(this);
	
				// 1. 统计总答题数
				const totalRes = await db.collection('quiz-records')
					.where({ user_id: uid })
					.count();
				
				// 2. 统计答对数
				const correctRes = await db.collection('quiz-records')
					.where({ user_id: uid, is_correct: true })
					.count();
	
				// 3. 计算正确率
				const total = totalRes.total;
				const correct = correctRes.total;
				const rate = total > 0 ? Math.floor((correct / total) * 100) : 0;
	
				// 4. (进阶) 计算连续打卡天数 (这里暂时模拟，实际需要按日期 group 查询)
				const streak = await this.getStreakDays;
				
				return {
					errCode: 0,
					errMsg: 'success',
					data: {
						total_answered: total,
						total_correct: correct,
						correct_rate: rate,
						streak_days: 'NaN' // 暂时硬编码，后期可扩展
					}
				};
			} catch (e) {
				if (e.errCode === 401) return e;
				return { errCode: 500, errMsg: e.message };
			}
	},
	
	/**
	 * 基于答题日期的连续打卡计算
	 * {number} 连续打卡天数
	 */
	async getStreakDays() {
	  const db = uniCloud.database();
	  
	  // 获取用户所有答对记录
	  const res = await db.collection('quiz-records')
	    .where({ 
	      user_id: this.uid, 
	      is_correct: true 
	    })
	    .field('create_time')
	    .orderBy('create_time', 'desc')
	    .limit(30) // 检查最近30天足够
	    .get();
	  
	  // 如果没有记录，返回0
	  if (!res.data || res.data.length === 0) return 0;
	  
	  // 去重：同一天多次答对只算一次
	  const dateSet = new Set();
	  res.data.forEach(item => {
	    const date = new Date(item.create_time);
	    dateSet.add(date.toDateString()); // 使用 toDateString 去重
	  });
	  
	  const dates = Array.from(dateSet);
	  
	  // 获取当前日期
	  const now = new Date();
	  const today = now.toDateString();
	  const yesterday = new Date(now);
	  yesterday.setDate(yesterday.getDate() - 1);
	  const yesterdayStr = yesterday.toDateString();
	  // 判断逻辑
	  if (dates.includes(today)) {
	    // 今天已经答对了
	    return this.countConsecutiveDays(dates, today);
	  } else if (dates.includes(yesterdayStr)) {
	    // 今天还没答对，但昨天答对了（今天还没结束）
	    return this.countConsecutiveDays(dates, yesterdayStr);
	  } else {
	    // 今天和昨天都没答对，连续已中断
	    return 0;
	  }
	},
	
	/**
	 * 统计连续天数
	 * {Array} dates 所有答对日期数组
	 * {string} startDate 开始日期
	 * {number} 连续天数
	 */
	countConsecutiveDays(dates, startDate) {
	  let count = 1;
	  let currentDate = new Date(startDate);
	  
	  while (true) {
	    currentDate.setDate(currentDate.getDate() - 1);
	    const prevDateStr = currentDate.toDateString();
	    
	    if (dates.includes(prevDateStr)) {
	      count++;
	    } else {
	      break;
	    }
	  }
	  
	  return count;
	},
	/**
		 * 获取用户答题数据看板 (V4: 全维度统计 + 容错增强)
		 */
	async getUserStatsToProfit() {
			try {
				const uid = await verifyLogin(this);
	
				// --- 维度 1: 原始记录统计 (不做任何过滤，看看总共有多少条) ---
				const totalAttemptsRes = await db.collection('quiz-records')
					.where({ user_id: uid })
					.count();
				const totalAttempts = totalAttemptsRes.total;
	
				// --- 维度 2: 只要答对的记录数 (不去重) ---
				const totalCorrectRes = await db.collection('quiz-records')
					.where({ user_id: uid, is_correct: true })
					.count();
				const totalCorrect = totalCorrectRes.total;
				
				// --- 维度 3: 掌握的题目数 (答对且去重，并按难度分布) ---
				const distStatsRes = await db.collection('quiz-records')
					.aggregate()
					// 1. 只看答对的
					.match({ user_id: uid, is_correct: true }) 
					// 2. 按题目去重 (核心：同一题做对100次也只算掌握了1个知识点)
					.group({ _id: '$question_id' })
					.end()
					
				// 提取题目ID数组
				  const questionIds = distStatsRes.data.map(item => item._id);
				
				  // 第二步：批量查询题目信息
				  const questionsInfo = await db.collection('quiz-questions')
				    .where({
				      _id: db.command.in(questionIds)
				    })
				    .get();
				
				  // console.log('questionsInfo:', questionsInfo);
				  // 按难度分类题目
				  const categorizedQuestions = {
				    easy: [],    // difficulty: 1
				    medium: [],  // difficulty: 2
				    hard: []     // difficulty: 3
				  };
				  
				  questionsInfo.data.forEach(question => {
				    const diff = question.difficulty;
				    if (diff === 1) categorizedQuestions.easy.push(question);
				    else if (diff === 2) categorizedQuestions.medium.push(question);
				    else if (diff === 3) categorizedQuestions.hard.push(question);
				  });
				  
				  // 1. 统计总答题数
				  const totalRes = await db.collection('quiz-records')
				  	.where({ user_id: uid })
				  	.count();
				  
				  // 2. 统计答对数
				  const correctRes = await db.collection('quiz-records')
				  	.where({ user_id: uid, is_correct: true })
				  	.count();
				  	
				  // 3. 计算正确率
				  const total = totalRes.total;
				  const correct = correctRes.total;
				  const rate = total > 0 ? Math.floor((correct / total) * 100) : 0;
				  
				  return {
					  errCode : 0,
					  data:{
						  easy:categorizedQuestions.easy.length,
						  medium:categorizedQuestions.medium.length,
						  hard:categorizedQuestions.hard.length,
						  accuracy: rate
					  }
				  }

			} catch (e) {
				if (e.errCode === 401) return e;
				console.error('[getUserStats Error]', e);
				return { errCode: 500, errMsg: e.message };
			}
		},
	
		/**
		 * 获取用户答题历史 (时光轴列表)
		 * @description 使用聚合查询联表：Records + Questions + Categories
		 * @param {Number} page 页码
		 * @param {Number} limit 每页数量
		 */
	
	async getUserHistory(page = 1, limit = 10) {
			try {
				const uid = await verifyLogin(this);
				const skip = (page - 1) * limit;
	
				// 聚合查询：这是 NoSQL 处理复杂关联的大杀器
				const res = await db.collection('quiz-records')
					.aggregate()
					// 1. 筛选当前用户
					.match({ user_id: uid })
					// 2. 按时间倒序 (最近的在上面)
					.sort({ create_date: -1 })
					// 3. 分页
					.skip(skip)
					.limit(limit)
					// 4. 联表查询题目信息 (获取标题、难度、题型)
					.lookup({
						from: 'quiz-questions',
						localField: 'question_id',
						foreignField: '_id',
						as: 'question_info'
					})
					// 5. 联表查询章节信息 (获取章节名称)
					.lookup({
						from: 'quiz-categories',
						localField: 'category_id',
						foreignField: '_id',
						as: 'category_info'
					})
					// 6. 字段投影 (只返回前端需要的，保护数据，减少流量)
					.project({
						_id: 1,
						is_correct: 1,
						create_date: 1,
						score: 1,
						duration: 1,
						user_answer: 1, // 用于前端回显用户选了啥
						// 提取数组中的第一个元素 (lookup 默认返回数组)
						question_title: { $arrayElemAt: ['$question_info.title', 0] },
						question_type: { $arrayElemAt: ['$question_info.type', 0] },
						question_difficulty: { $arrayElemAt: ['$question_info.difficulty', 0] },
						// 注意：这里我们甚至可以把正确答案带回去，或者选择不带，看复习模式的设计
						// question_answer: { $arrayElemAt: ['$question_info.answer', 0] }, 
						
						category_name: { $arrayElemAt: ['$category_info.name', 0] }
					})
					.end();
	
				// 统计总数 (用于前端判断是否还有更多)
				// 注意：aggregate 统计总数比较麻烦，简单做法是单独 count 一次
				const totalRes = await db.collection('quiz-records').where({ user_id: uid }).count();
	
				return {
					errCode: 0,
					errMsg: 'success',
					data: {
						list: res.data,
						total: totalRes.total,
						has_more: (skip + limit) < totalRes.total
					}
				};
	
			} catch (e) {
				if (e.errCode === 401) return e;
				console.error(e);
				return { errCode: 500, errMsg: e.message };
			}
	},
	/**
		 * 获取单条答题记录详情 (用于复习弹窗)
		 * @param {String} recordId 记录ID
		 */
	
	async getRecordDetail(recordId) {
			if (!recordId) return { errCode: 400, errMsg: 'Missing recordId' };
			try {
				const uid = await verifyLogin(this);
	
				// 查记录表
				const recordRes = await db.collection('quiz-records')
					.doc(recordId)
					.get();
				
				if (recordRes.data.length === 0) return { errCode: 404, errMsg: 'Record not found' };
				const record = recordRes.data[0];
	
				// 鉴权：只能看自己的
				if (record.user_id !== uid) return { errCode: 403, errMsg: 'Permission denied' };
	
				// 查题目表 (获取完整的 content 和 answer)
				const questionRes = await db.collection('quiz-questions')
					.doc(record.question_id)
					.field({
						'title': true,
						'content': true,
						'type': true,
						'difficulty': true,
						// 复习模式下，必须返回答案和解析
						'answer': true 
					})
					.get();
	
				if (questionRes.data.length === 0) return { errCode: 404, errMsg: 'Question deleted' };
	
				return {
					errCode: 0,
					data: {
						record: record,
						question: questionRes.data[0]
					}
				};
			} catch (e) {
				if (e.errCode === 401) return e;
				return { errCode: 500, errMsg: e.message };
			}
	},
	
		/**
			 * 获取章节题目列表 (用于索引页)
			 * @description 返回题目基础信息 + 用户答题状态 (是否已做、是否正确)
			 */
	async getQuestionListMeta(categoryId) {
				if (!categoryId) return { errCode: 400, errMsg: 'Missing categoryId' };
		
				try {
					// 1. 尝试获取 UID
					let uid = null;
					try { uid = await verifyLogin(this); } catch (e) {}
		
					// 2. 查题目表 (只查元数据，不查 content 和 answer)
					const questionsRes = await db.collection('quiz-questions')
						.where({ category_id: categoryId })
						.field({
							'title': true,
							'type': true,
							'difficulty': true,
							'sort': true // 假设你有排序字段，或者按默认
						})
						// .orderBy('sort', 'asc') 
						.limit(200) // 一次拉取所有题目(上限200)
						.get();
					
					let questions = questionsRes.data;
					// 3. 如果用户已登录，查询答题记录状态
					if (uid && questions.length > 0) {
						// 查出该用户在该章节下的所有记录
						const recordsRes = await db.collection('quiz-records')
							.where({
								user_id: uid,
								category_id: categoryId
							})
							.field({ 'question_id': true, 'is_correct': true })
							.get();
						
						// 构建状态字典: { qid: 'correct' | 'wrong' }
						const statusMap = {};
						recordsRes.data.forEach(rec => {
							// 如果做对过一次，就标记为 correct；否则如果是错的，且没对过，标记 wrong
							if (rec.is_correct) {
								statusMap[rec.question_id] = 'correct';
							} else if (!statusMap[rec.question_id]) {
								statusMap[rec.question_id] = 'wrong';
							}
						});
		
						// 合并状态
						questions = questions.map(q => ({
							...q,
							user_status: statusMap[q._id] || 'unstarted' // correct, wrong, unstarted
						}));
					}
		
					return {
						errCode: 0,
						data: questions
					};
		
				} catch (e) {
					return { errCode: 500, errMsg: e.message };
				}
	},
};
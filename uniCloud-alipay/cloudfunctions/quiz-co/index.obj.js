// uniCloud/cloudfunctions/quiz-co/index.obj.js

const db = uniCloud.database();
const cmd = db.command;

module.exports = {
	_before: function () {
		// 这里可以做通用的鉴权，比如检查 token
		// const clientInfo = this.getClientInfo();
        // ...
	},

	/**
	 * 获取知识矩阵（分类列表）
	 * @returns {Promise<Object>}
	 */
	async getCategoryList() {
		try {
			// 1. 查询 quiz-categories 表
			// 筛选 status == true (已上架) 的分类
			// 按 sort 字段升序排列 (asc)
			const res = await db.collection('quiz-categories')
				.where({
					status: true
				})
				.orderBy('sort', 'asc') 
				.get();

			// 2. (可选) 未来可以在这里遍历 res.data，
            // 结合 quiz-user-progress 表，计算每个分类的“解锁状态”和“进度”
            // 这样前端拿到的直接就是带状态的数据，无需前端计算

			// 3. 返回标准结构
			return {
				errCode: 0,
				errMsg: 'success',
				data: res.data
			};
		} catch (e) {
			console.error(e);
			return {
				errCode: 500,
				errMsg: '获取题库列表失败',
				error: e
			};
		}
	},
	
	/**
		 * 获取课程详情（学习路线图）
		 * @param {String} parentId 父分类ID (例如 Python 的ID)
		 */
		async getCourseDetail(parentId) {
			if (!parentId) {
				return { errCode: 400, errMsg: 'Missing parentId' };
			}
	
			try {
				const uid = this.getUniIdToken()?.uid; // 获取当前用户ID
	
				// 1. 获取当前大类的详情（用于显示 Header 标题）
				const parentRes = await db.collection('quiz-categories').doc(parentId).get();
				const parentInfo = parentRes.data[0] || {};
	
				// 2. 获取子分类列表 (Chapters)
				const chaptersRes = await db.collection('quiz-categories')
					.where({ parent_id: parentId, status: true })
					.orderBy('sort', 'asc')
					.get();
				
				let chapters = chaptersRes.data;
	
				// 3. 【核心】遍历子分类，统计题目数和进度
				// 注意：实际生产环境建议使用 db.collection('...').aggregate() 聚合查询优化性能
				// 这里为了代码易读性和容错性，使用并发查询演示逻辑
				const tasks = chapters.map(async (chapter) => {
					// A. 查询该章节下的总题目数
					const qCount = await db.collection('quiz-questions')
						.where({ category_id: chapter._id })
						.count();
					
					// B. 查询用户在该章节下已答对的题目数 (quiz-records)
					// 需确保 quiz-records 表里有 category_id 字段，或者通过 question_id 联查
					// 这里简化逻辑：假设 records 存了 category_id (如果没有，建议在 Schema 补上，或者暂时返回模拟进度)
					let uCount = 0;
					if (uid) {
						// 暂时模拟进度，实际需查表
						// uCount = await db.collection('quiz-records').where({ user_id: uid, category_id: chapter._id, is_correct: true }).count().total;
					}
	
					return {
						...chapter,
						total_questions: qCount.total,
						finished_questions: uCount, // 暂时为0
						// 如果题目数为0，标记为 'coming_soon'
						status: qCount.total === 0 ? 'coming_soon' : 'active' 
					};
				});
	
				// 等待所有统计完成
				const chaptersWithStats = await Promise.all(tasks);
	
				return {
					errCode: 0,
					errMsg: 'success',
					data: {
						info: parentInfo,
						chapters: chaptersWithStats
					}
				};
	
			} catch (e) {
				console.error(e);
				return { errCode: 500, errMsg: e.message };
			}
		},
		
		/**
			 * 获取章节下的所有题目
			 * @param {String} chapterId 子分类ID
			 */
			async getQuestionsByChapter(chapterId) {
				if (!chapterId) return { errCode: 400, errMsg: 'Missing chapterId' };
		
				try {
					// 1. 查询题目表
					// 实际项目中可能需要 limit 限制数量，或者 random 随机排序
					const res = await db.collection('quiz-questions')
						.where({ category_id: chapterId })
						.limit(50) // 练习模式一次拉取50题足够了
						.get();
		
					return {
						errCode: 0,
						errMsg: 'success',
						data: res.data
					};
				} catch (e) {
					console.error(e);
					return { errCode: 500, errMsg: 'Failed to load questions' };
				}
			}
}
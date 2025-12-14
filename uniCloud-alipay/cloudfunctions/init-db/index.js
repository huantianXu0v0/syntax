'use strict';
const db = uniCloud.database();
const cmd = db.command;

exports.main = async (event, context) => {
  try {
    // 🔥 警告：这将清空所有用户的答题历史
    // 在开发阶段这是清理脏数据的最佳方式
    const res = await db.collection('quiz-records').remove();

    return {
      code: 0,
      msg: `🧹 大扫除完成！已删除 ${res.deleted} 条脏记录。`,
      tip: "现在你的数据库干干净净，请去前端重新做题，生成完美的新数据。"
    };
  } catch (e) {
    return { code: 500, error: e };
  }
};
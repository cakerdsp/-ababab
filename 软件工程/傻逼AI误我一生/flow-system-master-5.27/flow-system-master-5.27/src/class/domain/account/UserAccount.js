class UserAccount {
  constructor(userId) {
    this.userId = userId;
    this.password = null; // 不存储密码
  }

  // 获取用户ID（同时作为用户名）
  getUserId() {
    return this.userId;
  }

  // 为了兼容性保留getUserName方法，返回userId
  getUserName() {
    return this.userId;
  }
}

module.exports = UserAccount;

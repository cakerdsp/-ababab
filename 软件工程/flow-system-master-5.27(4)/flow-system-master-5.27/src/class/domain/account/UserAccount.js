class UserAccount {
  constructor(userId) {
    this.userId = userId;
    this.password = null; // Do not store password
  }

  // Get user ID (also serves as username)
  getUserId() {
    return this.userId;
  }

  // Keep getUserName method for compatibility, returns userId
  getUserName() {
    return this.userId;
  }
}

module.exports = UserAccount;

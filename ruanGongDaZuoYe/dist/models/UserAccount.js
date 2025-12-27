"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UserAccount = void 0;
/**
 * 用户账号模型类
 * 存储用户的账号和密码信息
 */
class UserAccount {
    constructor(userName, password) {
        this.userName = userName;
        this.password = password;
    }
    /**
     * 获取用户名
     * @returns 用户名
     */
    getUserName() {
        return this.userName;
    }
    /**
     * 获取密码
     * @returns 密码
     */
    getPassword() {
        return this.password;
    }
}
exports.UserAccount = UserAccount;
//# sourceMappingURL=UserAccount.js.map
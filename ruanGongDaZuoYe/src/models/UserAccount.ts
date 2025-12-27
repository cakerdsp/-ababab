/**
 * 用户账号模型类
 * 存储用户的账号和密码信息
 */
export class UserAccount {
    private userName: string;
    private password: string;

    constructor(userName: string, password: string) {
        this.userName = userName;
        this.password = password;
    }

    /**
     * 获取用户名
     * @returns 用户名
     */
    getUserName(): string {
        return this.userName;
    }

    /**
     * 获取密码
     * @returns 密码
     */
    getPassword(): string {
        return this.password;
    }
}
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AccountManager = void 0;
const UserAccount_1 = require("../models/UserAccount");
const SupportedBrand_1 = require("../models/SupportedBrand");
/**
 * 账号管理器类
 * 负责用户账号的管理，包括登录、注册、第三方账号绑定等功能
 */
class AccountManager {
    constructor(userAccount, dataStorage) {
        this.userAccount = null;
        this.supportedBrands = new Map();
        this.userAccount = userAccount;
        this.dataStorage = dataStorage;
        // 初始化支持的品牌
        Object.values(SupportedBrand_1.SupportedBrand).forEach(brand => {
            this.supportedBrands.set(brand, false);
        });
    }
    /**
     * 从本地存储加载已保存的账号信息
     * @returns 加载结果
     */
    loadSavedAccounts() {
        try {
            const data = this.dataStorage.load();
            if (data && data.userAccount) {
                this.userAccount = new UserAccount_1.UserAccount(data.userAccount.userName, data.userAccount.password);
                // 加载品牌账号绑定状态
                if (data.brandAccounts) {
                    Object.entries(data.brandAccounts).forEach(([brand, status]) => {
                        if ((0, SupportedBrand_1.isSupportedBrand)(brand)) {
                            this.supportedBrands.set(brand, status);
                        }
                    });
                }
                return {
                    success: true,
                    user: {
                        userName: this.userAccount.getUserName()
                    }
                };
            }
            return { success: false };
        }
        catch (error) {
            console.error('加载保存的账号失败:', error);
            return { success: false };
        }
    }
    /**
     * 用户登录
     * @param userId 用户ID
     * @param password 密码
     * @param autoLogin 是否自动登录
     * @returns 登录结果
     */
    login(userId, password, autoLogin = false) {
        // 这里应该调用服务器API进行验证
        // 模拟登录成功
        this.userAccount = new UserAccount_1.UserAccount(userId, password);
        if (autoLogin) {
            this.saveUserState();
        }
        return {
            success: true,
            message: '登录成功',
            user: {
                userName: userId
            }
        };
    }
    /**
     * 用户注册
     * @param userId 用户ID
     * @param password 密码
     * @returns 注册结果
     */
    register(userId, password) {
        // 这里应该调用服务器API进行注册
        // 模拟注册成功
        return { success: true, message: '注册成功' };
    }
    /**
     * 用户登出
     * @returns 登出结果
     */
    logout() {
        this.userAccount = null;
        this.dataStorage.clear();
        return { success: true, message: '登出成功' };
    }
    /**
     * 获取品牌授权码
     * @param supportedBrand 支持的品牌
     * @returns 授权码
     */
    getBrandAuthorization_code(supportedBrand) {
        // 这里应该调用第三方API获取授权码
        return `auth_code_for_${supportedBrand}`;
    }
    /**
     * 添加品牌账号
     * @param supportedBrand 支持的品牌
     * @param userAccount 用户账号
     * @returns 是否添加成功
     */
    addBrandAccount(supportedBrand, userAccount) {
        if (!this.userAccount) {
            return false;
        }
        // 这里应该调用服务器API进行绑定
        this.supportedBrands.set(supportedBrand, true);
        this.saveUserState();
        return true;
    }
    /**
     * 移除品牌账号
     * @param userAccount 用户账号
     * @param supportedBrand 支持的品牌
     * @returns 是否移除成功
     */
    removeBrandAccount(userAccount, supportedBrand) {
        if (!this.userAccount) {
            return false;
        }
        // 这里应该调用服务器API进行解绑
        this.supportedBrands.set(supportedBrand, false);
        this.saveUserState();
        return true;
    }
    /**
     * 获取品牌账号
     * @returns 品牌账号列表
     */
    getBrandAccounts() {
        return this.supportedBrands;
    }
    /**
     * 获取用户账号
     * @returns 用户账号
     */
    getUserAccount() {
        return this.userAccount;
    }
    /**
     * 保存用户状态
     */
    saveUserState() {
        if (!this.userAccount) {
            return;
        }
        const brandAccountsObj = {};
        this.supportedBrands.forEach((value, key) => {
            brandAccountsObj[key] = value;
        });
        const data = {
            userAccount: {
                userName: this.userAccount.getUserName(),
                password: this.userAccount.getPassword()
            },
            brandAccounts: brandAccountsObj
        };
        this.dataStorage.save(data);
    }
}
exports.AccountManager = AccountManager;
//# sourceMappingURL=AccountManager.js.map
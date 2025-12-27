"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AccountAPIRegistryImpl = void 0;
const axios_1 = __importDefault(require("axios"));
/**
 * 账户API注册表实现类
 */
class AccountAPIRegistryImpl {
    constructor() {
        this.apiParams = new Map();
        this.apiResponse = new Map();
        this.baseUrl = 'http://localhost:3000'; // 服务器地址
    }
    /**
     * API配置方法
     * @param path API路径
     * @param method HTTP方法
     * @returns API配置
     */
    apiConfig(path, method) {
        return {
            url: `${this.baseUrl}${path}`,
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
    }
    /**
     * 发送API请求
     * @param config API配置
     * @param data 请求数据
     * @returns 请求结果
     */
    async apiRequest(config, data) {
        try {
            const response = await (0, axios_1.default)({
                ...config,
                data
            });
            return response.data;
        }
        catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
}
exports.AccountAPIRegistryImpl = AccountAPIRegistryImpl;
//# sourceMappingURL=AccountAPIRegistryImpl.js.map
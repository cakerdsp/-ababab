import { AccountAPIRegistry } from '../interfaces/AccountAPIRegistry';
import axios from 'axios';

/**
 * 账户API注册表实现类
 */
export class AccountAPIRegistryImpl implements AccountAPIRegistry {
    apiParams: Map<string, any> = new Map();
    apiResponse: Map<string, any> = new Map();
    private baseUrl: string = 'http://localhost:3000'; // 服务器地址

    /**
     * API配置方法
     * @param path API路径
     * @param method HTTP方法
     * @returns API配置
     */
    apiConfig(path: string, method: string): any {
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
    async apiRequest(config: any, data?: any): Promise<any> {
        try {
            const response = await axios({
                ...config,
                data
            });
            return response.data;
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }
}
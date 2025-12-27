/**
 * 账户API注册表接口
 * 定义了与账户相关的API方法
 */
export interface AccountAPIRegistry {
    /**
     * API配置方法
     * @param path API路径
     * @param method HTTP方法
     * @returns API配置
     */
    apiConfig(path: string, method: string): any;
    
    /**
     * API参数类型
     */
    apiParams: Map<string, any>;
    
    /**
     * API响应类型管理
     */
    apiResponse: Map<string, any>;
}
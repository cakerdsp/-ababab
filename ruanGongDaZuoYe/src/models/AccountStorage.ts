import { UserAccount } from './UserAccount';
import * as fs from 'fs';
import * as path from 'path';

/**
 * 账号存储类
 * 负责存储和加载用户账号信息
 */
export class AccountStorage {
    private filePath: string;

    constructor(filePath: string) {
        this.filePath = filePath;
        // 确保目录存在
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    /**
     * 保存数据
     * @param data 要保存的数据
     */
    save(data: any): void {
        try {
            const jsonData = JSON.stringify(data, null, 2);
            fs.writeFileSync(this.filePath, jsonData, 'utf8');
            console.log(`数据已保存到 ${this.filePath}`);
        } catch (error) {
            console.error(`保存数据到 ${this.filePath} 失败:`, error);
        }
    }

    /**
     * 加载数据
     * @returns 加载的数据
     */
    load(): any {
        try {
            if (!fs.existsSync(this.filePath)) {
                console.log(`文件 ${this.filePath} 不存在，返回null`);
                return null;
            }
            const jsonData = fs.readFileSync(this.filePath, 'utf8');
            return JSON.parse(jsonData);
        } catch (error) {
            console.error(`从 ${this.filePath} 加载数据失败:`, error);
            return null; // 添加返回值
        } // 添加缺失的右花括号
    }

    /**
     * 清除存储的数据
     */
    clear(): void {
        try {
            if (fs.existsSync(this.filePath)) {
                fs.unlinkSync(this.filePath);
                console.log(`已清除 ${this.filePath} 中的数据`);
            }
        } catch (error) {
            console.error(`清除 ${this.filePath} 中的数据失败:`, error);
        }
    }
}
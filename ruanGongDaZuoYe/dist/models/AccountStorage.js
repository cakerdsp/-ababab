"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AccountStorage = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
/**
 * 账号存储类
 * 负责存储和加载用户账号信息
 */
class AccountStorage {
    constructor(filePath) {
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
    save(data) {
        try {
            const jsonData = JSON.stringify(data, null, 2);
            fs.writeFileSync(this.filePath, jsonData, 'utf8');
            console.log(`数据已保存到 ${this.filePath}`);
        }
        catch (error) {
            console.error(`保存数据到 ${this.filePath} 失败:`, error);
        }
    }
    /**
     * 加载数据
     * @returns 加载的数据
     */
    load() {
        try {
            if (!fs.existsSync(this.filePath)) {
                console.log(`文件 ${this.filePath} 不存在，返回null`);
                return null;
            }
            const jsonData = fs.readFileSync(this.filePath, 'utf8');
            return JSON.parse(jsonData);
        }
        catch (error) {
            console.error(`从 ${this.filePath} 加载数据失败:`, error);
        }
    }
}
exports.AccountStorage = AccountStorage;
//# sourceMappingURL=AccountStorage.js.map
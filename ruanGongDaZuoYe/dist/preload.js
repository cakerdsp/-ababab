"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// 使用contextBridge暴露API给渲染进程，确保安全性
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    // 登录请求
    login: (username, password, autoLogin = false) => electron_1.ipcRenderer.invoke('login', username, password, autoLogin),
    // 注册请求
    register: (username, password) => electron_1.ipcRenderer.invoke('register', username, password),
    // 退出登录请求
    logout: () => electron_1.ipcRenderer.invoke('logout'),
    // 绑定第三方账号请求
    bindThirdParty: (provider, authData) => electron_1.ipcRenderer.invoke('bind-third-party', provider, authData),
    // 解绑第三方账号请求
    unbindThirdParty: (provider) => electron_1.ipcRenderer.invoke('unbind-third-party', provider),
    // 监听主进程发送的消息
    onUserLoggedIn: (callback) => electron_1.ipcRenderer.on('user-logged-in', (_event, userData) => callback(userData)),
    onUserLoggedOut: (callback) => electron_1.ipcRenderer.on('user-logged-out', () => callback()),
    onThirdPartyStatusUpdate: (callback) => electron_1.ipcRenderer.on('third-party-status-update', (_event, provider, status) => callback(provider, status)),
    // 移除监听器的方法，防止内存泄漏
    removeUserLoggedInListener: () => electron_1.ipcRenderer.removeAllListeners('user-logged-in'),
    removeUserLoggedOutListener: () => electron_1.ipcRenderer.removeAllListeners('user-logged-out'),
    removeThirdPartyStatusUpdateListener: () => electron_1.ipcRenderer.removeAllListeners('third-party-status-update'),
});
console.log('preload.ts 已加载，electronAPI 已暴露');
//# sourceMappingURL=preload.js.map
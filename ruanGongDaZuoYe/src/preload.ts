import { contextBridge, ipcRenderer } from 'electron';

// 使用contextBridge暴露API给渲染进程，确保安全性
contextBridge.exposeInMainWorld('electronAPI', {
    // 登录请求
    login: (username: string, password: string, autoLogin: boolean = false) => 
        ipcRenderer.invoke('login', username, password, autoLogin),
    
    // 注册请求
    register: (username: string, password: string) => 
        ipcRenderer.invoke('register', username, password),
    
    // 退出登录请求
    logout: () => 
        ipcRenderer.invoke('logout'),
    
    // 绑定第三方账号请求
    bindThirdParty: (provider: string, authData: any) => 
        ipcRenderer.invoke('bind-third-party', provider, authData),
    
    // 解绑第三方账号请求
    unbindThirdParty: (provider: string) => 
        ipcRenderer.invoke('unbind-third-party', provider),

    // 监听主进程发送的消息
    onUserLoggedIn: (callback: (userData: any) => void) => 
        ipcRenderer.on('user-logged-in', (_event, userData) => callback(userData)),
    
    onUserLoggedOut: (callback: () => void) => 
        ipcRenderer.on('user-logged-out', () => callback()),
    
    onThirdPartyStatusUpdate: (callback: (provider: string, status: any) => void) => 
        ipcRenderer.on('third-party-status-update', (_event, provider, status) => callback(provider, status)),
    
    // 移除监听器的方法，防止内存泄漏
    removeUserLoggedInListener: () => 
        ipcRenderer.removeAllListeners('user-logged-in'),
    
    removeUserLoggedOutListener: () => 
        ipcRenderer.removeAllListeners('user-logged-out'),
    
    removeThirdPartyStatusUpdateListener: () => 
        ipcRenderer.removeAllListeners('third-party-status-update'),
});

console.log('preload.ts 已加载，electronAPI 已暴露');
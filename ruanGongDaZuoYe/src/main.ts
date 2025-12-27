import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import * as url from 'url';
import { AccountManager } from './services/AccountManager';
import { AccountStorage } from './models/AccountStorage';
import { UserAccount } from './models/UserAccount';
import { SupportedBrand } from './models/SupportedBrand';

// 主窗口引用
let mainWindow: BrowserWindow | null = null;

// 创建账号存储和账号管理器实例
const accountStorage = new AccountStorage(path.join(app.getPath('userData'), 'accounts.json'));
const accountManager = new AccountManager(null, accountStorage);

function createWindow(): void {
    // 创建浏览器窗口
    mainWindow = new BrowserWindow({
        width: 1024,
        height: 768,
        transparent: false,
        frame: true,
        resizable: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    // 加载应用的index.html
    const startUrl = url.format({
        pathname: path.join(__dirname, '../index.html'),
        protocol: 'file:',
        slashes: true
    });

    mainWindow.loadURL(startUrl);
    console.log('加载URL:', startUrl);

    // 打开开发者工具
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    // 窗口加载完成后尝试自动登录
    mainWindow.webContents.on('did-finish-load', async () => {
        console.log('主进程: 窗口加载完成，尝试自动登录');
        try {
            const autoLoginResult = await accountManager.loadSavedAccounts();
            
            if (autoLoginResult.success && autoLoginResult.user) {
                console.log('主进程: 自动登录成功');
                // 通知渲染进程自动登录成功
                notifyUserLoginStateChange(true, autoLoginResult.user);
                
                // 通知第三方账号状态
                const brandAccounts = accountManager.getBrandAccounts();
                brandAccounts.forEach((bound, brand) => {
                    notifyThirdPartyStatusChange(brand, { bound });
                });
            } else {
                console.log('主进程: 自动登录失败或无保存的账号信息');
            }
        } catch (error) {
            console.error('主进程: 自动登录过程中发生错误', error);
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// 通知用户登录状态变化
function notifyUserLoginStateChange(loggedIn: boolean, userData?: any): void {
    if (!mainWindow) return;
    
    if (loggedIn && userData) {
        mainWindow.webContents.send('user-logged-in', userData);
    } else {
        mainWindow.webContents.send('user-logged-out');
    }
}

// 通知第三方账号状态变化
function notifyThirdPartyStatusChange(provider: SupportedBrand, status: { bound: boolean, accountId?: string }): void {
    if (!mainWindow) return;
    mainWindow.webContents.send('third-party-status-update', provider, status);
}

// 设置IPC处理程序
function setupIpcHandlers(): void {
    // 登录处理
    ipcMain.handle('login', async (_, userId: string, password: string, autoLogin: boolean = false) => {
        console.log(`主进程: 收到登录请求，用户ID: ${userId}`);
        const loginResponse = await accountManager.login(userId, password, autoLogin);
        
        if (loginResponse.success) {
            notifyUserLoginStateChange(true, loginResponse.user);
        }
        
        return loginResponse;
    });

    // 注册处理
    ipcMain.handle('register', async (_, userId: string, password: string) => {
        console.log(`主进程: 收到注册请求，用户ID: ${userId}`);
        return await accountManager.register(userId, password);
    });

    // 登出处理
    ipcMain.handle('logout', async () => {
        console.log('主进程: 收到登出请求');
        const logoutResponse = await accountManager.logout();
        
        if (logoutResponse.success) {
            notifyUserLoginStateChange(false);
        }
        
        return logoutResponse;
    });

    // 绑定第三方账号处理
    ipcMain.handle('bind-third-party', async (_, provider: string, authData: any) => {
        console.log(`主进程: 收到绑定请求，提供商: ${provider}`, authData);
        
        if (!Object.values(SupportedBrand).includes(provider as SupportedBrand)) {
            return { success: false, message: '不支持的品牌' };
        }
        
        const userAccount = accountManager.getUserAccount();
        if (!userAccount) {
            return { success: false, message: '用户未登录' };
        }
        
        const success = accountManager.addBrandAccount(provider as SupportedBrand, userAccount);
        
        if (success) {
            notifyThirdPartyStatusChange(provider as SupportedBrand, { bound: true, accountId: authData.accountId });
            return { success: true, message: '绑定成功', details: { accountId: authData.accountId } };
        } else {
            return { success: false, message: '绑定失败' };
        }
    });

    // 解绑第三方账号处理
    ipcMain.handle('unbind-third-party', async (_, provider: string) => {
        console.log(`主进程: 收到解绑请求，提供商: ${provider}`);
        
        if (!Object.values(SupportedBrand).includes(provider as SupportedBrand)) {
            return { success: false, message: '不支持的品牌' };
        }
        
        const userAccount = accountManager.getUserAccount();
        if (!userAccount) {
            return { success: false, message: '用户未登录' };
        }
        
        const success = accountManager.removeBrandAccount(userAccount, provider as SupportedBrand);
        
        if (success) {
            notifyThirdPartyStatusChange(provider as SupportedBrand, { bound: false });
            return { success: true, message: '解绑成功' };
        } else {
            return { success: false, message: '解绑失败' };
        }
    });
}

// 应用准备就绪时创建窗口
app.whenReady().then(() => {
    setupIpcHandlers();
    createWindow();
    
    app.on('activate', () => {
        // 在macOS上，当点击dock图标且没有其他窗口打开时，通常会重新创建一个窗口
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// 当所有窗口关闭时退出应用
app.on('window-all-closed', () => {
    // 在macOS上，用户通常希望应用在点击关闭按钮后仍然保持活动状态，除非用户使用Cmd + Q显式退出
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
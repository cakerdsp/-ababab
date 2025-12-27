// 定义electronAPI接口，与preload.ts中暴露的API保持一致
interface ElectronAPI {
    login: (username: string, password: string, autoLogin?: boolean) => Promise<any>;
    register: (username: string, password: string) => Promise<any>;
    logout: () => Promise<any>;
    bindThirdParty: (provider: string, authData: any) => Promise<any>;
    unbindThirdParty: (provider: string) => Promise<any>;
    onUserLoggedIn: (callback: (userData: any) => void) => void;
    onUserLoggedOut: (callback: () => void) => void;
    onThirdPartyStatusUpdate: (callback: (provider: string, status: any) => void) => void;
    removeUserLoggedInListener: () => void;
    removeUserLoggedOutListener: () => void;
    removeThirdPartyStatusUpdateListener: () => void;
}

// 声明全局window对象包含electronAPI
declare global {
    interface Window {
        electronAPI: ElectronAPI;
    }
}

// DOM元素引用
const loginView = document.getElementById('loginView') as HTMLDivElement;
const registerView = document.getElementById('registerView') as HTMLDivElement;
const mainAppView = document.getElementById('mainAppView') as HTMLDivElement;

const loginUsername = document.getElementById('loginUsername') as HTMLInputElement;
const loginPassword = document.getElementById('loginPassword') as HTMLInputElement;
const autoLogin = document.getElementById('autoLogin') as HTMLInputElement;
const loginButton = document.getElementById('loginButton') as HTMLButtonElement;

const registerUsername = document.getElementById('registerUsername') as HTMLInputElement;
const registerPassword = document.getElementById('registerPassword') as HTMLInputElement;
const registerEmail = document.getElementById('registerEmail') as HTMLInputElement;
const registerButton = document.getElementById('registerButton') as HTMLButtonElement;

const showLoginViewLink = document.getElementById('showLoginViewLink') as HTMLParagraphElement;
const showRegisterViewLink = document.getElementById('showRegisterViewLink') as HTMLParagraphElement;

const logoutButton = document.getElementById('logoutButton') as HTMLButtonElement;

const bindXiaomiButton = document.getElementById('bindXiaomiButton') as HTMLButtonElement;
const bindMideaButton = document.getElementById('bindMideaButton') as HTMLButtonElement;
const unbindXiaomiButton = document.getElementById('unbindXiaomiButton') as HTMLButtonElement;
const unbindMideaButton = document.getElementById('unbindMideaButton') as HTMLButtonElement;

// 当前登录的用户
let currentUser: any = null;

// 视图切换函数
function showView(viewToShow: HTMLDivElement): void {
    // 隐藏所有视图
    loginView.classList.add('hidden');
    registerView.classList.add('hidden');
    mainAppView.classList.add('hidden');
    
    // 显示指定视图
    viewToShow.classList.remove('hidden');
}

// 登录处理
async function handleLogin(): Promise<void> {
    const username = loginUsername.value.trim();
    const password = loginPassword.value.trim();
    const autoLoginChecked = autoLogin.checked;
    
    if (!username || !password) {
        alert('请输入账号和密码');
        return;
    }
    
    try {
        const response = await window.electronAPI.login(username, password, autoLoginChecked);
        
        if (response.success) {
            // 登录成功处理由onUserLoggedIn事件监听器处理
            console.log('登录成功');
        } else {
            alert(`登录失败: ${response.message}`);
        }
    } catch (error) {
        console.error('登录过程中发生错误:', error);
        alert('登录过程中发生错误');
    }
}

// 注册处理
async function handleRegister(): Promise<void> {
    const username = registerUsername.value.trim();
    const password = registerPassword.value.trim();
    const email = registerEmail.value.trim();
    
    if (!username || !password) {
        alert('请输入账号和密码');
        return;
    }
    
    try {
        const response = await window.electronAPI.register(username, password);
        
        if (response.success) {
            alert('注册成功，请登录');
            // 清空注册表单
            registerUsername.value = '';
            registerPassword.value = '';
            registerEmail.value = '';
            // 切换到登录视图
            showView(loginView);
        } else {
            alert(`注册失败: ${response.message}`);
        }
    } catch (error) {
        console.error('注册过程中发生错误:', error);
        alert('注册过程中发生错误');
    }
}

// 登出处理
async function handleLogout(): Promise<void> {
    try {
        const response = await window.electronAPI.logout();
        
        if (response.success) {
            // 登出成功处理由onUserLoggedOut事件监听器处理
            console.log('登出成功');
        } else {
            alert(`登出失败: ${response.message}`);
        }
    } catch (error) {
        console.error('登出过程中发生错误:', error);
        alert('登出过程中发生错误');
    }
}

// 绑定第三方账号处理
async function handleBindThirdParty(provider: string): Promise<void> {
    try {
        // 模拟第三方授权过程
        const authData = {
            accountId: `${provider}_${Date.now()}`,
            token: `token_${Date.now()}`
        };
        
        const response = await window.electronAPI.bindThirdParty(provider, authData);
        
        if (response.success) {
            alert(`绑定${provider}账号成功`);
        } else {
            alert(`绑定${provider}账号失败: ${response.message}`);
        }
    } catch (error) {
        console.error(`绑定${provider}账号过程中发生错误:`, error);
        alert(`绑定${provider}账号过程中发生错误`);
    }
}

// 解绑第三方账号处理
async function handleUnbindThirdParty(provider: string): Promise<void> {
    try {
        const response = await window.electronAPI.unbindThirdParty(provider);
        
        if (response.success) {
            alert(`解绑${provider}账号成功`);
        } else {
            alert(`解绑${provider}账号失败: ${response.message}`);
        }
    } catch (error) {
        console.error(`解绑${provider}账号过程中发生错误:`, error);
        alert(`解绑${provider}账号过程中发生错误`);
    }
}

// 设置事件监听器
document.addEventListener('DOMContentLoaded', () => {
    // 登录按钮点击事件
    loginButton.addEventListener('click', handleLogin);
    
    // 注册按钮点击事件
    registerButton.addEventListener('click', handleRegister);
    
    // 登出按钮点击事件
    logoutButton.addEventListener('click', handleLogout);
    
    // 绑定第三方账号按钮点击事件
    bindXiaomiButton.addEventListener('click', () => handleBindThirdParty('Xiaomi'));
    bindMideaButton.addEventListener('click', () => handleBindThirdParty('Midea'));
    
    // 解绑第三方账号按钮点击事件
    unbindXiaomiButton.addEventListener('click', () => handleUnbindThirdParty('Xiaomi'));
    unbindMideaButton.addEventListener('click', () => handleUnbindThirdParty('Midea'));
    
    // 视图切换链接点击事件
    showLoginViewLink.addEventListener('click', () => showView(loginView));
    showRegisterViewLink.addEventListener('click', () => showView(registerView));
    
    // 监听用户登录事件
    window.electronAPI.onUserLoggedIn((userData) => {
        currentUser = userData;
        showView(mainAppView);
    });
    
    // 监听用户登出事件
    window.electronAPI.onUserLoggedOut(() => {
        currentUser = null;
        showView(loginView);
    });
    
    // 监听第三方账号状态更新事件
    window.electronAPI.onThirdPartyStatusUpdate((provider, status) => {
        console.log(`第三方账号状态更新: ${provider}`, status);
        
        // 根据绑定状态更新按钮状态
        if (provider === 'Xiaomi') {
            bindXiaomiButton.disabled = status.bound;
            unbindXiaomiButton.disabled = !status.bound;
        } else if (provider === 'Midea') {
            bindMideaButton.disabled = status.bound;
            unbindMideaButton.disabled = !status.bound;
        }
    });
    
    // 默认显示登录视图
    showView(loginView);
});
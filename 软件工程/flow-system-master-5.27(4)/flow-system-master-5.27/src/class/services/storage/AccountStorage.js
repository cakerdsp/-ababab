const fs = require('fs');
const path = require('path');
const { app } = require('electron');

class AccountStorage {
  constructor() {
    this.storagePrefix = 'flow_system_';
    // 确定存储目录
    this.storageDir = this.getStorageDirectory();
    this.ensureStorageDirectory();
    console.log(`Account storage directory: ${this.storageDir}`);
  }

  // 获取存储目录
  getStorageDirectory() {
    try {
      // 在主进程中使用app.getPath('userData')
      return path.join(app.getPath('userData'), 'storage');
    } catch (error) {
      // 如果在渲染进程或其他环境中，使用临时目录
      return path.join(process.cwd(), 'temp_storage');
    }
  }

  // 确保存储目录存在
  ensureStorageDirectory() {
    if (!fs.existsSync(this.storageDir)) {
      fs.mkdirSync(this.storageDir, { recursive: true });
    }
  }

  // 获取文件路径
  getFilePath(key) {
    return path.join(this.storageDir, `${this.storagePrefix}${key}.json`);
  }

  // 通用存储方法
  setItem(key, value) {
    try {
      const filePath = this.getFilePath(key);
      fs.writeFileSync(filePath, value, 'utf8');
      return true;
    } catch (error) {
      console.error(`Error saving data (${key}):`, error);
      return false;
    }
  }

  // 通用获取方法（文件）
  getItem(key) {
    try {
      const filePath = this.getFilePath(key);
      if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath, 'utf8');
      }
      return null;
    } catch (error) {
      console.error(`Error reading data (${key}):`, error);
      return null;
    }
  }

  // 通用删除方法（文件）
  removeItem(key) {
    try {
      const filePath = this.getFilePath(key);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
      return true;
    } catch (error) {
      console.error(`Error deleting data (${key}):`, error);
      return false;
    }
  }

  // 保存用户账户信息
  saveUserAccount(userAccount) {
    if (!userAccount) return false;

    const userData = {
      userId: userAccount.getUserId()
    };

    return this.setItem('user', JSON.stringify(userData));
  }

  // 获取用户账户信息
  getUserAccount() {
    const userData = this.getItem('user');
    if (!userData) return null;

    try {
      const parsedData = JSON.parse(userData);

      // 兼容旧数据：如果有username但没有userId，使用username作为userId
      if (parsedData.username && !parsedData.userId) {
        parsedData.userId = parsedData.username;
      }

      // 如果仍然没有userId，返回null
      if (!parsedData.userId) {
        return null;
      }

      return {
        userId: parsedData.userId
      };
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  }

  // 保存令牌
  saveToken(token) {
    if (!token) return false;
    return this.setItem('token', token);
  }

  // 获取令牌
  getToken() {
    return this.getItem('token');
  }

  // 保存刷新令牌
  saveRefreshToken(refreshToken) {
    if (!refreshToken) return false;
    return this.setItem('refresh_token', refreshToken);
  }

  // 获取刷新令牌
  getRefreshToken() {
    return this.getItem('refresh_token');
  }

  // 保存SSE连接ID
  saveSseConnectionId(sseConnectionId) {
    if (!sseConnectionId) return false;
    return this.setItem('sse_connection_id', sseConnectionId);
  }

  // 获取SSE连接ID
  getSseConnectionId() {
    return this.getItem('sse_connection_id');
  }

  // 保存登录凭据（用于自动登录）
  saveLoginCredentials(userId, rememberMe = false) {
    if (!userId) return false;

    const credentials = {
      userId: userId,
      rememberMe: rememberMe,
      lastLoginTime: new Date().getTime()
    };

    return this.setItem('credentials', JSON.stringify(credentials));
  }

  // 获取登录凭据
  getLoginCredentials() {
    const credentialsData = this.getItem('credentials');
    if (!credentialsData) return null;

    try {
      const credentials = JSON.parse(credentialsData);
      // 检查是否过期（30天）
      const now = new Date().getTime();
      const thirtyDays = 30 * 24 * 60 * 60 * 1000;

      if (credentials.rememberMe && (now - credentials.lastLoginTime) < thirtyDays) {
        return credentials;
      } else if (!credentials.rememberMe && (now - credentials.lastLoginTime) < 24 * 60 * 60 * 1000) {
        // 未勾选记住我，但24小时内
        return credentials;
      }

      // 过期则清除
      this.clearLoginCredentials();
      return null;
    } catch (error) {
      console.error('Error parsing login credentials:', error);
      return null;
    }
  }

  // 清除登录凭据
  clearLoginCredentials() {
    return this.removeItem('credentials');
  }

  // 保存支持的品牌
  saveSupportedBrands(brands) {
    if (!brands) return false;
    return this.setItem('brands', JSON.stringify(brands));
  }

  // 获取支持的品牌
  getSupportedBrands() {
    const brandsData = this.getItem('brands');
    if (!brandsData) return {};

    try {
      return JSON.parse(brandsData);
    } catch (error) {
      console.error('Error parsing brand data:', error);
      return {};
    }
  }

  // 保存应用设置
  saveAppSettings(settings) {
    if (!settings) return false;
    return this.setItem('settings', JSON.stringify(settings));
  }

  // 获取应用设置
  getAppSettings() {
    const settingsData = this.getItem('settings');
    if (!settingsData) return { autoLogin: false, rememberMe: false };

    try {
      return JSON.parse(settingsData);
    } catch (error) {
      console.error('Error parsing application settings:', error);
      return { autoLogin: false, rememberMe: false };
    }
  }

  // 清除用户数据
  clearUserData() {
    this.removeItem('user');
    this.removeItem('token');
    this.removeItem('refresh_token');
    this.removeItem('sse_connection_id');
    this.removeItem('brands');
    this.clearLoginCredentials();
    return true;
  }

  // 检查是否有有效的登录状态
  hasValidSession() {
    const userAccount = this.getUserAccount();
    const credentials = this.getLoginCredentials();
    const refreshToken = this.getRefreshToken();

    // 必须有用户账户、有效的登录凭据和刷新令牌
    return !!(userAccount && credentials && refreshToken);
  }
}

module.exports = AccountStorage;

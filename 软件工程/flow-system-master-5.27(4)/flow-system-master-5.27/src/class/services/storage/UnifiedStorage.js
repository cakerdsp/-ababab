const fs = require('fs');
const path = require('path');
const { app } = require('electron');

class UnifiedStorage {
  constructor() {
    this.storagePrefix = 'flow_system_';
    // 确定存储目录
    this.storageDir = this.getStorageDirectory();
    this.ensureStorageDirectory();

    // 缓存机制
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存

    console.log(`Unified storage directory: ${this.storageDir}`);
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
  setItem(key, value, useCache = true) {
    try {
      const filePath = this.getFilePath(key);
      const jsonValue = typeof value === 'string' ? value : JSON.stringify(value);

      fs.writeFileSync(filePath, jsonValue, 'utf8');

      // 更新缓存
      if (useCache) {
        this.cache.set(key, {
          data: value,
          timestamp: Date.now()
        });
      }

      return true;
    } catch (error) {
      console.error(`存储数据错误 (${key}):`, error);
      return false;
    }
  }

  // 通用获取方法
  getItem(key, useCache = true) {
    try {
      // 先检查缓存
      if (useCache && this.cache.has(key)) {
        const cached = this.cache.get(key);
        if (Date.now() - cached.timestamp < this.cacheTimeout) {
          return cached.data;
        } else {
          this.cache.delete(key);
        }
      }

      const filePath = this.getFilePath(key);
      if (fs.existsSync(filePath)) {
        const data = fs.readFileSync(filePath, 'utf8');

        // 尝试解析JSON，如果失败则返回原始字符串
        let parsedData;
        try {
          parsedData = JSON.parse(data);
        } catch {
          parsedData = data;
        }

        // 更新缓存
        if (useCache) {
          this.cache.set(key, {
            data: parsedData,
            timestamp: Date.now()
          });
        }

        return parsedData;
      }
      return null;
    } catch (error) {
      console.error(`读取数据错误 (${key}):`, error);
      return null;
    }
  }

  // 通用删除方法
  removeItem(key) {
    try {
      const filePath = this.getFilePath(key);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }

      // 删除缓存
      this.cache.delete(key);
      return true;
    } catch (error) {
      console.error(`删除数据错误 (${key}):`, error);
      return false;
    }
  }

  // 清除缓存
  clearCache() {
    this.cache.clear();
  }

  // ==================== 用户账户相关 ====================

  // 保存用户账户信息
  saveUserAccount(userAccount) {
    if (!userAccount) return false;

    const userData = {
      userId: userAccount.getUserId(),
      lastLoginTime: new Date().toISOString()
    };

    return this.setItem('user', userData);
  }

  // 获取用户账户信息
  getUserAccount() {
    const userData = this.getItem('user');
    if (!userData) return null;

    try {
      // 兼容旧数据
      if (typeof userData === 'string') {
        const parsedData = JSON.parse(userData);
        if (parsedData.username && !parsedData.userId) {
          parsedData.userId = parsedData.username;
        }
        if (!parsedData.userId) return null;
        return { userId: parsedData.userId };
      }

      if (!userData.userId) return null;
      return userData;
    } catch (error) {
      console.error('解析用户数据错误:', error);
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

  // 保存登录凭据
  saveLoginCredentials(userId, rememberMe = false) {
    if (!userId) return false;

    const credentials = {
      userId: userId,
      rememberMe: rememberMe,
      lastLoginTime: new Date().getTime()
    };

    return this.setItem('credentials', credentials);
  }

  // 获取登录凭据
  getLoginCredentials() {
    const credentials = this.getItem('credentials');
    if (!credentials) return null;

    try {
      const now = new Date().getTime();
      const thirtyDays = 30 * 24 * 60 * 60 * 1000;

      if (credentials.rememberMe && (now - credentials.lastLoginTime) < thirtyDays) {
        return credentials;
      } else if (!credentials.rememberMe && (now - credentials.lastLoginTime) < 24 * 60 * 60 * 1000) {
        return credentials;
      }

      this.clearLoginCredentials();
      return null;
    } catch (error) {
      console.error('解析登录凭据错误:', error);
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
    return this.setItem('brands', brands);
  }

  // 获取支持的品牌
  getSupportedBrands() {
    const brands = this.getItem('brands');
    return brands || {};
  }

  // 保存应用设置
  saveAppSettings(settings) {
    if (!settings) return false;
    return this.setItem('settings', settings);
  }

  // 获取应用设置
  getAppSettings() {
    const settings = this.getItem('settings');
    return settings || { autoLogin: false, rememberMe: false };
  }

  // ==================== 设备相关 ====================

  // 保存设备列表
  saveDevices(devices) {
    if (!devices) return false;

    const deviceData = {
      devices: devices,
      lastUpdated: new Date().toISOString(),
      count: devices.length
    };

    return this.setItem('devices', deviceData);
  }

  // 获取设备列表
  getDevices() {
    const deviceData = this.getItem('devices');
    if (!deviceData) return null;

    return deviceData.devices || [];
  }

  // 获取设备最后更新时间
  getDevicesLastUpdated() {
    const deviceData = this.getItem('devices');
    return deviceData ? deviceData.lastUpdated : null;
  }

  // 保存特定设备状态
  saveDeviceState(deviceId, state) {
    if (!deviceId || !state) return false;

    const stateData = {
      ...state,
      lastUpdated: new Date().toISOString()
    };

    return this.setItem(`device_${deviceId}`, stateData);
  }

  // 获取特定设备状态
  getDeviceState(deviceId) {
    if (!deviceId) return null;
    return this.getItem(`device_${deviceId}`);
  }

  // ==================== 应用状态相关 ====================

  // 保存应用状态
  saveAppState(state) {
    if (!state) return false;

    const appState = {
      ...state,
      lastUpdated: new Date().toISOString()
    };

    return this.setItem('app_state', appState);
  }

  // 获取应用状态
  getAppState() {
    const state = this.getItem('app_state');
    return state || {};
  }

  // 保存页面状态
  savePageState(pageName, state) {
    if (!pageName || !state) return false;

    const pageState = {
      ...state,
      lastUpdated: new Date().toISOString()
    };

    return this.setItem(`page_${pageName}`, pageState);
  }

  // 获取页面状态
  getPageState(pageName) {
    if (!pageName) return null;
    return this.getItem(`page_${pageName}`);
  }

  // ==================== 传感器数据相关 ====================

  // 保存传感器历史数据
  saveSensorHistory(deviceId, metricType, data) {
    if (!deviceId || !metricType || !data) return false;

    const historyData = {
      deviceId,
      metricType,
      data,
      lastUpdated: new Date().toISOString()
    };

    return this.setItem(`sensor_${deviceId}_${metricType}`, historyData);
  }

  // 获取传感器历史数据
  getSensorHistory(deviceId, metricType) {
    if (!deviceId || !metricType) return null;
    return this.getItem(`sensor_${deviceId}_${metricType}`);
  }

  // ==================== 数据清理相关 ====================

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

  // 清除设备数据
  clearDeviceData() {
    this.removeItem('devices');
    // 清除所有单个设备状态
    const files = fs.readdirSync(this.storageDir);
    files.forEach(file => {
      if (file.startsWith(`${this.storagePrefix}device_`) && file.endsWith('.json')) {
        const filePath = path.join(this.storageDir, file);
        fs.unlinkSync(filePath);
      }
    });
    return true;
  }

  // 清除传感器数据
  clearSensorData() {
    const files = fs.readdirSync(this.storageDir);
    files.forEach(file => {
      if (file.startsWith(`${this.storagePrefix}sensor_`) && file.endsWith('.json')) {
        const filePath = path.join(this.storageDir, file);
        fs.unlinkSync(filePath);
      }
    });
    return true;
  }

  // ==================== 设备分组相关 ====================

  // 保存设备分组数据
  saveDeviceGroups(groups) {
    if (!groups || !Array.isArray(groups)) return false;

    const groupData = {
      groups: groups,
      lastUpdated: new Date().toISOString(),
      count: groups.length
    };

    return this.setItem('device_groups', groupData);
  }

  // 获取设备分组数据
  getDeviceGroups() {
    const groupData = this.getItem('device_groups');
    if (!groupData) return [];

    try {
      // 兼容性处理
      if (Array.isArray(groupData)) {
        return groupData;
      }

      if (groupData.groups && Array.isArray(groupData.groups)) {
        return groupData.groups;
      }

      return [];
    } catch (error) {
      console.error('解析设备分组数据错误:', error);
      return [];
    }
  }

  // 获取设备分组最后更新时间
  getDeviceGroupsLastUpdated() {
    const groupData = this.getItem('device_groups');
    return groupData && groupData.lastUpdated ? groupData.lastUpdated : null;
  }

  // 保存单个设备分组
  saveDeviceGroup(groupId, groupData) {
    if (!groupId || !groupData) return false;
    return this.setItem(`device_group_${groupId}`, groupData);
  }

  // 获取单个设备分组
  getDeviceGroup(groupId) {
    if (!groupId) return null;
    return this.getItem(`device_group_${groupId}`);
  }

  // 删除设备分组数据
  clearDeviceGroups() {
    try {
      // 删除主分组文件
      this.removeItem('device_groups');

      // 删除所有单个分组文件
      const files = fs.readdirSync(this.storageDir);
      const groupFiles = files.filter(file => 
        file.startsWith(`${this.storagePrefix}device_group_`) && file.endsWith('.json')
      );

      groupFiles.forEach(file => {
        fs.unlinkSync(path.join(this.storageDir, file));
      });

      console.log('Device group data cleared');
      return true;
    } catch (error) {
      console.error('清除设备分组数据错误:', error);
      return false;
    }
  }

  // 清除所有数据
  clearAllData() {
    this.clearUserData();
    this.clearDeviceData();
    this.clearSensorData();
    this.clearDeviceGroups();
    this.removeItem('app_state');

    // 清除所有页面状态
    const files = fs.readdirSync(this.storageDir);
    files.forEach(file => {
      if (file.startsWith(`${this.storagePrefix}page_`) && file.endsWith('.json')) {
        const filePath = path.join(this.storageDir, file);
        fs.unlinkSync(filePath);
      }
    });

    this.clearCache();
    return true;
  }

  // 彻底清除整个存储目录（登出时使用）
  clearAllDataCompletely() {
    try {
      console.log(`Starting thorough cleanup of storage directory: ${this.storageDir}`);

      // 1. 清除内存缓存
      this.clearCache();

      // 2. 删除所有存储目录下的文件
      if (fs.existsSync(this.storageDir)) {
        const files = fs.readdirSync(this.storageDir);
        let deletedCount = 0;
        let failedCount = 0;

        files.forEach(file => {
          try {
            const filePath = path.join(this.storageDir, file);
            const stat = fs.statSync(filePath);

            if (stat.isFile()) {
              fs.unlinkSync(filePath);
              deletedCount++;
              console.log(`File deleted: ${file}`);
            } else if (stat.isDirectory()) {
              // 递归删除子目录
              fs.rmSync(filePath, { recursive: true, force: true });
              deletedCount++;
              console.log(`Directory deleted: ${file}`);
            }
          } catch (error) {
            failedCount++;
            console.error(`删除文件失败: ${file}`, error.message);
          }
        });

        console.log(`File cleanup completed: successfully deleted ${deletedCount}, failed ${failedCount}`);

        // 3. 尝试删除存储目录本身（如果为空）
        try {
          const remainingFiles = fs.readdirSync(this.storageDir);
          if (remainingFiles.length === 0) {
            fs.rmdirSync(this.storageDir);
            console.log('Storage directory deleted');
          } else {
            console.log(`Storage directory still has ${remainingFiles.length} files, keeping directory`);
          }
        } catch (error) {
          console.log('Storage directory deletion failed or does not exist:', error.message);
        }

        return {
          success: true,
          deletedFiles: deletedCount,
          failedFiles: failedCount,
          message: '存储目录清理完成'
        };
      } else {
        console.log('Storage directory does not exist, no cleanup needed');
        return {
          success: true,
          deletedFiles: 0,
          failedFiles: 0,
          message: '存储目录不存在'
        };
      }
    } catch (error) {
      console.error('彻底清理存储目录失败:', error);
      return {
        success: false,
        deletedFiles: 0,
        failedFiles: 0,
        message: `清理失败: ${error.message}`,
        error: error.message
      };
    }
  }

  // ==================== 工具方法 ====================

  // 检查是否有有效的登录状态
  hasValidSession() {
    const userAccount = this.getUserAccount();
    const credentials = this.getLoginCredentials();
    const refreshToken = this.getRefreshToken();

    return !!(userAccount && credentials && refreshToken);
  }

  // 获取存储统计信息
  getStorageStats() {
    const stats = {
      totalFiles: 0,
      totalSize: 0,
      categories: {
        user: 0,
        devices: 0,
        sensors: 0,
        pages: 0,
        other: 0
      }
    };

    try {
      const files = fs.readdirSync(this.storageDir);

      files.forEach(file => {
        if (file.startsWith(this.storagePrefix) && file.endsWith('.json')) {
          stats.totalFiles++;

          const filePath = path.join(this.storageDir, file);
          const stat = fs.statSync(filePath);
          stats.totalSize += stat.size;

          // 分类统计
          if (file.includes('user') || file.includes('token') || file.includes('credentials')) {
            stats.categories.user++;
          } else if (file.includes('device')) {
            stats.categories.devices++;
          } else if (file.includes('sensor')) {
            stats.categories.sensors++;
          } else if (file.includes('page_')) {
            stats.categories.pages++;
          } else {
            stats.categories.other++;
          }
        }
      });
    } catch (error) {
      console.error('获取存储统计信息失败:', error);
    }

    return stats;
  }

  // 导出数据
  exportData() {
    const data = {};

    try {
      const files = fs.readdirSync(this.storageDir);

      files.forEach(file => {
        if (file.startsWith(this.storagePrefix) && file.endsWith('.json')) {
          const key = file.replace(this.storagePrefix, '').replace('.json', '');
          const filePath = path.join(this.storageDir, file);
          const content = fs.readFileSync(filePath, 'utf8');

          try {
            data[key] = JSON.parse(content);
          } catch {
            data[key] = content;
          }
        }
      });
    } catch (error) {
      console.error('导出数据失败:', error);
    }

    return data;
  }

  // 导入数据
  importData(data) {
    if (!data || typeof data !== 'object') return false;

    try {
      Object.keys(data).forEach(key => {
        this.setItem(key, data[key], false); // 不使用缓存
      });

      this.clearCache(); // 清除缓存以强制重新读取
      return true;
    } catch (error) {
      console.error('导入数据失败:', error);
      return false;
    }
  }
}

module.exports = UnifiedStorage;

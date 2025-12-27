const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class StateManager {
  constructor() {
    this.storage = new UnifiedStorage();
    this.listeners = new Map(); // 状态变化监听器
    this.currentState = {}; // 当前状态缓存
    this.isInitialized = false;

    // 初始化状态
    this.initializeState();
  }

  // 初始化状态
  initializeState() {
    try {
      // 从本地存储加载状态
      this.currentState = {
        user: this.storage.getUserAccount(),
        devices: this.storage.getDevices() || [],
        appSettings: this.storage.getAppSettings(),
        brands: this.storage.getSupportedBrands(),
        appState: this.storage.getAppState(),
        loginCredentials: this.storage.getLoginCredentials()
      };

      this.isInitialized = true;
      console.log('State manager initialized successfully');
    } catch (error) {
      console.error('State manager initialization failed:', error);
    }
  }

  // ==================== 状态监听相关 ====================

  // 添加状态变化监听器
  addListener(stateKey, callback) {
    if (!this.listeners.has(stateKey)) {
      this.listeners.set(stateKey, new Set());
    }
    this.listeners.get(stateKey).add(callback);

    // 立即触发一次，传递当前状态
    if (this.currentState[stateKey] !== undefined) {
      callback(this.currentState[stateKey]);
    }
  }

  // 移除状态变化监听器
  removeListener(stateKey, callback) {
    if (this.listeners.has(stateKey)) {
      this.listeners.get(stateKey).delete(callback);
    }
  }

  // 通知状态变化
  notifyStateChange(stateKey, newValue) {
    if (this.listeners.has(stateKey)) {
      this.listeners.get(stateKey).forEach(callback => {
        try {
          callback(newValue);
        } catch (error) {
          console.error(`State listener execution failed (${stateKey}):`, error);
        }
      });
    }
  }

  // ==================== 状态更新方法 ====================

  // 更新用户状态
  updateUserState(userData) {
    this.currentState.user = userData;
    this.storage.saveUserAccount(userData);
    this.notifyStateChange('user', userData);
  }

  // 更新设备列表状态
  updateDevicesState(devices) {
    this.currentState.devices = devices;
    this.storage.saveDevices(devices);
    this.notifyStateChange('devices', devices);
  }

  // 更新单个设备状态
  updateDeviceState(deviceId, deviceState) {
    // 更新设备列表中的设备状态
    const devices = [...this.currentState.devices];
    const deviceIndex = devices.findIndex(d => d.did === deviceId);

    if (deviceIndex !== -1) {
      devices[deviceIndex] = { ...devices[deviceIndex], ...deviceState };
      this.updateDevicesState(devices);
    }

    // 保存单个设备状态
    this.storage.saveDeviceState(deviceId, deviceState);
    this.notifyStateChange(`device_${deviceId}`, deviceState);
  }

  // 更新应用设置
  updateAppSettings(settings) {
    this.currentState.appSettings = { ...this.currentState.appSettings, ...settings };
    this.storage.saveAppSettings(this.currentState.appSettings);
    this.notifyStateChange('appSettings', this.currentState.appSettings);
  }

  // 更新品牌绑定状态
  updateBrandsState(brands) {
    this.currentState.brands = brands;
    this.storage.saveSupportedBrands(brands);
    this.notifyStateChange('brands', brands);
  }

  // 更新应用状态
  updateAppState(appState) {
    this.currentState.appState = { ...this.currentState.appState, ...appState };
    this.storage.saveAppState(this.currentState.appState);
    this.notifyStateChange('appState', this.currentState.appState);
  }

  // 更新页面状态
  updatePageState(pageName, pageState) {
    const stateKey = `page_${pageName}`;
    this.currentState[stateKey] = pageState;
    this.storage.savePageState(pageName, pageState);
    this.notifyStateChange(stateKey, pageState);
  }

  // ==================== 状态获取方法 ====================

  // 获取当前状态
  getCurrentState() {
    return { ...this.currentState };
  }

  // 获取用户状态
  getUserState() {
    return this.currentState.user;
  }

  // 获取设备列表状态
  getDevicesState() {
    return this.currentState.devices || [];
  }

  // 获取单个设备状态
  getDeviceState(deviceId) {
    // 先从设备列表中查找
    const device = this.currentState.devices?.find(d => d.did === deviceId);
    if (device) {
      return device;
    }

    // 如果没找到，从存储中获取
    return this.storage.getDeviceState(deviceId);
  }

  // 获取应用设置
  getAppSettings() {
    return this.currentState.appSettings || { autoLogin: false, rememberMe: false };
  }

  // 获取品牌绑定状态
  getBrandsState() {
    return this.currentState.brands || {};
  }

  // 获取应用状态
  getAppState() {
    return this.currentState.appState || {};
  }

  // 获取页面状态
  getPageState(pageName) {
    const stateKey = `page_${pageName}`;
    if (this.currentState[stateKey]) {
      return this.currentState[stateKey];
    }

    // 从存储中获取
    const pageState = this.storage.getPageState(pageName);
    if (pageState) {
      this.currentState[stateKey] = pageState;
    }

    return pageState;
  }

  // ==================== 状态同步方法 ====================

  // 从存储同步所有状态
  syncFromStorage() {
    try {
      const newState = {
        user: this.storage.getUserAccount(),
        devices: this.storage.getDevices() || [],
        appSettings: this.storage.getAppSettings(),
        brands: this.storage.getSupportedBrands(),
        appState: this.storage.getAppState(),
        loginCredentials: this.storage.getLoginCredentials()
      };

      // 比较状态变化并通知监听器
      Object.keys(newState).forEach(key => {
        if (JSON.stringify(this.currentState[key]) !== JSON.stringify(newState[key])) {
          this.currentState[key] = newState[key];
          this.notifyStateChange(key, newState[key]);
        }
      });

      console.log('State synchronization complete');
      return true;
    } catch (error) {
      console.error('State synchronization failed:', error);
      return false;
    }
  }

  // 将当前状态同步到存储
  syncToStorage() {
    try {
      if (this.currentState.user) {
        this.storage.saveUserAccount(this.currentState.user);
      }

      if (this.currentState.devices) {
        this.storage.saveDevices(this.currentState.devices);
      }

      if (this.currentState.appSettings) {
        this.storage.saveAppSettings(this.currentState.appSettings);
      }

      if (this.currentState.brands) {
        this.storage.saveSupportedBrands(this.currentState.brands);
      }

      if (this.currentState.appState) {
        this.storage.saveAppState(this.currentState.appState);
      }

      console.log('State saved successfully');
      return true;
    } catch (error) {
      console.error('Failed to save state:', error);
      return false;
    }
  }

  // ==================== 认证状态相关 ====================

  // 检查登录状态
  isLoggedIn() {
    return !!(this.currentState.user && this.storage.getToken());
  }

  // 检查是否有有效会话
  hasValidSession() {
    return this.storage.hasValidSession();
  }

  // 登出时清理状态
  logout() {
    // 清理状态
    this.currentState.user = null;
    this.currentState.brands = {};
    this.currentState.loginCredentials = null;

    // 清理存储
    this.storage.clearUserData();

    // 通知监听器
    this.notifyStateChange('user', null);
    this.notifyStateChange('brands', {});
    this.notifyStateChange('loginCredentials', null);

    console.log('User state cleared');
  }

  // ==================== 设备状态相关 ====================

  // 添加设备
  addDevice(device) {
    const devices = [...this.getDevicesState()];
    const existingIndex = devices.findIndex(d => d.did === device.did);

    if (existingIndex !== -1) {
      // 更新现有设备
      devices[existingIndex] = device;
    } else {
      // 添加新设备
      devices.push(device);
    }

    this.updateDevicesState(devices);
  }

  // 移除设备
  removeDevice(deviceId) {
    const devices = this.getDevicesState().filter(d => d.did !== deviceId);
    this.updateDevicesState(devices);

    // 删除单个设备状态
    this.storage.removeItem(`device_${deviceId}`);
  }

  // 批量更新设备状态
  batchUpdateDevices(deviceUpdates) {
    const devices = [...this.getDevicesState()];
    let hasChanges = false;

    deviceUpdates.forEach(update => {
      const deviceIndex = devices.findIndex(d => d.did === update.did);
      if (deviceIndex !== -1) {
        devices[deviceIndex] = { ...devices[deviceIndex], ...update };
        hasChanges = true;
      }
    });

    if (hasChanges) {
      this.updateDevicesState(devices);
    }
  }

  // ==================== 页面状态辅助方法 ====================

  // 保存页面表单状态
  saveFormState(pageName, formName, formData) {
    const pageState = this.getPageState(pageName) || {};
    pageState.forms = pageState.forms || {};
    pageState.forms[formName] = formData;

    this.updatePageState(pageName, pageState);
  }

  // 获取页面表单状态
  getFormState(pageName, formName) {
    const pageState = this.getPageState(pageName);
    return pageState?.forms?.[formName] || null;
  }

  // 保存页面UI状态
  saveUIState(pageName, uiState) {
    const pageState = this.getPageState(pageName) || {};
    pageState.ui = { ...pageState.ui, ...uiState };

    this.updatePageState(pageName, pageState);
  }

  // 获取页面UI状态
  getUIState(pageName) {
    const pageState = this.getPageState(pageName);
    return pageState?.ui || {};
  }

  // ==================== 工具方法 ====================

  // 重置所有状态
  reset() {
    this.currentState = {};
    this.listeners.clear();
    this.storage.clearAllData();
    this.isInitialized = false;
    this.initializeState();
    console.log('State manager has been reset.');
  }

  // 获取状态统计信息
  getStateStats() {
    const storageStats = this.storage.getStorageStats();

    return {
      totalKeys: Object.keys(this.currentState).length,
      listenerCount: Array.from(this.listeners.values()).reduce((acc, set) => acc + set.size, 0),
      lastSync: this.currentState.appState?.lastSync || 'N/A'
    };
  }

  // 导出状态数据
  exportStateData() {
    const exportData = {
      currentState: this.getCurrentState(),
      storageData: this.storage.exportData(),
      stats: this.getStateStats()
    };

    return {
      success: true,
      data: exportData
    };
  }

  // 导入状态数据
  importStateData(data) {
    try {
      if (data) {
        this.storage.importData(data);
        this.syncFromStorage(); // 导入后同步状态
        console.log('State data imported successfully');
        return { success: true };
      }
      return { success: false, message: 'No data provided' };
    } catch (error) {
      console.error('Failed to import state data:', error);
      return { success: false, message: error.message };
    }
  }
}

module.exports = StateManager;

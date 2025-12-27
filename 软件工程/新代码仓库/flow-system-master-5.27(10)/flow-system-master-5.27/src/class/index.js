// class/index.js - 重构后的设备管理系统

// ==================== 导入新架构的类 ====================
// Domain层 - 数据模型
const UserAccount = require('./domain/account/UserAccount');
const SupportedBrand = require('./domain/account/SupportedBrand');
const Device = require('./domain/device/Device');

// 架构管理器
const SystemManager = require('./modules/SystemManager');

// 新的设备管理器
const DeviceSSEManager = require('./modules/device/DeviceSSEManager');
const DeviceStorageManager = require('./modules/device/DeviceStorageManager');
const DeviceGroupAPIManager = require('./modules/device/DeviceGroupAPIManager');

// 数据分析器
const SensorDataAnalyzer = require('./modules/data/SensorDataAnalyzer');

// Account相关管理器
const AccountManager = require('./modules/account/AccountManager');

// Services层 - 基础设施服务
const AccountAPIRegistry = require('./services/api/AccountAPIRegistry');
const AccountStorage = require('./services/storage/AccountStorage');
const UnifiedStorage = require('./services/storage/UnifiedStorage');
const SSEService = require('./services/sse/SSEService');

// ==================== 创建管理器实例 ====================
// 创建账户管理器实例
const accountManager = new AccountManager();

// 创建系统管理器实例（新的统一入口）
const systemManager = new SystemManager();

// 设置系统管理器的API注册器和AccountManager关联
systemManager.setApiRegistry(accountManager.apiRegistry);
systemManager.setAccountManager(accountManager);

// ==================== 向后兼容的包装器 ====================
// 为了保持向后兼容性，创建一个包装器来模拟原来的deviceController接口
const deviceController = {
  // 代理到SystemManager的方法
  async initialize(userId) {
    return await systemManager.initialize(userId);
  },

  setApiRegistry(apiRegistry) {
    systemManager.setApiRegistry(apiRegistry);
  },

  // 设备状态相关方法
  getAllDevices() {
    return systemManager.getAllDevices();
  },

  getDevicesByBrand(brand) {
    return systemManager.getDevicesByBrand(brand);
  },

  getControllableDevices() {
    return systemManager.getControllableDevices();
  },

  getSensorDevices() {
    return systemManager.getSensorDevices();
  },

  // 设备控制相关方法
  getDeviceControlOptions(did) {
    return systemManager.getDeviceControlOptions(did);
  },

  async controlDevice(did, operation, value) {
    return await systemManager.controlDevice(did, operation, value);
  },

  // 历史数据相关方法
  getSensorHistory(deviceId, metricType) {
    return systemManager.getSensorHistory(deviceId, metricType);
  },

  getAllSensorHistory() {
    return systemManager.getAllSensorHistory();
  },

  analyzeEnvironmentData(deviceIds = []) {
    return systemManager.analyzeEnvironmentData(deviceIds);
  },

  // 系统操作
  async refreshDevices() {
    return await systemManager.refreshDevices();
  },

  async refreshSensorHistory() {
    return await systemManager.refreshSensorHistory();
  },

  async refreshAllData() {
    return await systemManager.refreshAllData();
  },

  getSystemStatus() {
    return systemManager.getSystemStatus();
  },

  async reconnectSSE() {
    return await systemManager.reconnectSSE();
  },

  async logout() {
    return await systemManager.logout();
  },

  reset() {
    systemManager.reset();
  },

  registerSSEHandler(type, handler) {
    systemManager.registerSSEHandler(type, handler);
  },

  unregisterSSEHandler(type, handler) {
    systemManager.unregisterSSEHandler(type, handler);
  }
};

// ==================== 向后兼容的状态管理器 ====================
const stateManager = {
  // 代理到SystemManager获取状态
  getState() {
    return systemManager.getSystemStatus();
  },

  // 获取设备状态
  getDevicesState() {
    return systemManager.getAllDevices();
  },

  // 其他状态管理方法可以根据需要添加
};

// ==================== 导出接口 ====================
module.exports = {
  // ==================== 主要管理器实例（向后兼容） ====================
  stateManager,
  accountManager,
  deviceController, // 这是包装后的兼容接口

  // ==================== 新架构的管理器实例 ====================
  systemManager, // 新的统一系统管理器
  
  // 获取单独的管理器实例（用于高级操作）
  getSSEService: () => systemManager.getManagers().sseService,

  // ==================== Domain层类（供其他模块使用） ====================
  UserAccount,
  SupportedBrand,
  Device,

  // ==================== Modules层类 ====================
  // 系统管理器
  SystemManager,

  // 设备管理器类
  DeviceSSEManager,
  DeviceStorageManager,
  DeviceGroupAPIManager,

  // 数据分析器类
  SensorDataAnalyzer,

  // 账户管理相关
  AccountManager,

  // ==================== Services层类 ====================
  AccountAPIRegistry,
  AccountStorage,
  UnifiedStorage,
  SSEService,

  // ==================== 便捷方法 ====================
  // 设备相关便捷方法
  device: {
    getAll: () => systemManager.getAllDevices(),
    getByBrand: (brand) => systemManager.getDevicesByBrand(brand),
    getControllable: () => systemManager.getControllableDevices(),
    getSensors: () => systemManager.getSensorDevices(),
    getStatus: (did) => systemManager.getDeviceStatus(did),
    control: (did, operation, value) => systemManager.controlDevice(did, operation, value),
    refresh: () => systemManager.refreshDevices()
  },

  // 分组相关便捷方法
  group: {
    getAll: () => systemManager.getAllGroups(),
    get: (groupId) => systemManager.getGroup(groupId),
    create: (groupData) => systemManager.createGroup(groupData),
    update: (groupId, updateData) => systemManager.updateGroup(groupId, updateData),
    delete: (groupId) => systemManager.deleteGroup(groupId),
    addDevice: (groupId, deviceId) => systemManager.addDeviceToGroup(groupId, deviceId),
    removeDevice: (groupId, deviceId) => systemManager.removeDeviceFromGroup(groupId, deviceId),
    // 注意：批量控制等高级功能请直接使用相应的管理器
  },

  // 历史数据相关便捷方法
  history: {
    getSensor: (deviceId, metricType) => systemManager.getSensorHistory(deviceId, metricType),
    getAll: () => systemManager.getAllSensorHistory(),
    getDevice: (deviceId) => systemManager.getDeviceHistoryData(deviceId),
    analyze: (deviceIds) => systemManager.analyzeEnvironmentData(deviceIds),
    // 注意：环境报告生成请使用SensorDataAnalyzer,
    refresh: () => systemManager.refreshSensorHistory()
  },

  // 系统相关便捷方法
  system: {
    initialize: (userId) => systemManager.initialize(userId),
    getStatus: () => systemManager.getSystemStatus(),
    refreshAll: () => systemManager.refreshAllData(),
    logout: () => systemManager.logout(),
    reset: () => systemManager.reset(),
    export: () => systemManager.exportSystemData()
  },

  // 设备管理相关便捷方法（通过AccountManager访问）
  deviceManagement: {
    // 获取设备管理器实例
    getManagers: () => accountManager.getDeviceManagers(),
    
    // 设备存储相关
    storage: {
      getAllDevices: () => accountManager.getDeviceManagers().storageManager.getAllDevices(),
      getDevice: (did) => accountManager.getDeviceManagers().storageManager.getDevice(did),
      getDevicesByGroup: (groupId) => accountManager.getDeviceManagers().storageManager.getDevicesByGroup(groupId),
      getDevicesByBrand: (brand) => accountManager.getDeviceManagers().storageManager.getDevicesByBrand(brand),
      getDeviceStats: () => accountManager.getDeviceManagers().storageManager.getDeviceStats(),
      setDeviceGroup: (did, groupId) => accountManager.getDeviceManagers().storageManager.setDeviceGroup(did, groupId)
    },

    // 分组API相关
    groups: {
      getAll: () => accountManager.getDeviceManagers().groupAPIManager.getAllGroups(),
      get: (gid) => accountManager.getDeviceManagers().groupAPIManager.getGroup(gid),
      create: (gname) => accountManager.getDeviceManagers().groupAPIManager.createGroup(gname),
      delete: (gid) => accountManager.getDeviceManagers().groupAPIManager.deleteGroup(gid),
      setDeviceGroup: (deviceId, groupId) => accountManager.getDeviceManagers().groupAPIManager.setDeviceGroup(deviceId, groupId),
      getStats: () => accountManager.getDeviceManagers().groupAPIManager.getGroupStats(),
      refresh: () => accountManager.getDeviceManagers().groupAPIManager.refreshGroups()
    },

    // SSE连接相关
    sse: {
      getStatus: () => accountManager.getDeviceManagers().sseManager.getConnectionStatus(),
      reconnect: () => accountManager.getDeviceManagers().sseManager.reconnect(),
      registerHandler: (eventType, handler) => accountManager.getDeviceManagers().sseManager.registerEventHandler(eventType, handler),
      unregisterHandler: (eventType, handler) => accountManager.getDeviceManagers().sseManager.unregisterEventHandler(eventType, handler)
    },

    // 数据分析相关
    analysis: {
      analyzeGroup: (groupId) => accountManager.getDeviceManagers().dataAnalyzer.analyzeGroupSensorData(groupId),
      analyzeMultipleGroups: (groupIds) => accountManager.getDeviceManagers().dataAnalyzer.analyzeMultipleGroups(groupIds),
      getSupportedSensorTypes: () => accountManager.getDeviceManagers().dataAnalyzer.getSupportedSensorTypes(),
      exportResult: (result) => accountManager.getDeviceManagers().dataAnalyzer.exportAnalysisResult(result)
    }
  }
};

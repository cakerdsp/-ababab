// class/index.js - Refactored device management system

const { app } = require('electron');
const path = require('path');
const fs = require('fs');

// ==================== Debug Mode Initialization ====================
// This code block is executed first, before the application service layer is initialized
const UnifiedStorage = require('./services/storage/UnifiedStorage');

const userDataPath = app.getPath('userData');
const debugFlagPath = path.join(userDataPath, 'debug_mode.flag');

console.log('[Startup] Checking for debug mode flag at:', debugFlagPath);

if (fs.existsSync(debugFlagPath)) {
  console.log('[Startup] Debug mode flag found. Enabling offline storage mode.');
  const projectRoot = app.getAppPath();
  const debugStoragePath = path.join(projectRoot, 'debug-storage');

  console.log(`[Startup] Setting storage directory to: ${debugStoragePath}`);
  UnifiedStorage.setStorageDirectory(debugStoragePath);

  // Ensure the storage directory exists
  if (!fs.existsSync(debugStoragePath)) {
    console.log('[Startup] Creating debug storage directory.');
    fs.mkdirSync(debugStoragePath, { recursive: true });
  }

  // Delete the flag after use to avoid entering debug mode every time
  try {
    fs.unlinkSync(debugFlagPath);
    console.log('[Startup] Debug mode flag removed.');
  } catch (error) {
    console.error('[Startup] Failed to remove debug mode flag:', error);
  }
} else {
  console.log('[Startup] No debug mode flag found. Running in normal mode.');
}

// ==================== Import New Architecture Classes ====================
// Domain Layer - Data Models
const UserAccount = require('./domain/account/UserAccount');
const SupportedBrand = require('./domain/account/SupportedBrand');
const Device = require('./domain/device/Device');

// Architecture Manager
const SystemManager = require('./modules/SystemManager');

// New Device Managers
const DeviceSSEManager = require('./modules/device/DeviceSSEManager');
const DeviceStorageManager = require('./modules/device/DeviceStorageManager');
const DeviceGroupAPIManager = require('./modules/device/DeviceGroupAPIManager');

// Data Analyzer
const SensorDataAnalyzer = require('./modules/data/SensorDataAnalyzer');

// Account-related Manager
const AccountManager = require('./modules/account/AccountManager');

// Services Layer - Infrastructure Services
const AccountAPIRegistry = require('./services/api/AccountAPIRegistry');
const AccountStorage = require('./services/storage/AccountStorage');
const SSEService = require('./services/sse/SSEService');

// ==================== Create Manager Instances ====================
// Create AccountManager instance
const accountManager = new AccountManager();

// Create SystemManager instance (new unified entry point)
const systemManager = new SystemManager();

// Set the API registry and AccountManager association for the SystemManager
systemManager.setApiRegistry(accountManager.apiRegistry);
systemManager.setAccountManager(accountManager);

// ==================== Backward Compatibility Wrapper ====================
// To maintain backward compatibility, create a wrapper to simulate the original deviceController interface
const deviceController = {
  // Methods proxied to SystemManager
  async initialize(userId) {
    return await systemManager.initialize(userId);
  },

  setApiRegistry(apiRegistry) {
    systemManager.setApiRegistry(apiRegistry);
  },

  // Device status related methods
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

  // Device control related methods
  getDeviceControlOptions(did) {
    return systemManager.getDeviceControlOptions(did);
  },

  async controlDevice(did, operation, value) {
    return await systemManager.controlDevice(did, operation, value);
  },

  // History data related methods
  getSensorHistory(deviceId, metricType) {
    return systemManager.getSensorHistory(deviceId, metricType);
  },

  getAllSensorHistory() {
    return systemManager.getAllSensorHistory();
  },

  analyzeEnvironmentData(deviceIds = []) {
    return systemManager.analyzeEnvironmentData(deviceIds);
  },

  // System operations
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

// ==================== Backward Compatible State Manager ====================
const stateManager = {
  // Proxy to SystemManager to get state
  getState() {
    return systemManager.getSystemStatus();
  },

  // Get device state
  getDevicesState() {
    return systemManager.getAllDevices();
  },

  // Other state management methods can be added as needed
};

// ==================== Export Interface ====================
module.exports = {
  // ==================== Main Manager Instances (Backward Compatible) ====================
  stateManager,
  accountManager,
  deviceController, // This is the wrapped compatibility interface

  // ==================== New Architecture Manager Instances ====================
  systemManager, // New unified system manager

  // Get individual manager instances (for advanced operations)
  getSSEService: () => systemManager.getManagers().sseService,

  // ==================== Domain Layer Classes (for use by other modules) ====================
  UserAccount,
  SupportedBrand,
  Device,

  // ==================== Modules Layer Classes ====================
  // System Manager
  SystemManager,

  // Device Manager Classes
  DeviceSSEManager,
  DeviceStorageManager,
  DeviceGroupAPIManager,

  // Data Analyzer Class
  SensorDataAnalyzer,

  // Account Management Related
  AccountManager,

  // ==================== Services Layer Classes ====================
  AccountAPIRegistry,
  AccountStorage,
  SSEService,

  // ==================== Convenience Methods ====================
  // Device-related convenience methods
  device: {
    getAll: () => systemManager.getAllDevices(),
    getByBrand: (brand) => systemManager.getDevicesByBrand(brand),
    getControllable: () => systemManager.getControllableDevices(),
    getSensors: () => systemManager.getSensorDevices(),
    getStatus: (did) => systemManager.getDeviceStatus(did),
    control: (did, operation, value) => systemManager.controlDevice(did, operation, value),
    refresh: () => systemManager.refreshDevices()
  },

  // Group-related convenience methods
  group: {
    getAll: () => systemManager.getAllGroups(),
    get: (groupId) => systemManager.getGroup(groupId),
    create: (groupData) => systemManager.createGroup(groupData),
    update: (groupId, updateData) => systemManager.updateGroup(groupId, updateData),
    delete: (groupId) => systemManager.deleteGroup(groupId),
    addDevice: (groupId, deviceId) => systemManager.addDeviceToGroup(groupId, deviceId),
    removeDevice: (groupId, deviceId) => systemManager.removeDeviceFromGroup(groupId, deviceId),
    // Note: For advanced functions like batch control, please use the corresponding manager directly
  },

  // History data related convenience methods
  history: {
    getSensor: (deviceId, metricType) => systemManager.getSensorHistory(deviceId, metricType),
    getAll: () => systemManager.getAllSensorHistory(),
    getDevice: (deviceId) => systemManager.getDeviceHistoryData(deviceId),
    analyze: (deviceIds) => systemManager.analyzeEnvironmentData(deviceIds),
    // Note: For generating environment reports, please use SensorDataAnalyzer
    refresh: () => systemManager.refreshSensorHistory()
  },

  // System-related convenience methods
  system: {
    initialize: (userId) => systemManager.initialize(userId),
    getStatus: () => systemManager.getSystemStatus(),
    refreshAll: () => systemManager.refreshAllData(),
    logout: () => systemManager.logout(),
    reset: () => systemManager.reset(),
    export: () => systemManager.exportSystemData()
  },

  // Device management related convenience methods (accessed via AccountManager)
  deviceManagement: {
    // Get device manager instances
    getManagers: () => accountManager.getDeviceManagers(),

    // Device storage related
    storage: {
      getAllDevices: () => accountManager.getDeviceManagers().storageManager.getAllDevices(),
      getDevice: (did) => accountManager.getDeviceManagers().storageManager.getDevice(did),
      getDevicesByGroup: (groupId) => accountManager.getDeviceManagers().storageManager.getDevicesByGroup(groupId),
      getDevicesByBrand: (brand) => accountManager.getDeviceManagers().storageManager.getDevicesByBrand(brand),
      getDeviceStats: () => accountManager.getDeviceManagers().storageManager.getDeviceStats(),
      setDeviceGroup: (did, groupId) => accountManager.getDeviceManagers().storageManager.setDeviceGroup(did, groupId)
    },

    // Group API related
    groups: {
      getAll: () => accountManager.getDeviceManagers().groupAPIManager.getAllGroups(),
      get: (gid) => accountManager.getDeviceManagers().groupAPIManager.getGroup(gid),
      create: (gname) => accountManager.getDeviceManagers().groupAPIManager.createGroup(gname),
      delete: (gid) => accountManager.getDeviceManagers().groupAPIManager.deleteGroup(gid),
      setDeviceGroup: (deviceId, groupId) => accountManager.getDeviceManagers().groupAPIManager.setDeviceGroup(deviceId, groupId),
      getStats: () => accountManager.getDeviceManagers().groupAPIManager.getGroupStats(),
      refresh: () => accountManager.getDeviceManagers().groupAPIManager.refreshGroups()
    },

    // SSE connection related
    sse: {
      getStatus: () => accountManager.getDeviceManagers().sseManager.getConnectionStatus(),
      reconnect: () => accountManager.getDeviceManagers().sseManager.reconnect(),
      registerHandler: (eventType, handler) => accountManager.getDeviceManagers().sseManager.registerEventHandler(eventType, handler),
      unregisterHandler: (eventType, handler) => accountManager.getDeviceManagers().sseManager.unregisterEventHandler(eventType, handler)
    },

    // Data analysis related
    analysis: {
      analyzeGroup: (groupId) => accountManager.getDeviceManagers().dataAnalyzer.analyzeGroupSensorData(groupId),
      analyzeMultipleGroups: (groupIds) => accountManager.getDeviceManagers().dataAnalyzer.analyzeMultipleGroups(groupIds),
      getSupportedSensorTypes: () => accountManager.getDeviceManagers().dataAnalyzer.getSupportedSensorTypes(),
      exportResult: (result) => accountManager.getDeviceManagers().dataAnalyzer.exportAnalysisResult(result)
    }
  }
};

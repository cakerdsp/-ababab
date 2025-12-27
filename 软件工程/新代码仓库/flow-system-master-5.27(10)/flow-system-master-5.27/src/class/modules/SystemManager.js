// SystemManager - 向后兼容的包装器
// 现在通过AccountManager访问设备管理功能

class SystemManager {
  constructor(apiRegistry = null) {
    this.apiRegistry = apiRegistry;
    this.accountManager = null; // 将在setAccountManager中设置
    this.isInitialized = false;
    this.currentUserId = null;
  }

  // 设置AccountManager实例
  setAccountManager(accountManager) {
    this.accountManager = accountManager;
  }

  // 设置API注册器
  setApiRegistry(apiRegistry) {
    this.apiRegistry = apiRegistry;
  }

  // 设置当前用户ID
  setCurrentUserId(userId) {
    this.currentUserId = userId;
  }

  // 初始化整个系统（通过AccountManager）
  async initialize(userId) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }

    this.setCurrentUserId(userId);
    this.isInitialized = true;

    // SystemManager现在只是一个包装器，实际初始化由AccountManager处理
    return {
      success: true,
      message: 'System initialized successfully (via AccountManager)',
      note: 'SystemManager is now a wrapper for AccountManager'
    };
  }

  // ==================== 设备状态相关方法（通过AccountManager代理） ====================
  getAllDevices() {
    if (!this.accountManager) return [];
    return this.accountManager.getDeviceManagers().storageManager.getAllDevices();
  }

  getDevicesByBrand(brand) {
    if (!this.accountManager) return [];
    return this.accountManager.getDeviceManagers().storageManager.getDevicesByBrand(brand);
  }

  getControllableDevices() {
    if (!this.accountManager) return [];
    // 过滤出非传感器设备（可控制设备）
    const allDevices = this.accountManager.getDeviceManagers().storageManager.getAllDevices();
    return allDevices.filter(device =>
      device.type !== 'mi_temp_hum_sensor' && device.type !== 'mi_air_sensor'
    );
  }

  getSensorDevices() {
    if (!this.accountManager) return [];
    // 过滤出传感器设备
    const allDevices = this.accountManager.getDeviceManagers().storageManager.getAllDevices();
    return allDevices.filter(device =>
      device.type === 'mi_temp_hum_sensor' || device.type === 'mi_air_sensor'
    );
  }

  getDeviceStatus(did) {
    if (!this.accountManager) return null;
    return this.accountManager.getDeviceManagers().storageManager.getDevice(did);
  }

  async refreshDevices() {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }

    // 通过API重新获取设备状态
    try {
      const response = await this.accountManager.apiRegistry.callAPIGet('getDevicesStatus');
      if (response && response.code === 200 && response.data && response.data.devices) {
        const result = this.accountManager.getDeviceManagers().storageManager.storeAllDevices(response.data.devices);
        return {
          success: result.success,
          message: result.message,
          deviceCount: response.data.devices.length
        };
      } else {
        return { success: false, message: 'Failed to get device data' };
      }
    } catch (error) {
      return { success: false, message: 'Failed to refresh devices: ' + error.message };
    }
  }

  // ==================== 设备控制相关方法（直接调用API） ====================
  getDeviceControlOptions(did) {
    // 简单返回设备控制选项，基于设备类型
    const device = this.getDeviceStatus(did);
    if (!device || device.type === 'mi_temp_hum_sensor' || device.type === 'mi_air_sensor') {
      return null;
    }

    const options = {
      did: device.did,
      name: device.name,
      type: device.type,
      brand: device.brand,
      online: device.online,
      controls: []
    };

    // 根据设备类型生成控制选项
    switch (device.type) {
      case 'mi_ac':
      case 'midea_ac':
        options.controls = [
          { property: 'power', type: 'select', options: ['ON', 'OFF'], label: 'Power' },
          { property: 'target_temperature', type: 'number', min: 16, max: 30, label: 'Target Temperature' },
          { property: 'fan_speed', type: 'select', options: ['low', 'medium', 'high', 'auto'], label: 'Fan Speed' },
          { property: 'mode', type: 'select', options: ['cool', 'heat', 'dry', 'fan'], label: 'Mode' }
        ];
        break;
      default:
        options.controls = [];
    }

    return options;
  }

  async controlDevice(did, operation, value) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }

    try {
      const response = await this.accountManager.apiRegistry.callAPI('controlDevice', {
        did: did,
        control: { operation: operation, value: value }
      });

      if (response && response.code === 200) {
        return { success: true, message: 'Device control successful', did: did, operation: operation, value: value };
      } else {
        return { success: false, message: response.message || 'Device control failed' };
      }
    } catch (error) {
      return { success: false, message: 'Device control failed: ' + error.message };
    }
  }

  async controlMultipleDevices(controlCommands) {
    const results = [];
    for (const command of controlCommands) {
      const result = await this.controlDevice(command.did, command.operation, command.value);
      results.push({ ...command, ...result });
    }

    const successCount = results.filter(r => r.success).length;
    return {
      success: successCount > 0,
      message: `Batch control complete: ${successCount}/${results.length} devices controlled successfully`,
      results: results
    };
  }

  // ==================== 分组管理相关方法（通过AccountManager代理） ====================
  createGroup(groupData) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return this.accountManager.getDeviceManagers().groupAPIManager.createGroup(groupData.name);
  }

  getAllGroups() {
    if (!this.accountManager) return [];
    return this.accountManager.getDeviceManagers().groupAPIManager.getAllGroups();
  }

  getGroup(groupId) {
    if (!this.accountManager) return null;
    return this.accountManager.getDeviceManagers().groupAPIManager.getGroup(groupId);
  }

  updateGroup(groupId, updateData) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    // 简化的更新，实际需要根据updateData调用相应的API
    return { success: false, message: 'Please use DeviceGroupAPIManager directly' };
  }

  deleteGroup(groupId) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return this.accountManager.getDeviceManagers().groupAPIManager.deleteGroup(groupId);
  }

  addDeviceToGroup(groupId, deviceId) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return this.accountManager.getDeviceManagers().groupAPIManager.setDeviceGroup(deviceId, groupId);
  }

  removeDeviceFromGroup(groupId, deviceId) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return this.accountManager.getDeviceManagers().groupAPIManager.setDeviceGroup(deviceId, null);
  }

  // ==================== 数据分析相关方法（通过AccountManager代理） ====================
  getSensorHistory(deviceId, metricType) {
    // 返回空数组，建议直接使用SensorDataAnalyzer
    console.warn('Please use SensorDataAnalyzer to get sensor history data');
    return [];
  }

  getAllSensorHistory() {
    console.warn('Please use SensorDataAnalyzer to get sensor history data');
    return {};
  }

  getDeviceHistoryData(deviceId) {
    console.warn('Please use SensorDataAnalyzer to get device history data');
    return null;
  }

  analyzeEnvironmentData(deviceIds = []) {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    console.warn('Please use the SensorDataAnalyzer.analyzeGroupSensorData() method');
    return { success: false, message: 'Please use the SensorDataAnalyzer.analyzeGroupSensorData() method' };
  }

  generateEnvironmentReport(deviceIds = []) {
    console.warn('Please use SensorDataAnalyzer to generate environment reports');
    return null;
  }

  async refreshSensorHistory() {
    console.warn('Sensor history is now updated in real-time via SSE');
    return { success: true, message: 'Sensor history is now updated in real-time via SSE' };
  }

  // ==================== 系统操作方法 ====================
  async refreshAllData() {
    const deviceResult = await this.refreshDevices();
    return {
      success: deviceResult.success,
      message: 'Data refreshed successfully',
      results: {
        devices: deviceResult
      }
    };
  }

  getSystemStatus() {
    if (!this.accountManager) {
      return {
        isInitialized: false,
        message: 'AccountManager not set'
      };
    }

    const managers = this.accountManager.getDeviceManagers();
    const allDevices = managers.storageManager.getAllDevices();
    const stats = managers.storageManager.getDeviceStats();

    return {
      isInitialized: this.isInitialized,
      currentUserId: this.currentUserId,
      deviceCount: allDevices.length,
      onlineDeviceCount: allDevices.filter(d => d.online).length,
      offlineDeviceCount: allDevices.filter(d => !d.online).length,
      sensorCount: allDevices.filter(d => d.type === 'mi_temp_hum_sensor' || d.type === 'mi_air_sensor').length,
      groupCount: managers.groupAPIManager.getAllGroups().length,
      sseStatus: managers.sseManager.getConnectionStatus(),
      stats: stats,
      lastUpdated: new Date().toISOString()
    };
  }

  async reconnectSSE() {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return await this.accountManager.getDeviceManagers().sseManager.reconnect();
  }

  async logout() {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }
    return await this.accountManager.logout();
  }

  reset() {
    this.isInitialized = false;
    this.currentUserId = null;
    if (this.accountManager) {
      // 重置由AccountManager处理
      console.log('SystemManager has been reset.');
    }
  }

  // ==================== SSE相关方法 ====================
  registerSSEHandler(type, handler) {
    if (!this.accountManager) return;
    this.accountManager.getDeviceManagers().sseManager.registerEventHandler(type, handler);
  }

  unregisterSSEHandler(type, handler) {
    if (!this.accountManager) return;
    this.accountManager.getDeviceManagers().sseManager.unregisterEventHandler(type, handler);
  }

  // ==================== 兼容性方法 ====================
  exportSystemData() {
    if (!this.accountManager) {
      return { success: false, message: 'AccountManager not set' };
    }

    const managers = this.accountManager.getDeviceManagers();
    return {
      devices: managers.storageManager.exportDeviceData(),
      groups: managers.groupAPIManager.exportGroupData(),
      systemStatus: this.getSystemStatus(),
      exportedAt: new Date().toISOString(),
      note: 'SystemManager is now a wrapper for AccountManager'
    };
  }

  getManagers() {
    if (!this.accountManager) {
      return {
        deviceStatusManager: null,
        deviceController: null,
        groupManager: null,
        historyDataManager: null,
        sseService: null
      };
    }

    // 返回兼容的管理器映射
    const managers = this.accountManager.getDeviceManagers();
    return {
      deviceStatusManager: managers.storageManager, // 映射到存储管理器
      deviceController: this, // 控制功能由SystemManager包装
      groupManager: managers.groupAPIManager, // 映射到分组API管理器
      historyDataManager: managers.dataAnalyzer, // 映射到数据分析器
      sseService: managers.sseManager // 映射到SSE管理器
    };
  }
}

module.exports = SystemManager;

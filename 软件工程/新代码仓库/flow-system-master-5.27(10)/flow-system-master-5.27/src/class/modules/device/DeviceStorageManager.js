const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class DeviceStorageManager {
  constructor() {
    this.storage = new UnifiedStorage();
    this.devices = new Map(); // 存储设备数据，key为did
    this.deviceGroups = new Map(); // 存储设备到分组的映射，key为did，value为groupId
    this.isInitialized = false;
    this.groupAPIManager = null; // (新增) 用于访问分组信息
  }

  /**
   * 标准化power值到统一格式 (ON/OFF)
   * @param {any} value - 原始power值
   * @returns {string} 标准化后的power值
   */
  normalizePowerValue(value) {
    if (value === 'ON' || value === 'on' || value === 1 || value === '1' || value === true || value === 'true') {
      return 'ON';
    } else if (value === 'OFF' || value === 'off' || value === 0 || value === '0' || value === false || value === 'false') {
      return 'OFF';
    }
    return value; // 如果不是power相关值，返回原值
  }

  /**
   * 标准化设备状态中的所有power相关属性
   * @param {object} device - 设备对象
   * @returns {object} 标准化后的设备对象
   */
  normalizeDeviceStatus(device) {
    if (!device || !device.status) return device;

    const normalizedDevice = JSON.parse(JSON.stringify(device)); // 深拷贝

    // 标准化power属性
    if (normalizedDevice.status.power !== undefined) {
      normalizedDevice.status.power = this.normalizePowerValue(normalizedDevice.status.power);
    }

    return normalizedDevice;
  }

  /**
   * 同步设备的在线状态与power状态
   * 确保：power='ON'时在线，power='OFF'时离线，传感器设备始终在线
   * @param {object} device - 设备对象
   * @returns {object} 同步后的设备对象
   */
  syncOnlineStatusWithPower(device) {
    if (!device) return device;

    // 传感器设备始终在线
    if (device.type === 'history' ||
        device.type === 'mi_temp_hum_sensor' ||
        device.type === 'mi_air_sensor') {
      device.online = true;
    } else if (device.status && device.status.power !== undefined) {
      // 可控制设备的在线状态对应power字段
      device.online = device.status.power === 'ON';
    }

    return device;
  }

  /**
   * 同步所有设备的在线状态与power状态
   */
  syncAllDevicesOnlineStatus() {
    console.log('🔄 [Storage] 同步所有设备的在线状态与power状态...');

    let syncCount = 0;
    this.devices.forEach((device, did) => {
      const originalOnline = device.online;
      this.syncOnlineStatusWithPower(device);

      if (originalOnline !== device.online) {
        syncCount++;
        console.log(`🔄 [Storage] 设备 ${device.name} 在线状态同步: ${originalOnline} -> ${device.online} (power: ${device.status?.power})`);
      }
    });

    console.log(`✅ [Storage] 完成设备在线状态同步，共更新 ${syncCount} 个设备`);
    return syncCount;
  }

  /**
   * (新增) 设置DeviceGroupAPIManager的实例。
   * @param {object} manager - DeviceGroupAPIManager的实例。
   */
  setGroupAPIManager(manager) {
    this.groupAPIManager = manager;
  }

  // 初始化设备存储管理器
  async initialize() {
    if (this.isInitialized) {
      return { success: true, message: '设备存储管理器已初始化' };
    }

    try {
      // 从本地存储加载设备数据
      await this.loadDevicesFromStorage();

      // 从本地存储加载分组映射
      await this.loadGroupMappingsFromStorage();

      this.isInitialized = true;
      console.log(`Device storage manager initialized successfully, loaded ${this.devices.size} devices`);
      return {
        success: true,
        message: '设备存储管理器初始化成功',
        deviceCount: this.devices.size
      };
    } catch (error) {
      console.error('Device storage manager initialization failed:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 从本地存储加载设备数据
  async loadDevicesFromStorage() {
    try {
      const devicesData = this.storage.getDevices();
      if (devicesData && Array.isArray(devicesData)) {
        devicesData.forEach(deviceData => {
          // 统一处理设备分组信息 - 检查多个可能的分组字段
          let deviceGroupId = deviceData.groupId || deviceData.group || deviceData.gid;

          // 如果从映射表中有分组信息，使用映射表的数据
          const mappedGroupId = this.deviceGroups.get(deviceData.did);
          if (mappedGroupId) {
            deviceGroupId = mappedGroupId;
          }

          // 确保所有分组相关字段的一致性
          if (deviceGroupId) {
            deviceData.groupId = deviceGroupId;
            deviceData.group = deviceGroupId;
            deviceData.gid = deviceGroupId;
          }

          // 标准化设备状态
          const normalizedDevice = this.normalizeDeviceStatus(deviceData);

          // 同步在线状态与power状态
          const syncedDevice = this.syncOnlineStatusWithPower(normalizedDevice);

          this.devices.set(syncedDevice.did, syncedDevice);
        });
        console.log(`Loaded ${devicesData.length} devices from local storage`);

        // 显示同步结果统计
        const onlineCount = Array.from(this.devices.values()).filter(d => d.online).length;
        const offlineCount = devicesData.length - onlineCount;
        console.log(`📊 [Storage] 设备在线状态统计: ${onlineCount} 在线, ${offlineCount} 离线`);
      }
    } catch (error) {
      console.error('Failed to load device data from local storage:', error);
    }
  }

  // 从本地存储加载分组映射
  async loadGroupMappingsFromStorage() {
    try {
      const groups = this.storage.getDeviceGroups();
      if (groups && Array.isArray(groups)) {
        groups.forEach(group => {
          if (group.deviceIds && Array.isArray(group.deviceIds)) {
            group.deviceIds.forEach(did => {
              this.deviceGroups.set(did, group.groupId);
            });
          }
        });
        console.log(`Loaded device mappings for ${groups.length} groups`);
      }
    } catch (error) {
      console.error('Failed to load group mappings from local storage:', error);
    }
  }

  // 存储所有设备数据
  storeAllDevices(devicesArray) {
    try {
      if (!Array.isArray(devicesArray)) {
        return { success: false, message: '设备数据必须是数组格式' };
      }

      const newDevicesMap = new Map();
      const defaultGroupId = this.groupAPIManager ? this.groupAPIManager.getDefaultGroupId() : null;
      let hasUngroupedDevices = false;

      // 遍历新的设备列表
      devicesArray.forEach(newDevice => {
        const did = newDevice.did;
        const oldDevice = this.devices.get(did);
        const mergedDevice = { ...oldDevice, ...newDevice };

        // 标准化设备状态
        const normalizedDevice = this.normalizeDeviceStatus(mergedDevice);

        // 同步在线状态与power状态
        const syncedDevice = this.syncOnlineStatusWithPower(normalizedDevice);

        // 处理设备分组信息 - 保持原始字段结构
        // 实际环境中：gid字段 = group字段的值
        if (syncedDevice.group && !syncedDevice.gid) {
          // 如果有group字段但没有gid，设置gid = group
          syncedDevice.gid = syncedDevice.group;
        } else if (syncedDevice.gid && !syncedDevice.group) {
          // 如果有gid但没有group，设置group = gid
          syncedDevice.group = syncedDevice.gid;
        }

        // 设置groupId用于内部查询（向后兼容）
        syncedDevice.groupId = syncedDevice.group || syncedDevice.gid || null;

        // 更新设备分组映射表
        if (syncedDevice.groupId) {
          this.deviceGroups.set(did, syncedDevice.groupId);
        } else {
          hasUngroupedDevices = true;
          this.deviceGroups.delete(did);
        }

        newDevicesMap.set(did, syncedDevice);
      });

      // 更新设备映射
      this.devices = newDevicesMap;

      // 清理删除的设备的分组信息
      const currentDeviceIds = new Set(Array.from(this.devices.keys()));
      for (const [did] of this.deviceGroups) {
        if (!currentDeviceIds.has(did)) {
          this.deviceGroups.delete(did);
        }
      }

      // 获取统计信息
      const stats = this.getDeviceStats();
      console.log(`💾 [DeviceStorage] 设备存储完成: 总计${stats.total}台, 在线${stats.online}台, 离线${stats.offline}台, 分组${stats.grouped}台, 未分组${stats.ungrouped}台`);

      // 保存到本地存储
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      // 如果有分组API管理器且有未分组设备，进行处理
      if (this.groupAPIManager && hasUngroupedDevices && defaultGroupId) {
        console.log('🔄 [DeviceStorage] 检测到未分组设备，将在后台处理...');
        // 异步处理未分组设备，不阻塞主流程
        setTimeout(() => {
          this.groupAPIManager.assignUngroupedDevices().catch(error => {
            console.error('❌ [DeviceStorage] 自动分配未分组设备失败:', error);
          });
        }, 100);
      }

      return {
        success: true,
        message: '设备数据存储成功',
        stats: stats,
        hasUngroupedDevices: hasUngroupedDevices
      };

    } catch (error) {
      console.error('❌ [DeviceStorage] 存储设备数据时发生错误:', error);
      return { success: false, message: '存储设备数据失败: ' + error.message };
    }
  }

  // 更新设备状态
  updateDeviceStatus(did, statusUpdates) {
    try {
      if (!did) {
        return { success: false, message: '设备ID不能为空' };
      }

      const device = this.devices.get(did);
      if (!device) {
        return { success: false, message: `设备不存在: ${did}` };
      }

      // 更新设备数据
      // 特殊处理status字段，确保深度合并而不是覆盖
      if (statusUpdates.status && device.status) {
        // 深度合并status字段
        device.status = { ...device.status, ...statusUpdates.status };
        // 移除statusUpdates中的status字段，避免重复赋值
        const { status, ...otherUpdates } = statusUpdates;
        Object.assign(device, otherUpdates);
      } else {
        // 正常合并
        Object.assign(device, statusUpdates);
      }
      device.lastUpdated = new Date().toISOString();

      // 同步在线状态与power状态
      this.syncOnlineStatusWithPower(device);

      // 保存单个设备状态
      this.storage.saveDeviceState(did, device);

      // 更新整体设备列表
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      console.log(`[STORAGE_UPDATE] Device status updated: ${did} - ${device.online ? 'online' : 'offline'} (power: ${device.status?.power})`);
      console.log(`[STORAGE_UPDATE] Device status after update:`, JSON.stringify(device.status, null, 2));
      return {
        success: true,
        message: '设备状态更新成功',
        device: device
      };
    } catch (error) {
      console.error('Failed to update device status:', error);
      return { success: false, message: '更新失败：' + error.message };
    }
  }

  // 删除设备
  removeDevice(did) {
    try {
      if (!this.devices.has(did)) {
        return { success: false, message: `设备不存在: ${did}` };
      }

      this.devices.delete(did);
      this.deviceGroups.delete(did);

      // 更新本地存储
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      console.log(`Device deleted: ${did}`);
      return { success: true, message: '设备删除成功' };
    } catch (error) {
      console.error('Failed to delete device:', error);
      return { success: false, message: '删除失败：' + error.message };
    }
  }

  // 获取单个设备
  getDevice(did) {
    return this.devices.get(did) || null;
  }

  // 获取所有设备
  getAllDevices() {
    return Array.from(this.devices.values());
  }

  // 根据分组获取设备
  getDevicesByGroup(groupId) {
    return Array.from(this.devices.values()).filter(device => {
      // 检查多个可能的分组字段名称：groupId, group, gid
      return device.groupId === groupId ||
             device.group === groupId ||
             device.gid === groupId;
    });
  }

  // 获取未分组的设备
  getUngroupedDevices() {
    return Array.from(this.devices.values()).filter(device =>
      !device.groupId && !device.group && !device.gid
    );
  }

  // 根据品牌获取设备
  getDevicesByBrand(brand) {
    return Array.from(this.devices.values()).filter(device =>
      device.brand === brand
    );
  }

  // 根据类型获取设备
  getDevicesByType(type) {
    return Array.from(this.devices.values()).filter(device =>
      device.type === type
    );
  }

  // 获取在线设备
  getOnlineDevices() {
    return Array.from(this.devices.values()).filter(device =>
      device.online === true
    );
  }

  // 获取离线设备
  getOfflineDevices() {
    return Array.from(this.devices.values()).filter(device =>
      device.online === false
    );
  }

  // 设置设备分组
  setDeviceGroup(did, groupId) {
    try {
      const device = this.devices.get(did);
      if (!device) {
        return { success: false, message: `设备不存在: ${did}` };
      }

      // 更新设备的所有分组相关信息，确保一致性
      if (groupId) {
        device.groupId = groupId;
        device.group = groupId;
        device.gid = groupId;
        this.deviceGroups.set(did, groupId);
      } else {
        // 清除分组信息
        device.groupId = null;
        device.group = null;
        device.gid = null;
        this.deviceGroups.delete(did);
      }

      this.devices.set(did, device);

      // 保存到本地存储
      this.storage.saveDeviceState(did, device);
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      console.log(`Device group set: ${did} -> ${groupId || 'No Group'}`);
      return { success: true, message: '设备分组设置成功' };
    } catch (error) {
      console.error('Failed to set device group:', error);
      return { success: false, message: '设置失败：' + error.message };
    }
  }

  // 获取设备统计信息
  getDeviceStats() {
    const total = this.devices.size;
    const online = this.getOnlineDevices().length;
    const offline = this.getOfflineDevices().length;
    const grouped = Array.from(this.devices.values()).filter(d =>
      d.groupId || d.group || d.gid
    ).length;
    const ungrouped = total - grouped;

    // 按品牌统计
    const brandStats = {};
    this.devices.forEach(device => {
      const brand = device.brand || 'unknown';
      brandStats[brand] = (brandStats[brand] || 0) + 1;
    });

    // 按类型统计
    const typeStats = {};
    this.devices.forEach(device => {
      const type = device.type || 'unknown';
      typeStats[type] = (typeStats[type] || 0) + 1;
    });

    return {
      total,
      online,
      offline,
      grouped,
      ungrouped,
      brandStats,
      typeStats,
      lastUpdated: new Date().toISOString()
    };
  }

  // 清空所有设备数据
  clearAllDevices() {
    try {
      this.devices.clear();
      this.deviceGroups.clear();
      this.storage.clearDeviceData();
      console.log('All device data has been cleared');
      return { success: true, message: '设备数据清空成功' };
    } catch (error) {
      console.error('Failed to clear device data:', error);
      return { success: false, message: '清空失败：' + error.message };
    }
  }

  // 检查设备是否存在
  hasDevice(did) {
    return this.devices.has(did);
  }

  // 重置存储管理器
  reset() {
    this.devices.clear();
    this.deviceGroups.clear();
    this.isInitialized = false;
    console.log('Device storage manager has been reset');
  }

  // 导出设备数据
  exportDeviceData() {
    return {
      devices: Array.from(this.devices.values()),
      deviceGroups: Object.fromEntries(this.deviceGroups),
      stats: this.getDeviceStats(),
      exportTime: new Date().toISOString()
    };
  }

  // 调试方法：打印设备分组信息
  debugDeviceGroups(groupId = null) {
    console.log('=== 设备分组调试信息 ===');

    if (groupId) {
      console.log(`筛选分组ID: ${groupId}`);
      const groupDevices = this.getDevicesByGroup(groupId);
      console.log(`分组 ${groupId} 设备数量: ${groupDevices.length}`);

      groupDevices.forEach(device => {
        console.log(`  设备: ${device.name} (${device.did})`);
        console.log(`    - groupId: ${device.groupId}`);
        console.log(`    - group: ${device.group}`);
        console.log(`    - gid: ${device.gid}`);
      });
    } else {
      console.log('所有设备分组信息:');
      Array.from(this.devices.values()).forEach(device => {
        console.log(`设备: ${device.name} (${device.did})`);
        console.log(`  - groupId: ${device.groupId}`);
        console.log(`  - group: ${device.group}`);
        console.log(`  - gid: ${device.gid}`);
      });
    }

    console.log('设备分组映射表:');
    console.log(Object.fromEntries(this.deviceGroups));
    console.log('=== 调试信息结束 ===');
  }
}

module.exports = DeviceStorageManager;

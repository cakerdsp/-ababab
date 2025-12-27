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
      console.log(`设备存储管理器初始化成功，加载了 ${this.devices.size} 个设备`);
      return {
        success: true,
        message: '设备存储管理器初始化成功',
        deviceCount: this.devices.size
      };
    } catch (error) {
      console.error('设备存储管理器初始化失败:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 从本地存储加载设备数据
  async loadDevicesFromStorage() {
    try {
      const devicesData = this.storage.getDevices();
      if (devicesData && Array.isArray(devicesData)) {
        devicesData.forEach(deviceData => {
          // 为设备添加分组信息
          const groupId = this.deviceGroups.get(deviceData.did) || null;
          deviceData.groupId = groupId;
          this.devices.set(deviceData.did, deviceData);
        });
        console.log(`从本地存储加载了 ${devicesData.length} 个设备`);
      }
    } catch (error) {
      console.error('从本地存储加载设备数据失败:', error);
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
        console.log(`加载了 ${groups.length} 个分组的设备映射`);
      }
    } catch (error) {
      console.error('从本地存储加载分组映射失败:', error);
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

      // 遍历新的设备列表
      devicesArray.forEach(newDevice => {
        const did = newDevice.did;
        const oldDevice = this.devices.get(did);
        const mergedDevice = { ...oldDevice, ...newDevice };

        // 如果设备没有分组 (groupId/group 都为空)，则分配到默认分组
        if (!mergedDevice.groupId && !mergedDevice.group && defaultGroupId) {
          mergedDevice.groupId = defaultGroupId;
          mergedDevice.group = defaultGroupId; // 确保两个字段都更新
          console.log(`[DeviceStorage] 设备 ${did} 未分组，已自动归入默认分组 ${defaultGroupId}`);
        }

        newDevicesMap.set(did, mergedDevice);
      });

      // 更新内存中的设备列表
      this.devices = newDevicesMap;

      // 保存到本地存储
      this.storage.saveDevices(Array.from(this.devices.values()));

      console.log(`成功存储 ${this.devices.size} 个设备`);
      return {
        success: true,
        message: '设备数据存储成功',
        deviceCount: this.devices.size
      };
    } catch (error) {
      console.error('存储设备数据失败:', error);
      return { success: false, message: '存储失败：' + error.message };
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
      Object.assign(device, statusUpdates);
      device.lastUpdated = new Date().toISOString();

      // 保存单个设备状态
      this.storage.saveDeviceState(did, device);

      // 更新整体设备列表
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      console.log(`设备状态已更新: ${did}`);
      return {
        success: true,
        message: '设备状态更新成功',
        device: device
      };
    } catch (error) {
      console.error('更新设备状态失败:', error);
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

      console.log(`设备已删除: ${did}`);
      return { success: true, message: '设备删除成功' };
    } catch (error) {
      console.error('删除设备失败:', error);
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
    return Array.from(this.devices.values()).filter(device =>
      device.groupId === groupId
    );
  }

  // 获取未分组的设备
  getUngroupedDevices() {
    return Array.from(this.devices.values()).filter(device =>
      !device.groupId
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

      // 更新设备的分组信息
      device.groupId = groupId;
      this.devices.set(did, device);

      // 更新分组映射
      if (groupId) {
        this.deviceGroups.set(did, groupId);
      } else {
        this.deviceGroups.delete(did);
      }

      // 保存到本地存储
      this.storage.saveDeviceState(did, device);
      const allDevices = Array.from(this.devices.values());
      this.storage.saveDevices(allDevices);

      console.log(`设备分组已更新: ${did} -> ${groupId || '无分组'}`);
      return { success: true, message: '设备分组设置成功' };
    } catch (error) {
      console.error('设置设备分组失败:', error);
      return { success: false, message: '设置失败：' + error.message };
    }
  }

  // 获取设备统计信息
  getDeviceStats() {
    const total = this.devices.size;
    const online = this.getOnlineDevices().length;
    const offline = this.getOfflineDevices().length;
    const grouped = Array.from(this.devices.values()).filter(d => d.groupId).length;
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
      console.log('所有设备数据已清空');
      return { success: true, message: '设备数据清空成功' };
    } catch (error) {
      console.error('清空设备数据失败:', error);
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
    console.log('设备存储管理器已重置');
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
}

module.exports = DeviceStorageManager;

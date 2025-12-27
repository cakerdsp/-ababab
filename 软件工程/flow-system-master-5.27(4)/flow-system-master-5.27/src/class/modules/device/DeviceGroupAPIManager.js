const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class DeviceGroupAPIManager {
  constructor(apiRegistry = null, deviceStorageManager = null) {
    this.apiRegistry = apiRegistry;
    this.storage = new UnifiedStorage();
    this.deviceStorageManager = deviceStorageManager; // 存储设备管理器实例
    this.groups = new Map(); // 本地分组缓存
    this.isInitialized = false;
    this.offlineMode = false; // 离线调试模式标记
  }

  // 设置API注册器
  setApiRegistry(apiRegistry) {
    this.apiRegistry = apiRegistry;
  }

  // 初始化分组管理器
  async initialize() {
    if (this.isInitialized) {
      return { success: true, message: '分组API管理器已初始化' };
    }

    try {
      // 从本地存储加载分组数据
      await this.loadGroupsFromStorage();

      // 从服务端同步分组数据
      const syncResult = await this.syncGroupsFromServer();

      this.isInitialized = true;
      console.log('分组API管理器初始化成功');
      return {
        success: true,
        message: '分组API管理器初始化成功',
        groupCount: this.groups.size,
        syncResult: syncResult
      };
    } catch (error) {
      console.error('分组API管理器初始化失败:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 从本地存储加载分组数据
  async loadGroupsFromStorage() {
    try {
      const groupsData = this.storage.getDeviceGroups();
      if (groupsData && Array.isArray(groupsData)) {
        groupsData.forEach(group => {
          this.groups.set(group.gid || group.groupId, group);
        });
        console.log(`从本地存储加载了 ${groupsData.length} 个分组`);
      }
    } catch (error) {
      console.error('从本地存储加载分组数据失败:', error);
    }
  }

  // 从服务端同步分组数据
  async syncGroupsFromServer() {
    try {
      if (!this.apiRegistry) {
        return { success: false, message: 'API注册器未设置' };
      }

      const response = await this.apiRegistry.callAPIGet('getGroups');

      if (response && response.code === 200 && response.data) {
        // 清空本地分组缓存
        this.groups.clear();

        // 存储服务端分组数据
        response.data.forEach(group => {
          // 规范化分组数据格式
          const normalizedGroup = {
            gid: group.gid,
            gname: group.gname,
            device_count: group.device_count || 0,
            deviceIds: [], // 需要单独获取设备列表
            created: group.created || new Date().toISOString(),
            updated: group.updated || new Date().toISOString()
          };
          this.groups.set(group.gid, normalizedGroup);
        });

        // 保存到本地存储
        this.saveGroupsToStorage();

        console.log(`从服务端同步了 ${response.data.length} 个分组`);
        return {
          success: true,
          message: '分组数据同步成功',
          groupCount: response.data.length
        };
      } else {
        return {
          success: false,
          message: response.message || '获取分组数据失败'
        };
      }
    } catch (error) {
      console.error('从服务端同步分组数据失败:', error);
      return { success: false, message: '同步失败：' + error.message };
    }
  }

  // 创建新分组
  async createGroup(gname) {
    console.log('🔧 [后端调试] GroupAPI - 开始创建分组');
    console.log('🔧 [后端调试] 分组名称:', gname);
    console.log('🔧 [后端调试] API注册器状态:', !!this.apiRegistry);
    console.log('🔧 [后端调试] 当前分组数量:', this.groups.size);
    console.log('🔧 [后端调试] 离线模式:', this.offlineMode);

    try {
      if (!gname || gname.trim() === '') {
        console.log('❌ [后端调试] 分组名称为空');
        return { success: false, message: '分组名称不能为空' };
      }

      const trimmedName = gname.trim();
      console.log('🔧 [后端调试] 处理后的分组名称:', trimmedName);

      // 检查重名
      const existingGroups = Array.from(this.groups.values());
      const duplicateGroup = existingGroups.find(g => g.gname === trimmedName);
      if (duplicateGroup) {
        console.log('❌ [后端调试] 分组名称已存在:', duplicateGroup);
        return { success: false, message: '分组名称已存在' };
      }

      // 检查是否为离线模式或API注册器不可用
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [后端调试] 离线模式：使用本地创建分组');

        // 生成模拟的分组ID
        const mockGid = 'group_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const newGroup = {
          gid: mockGid,
          gname: trimmedName,
          device_count: 0,
          deviceIds: [],
          created: new Date().toISOString(),
          updated: new Date().toISOString()
        };

        console.log('🟡 [后端调试] 离线模式创建的分组对象:', newGroup);
        this.groups.set(mockGid, newGroup);
        console.log('🟡 [后端调试] 添加到本地缓存，当前分组数量:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🟡 [后端调试] 已保存到本地存储');

        console.log(`✅ [后端调试] 离线模式分组创建成功: ${trimmedName} (${mockGid})`);
        return {
          success: true,
          message: '分组创建成功（离线模式）',
          data: {
            gid: mockGid,
            gname: trimmedName
          }
        };
      }

      console.log('🔧 [后端调试] 调用API创建分组...');
      const response = await this.apiRegistry.callAPI('createGroup', {
        gname: trimmedName
      });
      console.log('🔧 [后端调试] API响应:', response);

      if (response && response.code === 200 && response.data) {
        // 添加到本地缓存
        const newGroup = {
          gid: response.data.gid,
          gname: response.data.gname,
          device_count: 0,
          deviceIds: [],
          created: new Date().toISOString(),
          updated: new Date().toISOString()
        };

        console.log('🔧 [后端调试] 创建的新分组对象:', newGroup);
        this.groups.set(response.data.gid, newGroup);
        console.log('🔧 [后端调试] 添加到本地缓存，当前分组数量:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🔧 [后端调试] 已保存到本地存储');

        console.log(`✅ [后端调试] 分组创建成功: ${trimmedName} (${response.data.gid})`);
        return {
          success: true,
          message: '分组创建成功',
          data: {
            gid: response.data.gid,
            gname: response.data.gname
          }
        };
      } else {
        console.log('❌ [后端调试] API响应失败:', response?.message || '未知错误');
        return {
          success: false,
          message: response?.message || '分组创建失败'
        };
      }
    } catch (error) {
      console.error('❌ [后端调试] 创建分组异常:', error);
      console.error('❌ [后端调试] 错误堆栈:', error.stack);

      // 在API调用失败时，尝试离线模式
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log('🟡 [后端调试] 网络错误，切换到离线模式');
        this.offlineMode = true;
        return await this.createGroup(gname); // 递归调用，使用离线模式
      }

      return { success: false, message: '创建失败：' + error.message };
    }
  }

  // 删除分组
  async deleteGroup(gid) {
    console.log('🔧 [后端调试] GroupAPI - 开始删除分组');
    console.log('🔧 [后端调试] 分组ID:', gid);
    console.log('🔧 [后端调试] API注册器状态:', !!this.apiRegistry);
    console.log('🔧 [后端调试] 当前分组数量:', this.groups.size);

    try {
      if (!this.apiRegistry) {
        console.log('❌ [后端调试] API注册器未设置');
        return { success: false, message: 'API注册器未设置' };
      }

      if (!gid) {
        console.log('❌ [后端调试] 分组ID为空');
        return { success: false, message: '分组ID不能为空' };
      }

      // 检查分组是否存在
      const targetGroup = this.groups.get(gid);
      if (!targetGroup) {
        console.log('❌ [后端调试] 目标分组不存在:', gid);
        return { success: false, message: '分组不存在' };
      }

      console.log('🔧 [后端调试] 要删除的分组信息:', targetGroup);

      // 检查是否为默认分组
      if (targetGroup.gname === '默认分组') {
        console.log('❌ [后端调试] 尝试删除默认分组');
        return { success: false, message: '默认分组不能删除' };
      }

      // 获取默认分组
      const defaultGroup = Array.from(this.groups.values()).find(g => g.gname === '默认分组');
      if (!defaultGroup) {
        console.log('❌ [后端调试] 找不到默认分组');
        return { success: false, message: '找不到默认分组' };
      }

      // 获取该分组下的所有设备
      if (!this.deviceStorageManager) {
        console.error('❌ [后端调试] DeviceStorageManager 未初始化');
        return { success: false, message: '内部错误：设备管理器未初始化' };
      }
      const devices = this.deviceStorageManager.getAllDevices();
      const groupDevices = devices.filter(device => device.groupId === gid);
      console.log('🔧 [后端调试] 分组下设备数量:', groupDevices.length);

      // 将设备移动到默认分组
      for (const device of groupDevices) {
        await this.setDeviceGroup(device.did, defaultGroup.gid);
      }

      // 检查是否为离线模式或API注册器不可用
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [后端调试] 离线模式：使用本地删除分组');

        // 从本地缓存删除
        console.log('🟡 [后端调试] 从本地缓存删除分组');
        this.groups.delete(gid);
        console.log('🟡 [后端调试] 删除后分组数量:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🟡 [后端调试] 已保存到本地存储');

        console.log(`✅ [后端调试] 离线模式分组删除成功: ${gid}`);

        return {
          success: true,
          message: '分组删除成功（离线模式）',
          data: {
            affected_devices: groupDevices.length
          }
        };
      }

      console.log('🔧 [后端调试] 调用API删除分组...');
      const response = await this.apiRegistry.callAPI('deleteGroup', {
        gid: gid
      });
      console.log('🔧 [后端调试] API响应:', response);

      if (response && response.code === 200) {
        // 从本地缓存删除
        console.log('🔧 [后端调试] 从本地缓存删除分组');
        this.groups.delete(gid);
        console.log('🔧 [后端调试] 删除后分组数量:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🔧 [后端调试] 已保存到本地存储');

        console.log(`✅ [后端调试] 分组删除成功: ${gid}, 影响设备数量: ${groupDevices.length}`);

        return {
          success: true,
          message: '分组删除成功',
          data: {
            affected_devices: groupDevices.length
          }
        };
      } else {
        console.log('❌ [后端调试] API响应失败:', response?.message || '未知错误');
        return {
          success: false,
          message: response?.message || '分组删除失败'
        };
      }
    } catch (error) {
      console.error('❌ [后端调试] 删除分组异常:', error);
      console.error('❌ [后端调试] 错误堆栈:', error.stack);

      // 在API调用失败时，尝试离线模式
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log('🟡 [后端调试] 网络错误，切换到离线模式');
        this.offlineMode = true;
        return await this.deleteGroup(gid); // 递归调用，使用离线模式
      }

      return { success: false, message: '删除失败：' + error.message };
    }
  }

  // 设置设备分组
  async setDeviceGroup(deviceId, groupId) {
    try {
      if (!this.apiRegistry) {
        return { success: false, message: 'API注册器未设置' };
      }

      if (!deviceId) {
        return { success: false, message: '设备ID不能为空' };
      }

      const response = await this.apiRegistry.callAPI('setGroup', {
        device_id: deviceId,
        group_id: groupId // 传null表示移除分组
      });

      if (response && response.code === 200) {
        console.log(`设备分组设置成功: ${deviceId} -> ${groupId || '无分组'}`);
        return {
          success: true,
          message: '设备分组设置成功',
          data: {
            device_id: response.data.device_id,
            group_id: response.data.group_id
          }
        };
      } else {
        return {
          success: false,
          message: response.message || '设备分组设置失败'
        };
      }
    } catch (error) {
      console.error('设置设备分组失败:', error);
      return { success: false, message: '设置失败：' + error.message };
    }
  }

  // 获取所有分组
  getAllGroups() {
    console.log('🔧 [后端调试] GroupAPI - 获取所有分组');
    console.log('🔧 [后端调试] 当前分组数量:', this.groups.size);
    const groupsList = Array.from(this.groups.values());
    console.log('🔧 [后端调试] 返回分组列表:', groupsList.map(g => ({ gid: g.gid, gname: g.gname })));
    return groupsList;
  }

  // 获取单个分组
  getGroup(gid) {
    return this.groups.get(gid) || null;
  }

  // 检查分组是否存在
  hasGroup(gid) {
    return this.groups.has(gid);
  }

  // 保存分组数据到本地存储
  saveGroupsToStorage() {
    try {
      const groupsArray = Array.from(this.groups.values());
      this.storage.saveDeviceGroups(groupsArray);
      console.log(`已保存 ${groupsArray.length} 个分组到本地存储`);
    } catch (error) {
      console.error('保存分组数据到本地存储失败:', error);
    }
  }

  // 获取分组统计信息
  getGroupStats() {
    const totalGroups = this.groups.size;
    const totalDevices = Array.from(this.groups.values())
      .reduce((sum, group) => sum + (group.device_count || 0), 0);

    return {
      totalGroups,
      totalDevices,
      groups: Array.from(this.groups.values()).map(group => ({
        gid: group.gid,
        gname: group.gname,
        deviceCount: group.device_count || 0
      })),
      lastUpdated: new Date().toISOString()
    };
  }

  // 刷新分组数据
  async refreshGroups() {
    return await this.syncGroupsFromServer();
  }

  // 清空本地分组数据
  clearLocalGroups() {
    this.groups.clear();
    this.storage.clearDeviceGroups();
    console.log('本地分组数据已清空');
  }

  // 重置分组API管理器
  reset() {
    this.groups.clear();
    this.isInitialized = false;
    console.log('分组API管理器已重置');
  }

  // 导出分组数据
  exportGroupData() {
    return {
      groups: Array.from(this.groups.values()),
      stats: this.getGroupStats(),
      exportTime: new Date().toISOString()
    };
  }

  // 启用离线调试模式
  enableOfflineMode() {
    this.offlineMode = true;
    console.log('🟡 [后端调试] 离线调试模式已启用');
  }

  // 禁用离线调试模式
  disableOfflineMode() {
    this.offlineMode = false;
    console.log('🔧 [后端调试] 离线调试模式已禁用');
  }

  // 检查是否为离线模式
  isOfflineMode() {
    return this.offlineMode;
  }

  /**
   * (新增) 获取默认分组的ID。
   * 默认分组被假定为名称是 '默认分组'。
   * @returns {string|null} 默认分组的ID，如果找不到则返回null。
   */
  getDefaultGroupId() {
    const groups = Array.from(this.groups.values());
    const defaultGroup = groups.find(g => g.gname === '默认分组');
    return defaultGroup ? defaultGroup.gid : null;
  }

  /**
   * (新增) 将所有未分组的设备分配到默认分组。
   * 这个方法会修改设备和分组的本地缓存，并持久化存储。
   * 5. Updates the default group's `deviceIds` and `deviceCount`.
   * 6. Saves all changes to storage.
   */
  async assignUngroupedDevices() {
    console.log('[DeviceGroupAPIManager] Starting to assign ungrouped devices to default group.');

    const defaultGroup = this.getDefaultGroup();
    if (!defaultGroup) {
      console.error('[DeviceGroupAPIManager] Cannot assign devices: Default group not found.');
      return;
    }

    const allDevices = this.deviceStorageManager.getAllDevices();
    const ungroupedDevices = allDevices.filter(device => !device.group && !device.groupId);

    if (ungroupedDevices.length === 0) {
      console.log('[DeviceGroupAPIManager] No ungrouped devices found to assign.');
      return;
    }

    console.log(`[DeviceGroupAPIManager] Found ${ungroupedDevices.length} ungrouped devices to process.`);

    const defaultGroupId = defaultGroup.gid;

    // Use a Set for efficient handling of unique device IDs
    const deviceIdsForDefaultGroup = new Set(defaultGroup.deviceIds || []);

    // Iterate through ungrouped devices to update them and collect their IDs
    ungroupedDevices.forEach(device => {
      device.group = defaultGroupId;
      device.groupId = defaultGroupId;
      deviceIdsForDefaultGroup.add(device.did);
    });

    // Update the default group's properties
    defaultGroup.deviceIds = Array.from(deviceIdsForDefaultGroup);
    defaultGroup.deviceCount = defaultGroup.deviceIds.length;

    console.log(`[DeviceGroupAPIManager] Default group ${defaultGroupId} now contains ${defaultGroup.deviceCount} devices.`);

    // --- Persist all changes to storage ---

    // 1. Save the updated devices array (modified by reference)
    this.deviceStorageManager.storeAllDevices(allDevices);

    // 2. Save the updated groups list
    this.groups.set(defaultGroupId, defaultGroup);
    this.storage.saveDeviceGroups(Array.from(this.groups.values()));

    console.log('[DeviceGroupAPIManager] Successfully assigned devices and saved all changes.');
  }

  /**
   * (New) Fetches the full device list and then their statuses, storing them.
   * This orchestrates the two-step process of getting all devices and then updating
   * their status information.
   */
  async fetchDeviceListWithStatus() {
    console.log('[DeviceGroupAPIManager] Starting device fetch process...');
    if (!this.apiRegistry || !this.deviceStorageManager) {
      console.error('[DeviceGroupAPIManager] Cannot fetch devices: API Registry or Device Storage Manager not set.');
      return;
    }

    try {
      // Step 1: Get the basic device list from the /devices/getList API
      console.log('[DeviceGroupAPIManager] Fetching base device list...');
      const listResult = await this.apiRegistry.callAPIGet('getDeviceList');

      if (listResult && listResult.devices) {
        console.log(`[DeviceGroupAPIManager] Fetched ${listResult.devices.length} devices from getList API.`);
        // This call will merge the new data with any existing data
        this.deviceStorageManager.storeAllDevices(listResult.devices);
      } else {
        console.warn('[DeviceGroupAPIManager] getDeviceList API returned no devices or an error.');
      }

      // Step 2: Get the device statuses from the /devices/status API
      console.log('[DeviceGroupAPIManager] Fetching device statuses...');
      const statusResult = await this.apiRegistry.callAPIGet('getDevicesStatus');

      if (statusResult && statusResult.devices) {
        console.log(`[DeviceGroupAPIManager] Fetched ${statusResult.devices.length} device statuses.`);
        // This will merge the status data into the already stored devices
        this.deviceStorageManager.storeAllDevices(statusResult.devices);
      } else {
        console.warn('[DeviceGroupAPIManager] getDevicesStatus API returned no devices or an error.');
      }

      console.log('[DeviceGroupAPIManager] Device fetch process completed.');
    } catch (error) {
      console.error('[DeviceGroupAPIManager] An error occurred during the device fetch process:', error);
    }
  }

  /**
   * (New) Finds or creates the default group.
   * Ensures a default group exists and saves it if newly created.
   * @returns {object} The default group object.
   */
  findOrCreateDefaultGroup() {
    let defaultGroup = this.getDefaultGroup();

    if (!defaultGroup) {
      console.log('[DeviceGroupAPIManager] Default group not found. Creating a new one.');
      const newGid = 'default_group_001'; // A consistent, predictable ID
      defaultGroup = {
        gid: newGid,
        gname: '默认分组', // Default Group Name
        isDefault: true,
        device_count: 0,
        deviceIds: [],
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
      };
      this.groups.set(newGid, defaultGroup);
      this.saveGroupsToStorage(); // Persist the new default group
    }

    return defaultGroup;
  }

  /**
   * (New) Assigns all devices with null group to the default group.
   * This is a comprehensive operation that:
   * 1. Finds or creates the default group.
   * 2. Gets all devices from DeviceStorageManager.
   * 3. Filters for devices where `group` is null.
   * 4. Updates the `group` and `groupId` for each of these devices.
   * 5. Updates the default group's `deviceIds` and `deviceCount`.
   * 6. Saves all changes to storage.
   */
  async assignUngroupedDevices() {
    console.log('[DeviceGroupAPIManager] Starting to assign ungrouped devices to default group.');

    const defaultGroup = this.findOrCreateDefaultGroup();
    const defaultGroupId = defaultGroup.gid;

    const allDevices = this.deviceStorageManager.getAllDevices();
    const ungroupedDevices = allDevices.filter(device => !device.group && !device.groupId);

    if (ungroupedDevices.length === 0) {
      console.log('[DeviceGroupAPIManager] No ungrouped devices found to assign.');
      return;
    }

    console.log(`[DeviceGroupAPIManager] Found ${ungroupedDevices.length} ungrouped devices to process.`);

    const deviceIdsForDefaultGroup = new Set(defaultGroup.deviceIds || []);

    ungroupedDevices.forEach(device => {
      device.group = defaultGroupId;
      device.groupId = defaultGroupId;
      deviceIdsForDefaultGroup.add(device.did);
    });

    defaultGroup.deviceIds = Array.from(deviceIdsForDefaultGroup);
    defaultGroup.deviceCount = defaultGroup.deviceIds.length;
    defaultGroup.device_count = defaultGroup.deviceIds.length; // Also update this property if used

    console.log(`[DeviceGroupAPIManager] Default group '${defaultGroup.gname}' now contains ${defaultGroup.deviceCount} devices.`);

    // --- Persist all changes to storage ---
    this.deviceStorageManager.storeAllDevices(allDevices);
    this.groups.set(defaultGroupId, defaultGroup);
    this.storage.saveDeviceGroups(Array.from(this.groups.values()));

    console.log('[DeviceGroupAPIManager] Successfully assigned devices and saved all changes.');
  }

  /**
   * (New) Gets the default group object.
   * @returns {object|null} The default group object or null if not found.
   */
  getDefaultGroup() {
    for (const group of this.groups.values()) {
      if (group.isDefault) {
        return group;
      }
    }
    // Also check by name, just in case
    for (const group of this.groups.values()) {
      if (group.gname === '默认分组') {
        return group;
      }
    }
    return null;
  }
}

module.exports = DeviceGroupAPIManager;

const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class DeviceGroupAPIManager {
  constructor(apiRegistry = null, deviceStorageManager = null) {
    this.apiRegistry = apiRegistry;
    this.storage = new UnifiedStorage();
    this.deviceStorageManager = deviceStorageManager; // 存储设备管理器实例
    this.groups = new Map(); // 本地分组缓存
    this.isInitialized = false;
    this.offlineMode = false; // 离线调试模式标记

    // 传感器历史数据管理
    this.sensorHistoryData = new Map(); // deviceId -> 历史数据数组
    this.maxHistoryDays = 7; // 保留7天历史数据
    this.maxDataPointsPerDay = 24; // 每天24个数据点（每小时1个）
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
      console.log('Group API manager initialized successfully');
      return {
        success: true,
        message: '分组API管理器初始化成功',
        groupCount: this.groups.size,
        syncResult: syncResult
      };
    } catch (error) {
      console.error('Group API manager initialization failed:', error);
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
        console.log(`Loaded ${groupsData.length} groups from local storage`);
      }
    } catch (error) {
      console.error('Failed to load group data from local storage:', error);
    }
  }

  // 从服务端同步分组数据
  async syncGroupsFromServer() {
    try {
      if (!this.apiRegistry || this.offlineMode) {
        console.log('Skip server sync: API registry not set or offline mode');
        return { success: false, message: 'API注册器未设置或处于离线模式' };
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

        console.log(`Synced ${response.data.length} groups from server`);
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
      console.error('Failed to synchronize group data from server:', error);
      return { success: false, message: '同步失败：' + error.message };
    }
  }

  // 创建新分组
  async createGroup(gname) {
    console.log('🔧 [Backend Debug] GroupAPI - Starting to create group');
    console.log('🔧 [Backend Debug] Group name:', gname);
    console.log('🔧 [Backend Debug] API registry status:', !!this.apiRegistry);
    console.log('🔧 [Backend Debug] Current group count:', this.groups.size);
    console.log('🔧 [Backend Debug] Offline mode:', this.offlineMode);

    try {
      if (!gname || gname.trim() === '') {
        console.log('❌ [Backend Debug] Group name is empty');
        return { success: false, message: '分组名称不能为空' };
      }

      const trimmedName = gname.trim();
      console.log('🔧 [Backend Debug] Trimmed group name:', trimmedName);

      // 检查重名
      const existingGroups = Array.from(this.groups.values());
      const duplicateGroup = existingGroups.find(g => g.gname === trimmedName);
      if (duplicateGroup) {
        console.log('❌ [Backend Debug] Group name already exists:', duplicateGroup);
        return { success: false, message: '分组名称已存在' };
      }

      // 检查是否为离线模式或API注册器不可用
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Backend Debug] Offline mode: creating group locally');

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

        console.log('🟡 [Backend Debug] Group object created in offline mode:', newGroup);
        this.groups.set(mockGid, newGroup);
        console.log('🟡 [Backend Debug] Added to local cache, current group count:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🟡 [Backend Debug] Saved to local storage');

        console.log(`✅ [Backend Debug] Group created successfully in offline mode: ${trimmedName} (${mockGid})`);
        return {
          success: true,
          message: '分组创建成功（离线模式）',
          data: {
            gid: mockGid,
            gname: trimmedName
          }
        };
      }

      console.log('🔧 [Backend Debug] Calling API to create group...');
      const response = await this.apiRegistry.callAPI('createGroup', {
        gname: trimmedName
      });
      console.log('🔧 [Backend Debug] API response:', response);

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

        console.log('🔧 [Backend Debug] New group object created:', newGroup);
        this.groups.set(response.data.gid, newGroup);
        console.log('🔧 [Backend Debug] Added to local cache, current group count:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🔧 [Backend Debug] Saved to local storage');

        console.log(`✅ [Backend Debug] Group created successfully: ${trimmedName} (${response.data.gid})`);
        return {
          success: true,
          message: '分组创建成功',
          data: {
            gid: response.data.gid,
            gname: response.data.gname
          }
        };
      } else {
        console.log('❌ [Backend Debug] API response failed:', response?.message || 'Unknown error');
        return {
          success: false,
          message: response?.message || '分组创建失败'
        };
      }
    } catch (error) {
      console.error('❌ [Backend Debug] Exception while creating group:', error);
      console.error('❌ [Backend Debug] Error stack:', error.stack);

      // 在API调用失败时，尝试离线模式
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log('🟡 [Backend Debug] Network error, switching to offline mode');
        this.offlineMode = true;
        return await this.createGroup(gname); // 递归调用，使用离线模式
      }

      return { success: false, message: '创建失败：' + error.message };
    }
  }

  // 删除分组
  async deleteGroup(gid) {
    console.log('🔧 [Backend Debug] GroupAPI - Starting to delete group');
    console.log('🔧 [Backend Debug] Group ID:', gid);
    console.log('🔧 [Backend Debug] API registry status:', !!this.apiRegistry);
    console.log('🔧 [Backend Debug] Current group count:', this.groups.size);

    try {
      if (!this.apiRegistry) {
        console.log('❌ [Backend Debug] API registry not set');
        return { success: false, message: 'API注册器未设置' };
      }

      if (!gid) {
        console.log('❌ [Backend Debug] Group ID is empty');
        return { success: false, message: '分组ID不能为空' };
      }

      // 检查分组是否存在
      const targetGroup = this.groups.get(gid);
      if (!targetGroup) {
        console.log('❌ [Backend Debug] Target group does not exist:', gid);
        return { success: false, message: '分组不存在' };
      }

      console.log('🔧 [Backend Debug] Group info to be deleted:', targetGroup);

      // 检查是否为默认分组
      if (targetGroup.gname === '默认分组') {
        console.log('❌ [Backend Debug] Attempting to delete the default group');
        return { success: false, message: '默认分组不能删除' };
      }

      // 获取默认分组
      const defaultGroup = Array.from(this.groups.values()).find(g => g.gname === '默认分组');
      if (!defaultGroup) {
        console.log('❌ [Backend Debug] Could not find the default group');
        return { success: false, message: '找不到默认分组' };
      }

      // 获取该分组下的所有设备
      if (!this.deviceStorageManager) {
        console.error('❌ [Backend Debug] DeviceStorageManager not initialized');
        return { success: false, message: '内部错误：设备管理器未初始化' };
      }
      const devices = this.deviceStorageManager.getAllDevices();
      const groupDevices = devices.filter(device => device.groupId === gid);
      console.log('🔧 [Backend Debug] Number of devices in the group:', groupDevices.length);

      // 将设备移动到默认分组
      for (const device of groupDevices) {
        await this.setDeviceGroup(device.did, defaultGroup.gid);
      }

      // 检查是否为离线模式或API注册器不可用
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Backend Debug] Offline mode: deleting group locally');

        // 从本地缓存删除
        console.log('🟡 [Backend Debug] Deleting group from local cache');
        this.groups.delete(gid);
        console.log('🟡 [Backend Debug] Group count after deletion:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🟡 [Backend Debug] Saved to local storage');

        console.log(`✅ [Backend Debug] Group deleted successfully in offline mode: ${gid}`);

        return {
          success: true,
          message: '分组删除成功（离线模式）',
          data: {
            affected_devices: groupDevices.length
          }
        };
      }

      console.log('🔧 [Backend Debug] Calling API to delete group...');
      const response = await this.apiRegistry.callAPI('deleteGroup', {
        gid: gid
      });
      console.log('🔧 [Backend Debug] API response:', response);

      if (response && response.code === 200) {
        // 从本地缓存删除
        console.log('🔧 [Backend Debug] Deleting group from local cache');
        this.groups.delete(gid);
        console.log('🔧 [Backend Debug] Group count after deletion:', this.groups.size);

        // 保存到本地存储
        this.saveGroupsToStorage();
        console.log('🔧 [Backend Debug] Saved to local storage');

        console.log(`✅ [Backend Debug] Group deleted successfully: ${gid}, number of affected devices: ${groupDevices.length}`);

        return {
          success: true,
          message: '分组删除成功',
          data: {
            affected_devices: groupDevices.length
          }
        };
      } else {
        console.log('❌ [Backend Debug] API response failed:', response?.message || 'Unknown error');
        return {
          success: false,
          message: response?.message || '分组删除失败'
        };
      }
    } catch (error) {
      console.error('❌ [Backend Debug] Exception while deleting group:', error);
      console.error('❌ [Backend Debug] Error stack:', error.stack);

      // 在API调用失败时，尝试离线模式
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log('🟡 [Backend Debug] Network error, switching to offline mode');
        this.offlineMode = true;
        return await this.deleteGroup(gid); // 递归调用，使用离线模式
      }

      return { success: false, message: '删除失败：' + error.message };
    }
  }

  // 设置设备分组
  async setDeviceGroup(deviceId, groupId) {
    try {
      if (!deviceId) {
        return { success: false, message: '设备ID不能为空' };
      }

      // 验证设备是否存在
      if (!this.deviceStorageManager) {
        return { success: false, message: '设备存储管理器未设置' };
      }

      const device = this.deviceStorageManager.getDevice(deviceId);
      if (!device) {
        return { success: false, message: `设备不存在: ${deviceId}` };
      }

      // 如果指定了新分组，验证分组是否存在
      if (groupId && !this.hasGroup(groupId)) {
        return { success: false, message: `分组不存在: ${groupId}` };
      }

      // 记录原分组信息
      const oldGroupId = device.groupId || device.group;
      console.log(`🔄 [DeviceGroup] Moving device ${deviceId} from group ${oldGroupId} to ${groupId}`);

      // 如果设备有传感器历史数据，这些数据保持在当前位置
      // 历史数据不需要随设备移动，因为它们是按设备ID存储的
      const isHistoryDevice = this.isSensorDevice(device.type);
      if (isHistoryDevice) {
        const historyDataCount = this.sensorHistoryData.get(deviceId)?.length || 0;
        console.log(`📊 [DeviceGroup] Device ${deviceId} has ${historyDataCount} historical data points (will remain accessible)`);
      }

      // 首先在本地更新设备分组信息
      const localUpdateResult = this.deviceStorageManager.setDeviceGroup(deviceId, groupId);
      if (!localUpdateResult.success) {
        return localUpdateResult;
      }

      // 如果在离线模式或API不可用，只进行本地更新
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [DeviceGroup] Offline mode: device group updated locally only');

        // 更新分组统计信息
        this.refreshGroupStats();

        return {
          success: true,
          message: '设备分组设置成功（离线模式）',
          data: {
            device_id: deviceId,
            group_id: groupId,
            old_group_id: oldGroupId,
            offline_mode: true
          }
        };
      }

      // 调用API通知服务端
      console.log(`🌐 [DeviceGroup] Calling API to update device group...`);
      const response = await this.apiRegistry.callAPI('setGroup', {
        device_id: deviceId,
        group_id: groupId // 传null表示移除分组
      });

      if (response && response.code === 200) {
        console.log(`✅ [DeviceGroup] Device group updated successfully: ${deviceId} -> ${groupId || 'No Group'}`);

        // 更新分组统计信息
        this.refreshGroupStats();

        return {
          success: true,
          message: '设备分组设置成功',
          data: {
            device_id: response.data?.device_id || deviceId,
            group_id: response.data?.group_id || groupId,
            old_group_id: oldGroupId
          }
        };
      } else {
        // API调用失败，回滚本地更改
        console.error(`❌ [DeviceGroup] API failed, rolling back local changes...`);
        this.deviceStorageManager.setDeviceGroup(deviceId, oldGroupId);

        return {
          success: false,
          message: response?.message || '设备分组设置失败'
        };
      }
    } catch (error) {
      console.error('❌ [DeviceGroup] Failed to set device group:', error);

      // 在API调用失败时，如果是网络错误，可以选择保留本地更改
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log('🟡 [DeviceGroup] Network error, keeping local changes (offline mode)');
        this.offlineMode = true;

        // 更新分组统计信息
        this.refreshGroupStats();

        return {
          success: true,
          message: '设备分组设置成功（网络错误，已切换到离线模式）',
          data: {
            device_id: deviceId,
            group_id: groupId,
            offline_mode: true,
            network_error: true
          }
        };
      }

      return { success: false, message: '设置失败：' + error.message };
    }
  }

  /**
   * 移动设备到指定分组（高级方法，包含验证和批处理）
   * @param {string} deviceId - 设备ID
   * @param {string} targetGroupId - 目标分组ID
   * @param {string} targetGroupName - 目标分组名称（用于验证）
   * @returns {object} 操作结果
   */
  async moveDeviceToGroup(deviceId, targetGroupId, targetGroupName = null) {
    try {
      console.log(`🔄 [DeviceGroup] Starting device move: ${deviceId} -> ${targetGroupId} (${targetGroupName})`);

      // 验证设备存在
      const device = this.deviceStorageManager?.getDevice(deviceId);
      if (!device) {
        return { success: false, message: `设备不存在: ${deviceId}` };
      }

      // 验证目标分组存在
      const targetGroup = this.getGroup(targetGroupId);
      if (!targetGroup) {
        return { success: false, message: `目标分组不存在: ${targetGroupName || targetGroupId}` };
      }

      // 验证分组名称匹配（如果提供了名称）
      if (targetGroupName && targetGroup.gname !== targetGroupName) {
        return { success: false, message: `分组名称不匹配，期望: ${targetGroupName}，实际: ${targetGroup.gname}` };
      }

      // 检查是否已经在目标分组
      const currentGroupId = device.groupId || device.group;
      if (currentGroupId === targetGroupId) {
        return {
          success: true,
          message: `设备已在目标分组中`,
          data: {
            device_id: deviceId,
            group_id: targetGroupId,
            no_change: true
          }
        };
      }

      // 执行分组移动
      const moveResult = await this.setDeviceGroup(deviceId, targetGroupId);

      if (moveResult.success) {
        console.log(`✅ [DeviceGroup] Device moved successfully: ${device.name} -> ${targetGroup.gname}`);

        return {
          success: true,
          message: `设备"${device.name}"已成功移动到分组"${targetGroup.gname}"`,
          data: {
            device_id: deviceId,
            device_name: device.name,
            group_id: targetGroupId,
            group_name: targetGroup.gname,
            old_group_id: currentGroupId,
            move_time: new Date().toISOString()
          }
        };
      } else {
        return moveResult;
      }

    } catch (error) {
      console.error(`❌ [DeviceGroup] Device move failed:`, error);
      return { success: false, message: '设备移动失败：' + error.message };
    }
  }

  /**
   * 批量移动设备到分组
   * @param {Array} deviceIds - 设备ID列表
   * @param {string} targetGroupId - 目标分组ID
   * @returns {object} 批量操作结果
   */
  async batchMoveDevicesToGroup(deviceIds, targetGroupId) {
    try {
      console.log(`🔄 [DeviceGroup] Starting batch device move: ${deviceIds.length} devices -> ${targetGroupId}`);

      const results = [];
      let successCount = 0;
      let failCount = 0;

      for (const deviceId of deviceIds) {
        const result = await this.setDeviceGroup(deviceId, targetGroupId);
        results.push({
          deviceId: deviceId,
          success: result.success,
          message: result.message
        });

        if (result.success) {
          successCount++;
        } else {
          failCount++;
        }
      }

      console.log(`✅ [DeviceGroup] Batch move completed: ${successCount} success, ${failCount} failed`);

      return {
        success: failCount === 0,
        message: `批量移动完成：${successCount} 个成功，${failCount} 个失败`,
        data: {
          total: deviceIds.length,
          success_count: successCount,
          fail_count: failCount,
          results: results
        }
      };

    } catch (error) {
      console.error(`❌ [DeviceGroup] Batch device move failed:`, error);
      return { success: false, message: '批量移动失败：' + error.message };
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
    console.log('🟡 [Debug] Group manager switched to offline mode');
  }

  // 禁用离线调试模式
  disableOfflineMode() {
    this.offlineMode = false;
    console.log('🟢 [Debug] Group manager switched to online mode');
  }

  // 检查是否处于离线模式
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
        deviceCount: 0,
        deviceIds: [],
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
      };
      this.groups.set(newGid, defaultGroup);
      this.saveGroupsToStorage(); // Persist the new default group
      console.log(`[DeviceGroupAPIManager] Created default group: ${newGid}`);
    }

    return defaultGroup;
  }

  /**
   * (New) Assigns all devices with null group to the default group.
   * This is a comprehensive operation that:
   * 1. Finds or creates the default group.
   * 2. Gets all devices from DeviceStorageManager.
   * 3. Filters for devices where all group fields are null.
   * 4. Updates all group fields for each of these devices.
   * 5. Updates the default group's `deviceIds` and `deviceCount`.
   * 6. Saves all changes to storage.
   */
  async assignUngroupedDevices() {
    console.log('[DeviceGroupAPIManager] Starting to assign ungrouped devices to default group.');

    const defaultGroup = this.findOrCreateDefaultGroup();
    const defaultGroupId = defaultGroup.gid;

    if (!this.deviceStorageManager) {
      console.error('[DeviceGroupAPIManager] DeviceStorageManager not available.');
      return;
    }

    const allDevices = this.deviceStorageManager.getAllDevices();
    // 修改过滤条件，检查所有可能的分组字段
    const ungroupedDevices = allDevices.filter(device =>
      !device.group && !device.groupId && !device.gid
    );

    if (ungroupedDevices.length === 0) {
      console.log('[DeviceGroupAPIManager] No ungrouped devices found to assign.');
      // 但仍需要更新默认分组的统计信息
      this.updateDefaultGroupStats();
      return;
    }

    console.log(`[DeviceGroupAPIManager] Found ${ungroupedDevices.length} ungrouped devices to process.`);

    // 更新设备的所有分组相关字段，确保一致性
    ungroupedDevices.forEach(device => {
      device.group = defaultGroupId;
      device.groupId = defaultGroupId;
      device.gid = defaultGroupId;
      console.log(`[DeviceGroupAPIManager] Assigned device ${device.did} to default group`);
    });

    // 更新默认分组统计信息
    this.updateDefaultGroupStats();

    // 保存所有更改
    this.deviceStorageManager.storeAllDevices(allDevices);
    this.saveGroupsToStorage();

    console.log('[DeviceGroupAPIManager] Successfully assigned devices and saved all changes.');
  }

  /**
   * 更新默认分组的统计信息
   */
  updateDefaultGroupStats() {
    const defaultGroup = this.getDefaultGroup();
    if (!defaultGroup || !this.deviceStorageManager) {
      return;
    }

    // 获取属于默认分组的所有设备
    const defaultGroupDevices = this.deviceStorageManager.getDevicesByGroup(defaultGroup.gid);
    const deviceIds = defaultGroupDevices.map(device => device.did);

    // 更新默认分组信息
    defaultGroup.deviceIds = deviceIds;
    defaultGroup.deviceCount = deviceIds.length;
    defaultGroup.device_count = deviceIds.length; // 保持两个字段一致
    defaultGroup.updated = new Date().toISOString();

    // 更新到内存缓存
    this.groups.set(defaultGroup.gid, defaultGroup);

    console.log(`[DeviceGroupAPIManager] Updated default group stats: ${deviceIds.length} devices`);
  }

  /**
   * (New) Gets the default group object.
   * @returns {object|null} The default group object or null if not found.
   */
  getDefaultGroup() {
    for (const group of this.groups.values()) {
      if (group.isDefault || group.gname === '默认分组') {
        return group;
      }
    }
    return null;
  }

  /**
   * 重新计算所有分组的设备统计信息
   */
  refreshGroupStats() {
    if (!this.deviceStorageManager) {
      console.warn('[DeviceGroupAPIManager] Cannot refresh stats: DeviceStorageManager not available.');
      return;
    }

    console.log('[DeviceGroupAPIManager] Refreshing group statistics...');

    this.groups.forEach((group, gid) => {
      const groupDevices = this.deviceStorageManager.getDevicesByGroup(gid);
      const deviceIds = groupDevices.map(device => device.did);

      group.deviceIds = deviceIds;
      group.deviceCount = deviceIds.length;
      group.device_count = deviceIds.length;
      group.updated = new Date().toISOString();

      console.log(`[DeviceGroupAPIManager] Group ${group.gname} has ${deviceIds.length} devices`);
    });

    this.saveGroupsToStorage();
    console.log('[DeviceGroupAPIManager] Group statistics refreshed.');
  }

  // ==================== 传感器历史数据管理 ====================

  /**
   * 添加传感器数据点
   * @param {string} deviceId - 设备ID
   * @param {object} dataPoint - 数据点
   */
  addSensorDataPoint(deviceId, dataPoint) {
    try {
      if (!this.sensorHistoryData.has(deviceId)) {
        this.sensorHistoryData.set(deviceId, []);
      }

      const history = this.sensorHistoryData.get(deviceId);

      // 添加时间戳
      const timestampedData = {
        ...dataPoint,
        timestamp: new Date().toISOString(),
        time: new Date().toISOString()
      };

      history.push(timestampedData);

      // 清理过期数据
      this.cleanupOldSensorData(deviceId);

      console.log(`Added sensor data point for device ${deviceId}, total points: ${history.length}`);
    } catch (error) {
      console.error(`Failed to add sensor data point for device ${deviceId}:`, error);
    }
  }

  /**
   * 获取传感器历史数据
   * @param {string} deviceId - 设备ID
   * @param {number} hours - 获取最近几小时的数据，默认24小时
   * @returns {Array} 历史数据数组
   */
  getSensorHistory(deviceId, hours = 24) {
    try {
      const history = this.sensorHistoryData.get(deviceId) || [];

      if (hours === 'all') {
        return [...history];
      }

      const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);

      return history.filter(dataPoint => {
        const dataTime = new Date(dataPoint.timestamp || dataPoint.time);
        return dataTime >= cutoffTime;
      });
    } catch (error) {
      console.error(`Failed to get sensor history for device ${deviceId}:`, error);
      return [];
    }
  }

  /**
   * 清理过期的传感器数据
   * @param {string} deviceId - 设备ID
   */
  cleanupOldSensorData(deviceId) {
    try {
      const history = this.sensorHistoryData.get(deviceId);
      if (!history || history.length === 0) return;

      const cutoffTime = new Date(Date.now() - this.maxHistoryDays * 24 * 60 * 60 * 1000);

      const filteredHistory = history.filter(dataPoint => {
        const dataTime = new Date(dataPoint.timestamp || dataPoint.time);
        return dataTime >= cutoffTime;
      });

      // 如果数据点太多，保留最新的数据
      const maxPoints = this.maxHistoryDays * this.maxDataPointsPerDay;
      if (filteredHistory.length > maxPoints) {
        filteredHistory.splice(0, filteredHistory.length - maxPoints);
      }

      this.sensorHistoryData.set(deviceId, filteredHistory);
    } catch (error) {
      console.error(`Failed to cleanup old sensor data for device ${deviceId}:`, error);
    }
  }

  /**
   * 批量更新传感器数据（用于SSE更新）
   * @param {Array} deviceUpdates - 设备更新数组
   */
  updateSensorDataFromSSE(deviceUpdates) {
    try {
      deviceUpdates.forEach(update => {
        if (this.isSensorDevice(update.type)) {
          const sensorData = this.extractSensorDataFromUpdate(update);
          if (sensorData) {
            this.addSensorDataPoint(update.deviceId || update.did, sensorData);
          }
        }
      });
    } catch (error) {
      console.error('Failed to update sensor data from SSE:', error);
    }
  }

  /**
   * 检查是否为传感器设备
   * @param {string} deviceType - 设备类型
   * @returns {boolean}
   */
  isSensorDevice(deviceType) {
    return deviceType === 'mi_temp_hum_sensor' ||
           deviceType === 'mi_air_sensor' ||
           deviceType === 'history';
  }

  /**
   * 从设备更新中提取传感器数据
   * @param {object} deviceUpdate - 设备更新对象
   * @returns {object|null} 传感器数据
   */
  extractSensorDataFromUpdate(deviceUpdate) {
    try {
      const sensorData = {};
      const status = deviceUpdate.status || {};

      // 提取温度数据
      if (status.temperature !== undefined) {
        sensorData.temperature = parseFloat(status.temperature);
      }

      // 提取湿度数据
      if (status.humidity !== undefined) {
        sensorData.humidity = parseFloat(status.humidity);
      }

      // 提取PM2.5数据
      if (status.pm25 !== undefined) {
        sensorData.pm25 = parseFloat(status.pm25);
      }

      // 如果没有任何传感器数据，返回null
      if (Object.keys(sensorData).length === 0) {
        return null;
      }

      return sensorData;
    } catch (error) {
      console.error('Failed to extract sensor data from update:', error);
      return null;
    }
  }

  /**
   * 生成模拟历史数据（用于离线调试模式）
   * @param {string} deviceId - 设备ID
   * @param {string} sensorType - 传感器类型
   * @param {number} hours - 生成多少小时的数据
   */
  generateMockSensorHistory(deviceId, sensorType, hours = 24) {
    try {
      console.log(`生成模拟传感器历史数据: ${deviceId} (${sensorType})`);

      const history = [];
      const now = new Date();

      for (let i = hours - 1; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);

        let dataPoint = {
          timestamp: timestamp.toISOString(),
          time: timestamp.toISOString()
        };

        // 根据传感器类型生成不同的数据
        if (sensorType === 'mi_temp_hum_sensor' || sensorType === 'history') {
          // 判断是否为温湿度传感器（检查设备名称）
          if (sensorType === 'history') {
            // 从设备存储管理器获取设备信息来判断传感器类型
            const device = this.deviceStorageManager?.getDevice(deviceId);
            if (device && device.name.includes('空气质量')) {
              // 空气质量传感器
              dataPoint.pm25 = Math.floor(Math.random() * 180 + 15); // 15-195 μg/m³
              dataPoint.temperature = Math.round((Math.random() * 10 + 20) * 10) / 10; // 20-30°C
              dataPoint.humidity = Math.floor(Math.random() * 30 + 40); // 40-70%
            } else {
              // 温湿度传感器
              dataPoint.temperature = Math.round((Math.random() * 12 + 18) * 10) / 10; // 18-30°C
              dataPoint.humidity = Math.floor(Math.random() * 35 + 35); // 35-70%
            }
          } else {
            // 温湿度传感器
            dataPoint.temperature = Math.round((Math.random() * 12 + 18) * 10) / 10; // 18-30°C
            dataPoint.humidity = Math.floor(Math.random() * 35 + 35); // 35-70%
          }
        } else if (sensorType === 'mi_air_sensor') {
          // 空气质量传感器
          dataPoint.pm25 = Math.floor(Math.random() * 180 + 15); // 15-195 μg/m³
          dataPoint.temperature = Math.round((Math.random() * 10 + 20) * 10) / 10; // 20-30°C
          dataPoint.humidity = Math.floor(Math.random() * 30 + 40); // 40-70%
        }

        history.push(dataPoint);
      }

      this.sensorHistoryData.set(deviceId, history);
      console.log(`生成了 ${history.length} 个历史数据点`);

      return history;
    } catch (error) {
      console.error(`Failed to generate mock sensor history for ${deviceId}:`, error);
      return [];
    }
  }

  /**
   * 为所有传感器设备生成模拟历史数据
   */
  generateMockHistoryForAllSensors() {
    try {
      if (!this.deviceStorageManager) {
        console.warn('Device storage manager not available for generating mock history');
        return;
      }

      const allDevices = this.deviceStorageManager.getAllDevices();
      const sensorDevices = allDevices.filter(device => this.isSensorDevice(device.type));

      console.log(`为 ${sensorDevices.length} 个传感器设备生成模拟历史数据...`);

      sensorDevices.forEach(device => {
        this.generateMockSensorHistory(device.did, device.type, 48); // 生成48小时数据
      });

      console.log('模拟传感器历史数据生成完成');
    } catch (error) {
      console.error('Failed to generate mock history for all sensors:', error);
    }
  }

  /**
   * 清空所有传感器历史数据
   */
  clearAllSensorHistory() {
    this.sensorHistoryData.clear();
    console.log('已清空所有传感器历史数据');
  }

  /**
   * 获取传感器历史数据统计
   * @returns {object} 统计信息
   */
  getSensorHistoryStats() {
    const stats = {
      totalSensors: this.sensorHistoryData.size,
      totalDataPoints: 0,
      sensorsWithData: []
    };

    this.sensorHistoryData.forEach((history, deviceId) => {
      stats.totalDataPoints += history.length;
      stats.sensorsWithData.push({
        deviceId: deviceId,
        dataPoints: history.length,
        latestUpdate: history.length > 0 ? history[history.length - 1].timestamp : null
      });
    });

    return stats;
  }

  /**
   * 从SSE更新传感器历史数据（新方法）
   * @param {string} deviceId - 设备ID
   * @param {string} metricType - 指标类型（temperature, humidity, pm25等）
   * @param {Array} historyDataPoints - 历史数据点数组
   * @returns {object} 操作结果
   */
  updateSensorHistoryFromSSE(deviceId, metricType, historyDataPoints) {
    try {
      console.log(`[SENSOR_HISTORY] Updating sensor history for device ${deviceId}, metric: ${metricType}, points: ${historyDataPoints.length}`);

      if (!Array.isArray(historyDataPoints) || historyDataPoints.length === 0) {
        return { success: false, message: 'Invalid history data points' };
      }

      // 确保设备有历史数据存储
      if (!this.sensorHistoryData.has(deviceId)) {
        this.sensorHistoryData.set(deviceId, []);
      }

      // 获取现有的历史数据
      const existingHistory = this.sensorHistoryData.get(deviceId) || [];
      console.log(`[SENSOR_HISTORY] Existing history points: ${existingHistory.length}`);

      // 创建时间戳到数据点的映射，用于合并数据
      const timeToDataMap = new Map();

      // 首先添加现有的历史数据到映射中
      existingHistory.forEach(point => {
        const timeKey = point.timestamp || point.time;
        if (timeKey) {
          timeToDataMap.set(timeKey, { ...point });
        }
      });

      // 然后添加或更新新的指标数据
      historyDataPoints.forEach(point => {
        const timeKey = point.hour;
        if (timeToDataMap.has(timeKey)) {
          // 如果时间点已存在，更新该指标的值
          timeToDataMap.get(timeKey)[metricType] = point.value;
        } else {
          // 如果时间点不存在，创建新的数据点
          timeToDataMap.set(timeKey, {
            timestamp: point.hour,
            time: point.hour,
            [metricType]: point.value,
            deviceId: deviceId,
            source: 'sse_history'
          });
        }
      });

      // 将映射转换回数组，并按时间排序
      const mergedHistory = Array.from(timeToDataMap.values()).sort((a, b) => {
        const timeA = new Date(a.timestamp || a.time);
        const timeB = new Date(b.timestamp || b.time);
        return timeA - timeB;
      });

      // 更新存储的历史数据
      this.sensorHistoryData.set(deviceId, mergedHistory);

      console.log(`[SENSOR_HISTORY] Successfully merged ${historyDataPoints.length} new ${metricType} points with existing data`);
      console.log(`[SENSOR_HISTORY] Total history points after merge: ${mergedHistory.length}`);

      // 保存到本地存储
      this.saveSensorHistoryToStorage(deviceId, mergedHistory);

      return {
        success: true,
        message: `Updated ${historyDataPoints.length} history data points for ${metricType}`,
        dataPointCount: historyDataPoints.length,
        totalHistoryPoints: mergedHistory.length,
        metricType: metricType,
        deviceId: deviceId
      };
    } catch (error) {
      console.error(`[SENSOR_HISTORY] Failed to update sensor history for device ${deviceId}:`, error);
      return { success: false, message: 'Failed to update sensor history: ' + error.message };
    }
  }

  /**
   * 保存传感器历史数据到本地存储
   * @param {string} deviceId - 设备ID
   * @param {Array} historyData - 历史数据
   */
  saveSensorHistoryToStorage(deviceId, historyData) {
    try {
      // 使用UnifiedStorage保存传感器历史数据
      this.storage.saveSensorHistory(deviceId, historyData);
      console.log(`[SENSOR_HISTORY] Saved ${historyData.length} history points to storage for device ${deviceId}`);
    } catch (error) {
      console.error(`[SENSOR_HISTORY] Failed to save sensor history to storage for device ${deviceId}:`, error);
    }
  }

  /**
   * 从本地存储加载传感器历史数据
   * @param {string} deviceId - 设备ID
   * @returns {Array} 历史数据数组
   */
  loadSensorHistoryFromStorage(deviceId) {
    try {
      const historyData = this.storage.getSensorHistory(deviceId, 'all');
      if (historyData && Array.isArray(historyData)) {
        this.sensorHistoryData.set(deviceId, historyData);
        console.log(`[SENSOR_HISTORY] Loaded ${historyData.length} history points from storage for device ${deviceId}`);
        return historyData;
      }
      return [];
    } catch (error) {
      console.error(`[SENSOR_HISTORY] Failed to load sensor history from storage for device ${deviceId}:`, error);
      return [];
    }
  }
}

module.exports = DeviceGroupAPIManager;

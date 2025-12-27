const UnifiedStorage = require('../../services/storage/UnifiedStorage');

/**
 * 设备控制管理器
 * 负责设备控制指令的验证、发送和状态同步
 */
class DeviceControlManager {
  constructor(apiRegistry = null, deviceStorageManager = null) {
    this.apiRegistry = apiRegistry;
    this.deviceStorageManager = deviceStorageManager;
    this.storage = new UnifiedStorage();
    this.isInitialized = false;
    this.offlineMode = false; // 离线模式标记

    // 设备属性值范围配置
    this.deviceLimits = {
      // 空调类设备
      'mi_ac': {
        target_temperature: { min: 16, max: 30, precision: 0.1 },
        fan_speed: { values: ['low', 'medium', 'high', 'auto'] },
        mode: { values: ['cool', 'heat', 'dry', 'fan'] },
        power: { values: ['ON', 'OFF'] }
      },
      'midea_ac': {
        target_temperature: { min: 16, max: 30, precision: 0.1 },
        fan_speed: { values: ['low', 'medium', 'high', 'auto'] },
        mode: { values: ['cool', 'heat', 'dry', 'fan'] },
        power: { values: ['ON', 'OFF'] }
      },

      // 加湿器 - 统一使用ON/OFF格式
      'mi_humidifier': {
        power: { values: ['ON', 'OFF'] },
        status: { values: ['running', 'paused', 'off'] },
        mode: { values: ['auto', 'sleep', 'strong'] },
        target_humidity: { min: 30, max: 80, precision: 1 }
      },
      'midea_humidifier': {
        power: { values: ['ON', 'OFF'] },
        status: { values: ['on', 'off'] },
        mode: { values: ['auto', 'sleep', 'strong'] },
        target_humidity: { min: 30, max: 80, precision: 1 }
      },

      // 除湿器 - 统一使用ON/OFF格式
      'mi_dehumidifier': {
        power: { values: ['ON', 'OFF'] },
        mode: { values: ['auto', 'sleep', 'dry'] },
        target_humidity: { min: 30, max: 80, precision: 1 }
      },
      'midea_dehumidifier': {
        power: { values: ['ON', 'OFF'] },
        mode: { values: ['auto', 'sleep', 'dry'] },
        target_humidity: { min: 30, max: 80, precision: 1 }
      },

      // 空气净化器 - 统一使用ON/OFF格式
      'mi_air_purifier': {
        power: { values: ['ON', 'OFF'] },
        mode: { values: ['auto', 'silent', 'strong'] },
        fan_level: { values: [1, 2, 3] }
      },
      'midea_air_purifier': {
        power: { values: ['ON', 'OFF'] },
        mode: { values: ['auto', 'silent', 'strong'] },
        fan_level: { values: [1, 2, 3] }
      }
    };

    // 设备状态约束规则
    this.constraintRules = {
      // 空调约束
      'mi_ac': {
        'target_temperature': {
          disallowedWhen: [
            { property: 'mode', value: 'dry' }
          ]
        }
      },
      'midea_ac': {
        'target_temperature': {
          disallowedWhen: [
            { property: 'mode', value: 'dry' }
          ]
        }
      },

      // 加湿器约束
      'mi_humidifier': {
        'target_humidity': {
          disallowedWhen: [
            { property: 'status', values: ['paused', 'off'] },
            { property: 'mode', value: 'auto' }
          ]
        }
      },
      'midea_humidifier': {
        'target_humidity': {
          disallowedWhen: [
            { property: 'status', values: ['off'] },
            { property: 'mode', value: 'auto' }
          ]
        }
      },

      // 空气净化器约束 - 根据文档修正power值判断
      'mi_air_purifier': {
        'mode': {
          disallowedWhen: [
            { property: 'power', value: 'OFF' }
          ]
        },
        'fan_level': {
          disallowedWhen: [
            { property: 'power', value: 'OFF' },
            { property: 'mode', value: 'auto' }
          ]
        }
      },
      'midea_air_purifier': {
        'mode': {
          disallowedWhen: [
            { property: 'power', value: 'OFF' }
          ]
        },
        'fan_level': {
          disallowedWhen: [
            { property: 'power', value: 'OFF' },
            { property: 'mode', value: 'auto' }
          ]
        }
      }
    };
  }

  // 设置API注册器
  setApiRegistry(apiRegistry) {
    this.apiRegistry = apiRegistry;
  }

  // 设置设备存储管理器
  setDeviceStorageManager(deviceStorageManager) {
    this.deviceStorageManager = deviceStorageManager;
  }

  // 初始化控制管理器
  async initialize() {
    if (this.isInitialized) {
      return { success: true, message: '设备控制管理器已初始化' };
    }

    try {
      this.isInitialized = true;
      console.log('🔧 [Control] Device control manager initialized successfully');
      console.log('🔧 [Control] Initial offline mode status:', this.offlineMode);
      return {
        success: true,
        message: '设备控制管理器初始化成功'
      };
    } catch (error) {
      console.error('❌ [Control] Device control manager initialization failed:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  /**
   * 验证设备是否可控制
   * @param {object} device - 设备对象
   * @returns {object} 验证结果
   */
  validateDeviceControllable(device) {
    if (!device) {
      return { valid: false, message: '设备不存在' };
    }

    // 检查设备类型是否为传感器（传感器不可控制）
    const sensorTypes = ['mi_temp_hum_sensor', 'mi_air_sensor', 'history'];
    if (sensorTypes.includes(device.type)) {
      return { valid: false, message: '传感器设备不支持控制' };
    }

    // 允许控制离线设备（用户需求：即使设备显示离线也要能控制）
    // 在离线模式下，明确允许控制离线设备
    if (this.offlineMode) {
      console.log('🟡 [Control] Offline mode: allowing control of offline devices');
      return { valid: true, message: '设备可控制（离线模式）' };
    }

    // 在线模式下，也允许控制离线设备（可能设备实际可控制但状态显示为离线）
    if (!device.online) {
      console.log('🟡 [Control] Device appears offline but allowing control attempt');
      return { valid: true, message: '设备可控制（离线状态下尝试控制）' };
    }

    return { valid: true, message: '设备可控制' };
  }

  /**
   * 验证控制命令
   * @param {object} device - 设备对象
   * @param {string} operation - 操作属性
   * @param {any} value - 操作值
   * @returns {object} 验证结果
   */
  validateControlCommand(device, operation, value) {
    console.log(`🔧 [Control] Validating command: ${device.did} -> ${operation}=${value}`);

    // 1. 基础验证
    const controllableCheck = this.validateDeviceControllable(device);
    if (!controllableCheck.valid) {
      return controllableCheck;
    }

    // 2. 检查设备是否支持该属性
    const deviceLimits = this.deviceLimits[device.type];
    if (!deviceLimits || !deviceLimits[operation]) {
      return { valid: false, message: `设备不支持属性 ${operation}` };
    }

    // 3. 验证属性值范围
    const propertyConfig = deviceLimits[operation];
    const valueValidation = this.validatePropertyValue(operation, value, propertyConfig);
    if (!valueValidation.valid) {
      return valueValidation;
    }

    // 4. 检查设备状态约束
    const constraintCheck = this.checkDeviceConstraints(device, operation, value);
    if (!constraintCheck.valid) {
      return constraintCheck;
    }

    // 5. 特殊规则：关机状态只能执行开机操作
    if (device.status && this.isPowerOff(device) && operation !== 'power') {
      return { valid: false, message: '设备已关机，只能执行开机操作' };
    }

    return { valid: true, message: '控制命令验证通过' };
  }

  /**
   * 判断设备是否处于关机状态
   * @param {object} device - 设备对象
   * @returns {boolean} 是否关机
   */
  isPowerOff(device) {
    if (!device.status || device.status.power === undefined) {
      return true; // 没有power状态认为是关机
    }

    // 统一使用ON/OFF格式判断
    return device.status.power === 'OFF';
  }

  /**
   * 验证属性值
   * @param {string} property - 属性名
   * @param {any} value - 属性值
   * @param {object} config - 属性配置
   * @returns {object} 验证结果
   */
  validatePropertyValue(property, value, config) {
    // 检查枚举值
    if (config.values) {
      if (!config.values.includes(value)) {
        return {
          valid: false,
          message: `${property} 值必须为 ${config.values.join(', ')} 之一`
        };
      }
      return { valid: true };
    }

    // 检查数值范围
    if (config.min !== undefined && config.max !== undefined) {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return { valid: false, message: `${property} 必须为数值` };
      }

      if (numValue < config.min || numValue > config.max) {
        return {
          valid: false,
          message: `${property} 值必须在 ${config.min} 到 ${config.max} 之间`
        };
      }

      // 检查精度
      if (config.precision) {
        const decimalPlaces = (numValue.toString().split('.')[1] || '').length;
        const allowedDecimals = config.precision.toString().split('.')[1]?.length || 0;
        if (decimalPlaces > allowedDecimals) {
          return {
            valid: false,
            message: `${property} 精度不能超过 ${config.precision}`
          };
        }
      }

      return { valid: true };
    }

    return { valid: true };
  }

  /**
   * 检查设备状态约束
   * @param {object} device - 设备对象
   * @param {string} operation - 操作属性
   * @param {any} value - 操作值
   * @returns {object} 检查结果
   */
  checkDeviceConstraints(device, operation, value) {
    const constraints = this.constraintRules[device.type];
    if (!constraints || !constraints[operation]) {
      return { valid: true };
    }

    const operationConstraints = constraints[operation];
    if (!operationConstraints.disallowedWhen) {
      return { valid: true };
    }

    // 特殊情况：如果是开启设备的power操作，则允许通过
    if (operation === 'power' && (value === 'ON' || value === 1 || value === true)) {
      console.log('🔧 [Control] Power ON operation: bypassing other constraints');
      return { valid: true };
    }

    // 检查每个约束条件
    for (const constraint of operationConstraints.disallowedWhen) {
      // 获取当前设备状态值（标准化后的）
      const normalizedDevice = this.normalizeDeviceStatus(device);
      const currentValue = normalizedDevice.status?.[constraint.property];

      // 单值约束
      if (constraint.value !== undefined && currentValue === constraint.value) {
        return {
          valid: false,
          message: `当 ${constraint.property} 为 ${constraint.value} 时，不能设置 ${operation}`
        };
      }

      // 多值约束
      if (constraint.values && constraint.values.includes(currentValue)) {
        return {
          valid: false,
          message: `当 ${constraint.property} 为 ${currentValue} 时，不能设置 ${operation}`
        };
      }
    }

    return { valid: true };
  }

  /**
   * 启用离线模式
   */
  enableOfflineMode() {
    console.log('⚠️ [Control] WARNING: Enabling offline mode for device control!');
    console.log('⚠️ [Control] Stack trace:', new Error().stack);
    this.offlineMode = true;
    console.log('🟡 [Control] Device control manager switched to offline mode');
  }

  /**
   * 禁用离线模式
   */
  disableOfflineMode() {
    this.offlineMode = false;
    console.log('🟢 [Control] Device control manager switched to online mode');
  }

  /**
   * 检查是否处于离线模式
   */
  isOfflineMode() {
    return this.offlineMode;
  }

  /**
   * 控制设备
   * @param {string} did - 设备ID
   * @param {string} operation - 操作属性
   * @param {any} value - 操作值
   * @returns {object} 控制结果
   */
  async controlDevice(did, operation, value) {
    console.log(`🎮 [Control] Starting device control: ${did} -> ${operation}=${value}`);
    console.log(`🎮 [Control] Offline mode: ${this.offlineMode}`);
    console.log(`🎮 [Control] API Registry available: ${!!this.apiRegistry}`);

    try {
      // 1. 获取设备信息
      if (!this.deviceStorageManager) {
        return { success: false, message: '设备存储管理器未设置' };
      }

      const device = this.deviceStorageManager.getDevice(did);
      if (!device) {
        return { success: false, message: '设备不存在' };
      }

      console.log(`🎮 [Control] Device found: ${device.name} (${device.type})`);

      // 1.5. 标准化power值到统一ON/OFF格式（所有设备统一）
      if (operation === 'power') {
        value = this.normalizePowerValue(value);
        console.log(`🔧 [Control] Normalized power value: ${value} for device type: ${device.type}`);
      } else {
        console.log(`🔧 [Control] Using original value: ${value} for operation: ${operation}`);
      }

      // 2. 验证控制命令
      const validation = this.validateControlCommand(device, operation, value);
      if (!validation.valid) {
        console.log(`❌ [Control] Validation failed: ${validation.message}`);
        return { success: false, message: validation.message };
      }

      console.log(`✅ [Control] Command validation passed`);

      // 3. 检查是否为离线模式或API不可用
      if (this.offlineMode) {
        console.log(`🟡 [Control] Offline mode enabled: executing control locally`);

        // 直接更新本地设备状态
        const updateResult = await this.updateLocalDeviceStatus(did, operation, value);
        console.log(`💾 [Control] Local status update result:`, updateResult);

        if (updateResult.success) {
          return {
            success: true,
            message: '设备控制成功（离线模式）',
            data: {
              did: did,
              operation: operation,
              value: value,
              localUpdate: updateResult,
              offline: true
            }
          };
        } else {
          return {
            success: false,
            message: '离线模式控制失败：' + updateResult.message
          };
        }
      }

      // 4. 检查API是否可用
      if (!this.apiRegistry) {
        console.log(`❌ [Control] API Registry not available - cannot perform online control`);
        return {
          success: false,
          message: '设备控制失败：API服务不可用，且未启用离线模式'
        };
      }

      // 5. 在线模式：调用API执行控制
      console.log(`🌐 [DEVICE_CONTROL_API] Online mode: calling device control API...`);
      console.log(`🌐 [DEVICE_CONTROL_API] API Registry available: ${!!this.apiRegistry}`);

      const requestData = {
        did: did,
        control: {
          operation: operation,
          value: value
        }
      };

      console.log(`🌐 [DEVICE_CONTROL_API] 11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111Request data (raw):`, requestData);
      console.log(`🌐 [DEVICE_CONTROL_API] Request data (JSON):`, JSON.stringify(requestData, null, 2));
      console.log(`🌐 [DEVICE_CONTROL_API] Device ID: ${did}`);
      console.log(`🌐 [DEVICE_CONTROL_API] Operation: ${operation}`);
      console.log(`🌐 [DEVICE_CONTROL_API] Value: ${value}`);
      console.log(`🌐 [DEVICE_CONTROL_API] Sending request to server...`);

      const response = await this.apiRegistry.controlDevice(requestData);

      console.log(`22222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222[DEVICE_CONTROL_API] ===== MESSAGE FROM SERVER =====`);
      console.log(`[DEVICE_CONTROL_API] Response (raw):`, response);
      console.log(`[DEVICE_CONTROL_API] Response (JSON):`, JSON.stringify(response, null, 2));
      console.log(`[DEVICE_CONTROL_API] Response type:`, typeof response);
      console.log(`[DEVICE_CONTROL_API] Response code:`, response?.code);
      console.log(`[DEVICE_CONTROL_API] Response success:`, response?.success);
      console.log(`[DEVICE_CONTROL_API] Response message:`, response?.message);

      // 6. 处理API响应
      if (response && response.code === 200) {
        console.log(`[Control] Device control successful`);

        // 7. 更新本地设备状态
        const updateResult = await this.updateLocalDeviceStatus(did, operation, value);
        console.log(`[Control] Local status update result:`, updateResult);

        return {
          success: true,
          message: '设备控制成功',
          data: {
            did: did,
            operation: operation,
            value: value,
            localUpdate: updateResult,
            offline: false
          }
        };
      } else {
        console.log(`[DEVICE_CONTROL_API] ===== ERROR FROM SERVER =====`);
        console.log(`[DEVICE_CONTROL_API] Error message:`, response?.message || 'Unknown error');
        console.log(`[DEVICE_CONTROL_API] Error code:`, response?.code);
        console.log(`[DEVICE_CONTROL_API] Error status:`, response?.status);
        console.log(`[DEVICE_CONTROL_API] Full error response:`, response);
        console.log(`[DEVICE_CONTROL_API] Full error response (JSON):`, JSON.stringify(response, null, 2));

        // API失败时返回错误，不要自动启用离线模式
        console.log(`❌ [DEVICE_CONTROL_API] API call failed - returning error instead of fallback to offline mode`);
        return {
          success: false,
          message: `设备控制失败: ${response?.message || 'API调用失败'}`,
          apiError: true,
          errorCode: response?.code,
          errorDetails: response
        };

        return {
          success: false,
          message: response?.message || 'controlDevice request failed'
        };
      }

    } catch (error) {
      console.error(`❌ [Control] Control failed:`, error);

      // 网络错误时返回错误，不要自动启用离线模式
      if (error.message.includes('网络') || error.message.includes('连接') || error.code === 'ENOTFOUND') {
        console.log(`❌ [Control] Network error - returning error instead of fallback to offline mode`);
        return {
          success: false,
          message: `设备控制失败: 网络连接错误 - ${error.message}`,
          networkError: true,
          errorDetails: error
        };
      }

      return {
        success: false,
        message: '控制失败：' + error.message
      };
    }
  }

  /**
   * 更新本地设备状态
   * @param {string} did - 设备ID
   * @param {string} operation - 操作属性
   * @param {any} value - 操作值
   * @returns {object} 更新结果
   */
  async updateLocalDeviceStatus(did, operation, value) {
    try {
      console.log(`💾 [Control] Starting updateLocalDeviceStatus: ${did}.${operation} = ${value}`);

      // 1. 获取当前设备数据
      const device = this.deviceStorageManager.getDevice(did);
      if (!device) {
        console.error(`❌ [Control] Device not found: ${did}`);
        return { success: false, message: '设备不存在' };
      }

      console.log(`🔍 [Control] Current device state before update:`, {
        did: device.did,
        name: device.name,
        type: device.type,
        online: device.online,
        status: device.status
      });

      // 2. 更新设备状态
      if (!device.status) {
        device.status = {};
      }

      const oldValue = device.status[operation];
      device.status[operation] = value;
      device.lastUpdated = new Date().toISOString();

      console.log(`�� [Control] Property ${operation} updated: ${oldValue} -> ${value}`);

      // 3. 根据文档要求更新设备在线状态和相关状态字段
      // 文档：设备状态离线online=0且设备关闭off时不允许控制其他属性
      if (operation === 'power') {
        const isPowerOn = this.isPowerValueOn(value, device.type);
        console.log(`🔍 [Control] Power operation detected. isPowerOn: ${isPowerOn} (value: ${value}, type: ${device.type})`);

        if (isPowerOn) {
          // 设备开启时设为在线
          device.online = true;
          console.log(`💡 [Control] Device ${did} powered ON, setting online status to true`);

          // 美的加湿器特殊处理：power为ON时，status应该更新为"on"
          if (device.type === 'midea_humidifier' && device.status.status !== undefined) {
            // 如果当前status是'off'，则更新为'on'；如果是'running'或'paused'则保持不变
            if (device.status.status === 'off') {
              device.status.status = 'on';
              console.log(`🔧 [Control] Midea humidifier status updated: off -> on`);
            }
          }
        } else {
          // 设备关闭时设为离线（根据文档要求）
          device.online = false;
          console.log(`💡 [Control] Device ${did} powered OFF, setting online status to false`);

          // 美的加湿器特殊处理：power为OFF时，status应该更新为"off"
          if (device.type === 'midea_humidifier' && device.status.status !== undefined) {
            device.status.status = 'off';
            console.log(`🔧 [Control] Midea humidifier status updated to: off`);
          }
        }
      } else {
        // 任何非电源操作的成功控制都表明设备是在线的
        device.online = true;
        console.log(`💡 [Control] Device ${did} non-power control successful, confirming online status`);
      }

      console.log(`💾 [Control] Final device state after update:`, {
        did: device.did,
        name: device.name,
        online: device.online,
        status: device.status,
        lastUpdated: device.lastUpdated
      });

      // 4. 保存到存储管理器
      const allDevices = this.deviceStorageManager.getAllDevices();
      const deviceIndex = allDevices.findIndex(d => d.did === did);
      if (deviceIndex !== -1) {
        allDevices[deviceIndex] = device;
        const storeResult = this.deviceStorageManager.storeAllDevices(allDevices);

        if (storeResult.success) {
          console.log(`✅ [Control] Device status updated and stored successfully`);
          console.log(`📊 [Control] Updated device summary: ${device.name} - ${device.online ? '在线' : '离线'} - ${operation}=${value}`);
          return {
            success: true,
            message: '本地状态更新成功',
            updatedDevice: device
          };
        } else {
          console.error(`❌ [Control] Failed to store updated device:`, storeResult.message);
          return { success: false, message: '本地状态更新失败' };
        }
      } else {
        console.error(`❌ [Control] Device index not found in storage: ${did}`);
        return { success: false, message: '设备索引未找到' };
      }

    } catch (error) {
      console.error(`❌ [Control] Local status update failed:`, error);
      return {
        success: false,
        message: '本地状态更新失败：' + error.message
      };
    }
  }

  /**
   * 判断power值是否表示开启状态
   * @param {any} value - power值
   * @param {string} deviceType - 设备类型
   * @returns {boolean} 是否为开启状态
   */
  isPowerValueOn(value, deviceType) {
    // 统一使用ON/OFF格式，无需区分设备类型
    return value === 'ON';
  }

  /**
   * 获取设备控制选项
   * @param {string} did - 设备ID
   * @returns {object} 控制选项
   */
  getDeviceControlOptions(did) {
    console.log(`🎮 [Control] Getting control options for device: ${did}`);

    if (!this.deviceStorageManager) {
      console.error('❌ [Control] DeviceStorageManager not available');
      return null;
    }

    console.log(`🎮 [Control] DeviceStorageManager available, looking for device...`);
    const device = this.deviceStorageManager.getDevice(did);

    if (!device) {
      console.error(`❌ [Control] Device not found in storage: ${did}`);
      // 调试：打印所有可用设备的ID
      const allDevices = this.deviceStorageManager.getAllDevices();
      console.log(`🔍 [Control] Available devices (${allDevices.length}):`,
        allDevices.map(d => ({ did: d.did, name: d.name, type: d.type })));
      return null;
    }

    console.log(`✅ [Control] Device found: ${device.name} (${device.type})`);
    console.log(`🎮 [Control] Device details:`, {
      did: device.did,
      name: device.name,
      type: device.type,
      brand: device.brand,
      online: device.online,
      groupId: device.groupId,
      group: device.group,
      gid: device.gid
    });

    const controllableCheck = this.validateDeviceControllable(device);
    if (!controllableCheck.valid) {
      console.log(`❌ [Control] Device not controllable: ${controllableCheck.message}`);
      return null;
    }

    console.log(`✅ [Control] Device is controllable`);

    const deviceLimits = this.deviceLimits[device.type];
    if (!deviceLimits) {
      console.error(`❌ [Control] No device limits defined for type: ${device.type}`);
      console.log(`🔍 [Control] Available device types:`, Object.keys(this.deviceLimits));
      return null;
    }

    console.log(`✅ [Control] Device limits found for type: ${device.type}`);

    // 标准化设备状态
    const normalizedDevice = this.normalizeDeviceStatus(device);

    const options = {
      did: normalizedDevice.did,
      name: normalizedDevice.name,
      type: normalizedDevice.type,
      brand: normalizedDevice.brand,
      online: normalizedDevice.online,
      currentStatus: normalizedDevice.status || {},
      controls: []
    };

    // 生成控制选项
    Object.keys(deviceLimits).forEach(property => {
      const config = deviceLimits[property];
      const control = {
        property: property,
        label: this.getPropertyLabel(property),
        currentValue: normalizedDevice.status?.[property]
      };

      if (config.values) {
        control.type = 'select';
        control.options = config.values;
      } else if (config.min !== undefined && config.max !== undefined) {
        control.type = 'number';
        control.min = config.min;
        control.max = config.max;
        control.step = config.precision || 1;
      }

      // 检查是否被约束禁用（使用标准化设备）
      const constraintCheck = this.checkDeviceConstraints(normalizedDevice, property, null);
      control.disabled = !constraintCheck.valid;
      control.disabledReason = constraintCheck.valid ? null : constraintCheck.message;

      options.controls.push(control);
    });

    console.log(`✅ [Control] Generated ${options.controls.length} control options`);
    return options;
  }

  /**
   * 获取属性标签
   * @param {string} property - 属性名
   * @returns {string} 属性标签
   */
  getPropertyLabel(property) {
    const labels = {
      power: '电源',
      target_temperature: '目标温度',
      fan_speed: '风速',
      mode: '模式',
      status: '状态',
      target_humidity: '目标湿度',
      fan_level: '风扇等级'
    };
    return labels[property] || property;
  }

  /**
   * 获取可控制设备列表
   * @returns {Array} 可控制设备列表
   */
  getControllableDevices() {
    if (!this.deviceStorageManager) {
      return [];
    }

    const allDevices = this.deviceStorageManager.getAllDevices();
    return allDevices.filter(device => {
      const controllableCheck = this.validateDeviceControllable(device);
      return controllableCheck.valid;
    });
  }

  /**
   * 重置控制管理器
   */
  reset() {
    this.isInitialized = false;
    console.log('Device control manager has been reset');
  }

  /**
   * 导出控制数据
   */
  exportControlData() {
    return {
      deviceLimits: this.deviceLimits,
      constraintRules: this.constraintRules,
      isInitialized: this.isInitialized,
      exportTime: new Date().toISOString()
    };
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
   * 获取设备当前的标准化power状态
   * @param {object} device - 设备对象
   * @returns {string} 标准化的power状态
   */
  getDeviceNormalizedPowerStatus(device) {
    if (!device.status) return 'OFF';
    return this.normalizePowerValue(device.status.power);
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
}

module.exports = DeviceControlManager;

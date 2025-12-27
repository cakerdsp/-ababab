/**
 * 模拟设备数据生成器
 * 用于离线调试模式下生成真实的设备数据
 */
class MockDeviceGenerator {
  constructor() {
    this.deviceTemplates = [
      {
        namePrefix: '美的空调',
        type: 'midea_ac',
        brand: 'midea',
        defaultStatus: {
          power: 'ON',
          target_temperature: 25,
          mode: 'cool',
          fan_speed: 'auto'
        }
      },
      {
        namePrefix: '美的加湿器',
        type: 'midea_humidifier',
        brand: 'midea',
        defaultStatus: {
          power: 'ON',
          status: 'running',
          mode: 'auto',
          target_humidity: 50
        }
      },
      {
        namePrefix: '美的除湿器',
        type: 'midea_dehumidifier',
        brand: 'midea',
        defaultStatus: {
          power: 'ON',
          mode: 'dry',
          target_humidity: 55
        }
      },
      {
        namePrefix: '美的空气净化器',
        type: 'midea_air_purifier',
        brand: 'midea',
        defaultStatus: {
          power: 'OFF',
          mode: 'auto',
          fan_level: 2
        }
      },
      {
        namePrefix: '小米温湿度计',
        type: 'mi_temp_hum_sensor',
        brand: 'xiaomi',
        defaultStatus: {
          temperature: 22.5,
          humidity: 55
        }
      },
      {
        namePrefix: '小米空气质量检测仪',
        type: 'mi_air_sensor',
        brand: 'xiaomi',
        defaultStatus: {
          pm25: 35,
          temperature: 23.1,
          humidity: 58
        }
      },
      {
        namePrefix: '小米空调',
        type: 'mi_ac',
        brand: 'xiaomi',
        defaultStatus: {
          power: 'OFF',
          target_temperature: 24,
          mode: 'cool',
          fan_speed: 'medium'
        }
      },
      {
        namePrefix: '小米加湿器',
        type: 'mi_humidifier',
        brand: 'xiaomi',
        defaultStatus: {
          power: 'OFF',
          status: 'off',
          mode: 'strong',
          target_humidity: 45
        }
      },
      {
        namePrefix: '小米空气净化器',
        type: 'mi_air_purifier',
        brand: 'xiaomi',
        defaultStatus: {
          power: 'ON',
          mode: 'auto',
          fan_level: 3
        }
      }
    ];
  }

  /**
   * 生成随机设备ID
   * @param {string} brand - 品牌名
   * @param {string} type - 设备类型
   * @returns {string} 设备ID
   */
  generateDeviceId(brand, type) {
    const randomSuffix = Math.random().toString(36).substring(2, 8);
    return `${brand}_${type}_${randomSuffix}`;
  }

  /**
   * 生成随机状态值
   * @param {object} baseStatus - 基础状态
   * @param {string} type - 设备类型
   * @returns {object} 随机状态
   */
  generateRandomStatus(baseStatus, type) {
    const status = { ...baseStatus };

    // 根据设备类型生成随机状态
    switch (type) {
      case 'midea_ac':
      case 'mi_ac':
        status.target_temperature = Math.round((Math.random() * 10 + 20) * 10) / 10; // 20-30度
        status.power = Math.random() > 0.5 ? 'ON' : 'OFF';
        status.mode = ['cool', 'heat', 'dry', 'fan'][Math.floor(Math.random() * 4)];
        status.fan_speed = ['low', 'medium', 'high', 'auto'][Math.floor(Math.random() * 4)];
        break;

      case 'midea_humidifier':
      case 'mi_humidifier':
        status.power = Math.random() > 0.3 ? 'ON' : 'OFF';
        status.target_humidity = Math.floor(Math.random() * 30 + 40); // 40-70%
        status.mode = ['auto', 'sleep', 'strong'][Math.floor(Math.random() * 3)];
        if (type === 'midea_humidifier') {
          // 美的加湿器：power为ON时status应该为"on"，power为OFF时status为"off"
          status.status = status.power === 'ON' ? 'on' : 'off';
        } else {
          // 小米加湿器：保持原有逻辑
          status.status = status.power === 'ON' ? 'on' : 'off';
        }
        break;

      case 'midea_dehumidifier':
        status.power = Math.random() > 0.4 ? 'ON' : 'OFF';
        status.target_humidity = Math.floor(Math.random() * 20 + 50); // 50-70%
        status.mode = ['auto', 'sleep', 'dry'][Math.floor(Math.random() * 3)];
        break;

      case 'midea_air_purifier':
      case 'mi_air_purifier':
        status.power = Math.random() > 0.4 ? 'ON' : 'OFF';
        status.mode = ['auto', 'silent', 'strong'][Math.floor(Math.random() * 3)];
        status.fan_level = Math.floor(Math.random() * 3 + 1); // 1-3级
        break;

      case 'mi_temp_hum_sensor':
        status.temperature = Math.round((Math.random() * 15 + 15) * 10) / 10; // 15-30度
        status.humidity = Math.floor(Math.random() * 40 + 40); // 40-80%
        break;

      case 'mi_air_sensor':
        status.pm25 = Math.floor(Math.random() * 200 + 10); // 10-210
        status.temperature = Math.round((Math.random() * 15 + 15) * 10) / 10; // 15-30度
        status.humidity = Math.floor(Math.random() * 40 + 40); // 40-80%
        break;
    }

    return status;
  }

  /**
   * 判断设备是否在线
   * @returns {boolean} 在线状态
   */
  generateOnlineStatus() {
    // 85% 概率在线
    return Math.random() > 0.15;
  }

  /**
   * 生成历史数据（24小时）
   * @param {string} sensorType - 传感器类型
   * @returns {Array} 历史数据数组
   */
  generateHistoricalData(sensorType) {
    const historicalData = [];
    const now = new Date();

    // 生成最近24小时的数据，每小时一个数据点
    for (let i = 23; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);

      let dataPoint = {
        time: timestamp.toISOString(),
        timestamp: timestamp.toISOString()
      };

      if (sensorType === 'mi_temp_hum_sensor') {
        dataPoint.temperature = Math.round((Math.random() * 10 + 18) * 10) / 10; // 18-28度
        dataPoint.humidity = Math.floor(Math.random() * 30 + 40); // 40-70%
      } else if (sensorType === 'mi_air_sensor') {
        dataPoint.pm25 = Math.floor(Math.random() * 150 + 20); // 20-170
        dataPoint.temperature = Math.round((Math.random() * 8 + 20) * 10) / 10; // 20-28度
        dataPoint.humidity = Math.floor(Math.random() * 25 + 45); // 45-70%
      }

      historicalData.push(dataPoint);
    }

    return historicalData;
  }

  /**
   * 生成单个模拟设备
   * @param {object} template - 设备模板
   * @param {string} groupId - 分组ID
   * @param {number} index - 设备索引
   * @returns {object} 设备数据
   */
  generateDevice(template, groupId, index = 0) {
    const deviceId = this.generateDeviceId(template.brand, template.type);
    const deviceName = index > 0 ? `${template.namePrefix}${index + 1}` : template.namePrefix;
    const status = this.generateRandomStatus(template.defaultStatus, template.type);
    const now = new Date().toISOString();

    // 根据设备类型确定在线状态
    let online;
    if (template.type === 'mi_temp_hum_sensor' || template.type === 'mi_air_sensor') {
      // 传感器设备始终在线
      online = true;
    } else {
      // 可控制设备的在线状态对应power字段
      online = status.power === 'ON';
    }

    const device = {
      did: deviceId,
      name: deviceName,
      type: template.type,
      brand: template.brand,
      group: groupId,
      groupId: groupId,
      online: online,
      status: status,
      lastUpdated: now
    };

    // 为传感器设备添加特殊类型（但不包含历史数据）
    if (template.type === 'mi_temp_hum_sensor' || template.type === 'mi_air_sensor') {
      // 传感器设备的特殊处理
      device.type = 'history'; // 传感器设备类型设为history
      device.metric_type = 'humidity';
      device.timestamp = now;
      // 注意：不再在设备对象中存储历史数据，历史数据由DeviceGroupAPIManager管理
    }

    return device;
  }

  /**
   * 生成完整的模拟设备列表
   * @param {string} groupId - 默认分组ID
   * @param {number} deviceCount - 设备数量（可选，默认为模板数量）
   * @returns {Array} 设备列表
   */
  generateDeviceList(groupId, deviceCount = null) {
    console.log('🤖 [MockDeviceGenerator] 开始生成模拟设备数据...');
    console.log('🤖 [MockDeviceGenerator] 目标分组ID:', groupId);

    const devices = [];
    const actualCount = deviceCount || this.deviceTemplates.length;

    // 如果指定了数量且大于模板数量，则重复使用模板
    for (let i = 0; i < actualCount; i++) {
      const templateIndex = i % this.deviceTemplates.length;
      const template = this.deviceTemplates[templateIndex];
      const deviceIndex = Math.floor(i / this.deviceTemplates.length);

      const device = this.generateDevice(template, groupId, deviceIndex);
      devices.push(device);

      console.log(`🤖 [MockDeviceGenerator] 生成设备: ${device.name} (${device.did}) - ${device.online ? '在线' : '离线'}`);
    }

    console.log(`✅ [MockDeviceGenerator] 模拟设备生成完成，总计 ${devices.length} 个设备`);
    return devices;
  }

  /**
   * 更新设备状态（模拟实时变化）
   * @param {Array} devices - 设备列表
   * @returns {Array} 更新后的设备列表
   */
  updateDeviceStatus(devices) {
    console.log('🔄 [MockDeviceGenerator] 更新设备状态...');

    return devices.map(device => {
      // 更新设备状态值
      const template = this.deviceTemplates.find(t => t.type === device.type ||
        (device.type === 'history' && (t.type === 'mi_temp_hum_sensor' || t.type === 'mi_air_sensor')));

      if (template) {
        device.status = this.generateRandomStatus(device.status, template.type);

        // 根据设备类型确定在线状态
        if (device.type === 'history') {
          // 传感器设备始终在线
          device.online = true;
        } else {
          // 可控制设备的在线状态对应power字段
          device.online = device.status.power === 'ON';
        }
      }

      device.lastUpdated = new Date().toISOString();
      return device;
    });
  }
}

module.exports = MockDeviceGenerator;

class Device {
  constructor(did, name, type, brand, online = false, status = {}) {
    this.did = did; // 设备ID
    this.name = name; // 设备名称
    this.type = type; // 设备类型
    this.brand = brand; // 品牌
    this.online = online; // 是否在线
    this.status = status; // 设备状态属性map
  }

  // 更新设备状态
  updateStatus(newStatus) {
    this.status = { ...this.status, ...newStatus };
  }

  // 设置设备在线状态
  setOnline(online) {
    this.online = online;
  }

  // 获取特定属性值
  getProperty(property) {
    return this.status[property];
  }

  // 设置特定属性值
  setProperty(property, value) {
    this.status[property] = value;
  }

  // 检查设备是否支持某个属性
  hasProperty(property) {
    return property in this.status;
  }

  // 验证设备控制操作的合法性
  validateControl(operation, value) {
    const validationResult = {
      valid: false,
      message: ''
    };

    // 检查设备是否在线
    if (!this.online) {
      validationResult.message = '设备离线，无法执行任何操作';
      return validationResult;
    }

    // 检查设备是否支持该属性
    if (!this.hasProperty(operation)) {
      validationResult.message = `设备不支持属性：${operation}`;
      return validationResult;
    }

    // 检查power操作的特殊逻辑
    if (operation !== 'power' && this.getProperty('power') === 'OFF') {
      validationResult.message = '设备已关闭，只支持开机操作';
      return validationResult;
    }

    // 根据设备类型和属性进行具体验证
    const isValid = this._validatePropertyValue(operation, value);
    if (!isValid.valid) {
      validationResult.message = isValid.message;
      return validationResult;
    }

    validationResult.valid = true;
    return validationResult;
  }

  // 验证属性值的合法性
  _validatePropertyValue(operation, value) {
    const result = { valid: false, message: '' };

    switch (this.type) {
      case 'mi_ac':
      case 'midea_ac':
        return this._validateAirConditionerProperty(operation, value);
      case 'mi_humidifier':
      case 'midea_humidifier':
        return this._validateHumidifierProperty(operation, value);
      case 'mi_dehumidifier':
      case 'midea_dehumidifier':
        return this._validateDehumidifierProperty(operation, value);
      case 'mi_air_purifier':
      case 'midea_air_purifier':
        return this._validateAirPurifierProperty(operation, value);
      default:
        result.valid = true;
        return result;
    }
  }

  // 验证空调属性
  _validateAirConditionerProperty(operation, value) {
    const result = { valid: false, message: '' };

    switch (operation) {
      case 'power':
        if (value === 'ON' || value === 'OFF') {
          result.valid = true;
        } else {
          result.message = 'power值必须为ON或OFF';
        }
        break;
      case 'target_temperature':
        const temp = parseFloat(value);
        if (temp >= 16 && temp <= 30) {
          result.valid = true;
        } else {
          result.message = '目标温度必须在16°C到30°C之间';
        }
        break;
      case 'fan_speed':
        const validSpeeds = ['low', 'medium', 'high', 'auto'];
        if (validSpeeds.includes(value)) {
          result.valid = true;
        } else {
          result.message = `风速必须为：${validSpeeds.join(', ')}`;
        }
        break;
      case 'mode':
        const validModes = ['cool', 'heat', 'dry', 'fan'];
        if (validModes.includes(value)) {
          result.valid = true;
        } else {
          result.message = `模式必须为：${validModes.join(', ')}`;
        }
        break;
      default:
        result.valid = true;
        break;
    }

    return result;
  }

  // 验证加湿器属性
  _validateHumidifierProperty(operation, value) {
    const result = { valid: false, message: '' };

    switch (operation) {
      case 'power':
        if (value === 0 || value === 1 || value === '0' || value === '1') {
          result.valid = true;
        } else {
          result.message = 'power值必须为0或1';
        }
        break;
      case 'target_humidity':
        const humidity = parseInt(value);
        if (humidity >= 30 && humidity <= 80) {
          result.valid = true;
        } else {
          result.message = '目标湿度必须在30%到80%之间';
        }
        break;
      case 'mode':
        const validModes = ['auto', 'sleep', 'strong'];
        if (validModes.includes(value)) {
          result.valid = true;
        } else {
          result.message = `模式必须为：${validModes.join(', ')}`;
        }
        break;
      case 'status':
        const validStatus = ['running', 'paused', 'off'];
        if (validStatus.includes(value)) {
          result.valid = true;
        } else {
          result.message = `状态必须为：${validStatus.join(', ')}`;
        }
        break;
      default:
        result.valid = true;
        break;
    }

    return result;
  }

  // 验证除湿器属性
  _validateDehumidifierProperty(operation, value) {
    const result = { valid: false, message: '' };

    switch (operation) {
      case 'power':
        if (value === 0 || value === 1 || value === '0' || value === '1') {
          result.valid = true;
        } else {
          result.message = 'power值必须为0或1';
        }
        break;
      case 'target_humidity':
        const humidity = parseInt(value);
        if (humidity >= 30 && humidity <= 80) {
          result.valid = true;
        } else {
          result.message = '目标湿度必须在30%到80%之间';
        }
        break;
      case 'mode':
        const validModes = ['auto', 'sleep', 'dry'];
        if (validModes.includes(value)) {
          result.valid = true;
        } else {
          result.message = `模式必须为：${validModes.join(', ')}`;
        }
        break;
      default:
        result.valid = true;
        break;
    }

    return result;
  }

  // 验证空气净化器属性
  _validateAirPurifierProperty(operation, value) {
    const result = { valid: false, message: '' };

    switch (operation) {
      case 'power':
        if (value === 0 || value === 1 || value === '0' || value === '1') {
          result.valid = true;
        } else {
          result.message = 'power值必须为0或1';
        }
        break;
      case 'mode':
        const validModes = ['auto', 'silent', 'strong'];
        if (validModes.includes(value)) {
          result.valid = true;
        } else {
          result.message = `模式必须为：${validModes.join(', ')}`;
        }
        break;
      case 'fan_level':
        const level = parseInt(value);
        if ([1, 2, 3].includes(level)) {
          result.valid = true;
        } else {
          result.message = '风扇等级必须为1、2或3';
        }
        break;
      default:
        result.valid = true;
        break;
    }

    return result;
  }

  // 获取设备的简化对象表示，用于显示或记录
  toSimpleObject() {
    return {
      did: this.did,
      name: this.name,
      type: this.type,
      brand: this.brand,
      online: this.online,
      status: this.status
    };
  }

  // 自定义JSON序列化
  toJSON() {
    return this.toSimpleObject();
  }
}

module.exports = Device;

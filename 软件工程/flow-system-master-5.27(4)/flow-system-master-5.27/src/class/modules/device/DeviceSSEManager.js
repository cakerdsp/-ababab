const SSEService = require('../../services/sse/SSEService');
const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class DeviceSSEManager {
  constructor() {
    this.sseService = new SSEService();
    this.storage = new UnifiedStorage();
    this.deviceStorage = null; // 将在初始化时设置
    this.isConnected = false;
    this.isInitialized = false;
    this.eventHandlers = new Map();
  }

  // 初始化SSE管理器
  async initialize(userId, deviceStorage) {
    if (this.isInitialized) {
      return { success: true, message: 'SSE管理器已初始化' };
    }

    try {
      this.deviceStorage = deviceStorage;
      
      // 设置SSE连接ID（使用userId）
      this.sseService.setSseConnectionId(userId);
      
      // 保存sseid到本地
      this.storage.saveSseConnectionId(userId);
      
      // 注册设备状态更新处理器
      this.sseService.registerHandler('deviceUpdate', (data) => {
        this.handleDeviceStatusUpdate(data);
      });

      // 注册传感器数据更新处理器
      this.sseService.registerHandler('sensorUpdate', (data) => {
        this.handleSensorDataUpdate(data);
      });

      console.log('设备SSE管理器初始化成功');
      this.isInitialized = true;
      return { success: true, message: 'SSE管理器初始化成功' };
    } catch (error) {
      console.error('SSE管理器初始化失败:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 连接到SSE服务
  async connect() {
    if (this.isConnected) {
      return { success: true, message: 'SSE已连接' };
    }

    try {
      const result = await this.sseService.connect();
      if (result.success) {
        this.isConnected = true;
        console.log('设备SSE连接建立成功');
      }
      return result;
    } catch (error) {
      console.error('SSE连接失败:', error);
      return { success: false, message: 'SSE连接失败：' + error.message };
    }
  }

  // 断开SSE连接
  disconnect() {
    if (this.sseService) {
      this.sseService.disconnect();
      this.isConnected = false;
      console.log('设备SSE连接已断开');
    }
  }

  // 通知服务端退出SSE连接
  async notifyExit(apiRegistry) {
    try {
      const result = await this.sseService.notifyExit(apiRegistry);
      console.log('SSE退出通知结果:', result);
      return result;
    } catch (error) {
      console.error('SSE退出通知失败:', error);
      return { success: false, message: '退出通知失败：' + error.message };
    }
  }

  // 处理设备状态更新
  handleDeviceStatusUpdate(deviceData) {
    try {
      console.log('收到设备状态更新:', deviceData);
      
      if (!deviceData.did) {
        console.error('设备更新数据缺少设备ID');
        return;
      }

      // 更新本地设备存储
      if (this.deviceStorage) {
        const result = this.deviceStorage.updateDeviceStatus(deviceData.did, deviceData);
        if (result.success) {
          console.log(`设备状态已更新: ${deviceData.did}`);
          
          // 触发设备更新事件
          this.emitEvent('deviceStatusUpdated', {
            deviceId: deviceData.did,
            updates: deviceData,
            timestamp: new Date().toISOString()
          });
        } else {
          console.error('更新设备状态失败:', result.message);
        }
      }
    } catch (error) {
      console.error('处理设备状态更新失败:', error);
    }
  }

  // 处理传感器数据更新
  handleSensorDataUpdate(sensorData) {
    try {
      console.log('收到传感器数据更新:', sensorData);
      
      if (!sensorData.did) {
        console.error('传感器数据缺少设备ID');
        return;
      }

      // 更新本地设备存储中的传感器数据
      if (this.deviceStorage) {
        const result = this.deviceStorage.updateDeviceStatus(sensorData.did, sensorData);
        if (result.success) {
          console.log(`传感器数据已更新: ${sensorData.did}`);
          
          // 触发传感器数据更新事件
          this.emitEvent('sensorDataUpdated', {
            deviceId: sensorData.did,
            sensorData: sensorData,
            timestamp: new Date().toISOString()
          });
        }
      }
    } catch (error) {
      console.error('处理传感器数据更新失败:', error);
    }
  }

  // 注册事件处理器
  registerEventHandler(eventType, handler) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType).push(handler);
  }

  // 注销事件处理器
  unregisterEventHandler(eventType, handler) {
    if (this.eventHandlers.has(eventType)) {
      const handlers = this.eventHandlers.get(eventType);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  // 触发事件
  emitEvent(eventType, data) {
    if (this.eventHandlers.has(eventType)) {
      const handlers = this.eventHandlers.get(eventType);
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`事件处理器执行失败 (${eventType}):`, error);
        }
      });
    }
  }

  // 获取连接状态
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isInitialized: this.isInitialized,
      sseStatus: this.sseService.getConnectionStatus()
    };
  }

  // 重置SSE管理器
  reset() {
    this.disconnect();
    this.eventHandlers.clear();
    this.isConnected = false;
    this.isInitialized = false;
    this.deviceStorage = null;
    console.log('设备SSE管理器已重置');
  }

  // 重连SSE
  async reconnect() {
    this.disconnect();
    return await this.connect();
  }
}

module.exports = DeviceSSEManager; 
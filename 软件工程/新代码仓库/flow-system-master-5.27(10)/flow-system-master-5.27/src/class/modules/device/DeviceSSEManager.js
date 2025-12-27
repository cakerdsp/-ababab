const SSEService = require('../../services/sse/SSEService');
const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class DeviceSSEManager {
  constructor() {
    this.sseService = new SSEService();
    this.storage = new UnifiedStorage();
    this.deviceStorage = null; // 将在初始化时设置
    this.deviceGroupManager = null; // 将在初始化时设置
    this.isConnected = false;
    this.isInitialized = false;
    this.eventHandlers = new Map();
    this.sensorReportTimer = null; // 传感器报告定时器
    this.sensorReportInterval = 30000; // 30秒间隔
  }

  // 初始化SSE管理器
  async initialize(userId, deviceStorage, deviceGroupManager = null) {
    if (this.isInitialized) {
      return { success: true, message: 'SSE管理器已初始化' };
    }

    try {
      this.deviceStorage = deviceStorage;
      this.deviceGroupManager = deviceGroupManager;

      // 设置SSE连接ID（使用userId）
      this.sseService.setSseConnectionId(userId);

      // 保存sseid到本地
      this.storage.saveSseConnectionId(userId);

      // 注册设备状态更新处理器
      this.sseService.registerHandler('deviceUpdate', (data) => {
        this.handleDeviceStatusUpdate(data);
      });

      // 注册传感器历史数据更新处理器
      this.sseService.registerHandler('sensorHistoryUpdate', (data) => {
        this.handleSensorHistoryUpdate(data);
      });

      // 注册传感器数据更新处理器（备用）
      this.sseService.registerHandler('sensorUpdate', (data) => {
        this.handleSensorDataUpdate(data);
      });

      console.log('[SSE_INIT] Device SSE manager initialized successfully');
      this.isInitialized = true;

      // 启动传感器信息定期报告
      this.startSensorReporting();

      return { success: true, message: 'SSE管理器初始化成功' };
    } catch (error) {
      console.error('[SSE_INIT] SSE manager initialization failed:', error);
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

    // 停止传感器报告
    this.stopSensorReporting();
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
      console.log('[SSE_UPDATE] Received device status update:', JSON.stringify(deviceData, null, 2));

      if (!deviceData.did) {
        console.error('[SSE_UPDATE] Device update data missing device ID');
        return;
      }

      // 检查是否为传感器设备
      const device = this.deviceStorage ? this.deviceStorage.getDevice(deviceData.did) : null;
      const isSensor = device ? this.isSensorDevice(device.type) : false;

      console.log('[SSE_UPDATE] Device info:', {
        deviceId: deviceData.did,
        deviceType: device?.type || 'unknown',
        isSensor: isSensor,
        deviceExists: !!device
      });

      // 更新本地设备存储
      if (this.deviceStorage) {
        // 为传感器数据创建更完整的更新对象
        let updateData = { ...deviceData };

        // 如果是传感器数据，确保状态字段正确设置
        if (isSensor) {
          console.log('[SSE_UPDATE] Processing sensor data update');

          // 确保传感器数据被正确放入status字段
          if (!updateData.status) {
            updateData.status = {};
          }

          // 将传感器数值放入status字段
          Object.keys(deviceData).forEach(key => {
            if (key !== 'did' && key !== 'lastUpdated' && key !== 'status') {
              updateData.status[key] = deviceData[key];
              console.log('[SSE_UPDATE] Added sensor value to status:', key, '=', deviceData[key]);
            }
          });
        }

        console.log('[SSE_UPDATE] Final update data:', JSON.stringify(updateData, null, 2));

        const result = this.deviceStorage.updateDeviceStatus(deviceData.did, updateData);
        if (result.success) {
          console.log('[SSE_UPDATE] Device status updated successfully:', deviceData.did);

          // 获取更新后的设备信息
          const updatedDevice = this.deviceStorage.getDevice(deviceData.did);
          console.log('[SSE_UPDATE] Updated device state:', JSON.stringify(updatedDevice, null, 2));

          // 触发设备更新事件
          this.emitEvent('deviceStatusUpdated', {
            deviceId: deviceData.did,
            updates: updateData,
            device: updatedDevice,
            isSensor: isSensor,
            timestamp: new Date().toISOString()
          });

          // 如果是传感器，也触发传感器特定事件
          if (isSensor) {
            this.emitEvent('sensorDataUpdated', {
              deviceId: deviceData.did,
              sensorData: updateData,
              device: updatedDevice,
              timestamp: new Date().toISOString()
            });
          }
        } else {
          console.error('[SSE_UPDATE] Failed to update device status:', result.message);
        }
      } else {
        console.error('[SSE_UPDATE] Device storage not available');
      }
    } catch (error) {
      console.error('[SSE_UPDATE] Error processing device status update:', error);
    }
  }

  // 处理传感器历史数据更新
  handleSensorHistoryUpdate(historyData) {
    try {
      console.log('[SSE_HISTORY] Received sensor history update:', JSON.stringify(historyData, null, 2));

      if (!historyData.did || !historyData.metric_type || !Array.isArray(historyData.historyData)) {
        console.error('[SSE_HISTORY] Invalid sensor history data format');
        return;
      }

      const deviceId = historyData.did;
      const metricType = historyData.metric_type;
      const dataPoints = historyData.historyData;

      console.log(`[SSE_HISTORY] Processing ${dataPoints.length} data points for device ${deviceId}, metric: ${metricType}`);

      // 将历史数据传递给DeviceGroupManager进行存储
      if (this.deviceGroupManager && typeof this.deviceGroupManager.updateSensorHistoryFromSSE === 'function') {
        const result = this.deviceGroupManager.updateSensorHistoryFromSSE(deviceId, metricType, dataPoints);
        if (result.success) {
          console.log(`[SSE_HISTORY] Successfully stored ${dataPoints.length} history data points for device ${deviceId}`);
        } else {
          console.error(`[SSE_HISTORY] Failed to store history data for device ${deviceId}:`, result.message);
        }
      } else {
        console.warn('[SSE_HISTORY] DeviceGroupManager not available or method not found');
      }

      // 触发传感器历史数据更新事件
      this.emitEvent('sensorHistoryUpdated', {
        deviceId: deviceId,
        metricType: metricType,
        historyData: dataPoints,
        timestamp: historyData.timestamp,
        dataPointCount: dataPoints.length
      });

      console.log(`[SSE_HISTORY] Sensor history update completed for device ${deviceId}`);
    } catch (error) {
      console.error('[SSE_HISTORY] Error processing sensor history update:', error);
    }
  }

  // 处理传感器数据更新（备用处理器，通常不会被调用）
  handleSensorDataUpdate(sensorData) {
    try {
      console.log('[SSE_SENSOR] Received sensor data update:', JSON.stringify(sensorData, null, 2));

      if (!sensorData.did) {
        console.error('[SSE_SENSOR] Sensor data missing device ID');
        return;
      }

      // 更新本地设备存储中的传感器数据
      if (this.deviceStorage) {
        // 确保传感器数据被正确放入status字段
        let updateData = { ...sensorData };
        if (!updateData.status) {
          updateData.status = {};
        }

        // 将传感器数值放入status字段
        Object.keys(sensorData).forEach(key => {
          if (key !== 'did' && key !== 'lastUpdated' && key !== 'status') {
            updateData.status[key] = sensorData[key];
          }
        });

        const result = this.deviceStorage.updateDeviceStatus(sensorData.did, updateData);
        if (result.success) {
          console.log('[SSE_SENSOR] Sensor data updated successfully:', sensorData.did);

          // 获取更新后的设备信息
          const updatedDevice = this.deviceStorage.getDevice(sensorData.did);

          // 触发传感器数据更新事件
          this.emitEvent('sensorDataUpdated', {
            deviceId: sensorData.did,
            sensorData: updateData,
            device: updatedDevice,
            timestamp: new Date().toISOString()
          });
        } else {
          console.error('[SSE_SENSOR] Failed to update sensor data:', result.message);
        }
      } else {
        console.error('[SSE_SENSOR] Device storage not available');
      }
    } catch (error) {
      console.error('[SSE_SENSOR] Error processing sensor data update:', error);
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
    this.stopSensorReporting();
    this.eventHandlers.clear();
    this.isConnected = false;
    this.isInitialized = false;
    this.deviceStorage = null;
    this.deviceGroupManager = null;
    console.log('设备SSE管理器已重置');
  }

  // 重连SSE
  async reconnect() {
    this.disconnect();
    return await this.connect();
  }

  // 启动传感器信息定期报告
  startSensorReporting() {
    if (this.sensorReportTimer) {
      clearInterval(this.sensorReportTimer);
    }

    console.log('[SENSOR_REPORT] Starting sensor reporting every', this.sensorReportInterval, 'ms');

    this.sensorReportTimer = setInterval(() => {
      this.reportSensorInfo();
    }, this.sensorReportInterval);

    // 立即执行一次
    this.reportSensorInfo();
  }

  // 停止传感器信息报告
  stopSensorReporting() {
    if (this.sensorReportTimer) {
      clearInterval(this.sensorReportTimer);
      this.sensorReportTimer = null;
      console.log('[SENSOR_REPORT] Sensor reporting stopped');
    }
  }

  // 报告传感器信息
  reportSensorInfo() {
    try {
      console.log('999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999');
      console.log('999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999');
      console.log('[SENSOR_REPORT_DEBUG] ===== PERIODIC SENSOR REPORT START =====');

      if (!this.deviceStorage) {
        console.log('[SENSOR_REPORT_DEBUG] Device storage not available');
        return;
      }

      const allDevices = this.deviceStorage.getAllDevices();
      const sensorDevices = allDevices.filter(device => this.isSensorDevice(device.type));

      console.log('[SENSOR_REPORT_DEBUG] Total devices:', allDevices.length);
      console.log('[SENSOR_REPORT_DEBUG] Sensor devices found:', sensorDevices.length);

      sensorDevices.forEach((sensor, index) => {
        console.log(`[SENSOR_REPORT_DEBUG] ===== SENSOR ${index + 1}/${sensorDevices.length} =====`);

        const sensorInfo = {
          deviceId: sensor.did,
          deviceName: sensor.name || 'Unknown',
          deviceType: sensor.type,
          groupId: sensor.group || sensor.groupId || sensor.gid || 'ungrouped',
          lastUpdated: sensor.lastUpdated || 'never',
          online: sensor.online || false,
          status: sensor.status || {}
        };

        // 提取传感器数据
        const sensorData = this.extractSensorValues(sensor);
        if (sensorData && Object.keys(sensorData).length > 0) {
          sensorInfo.currentValues = sensorData;
        }

        console.log('[SENSOR_REPORT_DEBUG] Sensor basic info:', JSON.stringify(sensorInfo, null, 2));

        // 检查历史数据
        if (this.deviceGroupManager && typeof this.deviceGroupManager.getSensorHistory === 'function') {
          const historyData = this.deviceGroupManager.getSensorHistory(sensor.did, 24);
          console.log(`[SENSOR_REPORT_DEBUG] History data points for ${sensor.did}:`, historyData ? historyData.length : 0);

          if (historyData && historyData.length > 0) {
            console.log('[SENSOR_REPORT_DEBUG] Latest history point:', JSON.stringify(historyData[historyData.length - 1], null, 2));
            console.log('[SENSOR_REPORT_DEBUG] Oldest history point:', JSON.stringify(historyData[0], null, 2));

            // 统计各指标的数据点数量
            const metricStats = {};
            historyData.forEach(point => {
              if (point.temperature !== undefined) metricStats.temperature = (metricStats.temperature || 0) + 1;
              if (point.humidity !== undefined) metricStats.humidity = (metricStats.humidity || 0) + 1;
              if (point.pm25 !== undefined) metricStats.pm25 = (metricStats.pm25 || 0) + 1;
            });
            console.log('[SENSOR_REPORT_DEBUG] Metric statistics:', metricStats);
          }
        }
      });

      // 如果有设备分组管理器，也报告传感器历史数据统计
      if (this.deviceGroupManager && typeof this.deviceGroupManager.getSensorHistoryStats === 'function') {
        const historyStats = this.deviceGroupManager.getSensorHistoryStats();
        console.log('[SENSOR_REPORT_DEBUG] Overall history stats:', JSON.stringify(historyStats, null, 2));
      }

      console.log('[SENSOR_REPORT_DEBUG] ===== PERIODIC SENSOR REPORT END =====');
      console.log('999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999');
      console.log('999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999');

    } catch (error) {
      console.error('[SENSOR_REPORT_DEBUG] Error reporting sensor info:', error);
      console.error('[SENSOR_REPORT_DEBUG] Error stack:', error.stack);
    }
  }

  // 检查是否为传感器设备
  isSensorDevice(deviceType) {
    return deviceType === 'mi_temp_hum_sensor' ||
           deviceType === 'mi_air_sensor' ||
           deviceType === 'history';
  }

  // 提取传感器数值
  extractSensorValues(device) {
    const sensorData = {};
    const status = device.status || {};

    // 温度
    if (status.temperature !== undefined) {
      sensorData.temperature = parseFloat(status.temperature);
    }

    // 湿度
    if (status.humidity !== undefined) {
      sensorData.humidity = parseFloat(status.humidity);
    }

    // PM2.5
    if (status.pm25 !== undefined) {
      sensorData.pm25 = parseFloat(status.pm25);
    }

    // 其他可能的传感器数据
    if (status.co2 !== undefined) {
      sensorData.co2 = parseFloat(status.co2);
    }

    if (status.tvoc !== undefined) {
      sensorData.tvoc = parseFloat(status.tvoc);
    }

    return sensorData;
  }
}

module.exports = DeviceSSEManager;

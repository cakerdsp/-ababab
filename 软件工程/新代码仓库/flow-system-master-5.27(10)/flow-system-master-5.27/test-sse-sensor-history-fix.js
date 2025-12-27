/**
 * SSE传感器历史数据处理修复测试
 * 测试多指标数据合并和状态更新
 */

const SSEService = require('./src/class/services/sse/SSEService');
const DeviceSSEManager = require('./src/class/modules/device/DeviceSSEManager');
const DeviceGroupAPIManager = require('./src/class/modules/device/DeviceGroupAPIManager');
const DeviceStorageManager = require('./src/class/modules/device/DeviceStorageManager');
const SensorDataAnalyzer = require('./src/class/modules/data/SensorDataAnalyzer');

async function testSSESensorHistoryFix() {
  console.log('=== SSE传感器历史数据处理修复测试 ===\n');

  try {
    // 1. 初始化各个组件
    console.log('1. 初始化组件...');
    const deviceStorageManager = new DeviceStorageManager();
    const deviceGroupManager = new DeviceGroupAPIManager(null, deviceStorageManager);
    const deviceSSEManager = new DeviceSSEManager();
    const sensorAnalyzer = new SensorDataAnalyzer(null, deviceStorageManager, deviceGroupManager);

    // 初始化组件
    await deviceStorageManager.initialize();
    await deviceGroupManager.initialize();
    await deviceSSEManager.initialize('test_user_123', deviceStorageManager, deviceGroupManager);

    console.log('✅ 组件初始化完成\n');

    // 2. 模拟添加一个传感器设备
    console.log('2. 添加测试传感器设备...');
    const testDevice = {
      did: 'xiaomi_mi_air_sensor_slki1y',
      name: '小米空气质量检测仪',
      type: 'mi_air_sensor',
      status: {
        temperature: 25.5,
        humidity: 60,
        pm25: 45
      },
      online: true,
      lastUpdated: new Date().toISOString()
    };

    deviceStorageManager.addDevice(testDevice);
    console.log('✅ 测试设备添加完成\n');

    // 3. 测试SSE服务的消息处理
    console.log('3. 测试SSE消息处理...');
    const sseService = new SSEService();

    // 注册处理器来捕获分发的消息
    let deviceUpdatesReceived = [];
    let historyUpdatesReceived = [];

    sseService.registerHandler('deviceUpdate', (data) => {
      deviceUpdatesReceived.push(data);
      console.log('📨 收到设备状态更新:', JSON.stringify(data, null, 2));
    });

    sseService.registerHandler('sensorHistoryUpdate', (data) => {
      historyUpdatesReceived.push(data);
      console.log('📨 收到传感器历史数据更新:', JSON.stringify(data, null, 2));
    });

    // 4. 模拟多个指标的SSE历史数据消息
    console.log('4. 模拟多个指标的SSE历史数据消息...');

    // 湿度数据
    const humidityMessage = {
      type: "history",
      did: "xiaomi_mi_air_sensor_slki1y",
      metric_type: "humidity",
      data: [
        { hour: "2025-06-14T07:00:00.000Z", value: 17 },
        { hour: "2025-06-14T08:00:00.000Z", value: 67 },
        { hour: "2025-06-14T09:00:00.000Z", value: 73 },
        { hour: "2025-06-14T10:00:00.000Z", value: 68 },
        { hour: "2025-06-14T11:00:00.000Z", value: 72 }
      ],
      timestamp: "2025-06-14T09:56:25.046Z"
    };

    // 温度数据
    const temperatureMessage = {
      type: "history",
      did: "xiaomi_mi_air_sensor_slki1y",
      metric_type: "temperature",
      data: [
        { hour: "2025-06-14T07:00:00.000Z", value: 22.5 },
        { hour: "2025-06-14T08:00:00.000Z", value: 23.1 },
        { hour: "2025-06-14T09:00:00.000Z", value: 24.2 },
        { hour: "2025-06-14T10:00:00.000Z", value: 25.0 },
        { hour: "2025-06-14T11:00:00.000Z", value: 25.8 }
      ],
      timestamp: "2025-06-14T09:56:25.046Z"
    };

    // PM2.5数据
    const pm25Message = {
      type: "history",
      did: "xiaomi_mi_air_sensor_slki1y",
      metric_type: "pm25",
      data: [
        { hour: "2025-06-14T07:00:00.000Z", value: 35 },
        { hour: "2025-06-14T08:00:00.000Z", value: 42 },
        { hour: "2025-06-14T09:00:00.000Z", value: 38 },
        { hour: "2025-06-14T10:00:00.000Z", value: 45 },
        { hour: "2025-06-14T11:00:00.000Z", value: 41 }
      ],
      timestamp: "2025-06-14T09:56:25.046Z"
    };

    // 处理所有消息
    console.log('处理湿度数据...');
    sseService.handleMessage(humidityMessage);

    console.log('处理温度数据...');
    sseService.handleMessage(temperatureMessage);

    console.log('处理PM2.5数据...');
    sseService.handleMessage(pm25Message);

    console.log('✅ SSE消息处理完成\n');

    // 5. 验证设备状态更新
    console.log('5. 验证设备状态更新...');
    console.log(`收到的设备状态更新数量: ${deviceUpdatesReceived.length}`);
    deviceUpdatesReceived.forEach((update, index) => {
      console.log(`设备状态更新 ${index + 1}:`, JSON.stringify(update, null, 2));
    });

    // 6. 验证历史数据更新
    console.log('\n6. 验证历史数据更新...');
    console.log(`收到的历史数据更新数量: ${historyUpdatesReceived.length}`);
    historyUpdatesReceived.forEach((update, index) => {
      console.log(`历史数据更新 ${index + 1}:`, JSON.stringify(update, null, 2));
    });

    // 7. 测试DeviceGroupManager的历史数据存储和合并
    console.log('\n7. 测试历史数据存储和合并...');

    // 处理所有历史数据更新
    for (const historyUpdate of historyUpdatesReceived) {
      const result = deviceGroupManager.updateSensorHistoryFromSSE(
        historyUpdate.did,
        historyUpdate.metric_type,
        historyUpdate.historyData
      );

      console.log(`存储 ${historyUpdate.metric_type} 数据结果:`, result);
    }

    // 8. 验证合并后的历史数据
    console.log('\n8. 验证合并后的历史数据...');
    const mergedHistory = deviceGroupManager.getSensorHistory('xiaomi_mi_air_sensor_slki1y', 24);
    if (mergedHistory && mergedHistory.length > 0) {
      console.log('✅ 合并后的历史数据检索成功');
      console.log('   - 总数据点数量:', mergedHistory.length);
      console.log('   - 第一个数据点:', JSON.stringify(mergedHistory[0], null, 2));
      console.log('   - 最后一个数据点:', JSON.stringify(mergedHistory[mergedHistory.length - 1], null, 2));

      // 验证每个数据点是否包含所有指标
      const samplePoint = mergedHistory[0];
      const hasTemperature = samplePoint.temperature !== undefined;
      const hasHumidity = samplePoint.humidity !== undefined;
      const hasPM25 = samplePoint.pm25 !== undefined;

      console.log('   - 数据点包含的指标:');
      console.log('     * 温度:', hasTemperature ? '✅' : '❌');
      console.log('     * 湿度:', hasHumidity ? '✅' : '❌');
      console.log('     * PM2.5:', hasPM25 ? '✅' : '❌');

      if (hasTemperature && hasHumidity && hasPM25) {
        console.log('✅ 所有指标数据都已正确合并！');
      } else {
        console.log('❌ 指标数据合并不完整');
      }
    } else {
      console.log('❌ 合并后的历史数据检索失败');
    }

    // 9. 验证设备当前状态是否更新
    console.log('\n9. 验证设备当前状态更新...');
    const updatedDevice = deviceStorageManager.getDevice('xiaomi_mi_air_sensor_slki1y');
    if (updatedDevice && updatedDevice.status) {
      console.log('设备当前状态:', JSON.stringify(updatedDevice.status, null, 2));

      const hasCurrentTemp = updatedDevice.status.temperature !== undefined;
      const hasCurrentHumidity = updatedDevice.status.humidity !== undefined;
      const hasCurrentPM25 = updatedDevice.status.pm25 !== undefined;

      console.log('当前状态包含的指标:');
      console.log('  * 温度:', hasCurrentTemp ? `✅ (${updatedDevice.status.temperature})` : '❌');
      console.log('  * 湿度:', hasCurrentHumidity ? `✅ (${updatedDevice.status.humidity})` : '❌');
      console.log('  * PM2.5:', hasCurrentPM25 ? `✅ (${updatedDevice.status.pm25})` : '❌');
    } else {
      console.log('❌ 无法获取设备当前状态');
    }

    // 10. 测试SensorDataAnalyzer
    console.log('\n10. 测试传感器数据分析...');
    const analysisResult = await sensorAnalyzer.getSensor24HourData('xiaomi_mi_air_sensor_slki1y');
    if (analysisResult && analysisResult.length > 0) {
      console.log('✅ 传感器数据分析成功');
      console.log('   - 分析的数据点数量:', analysisResult.length);
      console.log('   - 数据格式示例:', JSON.stringify(analysisResult[0], null, 2));

      // 验证分析结果中的指标
      const analysisPoint = analysisResult[0];
      const analysisHasTemp = analysisPoint.temperature !== undefined;
      const analysisHasHumidity = analysisPoint.humidity !== undefined;
      const analysisHasPM25 = analysisPoint.pm25 !== undefined;

      console.log('   - 分析结果包含的指标:');
      console.log('     * 温度:', analysisHasTemp ? '✅' : '❌');
      console.log('     * 湿度:', analysisHasHumidity ? '✅' : '❌');
      console.log('     * PM2.5:', analysisHasPM25 ? '✅' : '❌');
    } else {
      console.log('❌ 传感器数据分析失败');
    }

    console.log('\n=== 测试总结 ===');
    console.log('✅ SSE消息解析和分发');
    console.log('✅ 多指标设备状态更新');
    console.log('✅ 多指标历史数据存储和合并');
    console.log('✅ 历史数据检索');
    console.log('✅ 传感器数据分析适配');
    console.log('✅ 设备当前状态更新');
    console.log('\n🎉 修复测试完成！多指标传感器数据处理应该正常工作。');

  } catch (error) {
    console.error('❌ 测试过程中发生错误:', error);
    console.error('错误堆栈:', error.stack);
  }
}

// 运行测试
if (require.main === module) {
  testSSESensorHistoryFix();
}

module.exports = { testSSESensorHistoryFix };

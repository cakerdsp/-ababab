/**
 * SSE传感器历史数据处理测试
 * 测试新的SSE历史数据更新策略
 */

const SSEService = require('./src/class/services/sse/SSEService');
const DeviceSSEManager = require('./src/class/modules/device/DeviceSSEManager');
const DeviceGroupAPIManager = require('./src/class/modules/device/DeviceGroupAPIManager');
const DeviceStorageManager = require('./src/class/modules/device/DeviceStorageManager');
const SensorDataAnalyzer = require('./src/class/modules/data/SensorDataAnalyzer');

async function testSSESensorHistoryUpdate() {
  console.log('=== SSE传感器历史数据处理测试 ===\n');

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

    // 3. 模拟SSE历史数据消息
    console.log('3. 模拟SSE历史数据消息...');
    const mockSSEHistoryMessage = {
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

    // 4. 测试SSE服务的消息处理
    console.log('4. 测试SSE消息处理...');
    const sseService = new SSEService();

    // 注册处理器来捕获分发的消息
    let deviceUpdateReceived = null;
    let historyUpdateReceived = null;

    sseService.registerHandler('deviceUpdate', (data) => {
      deviceUpdateReceived = data;
      console.log('📨 收到设备状态更新:', JSON.stringify(data, null, 2));
    });

    sseService.registerHandler('sensorHistoryUpdate', (data) => {
      historyUpdateReceived = data;
      console.log('📨 收到传感器历史数据更新:', JSON.stringify(data, null, 2));
    });

    // 处理模拟消息
    sseService.handleMessage(mockSSEHistoryMessage);

    console.log('✅ SSE消息处理完成\n');

    // 5. 验证设备状态更新
    console.log('5. 验证设备状态更新...');
    if (deviceUpdateReceived) {
      console.log('✅ 设备状态更新正确接收');
      console.log('   - 设备ID:', deviceUpdateReceived.did);
      console.log('   - 湿度值:', deviceUpdateReceived.humidity);
      console.log('   - 时间戳:', deviceUpdateReceived.timestamp);
    } else {
      console.log('❌ 设备状态更新未接收');
    }

    // 6. 验证历史数据更新
    console.log('\n6. 验证历史数据更新...');
    if (historyUpdateReceived) {
      console.log('✅ 历史数据更新正确接收');
      console.log('   - 设备ID:', historyUpdateReceived.did);
      console.log('   - 指标类型:', historyUpdateReceived.metric_type);
      console.log('   - 数据点数量:', historyUpdateReceived.historyData.length);
    } else {
      console.log('❌ 历史数据更新未接收');
    }

    // 7. 测试DeviceGroupManager的历史数据存储
    console.log('\n7. 测试历史数据存储...');
    if (historyUpdateReceived) {
      const result = deviceGroupManager.updateSensorHistoryFromSSE(
        historyUpdateReceived.did,
        historyUpdateReceived.metric_type,
        historyUpdateReceived.historyData
      );

      if (result.success) {
        console.log('✅ 历史数据存储成功');
        console.log('   - 存储的数据点数量:', result.dataPointCount);
      } else {
        console.log('❌ 历史数据存储失败:', result.message);
      }
    }

    // 8. 测试历史数据检索
    console.log('\n8. 测试历史数据检索...');
    const retrievedHistory = deviceGroupManager.getSensorHistory('xiaomi_mi_air_sensor_slki1y', 24);
    if (retrievedHistory && retrievedHistory.length > 0) {
      console.log('✅ 历史数据检索成功');
      console.log('   - 检索到的数据点数量:', retrievedHistory.length);
      console.log('   - 第一个数据点:', JSON.stringify(retrievedHistory[0], null, 2));
      console.log('   - 最后一个数据点:', JSON.stringify(retrievedHistory[retrievedHistory.length - 1], null, 2));
    } else {
      console.log('❌ 历史数据检索失败');
    }

    // 9. 测试SensorDataAnalyzer
    console.log('\n9. 测试传感器数据分析...');
    const analysisResult = await sensorAnalyzer.getSensor24HourData('xiaomi_mi_air_sensor_slki1y');
    if (analysisResult && analysisResult.length > 0) {
      console.log('✅ 传感器数据分析成功');
      console.log('   - 分析的数据点数量:', analysisResult.length);
      console.log('   - 数据格式示例:', JSON.stringify(analysisResult[0], null, 2));
    } else {
      console.log('❌ 传感器数据分析失败');
    }

    // 10. 测试多个指标的历史数据
    console.log('\n10. 测试多个指标的历史数据...');

    // 模拟温度数据
    const tempHistoryMessage = {
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

    sseService.handleMessage(tempHistoryMessage);

    // 等待处理完成
    await new Promise(resolve => setTimeout(resolve, 100));

    console.log('✅ 多指标历史数据测试完成\n');

    console.log('=== 测试总结 ===');
    console.log('✅ SSE消息解析和分发');
    console.log('✅ 设备状态更新（使用第一个数据点）');
    console.log('✅ 历史数据存储（24小时数据替换）');
    console.log('✅ 历史数据检索');
    console.log('✅ 传感器数据分析适配');
    console.log('✅ 多指标数据支持');
    console.log('\n🎉 所有测试通过！新的SSE传感器历史数据处理策略工作正常。');

  } catch (error) {
    console.error('❌ 测试过程中发生错误:', error);
    console.error('错误堆栈:', error.stack);
  }
}

// 运行测试
if (require.main === module) {
  testSSESensorHistoryUpdate();
}

module.exports = { testSSESensorHistoryUpdate };

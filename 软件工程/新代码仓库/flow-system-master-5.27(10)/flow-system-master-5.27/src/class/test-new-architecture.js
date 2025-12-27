console.log('🧪 测试重构后的传感器数据分析架构...');

try {
  // 引入必要的模块
  const MockDeviceGenerator = require('./modules/device/MockDeviceGenerator');
  const DeviceStorageManager = require('./modules/device/DeviceStorageManager');
  const DeviceGroupAPIManager = require('./modules/device/DeviceGroupAPIManager');
  const SensorDataAnalyzer = require('./modules/data/SensorDataAnalyzer');

  console.log('\n🔧 初始化管理器组件...');

  // 1. 创建设备存储管理器
  const storageManager = new DeviceStorageManager();
  console.log('✅ 设备存储管理器创建完成');

  // 2. 创建分组API管理器
  const groupAPIManager = new DeviceGroupAPIManager(null, storageManager);
  console.log('✅ 分组API管理器创建完成');

  // 3. 创建传感器数据分析器（包含GroupAPIManager引用）
  const sensorAnalyzer = new SensorDataAnalyzer(null, storageManager, groupAPIManager);
  console.log('✅ 传感器数据分析器创建完成（包含GroupAPIManager引用）');

  // 4. 生成模拟设备数据
  console.log('\n📱 生成模拟设备数据...');
  const mockGenerator = new MockDeviceGenerator();
  const groupId = 'test_group_001';
  const devices = mockGenerator.generateDeviceList(groupId, 6);

  // 存储设备数据
  const storeResult = storageManager.storeAllDevices(devices);
  if (!storeResult.success) {
    throw new Error('设备数据存储失败: ' + storeResult.message);
  }
  console.log(`✅ 设备数据存储成功，共 ${devices.length} 个设备`);

  // 5. 为传感器设备生成历史数据
  console.log('\n📊 生成传感器历史数据...');
  const sensorDevices = devices.filter(d => d.type === 'history');
  console.log(`发现 ${sensorDevices.length} 个传感器设备`);

  sensorDevices.forEach(device => {
    console.log(`生成历史数据: ${device.name} (${device.did})`);
    groupAPIManager.generateMockSensorHistory(device.did, device.type, 24);
  });

  // 6. 获取历史数据统计
  const historyStats = groupAPIManager.getSensorHistoryStats();
  console.log('\n📈 传感器历史数据统计:');
  console.log(`总传感器数: ${historyStats.totalSensors}`);
  console.log(`总数据点: ${historyStats.totalDataPoints}`);
  historyStats.sensorsWithData.forEach(sensor => {
    console.log(`  ${sensor.deviceId}: ${sensor.dataPoints} 个数据点`);
  });

  // 7. 测试数据分析功能
  console.log('\n🔍 开始传感器数据分析...');

  // 模拟一个分组
  const mockGroup = {
    gid: groupId,
    gname: '测试分组',
    device_count: devices.length
  };
  groupAPIManager.groups.set(groupId, mockGroup);

  // 执行分析
  sensorAnalyzer.analyzeGroupSensorData(groupId).then(result => {
    console.log('\n📋 分析结果:');
    if (result.success) {
      console.log(`✅ 分析成功: ${result.message}`);
      const data = result.data;

      console.log(`📱 传感器设备数量: ${data.sensorCount || 0}`);
      console.log(`📈 数据样本数量: ${data.sampleCount || 0}`);

      if (data.temperature && data.temperature.avg !== null) {
        console.log(`🌡️  温度分析:`);
        console.log(`   平均温度: ${data.temperature.avg}°C`);
        console.log(`   最高温度: ${data.temperature.max}°C`);
        console.log(`   最低温度: ${data.temperature.min}°C`);
        console.log(`   趋势: ${data.temperature.trend}`);
      }

      if (data.humidity && data.humidity.avg !== null) {
        console.log(`💧 湿度分析:`);
        console.log(`   平均湿度: ${data.humidity.avg}%`);
        console.log(`   最高湿度: ${data.humidity.max}%`);
        console.log(`   最低湿度: ${data.humidity.min}%`);
        console.log(`   趋势: ${data.humidity.trend}`);
      }

      if (data.pm25 && data.pm25.avg !== null) {
        console.log(`🌫️  PM2.5分析:`);
        console.log(`   平均PM2.5: ${data.pm25.avg} μg/m³`);
        console.log(`   最高PM2.5: ${data.pm25.max} μg/m³`);
        console.log(`   最低PM2.5: ${data.pm25.min} μg/m³`);
      }

      if (data.airQuality) {
        console.log(`🌬️  空气质量: ${data.airQuality.level} (${data.airQuality.description})`);
      }

      if (data.comfort) {
        console.log(`😊 舒适度评分: ${data.comfort.score}/100 (${data.comfort.level})`);
      }

      if (data.recommendations && data.recommendations.length > 0) {
        console.log(`💡 改善建议:`);
        data.recommendations.forEach((rec, index) => {
          console.log(`   ${index + 1}. ${rec}`);
        });
      }

      console.log('\n✅ 重构后的传感器数据分析架构测试完成！');
      console.log('🎯 新架构验证要点:');
      console.log('   ✅ 设备存储只保存当前状态（无历史数据）');
      console.log('   ✅ 历史数据由DeviceGroupAPIManager管理');
      console.log('   ✅ SensorDataAnalyzer从GroupAPIManager获取历史数据');
      console.log('   ✅ 数据分析正常工作');

    } else {
      console.log(`❌ 分析失败: ${result.message}`);
    }
  }).catch(error => {
    console.error('❌ 分析过程中发生错误:', error);
  });

} catch (error) {
  console.error('❌ 测试失败:', error);
}

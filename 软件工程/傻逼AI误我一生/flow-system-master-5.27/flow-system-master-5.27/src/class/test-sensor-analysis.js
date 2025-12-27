const path = require('path');

// 模拟环境设置
process.env.NODE_ENV = 'test';

console.log('🧪 开始传感器数据分析测试...');

async function testSensorAnalysis() {
  try {
    // 引入必要的模块
    const MockDeviceGenerator = require('./modules/device/MockDeviceGenerator');
    const SensorDataAnalyzer = require('./modules/data/SensorDataAnalyzer');

    // 创建mock设备生成器
    const mockGenerator = new MockDeviceGenerator();

    // 生成模拟设备（包括传感器设备）
    const groupId = 'test_group_001';
    const devices = mockGenerator.generateDeviceList(groupId, 9);

    console.log('\n📊 生成的设备列表:');
    devices.forEach((device, index) => {
      console.log(`${index + 1}. ${device.name} (${device.type}) - ${device.online ? '在线' : '离线'}`);
      if (device.type === 'history' && device.data) {
        console.log(`   └── 历史数据: ${device.data.length} 条记录`);
        if (device.data.length > 0) {
          const firstData = device.data[0];
          const lastData = device.data[device.data.length - 1];
          console.log(`   └── 数据范围: ${firstData.time} 到 ${lastData.time}`);
          if (firstData.temperature !== undefined) {
            console.log(`   └── 温度范围: ${Math.min(...device.data.map(d => d.temperature))}°C - ${Math.max(...device.data.map(d => d.temperature))}°C`);
          }
          if (firstData.humidity !== undefined) {
            console.log(`   └── 湿度范围: ${Math.min(...device.data.map(d => d.humidity))}% - ${Math.max(...device.data.map(d => d.humidity))}%`);
          }
          if (firstData.pm25 !== undefined) {
            console.log(`   └── PM2.5范围: ${Math.min(...device.data.map(d => d.pm25))} - ${Math.max(...device.data.map(d => d.pm25))} μg/m³`);
          }
        }
      }
    });

    // 模拟存储管理器
    const mockStorage = {
      getDevicesByGroup: (groupId) => {
        console.log(`📂 获取分组 ${groupId} 的设备列表`);
        return devices.filter(d => d.groupId === groupId);
      },
      getSensorHistory: (deviceId, timeRange) => {
        console.log(`📈 获取设备 ${deviceId} 的传感器历史数据`);
        return null; // 模拟没有传感器历史
      },
      getDevice: (deviceId) => {
        console.log(`📱 获取设备 ${deviceId} 的详细信息`);
        return devices.find(d => d.did === deviceId);
      }
    };

    // 创建传感器数据分析器
    const analyzer = new SensorDataAnalyzer(null, mockStorage);

    console.log('\n🔍 开始分析传感器数据...');

    // 执行数据分析
    const analysisResult = await analyzer.analyzeGroupSensorData(groupId);

    console.log('\n📋 分析结果:');
    console.log(JSON.stringify(analysisResult, null, 2));

    if (analysisResult.success) {
      const data = analysisResult.data;

      console.log('\n📊 分析统计:');
      console.log(`✅ 分析成功: ${analysisResult.message}`);
      console.log(`📱 传感器设备数量: ${data.sensorCount || 0}`);
      console.log(`📈 数据样本数量: ${data.sampleCount || 0}`);

      if (data.temperature) {
        console.log(`🌡️  温度分析:`);
        console.log(`   平均温度: ${data.temperature.avg}°C`);
        console.log(`   最高温度: ${data.temperature.max}°C`);
        console.log(`   最低温度: ${data.temperature.min}°C`);
        console.log(`   趋势: ${data.temperature.trend}`);
      }

      if (data.humidity) {
        console.log(`💧 湿度分析:`);
        console.log(`   平均湿度: ${data.humidity.avg}%`);
        console.log(`   最高湿度: ${data.humidity.max}%`);
        console.log(`   最低湿度: ${data.humidity.min}%`);
        console.log(`   趋势: ${data.humidity.trend}`);
      }

      if (data.pm25) {
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

      console.log('\n✅ 传感器数据分析测试完成！');
    } else {
      console.log(`❌ 分析失败: ${analysisResult.message}`);
    }

  } catch (error) {
    console.error('❌ 测试异常:', error);
  }
}

// 运行测试
testSensorAnalysis();

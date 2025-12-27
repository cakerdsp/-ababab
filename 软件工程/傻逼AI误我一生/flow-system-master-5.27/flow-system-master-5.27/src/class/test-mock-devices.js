// 测试模拟设备生成器
const MockDeviceGenerator = require('./modules/device/MockDeviceGenerator');

function testMockDeviceGenerator() {
  console.log('🧪 [测试] 开始测试模拟设备生成器\n');

  try {
    // 创建生成器实例
    const generator = new MockDeviceGenerator();
    console.log('✅ [测试] 模拟设备生成器创建成功');

    // 模拟默认分组ID
    const mockGroupId = '949dcedd-d796-46fd-b565-9e1f1b87b332';

    // 生成设备列表
    console.log('\n📱 [测试] 生成模拟设备列表...');
    const devices = generator.generateDeviceList(mockGroupId, 9);

    console.log(`\n✅ [测试] 成功生成 ${devices.length} 个设备:`);

    // 输出设备详情
    devices.forEach((device, index) => {
      console.log(`\n${index + 1}. ${device.name}`);
      console.log(`   设备ID: ${device.did}`);
      console.log(`   类型: ${device.type}`);
      console.log(`   品牌: ${device.brand}`);
      console.log(`   在线状态: ${device.online ? '在线' : '离线'}`);
      console.log(`   分组: ${device.groupId}`);
      console.log(`   状态:`, JSON.stringify(device.status, null, 2));

      if (device.type === 'history') {
        console.log(`   传感器类型: ${device.metric_type}`);
        console.log(`   历史数据:`, device.data);
        console.log(`   时间戳: ${device.timestamp}`);
      }

      console.log(`   最后更新: ${device.lastUpdated}`);
    });

    // 统计信息
    console.log('\n📊 [测试] 设备统计:');
    const onlineCount = devices.filter(d => d.online).length;
    const offlineCount = devices.length - onlineCount;
    const sensorCount = devices.filter(d => d.type === 'history').length;
    const controllableCount = devices.filter(d => d.type !== 'history').length;

    console.log(`   总设备数: ${devices.length}`);
    console.log(`   在线设备: ${onlineCount}`);
    console.log(`   离线设备: ${offlineCount}`);
    console.log(`   传感器设备: ${sensorCount}`);
    console.log(`   可控制设备: ${controllableCount}`);

    // 品牌统计
    const brandStats = {};
    devices.forEach(device => {
      brandStats[device.brand] = (brandStats[device.brand] || 0) + 1;
    });

    console.log('\n🏷️ [测试] 品牌统计:');
    Object.entries(brandStats).forEach(([brand, count]) => {
      console.log(`   ${brand}: ${count} 个设备`);
    });

    // 类型统计
    const typeStats = {};
    devices.forEach(device => {
      typeStats[device.type] = (typeStats[device.type] || 0) + 1;
    });

    console.log('\n🔧 [测试] 类型统计:');
    Object.entries(typeStats).forEach(([type, count]) => {
      console.log(`   ${type}: ${count} 个设备`);
    });

    // 测试状态更新
    console.log('\n🔄 [测试] 测试设备状态更新...');
    const updatedDevices = generator.updateDeviceStatus(devices);
    console.log('✅ [测试] 设备状态更新完成');

    const newOnlineCount = updatedDevices.filter(d => d.online).length;
    console.log(`   更新后在线设备: ${newOnlineCount} (原: ${onlineCount})`);

    console.log('\n✅ [测试] 模拟设备生成器测试完成!');

  } catch (error) {
    console.error('❌ [测试] 测试失败:', error);
    console.error('❌ [测试] 错误堆栈:', error.stack);
  }
}

// 运行测试
if (require.main === module) {
  testMockDeviceGenerator();
}

module.exports = { testMockDeviceGenerator };

// 测试增强后的分组管理功能
const { accountManager } = require('./index');

async function testGroupManagement() {
  console.log('🧪 [测试] 开始测试增强后的分组管理功能\n');

  try {
    // 1. 测试获取所有分组
    console.log('📋 [测试] 获取所有分组...');
    const managers = accountManager.getDeviceManagers();
    const groups = managers.groupAPIManager.getAllGroups();
    console.log(`✅ [测试] 共有 ${groups.length} 个分组`);
    groups.forEach(group => {
      console.log(`   - ${group.gname}: ${group.device_count || 0} 个设备`);
    });

    // 2. 测试获取所有设备
    console.log('\n📱 [测试] 获取所有设备...');
    const allDevices = managers.storageManager.getAllDevices();
    console.log(`✅ [测试] 共有 ${allDevices.length} 个设备`);

    // 统计设备状态
    const onlineDevices = allDevices.filter(d => d.online);
    const offlineDevices = allDevices.filter(d => !d.online);
    const sensorDevices = allDevices.filter(d =>
      d.type === 'mi_temp_hum_sensor' || d.type === 'mi_air_sensor'
    );
    const controllableDevices = allDevices.filter(d =>
      d.type !== 'mi_temp_hum_sensor' && d.type !== 'mi_air_sensor'
    );

    console.log(`   - 在线设备: ${onlineDevices.length}`);
    console.log(`   - 离线设备: ${offlineDevices.length}`);
    console.log(`   - 传感器设备: ${sensorDevices.length}`);
    console.log(`   - 可控制设备: ${controllableDevices.length}`);

    // 3. 测试按分组获取设备
    console.log('\n🔍 [测试] 按分组获取设备...');
    for (const group of groups) {
      const groupDevices = managers.storageManager.getDevicesByGroup(group.gid);
      console.log(`   - ${group.gname} (${group.gid}): ${groupDevices.length} 个设备`);

      groupDevices.forEach(device => {
        const statusText = device.online ? '在线' : '离线';
        const typeText = getDeviceTypeName(device.type);
        console.log(`     * ${device.name} - ${typeText} - ${statusText}`);

        // 显示设备状态详情
        if (device.status) {
          const statusKeys = Object.keys(device.status);
          if (statusKeys.length > 0) {
            console.log(`       状态: ${statusKeys.map(key =>
              `${key}=${device.status[key]}`
            ).join(', ')}`);
          }
        }

        // 显示最后更新时间
        if (device.lastUpdated) {
          console.log(`       最后更新: ${device.lastUpdated}`);
        }
      });
    }

    // 4. 测试设备分组统计
    console.log('\n📊 [测试] 设备分组统计...');
    const deviceStats = managers.storageManager.getDeviceStats();
    console.log('   设备统计信息:');
    console.log(`   - 总设备数: ${deviceStats.total}`);
    console.log(`   - 在线设备: ${deviceStats.online}`);
    console.log(`   - 离线设备: ${deviceStats.offline}`);
    console.log(`   - 已分组设备: ${deviceStats.grouped}`);
    console.log(`   - 未分组设备: ${deviceStats.ungrouped}`);

    console.log('   品牌统计:');
    Object.entries(deviceStats.brandStats).forEach(([brand, count]) => {
      console.log(`   - ${brand}: ${count} 个`);
    });

    console.log('   类型统计:');
    Object.entries(deviceStats.typeStats).forEach(([type, count]) => {
      console.log(`   - ${getDeviceTypeName(type)}: ${count} 个`);
    });

    // 5. 测试分组统计刷新
    console.log('\n🔄 [测试] 刷新分组统计...');
    managers.groupAPIManager.refreshGroupStats();
    const refreshedGroups = managers.groupAPIManager.getAllGroups();
    console.log('✅ [测试] 分组统计已刷新');
    refreshedGroups.forEach(group => {
      console.log(`   - ${group.gname}: ${group.device_count || 0} 个设备, ${(group.deviceIds || []).length} 个设备ID`);
    });

    console.log('\n✅ [测试] 分组管理功能测试完成');

  } catch (error) {
    console.error('❌ [测试] 测试失败:', error);
    console.error('❌ [测试] 错误堆栈:', error.stack);
  }
}

// 设备类型名称映射
function getDeviceTypeName(type) {
  const typeMap = {
    'mi_temp_hum_sensor': '小米温湿度计',
    'mi_air_sensor': '青萍空气质量检测仪',
    'mi_ac': '小米空调',
    'midea_ac': '美的空调',
    'mi_humidifier': '小米加湿器',
    'midea_humidifier': '美的加湿器'
  };
  return typeMap[type] || type;
}

// 如果直接运行此文件，执行测试
if (require.main === module) {
  testGroupManagement();
}

module.exports = { testGroupManagement };

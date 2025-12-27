/**
 * 数据流测试脚本
 * 用于验证设备分配到默认分组后的数据同步是否正确
 */

// 模拟Electron环境
const mockElectron = {
  app: {
    getPath: (name) => {
      const os = require('os');
      switch (name) {
        case 'userData':
          return require('path').join(os.tmpdir(), 'electron-test-app');
        default:
          return os.tmpdir();
      }
    }
  }
};

// 在全局环境中模拟electron
global.electron = mockElectron;

const DeviceStorageManager = require('./modules/device/DeviceStorageManager');
const DeviceGroupAPIManager = require('./modules/device/DeviceGroupAPIManager');

async function testDataFlow() {
  console.log('🧪 开始数据流测试...');

  // 1. 初始化管理器
  const deviceStorageManager = new DeviceStorageManager();
  const deviceGroupAPIManager = new DeviceGroupAPIManager(null, deviceStorageManager);

  // 设置关联关系
  deviceStorageManager.setGroupAPIManager(deviceGroupAPIManager);

  // 2. 初始化管理器
  await deviceStorageManager.initialize();
  await deviceGroupAPIManager.initialize();

  // 启用离线模式
  deviceGroupAPIManager.enableOfflineMode();

  console.log('✅ 管理器初始化完成');

  // 3. 创建默认分组
  console.log('🔧 创建默认分组...');
  const defaultGroup = deviceGroupAPIManager.findOrCreateDefaultGroup();
  console.log('✅ 默认分组:', defaultGroup);

  // 4. 创建测试设备数据
  const testDevices = [
    {
      did: 'test-device-001',
      name: '测试小米温湿度计',
      type: 'mi_temp_hum_sensor',
      brand: 'xiaomi',
      online: true,
      status: {
        temperature: 22.5,
        humidity: 45.2,
        time: new Date().toISOString()
      }
    },
    {
      did: 'test-device-002',
      name: '测试空气质量检测仪',
      type: 'mi_air_sensor',
      brand: 'xiaomi',
      online: true,
      status: {
        temperature: 23.1,
        humidity: 48.5,
        pm25: 35,
        time: new Date().toISOString()
      }
    },
    {
      did: 'test-device-003',
      name: '测试小米空调',
      type: 'mi_ac',
      brand: 'xiaomi',
      online: false,
      status: {
        power: 'OFF',
        target_temperature: 26,
        mode: 'cool',
        fan_speed: 'auto'
      }
    }
  ];

  console.log('🔧 存储测试设备...');
  const storeResult = deviceStorageManager.storeAllDevices(testDevices);
  console.log('✅ 设备存储结果:', storeResult);

  // 5. 检查设备分配情况
  console.log('🔍 检查设备分配...');
  const allDevices = deviceStorageManager.getAllDevices();
  console.log('所有设备:', allDevices.map(d => ({
    did: d.did,
    name: d.name,
    groupId: d.groupId,
    group: d.group
  })));

  // 6. 执行未分组设备分配
  console.log('🔧 分配未分组设备...');
  await deviceGroupAPIManager.assignUngroupedDevices();

  // 7. 检查默认分组状态
  console.log('🔍 检查默认分组状态...');
  const updatedDefaultGroup = deviceGroupAPIManager.getDefaultGroup();
  console.log('更新后的默认分组:', updatedDefaultGroup);

  // 8. 获取默认分组设备
  const defaultGroupDevices = deviceStorageManager.getDevicesByGroup(updatedDefaultGroup.gid);
  console.log('默认分组设备:', defaultGroupDevices.map(d => ({
    did: d.did,
    name: d.name,
    groupId: d.groupId
  })));

  // 9. 验证数据一致性
  console.log('🔍 验证数据一致性...');
  const isConsistent =
    updatedDefaultGroup.deviceCount === defaultGroupDevices.length &&
    updatedDefaultGroup.deviceIds.length === defaultGroupDevices.length &&
    updatedDefaultGroup.deviceIds.every(id => defaultGroupDevices.some(d => d.did === id));

  console.log('数据一致性检查:', isConsistent ? '✅ 通过' : '❌ 失败');

  // 10. 获取所有分组状态
  console.log('🔍 所有分组状态:');
  const allGroups = deviceGroupAPIManager.getAllGroups();
  allGroups.forEach(group => {
    console.log(`  - ${group.gname}: ${group.deviceCount || 0} 个设备 (IDs: ${(group.deviceIds || []).join(', ')})`);
  });

  // 11. 测试分组统计刷新
  console.log('🔧 测试分组统计刷新...');
  deviceGroupAPIManager.refreshGroupStats();
  const refreshedGroups = deviceGroupAPIManager.getAllGroups();
  console.log('刷新后的分组统计:');
  refreshedGroups.forEach(group => {
    console.log(`  - ${group.gname}: ${group.deviceCount || 0} 个设备`);
  });

  console.log('🧪 数据流测试完成');
  return isConsistent;
}

// 如果直接运行这个文件，执行测试
if (require.main === module) {
  testDataFlow().then(success => {
    console.log(success ? '✅ 测试通过' : '❌ 测试失败');
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('❌ 测试异常:', error);
    process.exit(1);
  });
}

module.exports = testDataFlow;

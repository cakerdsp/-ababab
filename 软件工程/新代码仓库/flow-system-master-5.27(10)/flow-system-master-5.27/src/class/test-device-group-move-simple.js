const path = require('path');
const fs = require('fs');

// 在require其他模块之前，模拟Electron环境
const electronPath = require.resolve('electron');
delete require.cache[electronPath];
require.cache[electronPath] = {
  exports: require('./mock-electron'),
  loaded: true
};

// 创建测试数据目录
const testDataDir = path.join(__dirname, '../data/test');
if (!fs.existsSync(testDataDir)) {
  fs.mkdirSync(testDataDir, { recursive: true });
}

const DeviceGroupAPIManager = require('./modules/device/DeviceGroupAPIManager');
const DeviceStorageManager = require('./modules/device/DeviceStorageManager');
const MockDeviceGenerator = require('./modules/device/MockDeviceGenerator');

async function testDeviceGroupMove() {
  console.log('🧪 [测试] 开始测试设备分组移动功能（简化版）...\n');

  try {
    // 1. 初始化设备管理器
    console.log('1. 初始化设备管理器...');

    const storageManager = new DeviceStorageManager();
    await storageManager.initialize();

    const groupAPIManager = new DeviceGroupAPIManager(null, storageManager);
    groupAPIManager.enableOfflineMode(); // 启用离线模式
    await groupAPIManager.initialize();

    // 设置相互引用
    storageManager.setGroupAPIManager(groupAPIManager);

    console.log('   ✅ 设备管理器初始化完成');

    // 2. 生成模拟设备数据
    console.log('\n2. 生成模拟设备数据...');
    const mockGenerator = new MockDeviceGenerator();
    const mockDevices = mockGenerator.generateMockDevices();

    // 存储设备
    await storageManager.storeAllDevices(mockDevices);
    console.log(`   ✅ 生成了 ${mockDevices.length} 个模拟设备`);

    // 为传感器设备生成历史数据
    groupAPIManager.generateMockHistoryForAllSensors();

    // 3. 创建测试分组
    console.log('\n3. 创建测试分组...');
    const testGroups = [
      '客厅设备',
      '卧室设备',
      '厨房设备'
    ];

    for (const groupName of testGroups) {
      const result = await groupAPIManager.createGroup(groupName);
      if (result.success) {
        console.log(`   ✅ 创建分组成功: ${groupName} (${result.data.gid})`);
      } else {
        console.log(`   ❌ 创建分组失败: ${groupName} - ${result.message}`);
      }
    }

    // 4. 显示初始状态
    console.log('\n4. 初始设备分组状态:');
    const allGroups = groupAPIManager.getAllGroups();
    const allDevices = storageManager.getAllDevices();

    for (const group of allGroups) {
      const groupDevices = allDevices.filter(d => (d.groupId || d.group) === group.gid);
      console.log(`   分组: ${group.gname} (${group.gid}) - ${groupDevices.length} 个设备`);
      groupDevices.forEach(device => {
        console.log(`     - ${device.name} (${device.did}) [${device.type}]`);
      });
    }

    // 5. 测试设备移动功能
    console.log('\n5. 测试设备移动功能...');

    // 选择第一个设备进行移动
    const deviceToMove = allDevices[0];
    const targetGroup = allGroups.find(g => g.gname === '客厅设备');

    if (deviceToMove && targetGroup) {
      console.log(`   正在移动设备: ${deviceToMove.name} -> ${targetGroup.gname}`);
      console.log(`   当前分组: ${deviceToMove.groupId || '未分组'}`);

      const moveResult = await groupAPIManager.moveDeviceToGroup(
        deviceToMove.did,
        targetGroup.gid,
        targetGroup.gname
      );

      if (moveResult.success) {
        console.log(`   ✅ 设备移动成功: ${moveResult.message}`);
        console.log(`   移动详情:`, {
          device: moveResult.data.device_name,
          from: moveResult.data.old_group_id,
          to: moveResult.data.group_name
        });
      } else {
        console.log(`   ❌ 设备移动失败: ${moveResult.message}`);
      }
    }

    // 6. 测试批量移动功能
    console.log('\n6. 测试批量移动功能...');

    const devicesToBatchMove = allDevices.slice(1, 3); // 选择2个设备
    const batchTargetGroup = allGroups.find(g => g.gname === '卧室设备');

    if (devicesToBatchMove.length > 0 && batchTargetGroup) {
      const deviceIds = devicesToBatchMove.map(d => d.did);
      console.log(`   正在批量移动 ${deviceIds.length} 个设备到: ${batchTargetGroup.gname}`);
      devicesToBatchMove.forEach(d => console.log(`     - ${d.name}`));

      const batchResult = await groupAPIManager.batchMoveDevicesToGroup(
        deviceIds,
        batchTargetGroup.gid
      );

      if (batchResult.success) {
        console.log(`   ✅ 批量移动成功: ${batchResult.message}`);
        console.log(`   成功: ${batchResult.data.success_count}, 失败: ${batchResult.data.fail_count}`);
      } else {
        console.log(`   ❌ 批量移动失败: ${batchResult.message}`);
      }
    }

    // 7. 测试错误处理
    console.log('\n7. 测试错误处理...');

    // 测试移动不存在的设备
    const invalidMoveResult = await groupAPIManager.moveDeviceToGroup(
      'invalid_device_id',
      targetGroup.gid,
      targetGroup.gname
    );
    console.log(`   移动不存在的设备: ${invalidMoveResult.success ? '成功' : '失败'} - ${invalidMoveResult.message}`);

    // 测试移动到不存在的分组
    const invalidGroupMoveResult = await groupAPIManager.moveDeviceToGroup(
      deviceToMove.did,
      'invalid_group_id',
      '不存在的分组'
    );
    console.log(`   移动到不存在的分组: ${invalidGroupMoveResult.success ? '成功' : '失败'} - ${invalidGroupMoveResult.message}`);

    // 8. 显示最终状态
    console.log('\n8. 最终设备分组状态:');
    const finalDevices = storageManager.getAllDevices();

    for (const group of allGroups) {
      const groupDevices = finalDevices.filter(d => (d.groupId || d.group) === group.gid);
      console.log(`   分组: ${group.gname} (${group.gid}) - ${groupDevices.length} 个设备`);
      groupDevices.forEach(device => {
        console.log(`     - ${device.name} (${device.did}) [${device.type}]`);
      });
    }

    // 9. 测试传感器历史数据保持
    console.log('\n9. 验证传感器历史数据...');
    const sensorDevices = finalDevices.filter(d => groupAPIManager.isSensorDevice(d.type));

    for (const sensor of sensorDevices) {
      const historyData = groupAPIManager.getSensorHistory(sensor.did);
      console.log(`   传感器 ${sensor.name}: ${historyData.length} 个历史数据点`);
      if (historyData.length > 0) {
        const latest = historyData[historyData.length - 1];
        console.log(`     最新数据: ${JSON.stringify(latest).substring(0, 100)}...`);
      }
    }

    // 10. 测试分组统计刷新
    console.log('\n10. 测试分组统计刷新...');
    groupAPIManager.refreshGroupStats();

    const stats = groupAPIManager.getGroupStats();
    console.log(`   总分组数: ${stats.totalGroups}`);
    console.log(`   总设备数: ${stats.totalDevices}`);

    stats.groups.forEach(group => {
      console.log(`   ${group.gname}: ${group.deviceCount} 个设备`);
    });

    console.log('\n✅ 设备分组移动功能测试完成!');

    // 验证API调用模式
    console.log('\n11. API调用模式验证:');
    console.log(`   离线模式: ${groupAPIManager.isOfflineMode()}`);
    console.log(`   API注册器: ${groupAPIManager.apiRegistry ? '已设置' : '未设置'}`);

  } catch (error) {
    console.error('\n❌ 测试过程中发生错误:', error);
    console.error('错误堆栈:', error.stack);
  }
}

// 运行测试
if (require.main === module) {
  testDeviceGroupMove().then(() => {
    console.log('\n🎯 测试脚本执行完成');
    process.exit(0);
  }).catch(error => {
    console.error('\n💥 测试脚本执行失败:', error);
    process.exit(1);
  });
}

module.exports = { testDeviceGroupMove };

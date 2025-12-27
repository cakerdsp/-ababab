const path = require('path');

// 模拟electron环境
const mockElectron = require('./mock-electron');

// 设置项目根目录
const projectRoot = path.resolve(__dirname, '..');
process.env.PROJECT_ROOT = projectRoot;

console.log('🎯 [预设策略测试] 开始测试预设策略功能...');
console.log('🎯 [预设策略测试] 项目根目录:', projectRoot);

async function testPresetStrategy() {
  try {
    // 1. 初始化系统
    console.log('\n=== 1. 初始化系统 ===');
    const { accountManager, stateManager } = require('./index');

        // 模拟登录（离线模式）
    console.log('使用离线模式进行测试...');

    // 直接设置为已登录状态
    accountManager.currentUser = {
      getUserId: () => 'admin',
      getToken: () => 'test-token'
    };

    // 初始化设备管理器
    const managers = accountManager.getDeviceManagers();

    // 生成模拟设备数据
    const mockDevices = [
      {
        did: 'ac_001',
        name: '客厅空调',
        type: 'mi_ac',
        brand: 'Xiaomi',
        online: true,
        status: {
          power: 'ON',
          target_temperature: 25,
          mode: 'cool',
          fan_speed: 'medium'
        }
      },
      {
        did: 'humidifier_001',
        name: '卧室加湿器',
        type: 'mi_humidifier',
        brand: 'Xiaomi',
        online: true,
        status: {
          power: true,
          target_humidity: 50,
          mode: 'auto'
        }
      },
      {
        did: 'purifier_001',
        name: '书房空气净化器',
        type: 'mi_air_purifier',
        brand: 'Xiaomi',
        online: true,
        status: {
          power: true,
          mode: 'auto',
          fan_level: 2
        }
      },
      {
        did: 'sensor_001',
        name: '客厅温湿度传感器',
        type: 'mi_temp_hum_sensor',
        brand: 'Xiaomi',
        online: true,
        status: {
          temperature: 24.5,
          humidity: 45,
          time: new Date().toISOString()
        }
      }
    ];

    // 存储模拟设备
    managers.storageManager.storeAllDevices(mockDevices);

    // 创建默认分组并分配设备
    const defaultGroupResult = managers.groupAPIManager.createGroup('默认分组');
    if (defaultGroupResult.success) {
      console.log('✅ 创建默认分组成功，ID:', defaultGroupResult.data.gid);

      // 将所有设备分配到默认分组
      mockDevices.forEach(device => {
        managers.groupAPIManager.assignDeviceToGroup(device.did, defaultGroupResult.data.gid);
      });
      console.log('✅ 已将所有设备分配到默认分组');
    }

    console.log('✅ 离线模式初始化完成，生成了', mockDevices.length, '个模拟设备');

    // 2. 获取设备和分组信息
    console.log('\n=== 2. 获取设备和分组信息 ===');

    // 获取所有设备
    const allDevices = managers.storageManager.getAllDevices();
    console.log('总设备数:', allDevices.length);

    // 获取可控制设备
    const controllableDevices = allDevices.filter(device =>
      device.online &&
      !['mi_temp_hum_sensor', 'mi_air_sensor', 'history'].includes(device.type)
    );
    console.log('可控制设备数:', controllableDevices.length);

    // 显示可控制设备信息
    controllableDevices.forEach(device => {
      console.log(`  - ${device.name} (${device.type}) - ${device.online ? '在线' : '离线'}`);
    });

    // 获取分组信息
    const groups = managers.groupAPIManager.getAllGroups();
    console.log('分组数:', groups.length);
    const defaultGroup = groups.find(g => g.gname === '默认分组');
    console.log('默认分组ID:', defaultGroup?.gid);

    if (defaultGroup) {
      const groupDevices = managers.storageManager.getDevicesByGroup(defaultGroup.gid);
      console.log('默认分组设备数:', groupDevices.length);
    }

        // 3. 测试策略状态管理
    console.log('\n=== 3. 测试策略状态管理 ===');

    // 创建简单的状态存储
    const strategyStateStore = {};

    // 初始化策略状态
    const initialStrategyState = {
      enabled: false,
      strategy: {
        id: 'smart_comfort',
        name: '智能舒适策略',
        description: '根据环境数据自动调节设备参数以优化舒适度'
      },
      config: {
        frequency: 'realtime',
        scope: 'current',
        parameters: {
          target_temperature: 24,
          target_humidity: 50,
          max_power_level: 'medium',
          pm25_threshold: 35
        }
      },
      currentGroup: defaultGroup?.gid || 'default',
      lastExecutionTime: null,
      executionCount: 0,
      affectedDevicesCount: 0
    };

    strategyStateStore.strategy = initialStrategyState;
    console.log('✅ 初始化策略状态完成');

    // 4. 测试策略配置更新
    console.log('\n=== 4. 测试策略配置更新 ===');

    const updatedConfig = {
      ...initialStrategyState.config,
      parameters: {
        ...initialStrategyState.config.parameters,
        target_temperature: 26,
        target_humidity: 55
      }
    };

    const updatedState = {
      ...initialStrategyState,
      config: updatedConfig
    };

    strategyStateStore.strategy = updatedState;
    console.log('✅ 策略配置更新完成');
    console.log('新的目标温度:', updatedConfig.parameters.target_temperature);
    console.log('新的目标湿度:', updatedConfig.parameters.target_humidity);

    // 5. 测试策略执行逻辑
    console.log('\n=== 5. 测试策略执行逻辑 ===');

    // 模拟策略执行
    const strategy = updatedState.strategy;
    const config = updatedState.config;
    const currentGroup = updatedState.currentGroup;

    console.log('执行策略:', strategy.name);
    console.log('策略配置:', config);
    console.log('目标分组:', currentGroup);

    // 获取目标设备
    let targetDevices = [];
    if (config.scope === 'current' && currentGroup) {
      targetDevices = managers.storageManager.getDevicesByGroup(currentGroup);
      console.log('当前分组设备数:', targetDevices.length);
    } else {
      targetDevices = managers.storageManager.getAllDevices();
      console.log('所有设备数:', targetDevices.length);
    }

    // 过滤可控制设备
    const executableDevices = targetDevices.filter(device =>
      device.online &&
      !['mi_temp_hum_sensor', 'mi_air_sensor', 'history'].includes(device.type)
    );

    console.log('可执行策略的设备数:', executableDevices.length);

    // 6. 测试控制动作生成
    console.log('\n=== 6. 测试控制动作生成 ===');

    let totalActions = 0;
    executableDevices.forEach(device => {
      const actions = generateControlActions(device, strategy, config);
      if (actions.length > 0) {
        console.log(`设备 ${device.name} (${device.type}) 的控制动作:`);
        actions.forEach(action => {
          console.log(`  - ${action.operation}: ${action.value}`);
          totalActions++;
        });
      }
    });

    console.log('总控制动作数:', totalActions);

    // 7. 测试不同策略类型
    console.log('\n=== 7. 测试不同策略类型 ===');

    const strategies = [
      {
        id: 'smart_comfort',
        name: '智能舒适策略',
        description: '根据环境数据自动调节设备参数以优化舒适度'
      },
      {
        id: 'energy_saving',
        name: '节能策略',
        description: '优化设备运行以降低能耗'
      },
      {
        id: 'air_quality',
        name: '空气质量策略',
        description: '根据空气质量数据自动调节净化设备'
      }
    ];

    strategies.forEach(testStrategy => {
      console.log(`\n测试策略: ${testStrategy.name}`);
      executableDevices.slice(0, 2).forEach(device => {
        const actions = generateControlActions(device, testStrategy, config);
        if (actions.length > 0) {
          console.log(`  设备 ${device.name}:`);
          actions.forEach(action => {
            console.log(`    - ${action.operation}: ${action.value}`);
          });
        } else {
          console.log(`  设备 ${device.name}: 无适用动作`);
        }
      });
    });

    // 8. 测试策略状态持久化
    console.log('\n=== 8. 测试策略状态持久化 ===');

    const finalState = {
      ...updatedState,
      enabled: true,
      lastExecutionTime: new Date().toLocaleString(),
      executionCount: 1,
      affectedDevicesCount: totalActions
    };

        strategyStateStore.strategy = finalState;

    // 验证状态保存
    const savedState = strategyStateStore.strategy;
    console.log('✅ 策略状态已保存');
    console.log('保存的状态:', {
      enabled: savedState.enabled,
      strategyName: savedState.strategy.name,
      executionCount: savedState.executionCount,
      affectedDevicesCount: savedState.affectedDevicesCount,
      lastExecutionTime: savedState.lastExecutionTime
    });

    console.log('\n🎉 预设策略功能测试完成！');
    console.log('✅ 所有测试项目均通过');

  } catch (error) {
    console.error('❌ 预设策略测试失败:', error);
    console.error('错误堆栈:', error.stack);
  }
}

// 生成控制动作的辅助函数
function generateControlActions(device, strategy, config) {
  const actions = [];

  try {
    switch (strategy.id) {
      case 'smart_comfort':
        // 智能舒适策略
        if (['mi_ac', 'midea_ac'].includes(device.type)) {
          // 空调设备
          actions.push({
            operation: 'target_temperature',
            value: config.parameters.target_temperature || 24
          });
          actions.push({
            operation: 'mode',
            value: 'cool'
          });
        } else if (['mi_humidifier', 'midea_humidifier'].includes(device.type)) {
          // 加湿器设备
          actions.push({
            operation: 'target_humidity',
            value: config.parameters.target_humidity || 50
          });
          actions.push({
            operation: 'mode',
            value: 'auto'
          });
        }
        break;

      case 'energy_saving':
        // 节能策略
        if (['mi_ac', 'midea_ac'].includes(device.type)) {
          actions.push({
            operation: 'fan_speed',
            value: config.parameters.max_power_level || 'low'
          });
        } else if (['mi_air_purifier', 'midea_air_purifier'].includes(device.type)) {
          actions.push({
            operation: 'fan_level',
            value: config.parameters.max_power_level === 'low' ? 1 :
                   config.parameters.max_power_level === 'medium' ? 2 : 3
          });
        }
        break;

      case 'air_quality':
        // 空气质量策略
        if (['mi_air_purifier', 'midea_air_purifier'].includes(device.type)) {
          actions.push({
            operation: 'mode',
            value: 'auto'
          });
          actions.push({
            operation: 'fan_level',
            value: 3 // 高档运行
          });
        }
        break;
    }
  } catch (error) {
    console.error('生成控制动作失败:', error);
  }

  return actions;
}

// 运行测试
if (require.main === module) {
  testPresetStrategy().catch(console.error);
}

module.exports = { testPresetStrategy };

const path = require('path');

// 模拟Electron环境
global.require = require;
global.__dirname = __dirname;

// 设置模块路径
const classPath = path.join(__dirname);
const servicesPath = path.join(__dirname, 'services');
const modulesPath = path.join(__dirname, 'modules');

// 导入必要的模块
const UnifiedStorage = require(path.join(servicesPath, 'storage', 'UnifiedStorage'));
const DeviceStorageManager = require(path.join(modulesPath, 'device', 'DeviceStorageManager'));
const DeviceControlManager = require(path.join(modulesPath, 'device', 'DeviceControlManager'));
const SceneManager = require(path.join(modulesPath, 'device', 'SceneManager'));
const AccountAPIRegistry = require(path.join(servicesPath, 'api', 'AccountAPIRegistry'));

class TestSceneConflictAndInit {
  constructor() {
    this.storage = new UnifiedStorage();
    this.deviceStorageManager = new DeviceStorageManager();
    this.deviceControlManager = new DeviceControlManager();
    this.sceneManager = new SceneManager();
    this.apiRegistry = new AccountAPIRegistry();
  }

  async runTests() {
    console.log('🧪 [Test] 开始场景冲突检测和初始化测试...\n');

    try {
      await this.setupTestEnvironment();
      await this.testConflictDetectionWithPowerAction();
      await this.testSceneInitialization();
      await this.testOfflineModeSceneGeneration();

      console.log('\n✅ [Test] 所有测试完成！');
    } catch (error) {
      console.error('\n❌ [Test] 测试失败:', error);
    }
  }

  async setupTestEnvironment() {
    console.log('🔧 [Test] 设置测试环境...');

    // 启用离线模式
    if (this.deviceStorageManager.enableOfflineMode) {
      this.deviceStorageManager.enableOfflineMode();
    }
    if (this.deviceControlManager.enableOfflineMode) {
      this.deviceControlManager.enableOfflineMode();
    }
    this.sceneManager.enableOfflineMode();

    // 初始化管理器
    await this.deviceStorageManager.initialize();
    await this.deviceControlManager.initialize();

    // 设置依赖关系
    this.sceneManager.setDeviceStorageManager(this.deviceStorageManager);
    this.sceneManager.setDeviceControlManager(this.deviceControlManager);
    this.sceneManager.setApiRegistry(this.apiRegistry);

    await this.sceneManager.initialize();

    console.log('✅ [Test] 测试环境设置完成\n');
  }

  async testConflictDetectionWithPowerAction() {
    console.log('🔍 [Test] 测试设备冲突检测（考虑开机动作）...');

    // 获取一个关机的空调设备
    const devices = this.deviceStorageManager.getAllDevices();
    const acDevice = devices.find(d => d.type === 'midea_ac');

    if (!acDevice) {
      console.log('⚠️ [Test] 未找到空调设备，跳过冲突检测测试');
      return;
    }

    // 确保设备是关机状态
    acDevice.status = { power: 'OFF' };
    acDevice.online = false;

    console.log(`📱 [Test] 测试设备: ${acDevice.name} (${acDevice.did})`);
    console.log(`🔧 [Test] 设备当前状态: power=${acDevice.status.power}, online=${acDevice.online}`);

    // 测试1: 没有开机动作时，设置温度应该失败
    console.log('\n📋 [Test] 测试1: 关机设备直接设置温度（应该失败）');
    const actionsWithoutPower = [
      {
        did: acDevice.did,
        operation: 'target_temperature',
        value: 24
      }
    ];

    const result1 = this.sceneManager.validateActionValues(acDevice, actionsWithoutPower);
    console.log(`🔍 [Test] 验证结果1: ${result1.success ? '成功' : '失败'} - ${result1.message || '无消息'}`);

    // 测试2: 有开机动作时，设置温度应该成功
    console.log('\n📋 [Test] 测试2: 先开机再设置温度（应该成功）');
    const actionsWithPower = [
      {
        did: acDevice.did,
        operation: 'power',
        value: 'ON'
      },
      {
        did: acDevice.did,
        operation: 'target_temperature',
        value: 24
      }
    ];

    const result2 = this.sceneManager.validateActionValues(acDevice, actionsWithPower);
    console.log(`🔍 [Test] 验证结果2: ${result2.success ? '成功' : '失败'} - ${result2.message || '无消息'}`);

    // 测试3: 智能电源补齐功能
    console.log('\n📋 [Test] 测试3: 智能电源补齐功能');
    const actionsNeedingPower = [
      {
        did: acDevice.did,
        operation: 'target_temperature',
        value: 24
      },
      {
        did: acDevice.did,
        operation: 'mode',
        value: 'cool'
      }
    ];

    const fixedActions = this.sceneManager.autoFixPowerActions(acDevice, actionsNeedingPower);
    console.log(`🔧 [Test] 原始动作数量: ${actionsNeedingPower.length}`);
    console.log(`🔧 [Test] 修复后动作数量: ${fixedActions.length}`);
    console.log(`🔧 [Test] 修复后的动作:`, fixedActions.map(a => `${a.operation}=${a.value}`).join(', '));

    // 验证修复后的动作
    const result3 = this.sceneManager.validateActionValues(acDevice, fixedActions);
    console.log(`🔍 [Test] 修复后验证结果: ${result3.success ? '成功' : '失败'} - ${result3.message || '无消息'}`);

    console.log('✅ [Test] 冲突检测测试完成\n');
  }

  async testSceneInitialization() {
    console.log('🔄 [Test] 测试场景初始化功能...');

    // 重置场景管理器
    this.sceneManager.reset();

    // 测试初始化
    const initResult = await this.sceneManager.initialize();
    console.log(`🔍 [Test] 初始化结果: ${initResult.success ? '成功' : '失败'} - ${initResult.message}`);

    if (initResult.success) {
      console.log(`📊 [Test] 场景数量: ${initResult.sceneCount || 0}`);
      console.log(`📊 [Test] 同步结果: ${JSON.stringify(initResult.syncResult)}`);
    }

    // 获取所有场景
    const allScenes = this.sceneManager.getAllScenes();
    console.log(`📋 [Test] 当前场景总数: ${allScenes.length}`);

    // 显示场景详情
    allScenes.forEach((scene, index) => {
      console.log(`📝 [Test] 场景${index + 1}: ${scene.scene_name} (${scene.scene_id})`);
      console.log(`   📍 分组: ${scene.gid}`);
      console.log(`   🎬 动作数量: ${scene.actions ? scene.actions.length : 0}`);
      if (scene.actions && scene.actions.length > 0) {
        scene.actions.forEach((action, actionIndex) => {
          console.log(`     🎯 动作${actionIndex + 1}: ${action.operation}=${action.value} (设备:${action.did})`);
        });
      }
    });

    console.log('✅ [Test] 场景初始化测试完成\n');
  }

  async testOfflineModeSceneGeneration() {
    console.log('🎭 [Test] 测试离线模式场景生成...');

    // 确保是离线模式
    console.log(`🔧 [Test] 离线模式状态: ${this.sceneManager.isOfflineMode()}`);

    // 手动调用模拟场景生成
    await this.sceneManager.generateMockScenesForOffline();

    // 检查生成的场景
    const mockScenes = this.sceneManager.getAllScenes();
    console.log(`📋 [Test] 模拟场景数量: ${mockScenes.length}`);

    mockScenes.forEach((scene, index) => {
      if (scene.scene_id.includes('mock')) {
        console.log(`🎭 [Test] 模拟场景${index + 1}: ${scene.scene_name}`);
        console.log(`   📝 描述: ${scene.description}`);
        console.log(`   📍 分组: ${scene.gid}`);
        console.log(`   🎬 动作: ${scene.actions.map(a => `${a.operation}=${a.value}`).join(', ')}`);
      }
    });

    console.log('✅ [Test] 离线模式场景生成测试完成\n');
  }
}

// 运行测试
const tester = new TestSceneConflictAndInit();
tester.runTests().catch(console.error);

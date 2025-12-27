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

class TestSceneActionBufferSimple {
  constructor() {
    this.storage = new UnifiedStorage();
    this.deviceStorageManager = new DeviceStorageManager();
    this.deviceControlManager = new DeviceControlManager();
    this.sceneManager = new SceneManager();
  }

  async runTests() {
    console.log('🧪 [Test] 开始场景动作缓冲区简化测试...\n');

    try {
      await this.setupTestEnvironment();
      await this.testActionBufferValidation();
      await this.testSceneActionReplacement();

      console.log('\n✅ [Test] 所有测试完成！');
    } catch (error) {
      console.error('\n❌ [Test] 测试失败:', error);
    }
  }

  async setupTestEnvironment() {
    console.log('🔧 [Test] 设置测试环境...');

    // 启用离线模式
    this.sceneManager.enableOfflineMode();

    // 初始化管理器
    await this.deviceStorageManager.initialize();
    await this.deviceControlManager.initialize();

    // 设置依赖关系
    this.sceneManager.setDeviceStorageManager(this.deviceStorageManager);
    this.sceneManager.setDeviceControlManager(this.deviceControlManager);

    await this.sceneManager.initialize();

    console.log('✅ [Test] 测试环境设置完成\n');
  }

  async testActionBufferValidation() {
    console.log('🔍 [Test] 测试动作缓冲区验证功能...');

    // 获取一个空调设备
    const devices = this.deviceStorageManager.getAllDevices();
    const acDevice = devices.find(d => d.type === 'midea_ac');

    if (!acDevice) {
      console.log('⚠️ [Test] 未找到空调设备，跳过测试');
      return;
    }

    // 设置设备为在线但关机状态
    acDevice.status = { power: 'OFF' };
    acDevice.online = true; // 设置为在线，这样可以控制

    console.log(`📱 [Test] 测试设备: ${acDevice.name} (${acDevice.did})`);
    console.log(`🔧 [Test] 设备当前状态: power=${acDevice.status.power}, online=${acDevice.online}`);

    // 模拟前端场景：用户先添加开机动作，然后添加温度设置
    console.log('\n📋 [Test] 模拟场景：先添加开机动作，再添加温度设置');

    // 第一步：添加开机动作
    const powerAction = {
      did: acDevice.did,
      operation: 'power',
      value: 'ON'
    };

    console.log('🎬 [Test] 第一步：验证开机动作');
    const powerValidation = this.sceneManager.validateSceneActions([powerAction]);
    console.log(`🔍 [Test] 开机动作验证: ${powerValidation.valid ? '成功' : '失败'} - ${powerValidation.message}`);

    // 第二步：在"动作缓冲区"中已有开机动作的情况下，添加温度设置
    const temperatureAction = {
      did: acDevice.did,
      operation: 'target_temperature',
      value: 24
    };

    const combinedActions = [powerAction, temperatureAction];

    console.log('🎬 [Test] 第二步：验证组合动作（开机+温度）');
    const combinedValidation = this.sceneManager.validateSceneActions(combinedActions);
    console.log(`🔍 [Test] 组合动作验证: ${combinedValidation.valid ? '成功' : '失败'} - ${combinedValidation.message}`);

    // 第三步：测试只有温度设置（没有开机动作）的情况
    console.log('🎬 [Test] 第三步：验证单独温度动作（应该失败）');
    const temperatureOnlyValidation = this.sceneManager.validateSceneActions([temperatureAction]);
    console.log(`🔍 [Test] 单独温度验证: ${temperatureOnlyValidation.valid ? '成功' : '失败'} - ${temperatureOnlyValidation.message}`);

    // 验证关键点：组合动作应该成功，单独温度动作应该失败
    if (combinedValidation.valid && !temperatureOnlyValidation.valid) {
      console.log('✅ [Test] 动作缓冲区验证逻辑正确！');
    } else {
      console.log('❌ [Test] 动作缓冲区验证逻辑有问题！');
    }

    console.log('✅ [Test] 动作缓冲区验证测试完成\n');
  }

  async testSceneActionReplacement() {
    console.log('🔄 [Test] 测试场景动作替换功能...');

    // 创建一个测试场景
    const testSceneData = {
      scene_name: '测试场景替换',
      description: '用于测试动作替换功能',
      gid: 'default',
      actions: []
    };

    console.log('🎬 [Test] 创建测试场景...');
    const createResult = await this.sceneManager.createScene(testSceneData);
    console.log(`🔍 [Test] 场景创建: ${createResult.success ? '成功' : '失败'} - ${createResult.message}`);

    if (!createResult.success) {
      console.log('❌ [Test] 场景创建失败，跳过替换测试');
      return;
    }

    const sceneId = createResult.data.scene_id;

    // 获取设备
    const devices = this.deviceStorageManager.getAllDevices();
    const acDevice = devices.find(d => d.type === 'midea_ac');

    if (!acDevice) {
      console.log('⚠️ [Test] 未找到空调设备，跳过替换测试');
      return;
    }

    // 设置设备为在线状态
    acDevice.online = true;

    // 第一次更新：添加一些动作
    const initialActions = [
      {
        did: acDevice.did,
        operation: 'power',
        value: 'ON'
      },
      {
        did: acDevice.did,
        operation: 'target_temperature',
        value: 26
      }
    ];

    console.log('🎬 [Test] 第一次更新：添加初始动作');
    const firstUpdate = await this.sceneManager.updateScene(sceneId, {
      replaceActions: initialActions
    });
    console.log(`🔍 [Test] 第一次更新: ${firstUpdate.success ? '成功' : '失败'} - ${firstUpdate.message}`);

    if (!firstUpdate.success) {
      console.log('❌ [Test] 第一次更新失败，跳过后续测试');
      return;
    }

    // 检查场景状态
    const sceneAfterFirst = this.sceneManager.getSceneDetail(sceneId);
    if (sceneAfterFirst && sceneAfterFirst.actions) {
      console.log(`📊 [Test] 第一次更新后动作数量: ${sceneAfterFirst.actions.length}`);
      sceneAfterFirst.actions.forEach((action, index) => {
        console.log(`   🎯 动作${index + 1}: ${action.operation}=${action.value}`);
      });
    }

    // 第二次更新：完全替换动作（模拟删除一个动作）
    const replacedActions = [
      {
        did: acDevice.did,
        operation: 'power',
        value: 'ON'
      }
      // 注意：这里删除了温度设置动作
    ];

    console.log('🎬 [Test] 第二次更新：替换动作（删除温度设置）');
    const secondUpdate = await this.sceneManager.updateScene(sceneId, {
      replaceActions: replacedActions
    });
    console.log(`🔍 [Test] 第二次更新: ${secondUpdate.success ? '成功' : '失败'} - ${secondUpdate.message}`);

    if (!secondUpdate.success) {
      console.log('❌ [Test] 第二次更新失败');
      return;
    }

    // 检查场景状态
    const sceneAfterSecond = this.sceneManager.getSceneDetail(sceneId);
    if (sceneAfterSecond && sceneAfterSecond.actions) {
      console.log(`📊 [Test] 第二次更新后动作数量: ${sceneAfterSecond.actions.length}`);
      sceneAfterSecond.actions.forEach((action, index) => {
        console.log(`   🎯 动作${index + 1}: ${action.operation}=${action.value}`);
      });

      // 验证删除是否生效
      const hasTemperatureAction = sceneAfterSecond.actions.some(action => action.operation === 'target_temperature');
      console.log(`🔍 [Test] 温度动作是否被删除: ${hasTemperatureAction ? '否（删除失败）' : '是（删除成功）'}`);

      if (!hasTemperatureAction) {
        console.log('✅ [Test] 动作删除功能正常！');
      } else {
        console.log('❌ [Test] 动作删除功能有问题！');
      }
    }

    console.log('✅ [Test] 场景动作替换测试完成\n');
  }
}

// 运行测试
const tester = new TestSceneActionBufferSimple();
tester.runTests().catch(console.error);

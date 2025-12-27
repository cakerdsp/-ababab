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

class TestSceneReplacement {
  constructor() {
    this.storage = new UnifiedStorage();
    this.deviceStorageManager = new DeviceStorageManager();
    this.deviceControlManager = new DeviceControlManager();
    this.sceneManager = new SceneManager();
  }

  async runTests() {
    console.log('🧪 [Test] 开始场景动作替换测试...\n');

    try {
      await this.setupTestEnvironment();
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

  async testSceneActionReplacement() {
    console.log('🔄 [Test] 测试场景动作替换功能...');

    // 获取设备的实际分组ID
    const devices = this.deviceStorageManager.getAllDevices();
    const acDevice = devices.find(d => d.type === 'midea_ac');

    if (!acDevice) {
      console.log('⚠️ [Test] 未找到空调设备，跳过测试');
      return;
    }

    const actualGroupId = acDevice.group || acDevice.gid || acDevice.groupId || 'default';
    console.log(`📱 [Test] 使用设备分组ID: ${actualGroupId}`);

    // 创建一个测试场景，使用唯一名称和正确的分组ID
    const uniqueName = `测试场景替换_${Date.now()}`;
    const testSceneData = {
      scene_name: uniqueName,
      description: '用于测试动作替换功能',
      gid: actualGroupId,
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
      },
      {
        did: acDevice.did,
        operation: 'mode',
        value: 'cool'
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
    console.log('🔍 [Test] 第一次更新后场景详情:', JSON.stringify(sceneAfterFirst, null, 2));
    if (sceneAfterFirst && sceneAfterFirst.actions) {
      console.log(`📊 [Test] 第一次更新后动作数量: ${sceneAfterFirst.actions.length}`);
      sceneAfterFirst.actions.forEach((action, index) => {
        console.log(`   🎯 动作${index + 1}: ${action.operation}=${action.value}`);
      });
    } else {
      console.log('⚠️ [Test] 无法获取场景动作信息');
      console.log('🔍 [Test] 场景对象结构:', Object.keys(sceneAfterFirst || {}));
    }

    // 第二次更新：完全替换动作（模拟删除一些动作）
    const replacedActions = [
      {
        did: acDevice.did,
        operation: 'power',
        value: 'ON'
      }
      // 注意：这里删除了温度设置和模式设置动作
    ];

    console.log('🎬 [Test] 第二次更新：替换动作（删除温度和模式设置）');
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
      const hasModeAction = sceneAfterSecond.actions.some(action => action.operation === 'mode');

      console.log(`🔍 [Test] 温度动作是否被删除: ${hasTemperatureAction ? '否（删除失败）' : '是（删除成功）'}`);
      console.log(`🔍 [Test] 模式动作是否被删除: ${hasModeAction ? '否（删除失败）' : '是（删除成功）'}`);

      if (!hasTemperatureAction && !hasModeAction) {
        console.log('✅ [Test] 动作删除功能正常！');
      } else {
        console.log('❌ [Test] 动作删除功能有问题！');
      }
    }

    // 第三次更新：测试空动作列表（删除所有动作）
    console.log('🎬 [Test] 第三次更新：删除所有动作');
    const thirdUpdate = await this.sceneManager.updateScene(sceneId, {
      replaceActions: []
    });
    console.log(`🔍 [Test] 第三次更新: ${thirdUpdate.success ? '成功' : '失败'} - ${thirdUpdate.message}`);

    if (thirdUpdate.success) {
      const sceneAfterThird = this.sceneManager.getSceneDetail(sceneId);
      if (sceneAfterThird && sceneAfterThird.actions) {
        console.log(`📊 [Test] 第三次更新后动作数量: ${sceneAfterThird.actions.length}`);
        if (sceneAfterThird.actions.length === 0) {
          console.log('✅ [Test] 清空动作功能正常！');
        } else {
          console.log('❌ [Test] 清空动作功能有问题！');
        }
      }
    }

    console.log('✅ [Test] 场景动作替换测试完成\n');
  }
}

// 运行测试
const tester = new TestSceneReplacement();
tester.runTests().catch(console.error);

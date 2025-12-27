/**
 * 账号中心功能测试脚本
 * 用于验证用户信息获取和品牌绑定状态的功能是否正常
 */

const AccountManager = require('./modules/account/AccountManager');
const UserAccount = require('./domain/account/UserAccount');

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

global.electron = mockElectron;

async function testAccountCenter() {
  console.log('🧪 开始账号中心功能测试...');

  // 1. 初始化AccountManager
  const accountManager = new AccountManager();
  await accountManager.initialize();

  console.log('✅ AccountManager初始化完成');

  // 2. 模拟admin用户登录
  console.log('🔧 模拟admin用户登录...');
  const adminUser = new UserAccount('admin');
  accountManager.currentUser = adminUser;

  // 3. 测试获取当前用户信息
  console.log('🔍 测试获取当前用户信息...');
  const currentUser = accountManager.getCurrentUser();
  if (currentUser) {
    console.log('✅ 用户信息:', {
      userId: currentUser.getUserId(),
      isLoggedIn: accountManager.isLoggedIn()
    });
  } else {
    console.log('❌ 无法获取当前用户信息');
  }

  // 4. 测试加载绑定状态
  console.log('🔍 测试加载品牌绑定状态...');
  const bindingsResult = await accountManager.loadUserBindings();
  console.log('绑定状态结果:', bindingsResult);

  if (bindingsResult.success) {
    console.log('✅ 绑定状态加载成功');

    // 转换为前端需要的格式
    const frontendBindings = {};
    if (bindingsResult.bindings) {
      Object.keys(bindingsResult.bindings).forEach(brand => {
        const brandInfo = bindingsResult.bindings[brand];
        frontendBindings[brand] = brandInfo.isBound && !brandInfo.isExpired;
      });
    }

    console.log('前端格式的绑定状态:', frontendBindings);
  } else {
    console.log('❌ 绑定状态加载失败:', bindingsResult.message);
  }

  // 5. 测试解绑操作
  console.log('🔧 测试解绑小米品牌...');
  const unbindResult = await accountManager.unbindThirdPartyBrand('xiaomi');
  console.log('解绑结果:', unbindResult);

  // 6. 再次检查绑定状态
  console.log('🔍 解绑后重新检查绑定状态...');
  const updatedBindingsResult = await accountManager.loadUserBindings();
  if (updatedBindingsResult.success) {
    const updatedFrontendBindings = {};
    if (updatedBindingsResult.bindings) {
      Object.keys(updatedBindingsResult.bindings).forEach(brand => {
        const brandInfo = updatedBindingsResult.bindings[brand];
        updatedFrontendBindings[brand] = brandInfo.isBound && !brandInfo.isExpired;
      });
    }
    console.log('更新后的绑定状态:', updatedFrontendBindings);
  }

  // 7. 测试重新绑定
  console.log('🔧 测试重新绑定小米品牌...');
  const rebindResult = await accountManager.bindThirdPartyBrand('xiaomi', 'debug-auth-xiaomi-123');
  console.log('重新绑定结果:', rebindResult);

  // 8. 最终检查绑定状态
  console.log('🔍 重新绑定后的最终状态...');
  const finalBindingsResult = await accountManager.loadUserBindings();
  if (finalBindingsResult.success) {
    const finalFrontendBindings = {};
    if (finalBindingsResult.bindings) {
      Object.keys(finalBindingsResult.bindings).forEach(brand => {
        const brandInfo = finalBindingsResult.bindings[brand];
        finalFrontendBindings[brand] = brandInfo.isBound && !brandInfo.isExpired;
      });
    }
    console.log('最终绑定状态:', finalFrontendBindings);
  }

  console.log('🧪 账号中心功能测试完成');

  return {
    userInfo: currentUser ? {
      userId: currentUser.getUserId(),
      isLoggedIn: accountManager.isLoggedIn()
    } : null,
    bindings: finalBindingsResult.success ? finalBindingsResult.bindings : {},
    testPassed: true
  };
}

// 如果直接运行这个文件，执行测试
if (require.main === module) {
  testAccountCenter().then(result => {
    console.log('✅ 测试完成:', result);
    process.exit(0);
  }).catch(error => {
    console.error('❌ 测试异常:', error);
    process.exit(1);
  });
}

module.exports = testAccountCenter;

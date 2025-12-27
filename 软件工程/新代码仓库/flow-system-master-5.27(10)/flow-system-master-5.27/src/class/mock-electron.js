const path = require('path');

// 模拟Electron的app对象
const mockApp = {
  getPath: (name) => {
    switch (name) {
      case 'userData':
        return path.join(__dirname, '../data/test');
      case 'documents':
        return path.join(__dirname, '../data/test/documents');
      case 'temp':
        return path.join(__dirname, '../data/test/temp');
      default:
        return path.join(__dirname, '../data/test');
    }
  },
  isReady: () => true,
  whenReady: () => Promise.resolve(),
  quit: () => {},
  on: () => {},
  once: () => {}
};

// IPC处理器注册表
const ipcHandlers = new Map();

// 模拟IPC Main的handle方法
const mockIpcMain = {
  handle: (channel, handler) => {
    ipcHandlers.set(channel, handler);
    console.log(`📡 [Mock IPC] Registered handler for: ${channel}`);
  },

  removeHandler: (channel) => {
    ipcHandlers.delete(channel);
    console.log(`📡 [Mock IPC] Removed handler for: ${channel}`);
  }
};

// 模拟IPC调用函数
async function mockIpcInvoke(channel, ...args) {
  console.log(`📡 [Mock IPC] Invoking: ${channel}`, args.length > 0 ? args : '');

  if (!ipcHandlers.has(channel)) {
    console.error(`❌ [Mock IPC] No handler registered for: ${channel}`);
    throw new Error(`No handler registered for channel: ${channel}`);
  }

  const handler = ipcHandlers.get(channel);

  try {
    // 创建模拟的event对象
    const mockEvent = {
      reply: () => {},
      sender: {
        send: () => {}
      }
    };

    const result = await handler(mockEvent, ...args);
    console.log(`✅ [Mock IPC] Handler for ${channel} returned:`, result);
    return result;
  } catch (error) {
    console.error(`❌ [Mock IPC] Handler for ${channel} failed:`, error);
    throw error;
  }
}

// 初始化函数，用于设置所有IPC处理器
async function initializeMockIPC() {
  console.log('🔧 [Mock IPC] Initializing IPC handlers...');

  try {
    // 先设置全局模拟，确保在require任何模块之前就设置好
    global.electron = {
      app: mockApp,
      ipcMain: mockIpcMain
    };

    // 模拟main process的一些全局变量
    if (!global.mainWindow) {
      global.mainWindow = {
        webContents: {
          send: () => {}
        }
      };
    }

    // 注册必要的处理器
    await registerEssentialHandlers();

    console.log('✅ [Mock IPC] IPC handlers initialized');
  } catch (error) {
    console.error('❌ [Mock IPC] Failed to initialize:', error);
    throw error;
  }
}

// 注册基本的IPC处理器
async function registerEssentialHandlers() {
  // 首先初始化核心模块
  const AccountManager = require('./modules/account/AccountManager');

  // 创建模拟的账户管理器实例
  const mockAccountManager = new AccountManager();
  await mockAccountManager.initializeForAdmin();

  // 将其设置为全局可访问
  global.testAccountManager = mockAccountManager;

  // 注册get-all-groups处理器
  mockIpcMain.handle('get-all-groups', async (event) => {
    console.log('🔍 [Mock IPC] Handling: get-all-groups');
    try {
      const managers = mockAccountManager.getDeviceManagers();
      managers.groupAPIManager.refreshGroupStats();
      const groups = managers.groupAPIManager.getAllGroups();
      return { success: true, data: groups };
    } catch (error) {
      console.error('❌ [Mock IPC] get-all-groups failed:', error);
      return { success: false, message: error.message };
    }
  });

  // 注册refresh-group-stats处理器
  mockIpcMain.handle('refresh-group-stats', async (event) => {
    console.log('🔍 [Mock IPC] Handling: refresh-group-stats');
    try {
      const managers = mockAccountManager.getDeviceManagers();
      managers.groupAPIManager.refreshGroupStats();
      const groups = managers.groupAPIManager.getAllGroups();
      return { success: true, data: groups, message: '分组统计信息已刷新' };
    } catch (error) {
      console.error('❌ [Mock IPC] refresh-group-stats failed:', error);
      return { success: false, message: error.message };
    }
  });

  // 注册force-reinitialize-groups处理器
  mockIpcMain.handle('force-reinitialize-groups', async (event) => {
    console.log('🔍 [Mock IPC] Handling: force-reinitialize-groups');
    try {
      const managers = mockAccountManager.getDeviceManagers();

      await managers.groupAPIManager.fetchDeviceListWithStatus();
      await managers.groupAPIManager.assignUngroupedDevices();
      managers.groupAPIManager.refreshGroupStats();

      const groups = managers.groupAPIManager.getAllGroups();
      return {
        success: true,
        data: groups,
        message: '分组和设备数据已重新初始化'
      };
    } catch (error) {
      console.error('❌ [Mock IPC] force-reinitialize-groups failed:', error);
      return { success: false, message: error.message };
    }
  });

  // 注册analyze-group-sensor-data处理器
  mockIpcMain.handle('analyze-group-sensor-data', async (event, groupId) => {
    console.log('🔍 [Mock IPC] Handling: analyze-group-sensor-data, groupId:', groupId);
    try {
      const managers = mockAccountManager.getDeviceManagers();

      if (!managers.dataAnalyzer) {
        return {
          success: false,
          message: '数据分析器未初始化'
        };
      }

      const result = await managers.dataAnalyzer.analyzeGroupSensorData(groupId);
      return result;
    } catch (error) {
      console.error('❌ [Mock IPC] analyze-group-sensor-data failed:', error);
      return { success: false, message: error.message };
    }
  });

  console.log('✅ [Mock IPC] Essential handlers registered');
}

module.exports = {
  app: mockApp,
  ipcMain: mockIpcMain,
  mockIpcInvoke,
  initializeMockIPC,
  registerEssentialHandlers
};

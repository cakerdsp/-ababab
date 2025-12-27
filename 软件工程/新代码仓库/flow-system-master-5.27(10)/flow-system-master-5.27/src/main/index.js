import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// 引入模拟设备生成器
const MockDeviceGenerator = require('../class/modules/device/MockDeviceGenerator')

// 设置控制台编码为UTF-8，解决中文乱码问题
if (process.platform === 'win32') {
  try {
    // 设置进程编码
    process.stdout.setEncoding('utf8');
    process.stderr.setEncoding('utf8');

    // 设置环境变量强制UTF-8编码
    process.env.PYTHONIOENCODING = 'utf-8';
    process.env.LANG = 'zh_CN.UTF-8';
    process.env.LC_ALL = 'zh_CN.UTF-8';

    // 在Windows上设置代码页为UTF-8
    const { execSync } = require('child_process');
    execSync('chcp 65001', { stdio: 'ignore' });

    // 重写console方法以确保UTF-8输出（仅处理字符串参数）
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    const fixEncoding = (str) => {
      if (typeof str !== 'string') return str;
      try {
        // 尝试检测和修复中文编码问题
        if (/[\u4e00-\u9fff]/.test(str)) {
          return str;
        }
        return str;
      } catch (e) {
        return str;
      }
    };

    console.log = (...args) => {
      const processedArgs = args.map(arg =>
        typeof arg === 'string' ? fixEncoding(arg) : arg
      );
      originalLog.apply(console, processedArgs);
    };

    console.error = (...args) => {
      const processedArgs = args.map(arg =>
        typeof arg === 'string' ? fixEncoding(arg) : arg
      );
      originalError.apply(console, processedArgs);
    };

    console.warn = (...args) => {
      const processedArgs = args.map(arg =>
        typeof arg === 'string' ? fixEncoding(arg) : arg
      );
      originalWarn.apply(console, processedArgs);
    };

    console.log('✅ Console UTF-8 encoding configured');
  } catch (error) {
    console.log('⚠️ Failed to set UTF-8 encoding, which may affect Chinese display:', error.message);
  }
}

const login_width = 800;
const register_height = 900;

// 模拟设备生成函数
async function generateMockDevicesForAdmin(managers, defaultGroupId) {
  try {
    console.log('🤖 [Mock Device] 开始为admin账户生成模拟设备...');
    console.log('🤖 [Mock Device] 默认分组ID:', defaultGroupId);

    // 检查是否已经存在设备数据
    const existingDevices = managers.storageManager.getAllDevices();
    if (existingDevices.length > 0) {
      console.log('🤖 [Mock Device] 发现已存在设备数据，跳过生成');
      console.log('🤖 [Mock Device] 现有设备数量:', existingDevices.length);
      return;
    }

    // 创建模拟设备生成器
    const mockGenerator = new MockDeviceGenerator();

    // 生成模拟设备列表（生成9个设备，与JSON文件中的数量一致）
    const mockDevices = mockGenerator.generateDeviceList(defaultGroupId, 9);

    // 存储设备数据
    const storeResult = managers.storageManager.storeAllDevices(mockDevices);

    if (storeResult.success) {
      console.log('✅ [Mock Device] 模拟设备数据生成并存储成功');
      console.log('✅ [Mock Device] 设备数量:', mockDevices.length);

      // 输出设备列表详情
      mockDevices.forEach(device => {
        console.log(`   - ${device.name} (${device.type}) - ${device.online ? '在线' : '离线'}`);
      });

      // 更新分组统计
      if (managers.groupAPIManager) {
        managers.groupAPIManager.updateDefaultGroupStats();
        console.log('✅ [Mock Device] 默认分组统计信息已更新');

        // 为传感器设备生成模拟历史数据
        console.log('🔍 [Mock Device] 开始生成传感器历史数据...');
        managers.groupAPIManager.generateMockHistoryForAllSensors();
        console.log('✅ [Mock Device] 传感器历史数据生成完成');

        // 输出历史数据统计
        const historyStats = managers.groupAPIManager.getSensorHistoryStats();
        console.log('📊 [Mock Device] 传感器历史数据统计:', historyStats);
      }
    } else {
      console.error('❌ [Mock Device] 模拟设备数据存储失败:', storeResult.message);
    }
  } catch (error) {
    console.error('❌ [Mock Device] 生成模拟设备数据失败:', error);
  }
}

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    icon: icon,
    width: login_width,
    height: register_height,
    show: false,
    transparent: true,
    autoHideMenuBar: true,
    titleBarStyle: 'hidden',
    resizable: false,
    frame: true,
    mediaAccess: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: false,
      webSecurity: false,
    }
  })

  ipcMain.on('toMain', (event, args) => {
    try {
      // 参数验证
      if (!args || typeof args !== 'object') {
        console.error('toMain: Invalid arguments', args)
        return
      }

      // 默认屏幕尺寸
      const screenWidth = Number(args.screenWidth) || 1200
      const screenHeight = Number(args.screenHeight) || 800

      console.log('Adjusting window size:', { screenWidth, screenHeight })

      // 计算窗口尺寸
      const windowWidth = Math.floor((screenWidth / 5) * 3) + 250
      const windowHeight = 800
      const maxWindowWidth = Math.floor((screenWidth / 5) * 3) + 300
      const maxWindowHeight = 900

      mainWindow.setResizable(true)
      mainWindow.setSize(windowWidth, windowHeight)
      mainWindow.setMinimumSize(windowWidth, windowHeight)
      mainWindow.center()
      mainWindow.setMaximizable(true)
      mainWindow.setMaximumSize(maxWindowWidth, maxWindowHeight)

      console.log('Window size adjustment complete')
    } catch (error) {
      console.error('Adjusting window size failed:', error)
    }
  })

  ipcMain.on('minimizing', (event, args) => {
    event.preventDefault(); // 阻止默认最小化行为
    mainWindow.minimize(); // 最小化到任务栏
  })

  ipcMain.on('expandWindow', (event, args) => {
    let defaultSize = mainWindow.getSize();
    let maxSize = mainWindow.getMaximumSize();
    if (defaultSize[0] === (((args.screenWidth / 5) * 3) + 250) && defaultSize[1] === 800) {
      mainWindow.setResizable(true)
      mainWindow.setSize(((args.screenWidth / 5) * 3) + 300, 900)
    } else if (maxSize[0] === (((args.screenWidth / 5) * 3) + 300) && maxSize[1] === 900) {
      mainWindow.setResizable(true)
      mainWindow.setSize(((args.screenWidth / 5) * 3) + 250, 800)
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    // 窗口调试
    mainWindow.webContents.openDevTools()
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// 检查自动登录 - 按照原始流程文档
ipcMain.handle('check-auto-login', async (event) => {
  console.log('Login page requests auto-login check')
  const { accountManager, deviceController } = require('../class');
  const result = await accountManager.initialize();

  if (result.success && result.autoLogin) {
    const currentUser = accountManager.getCurrentUser();
    const token = accountManager.dataStorage.getToken();
    const sseConnectionId = accountManager.dataStorage.getSseConnectionId();
    const userId = currentUser?.getUserId();

    // 检查是否为admin账户 - 完全跳过SSE连接
    if (userId === 'admin') {
      console.log('🟡 [Offline Debug] Admin account detected for auto-login, enabling offline debug mode');
      console.log('🟡 [Offline Debug] Skipping SSE connection and device controller initialization entirely');

                // 启用分组管理器的离线模式
          try {
            const managers = accountManager.getDeviceManagers();
            if (managers && managers.groupAPIManager) {
              managers.groupAPIManager.enableOfflineMode();
              console.log('🟡 [Offline Debug] Group manager offline mode enabled');

              // 确保默认分组存在（离线模式）
              let defaultGroupId = null;
              try {
                console.log('🔍 [Offline Debug] Checking for default group...');
                const groups = managers.groupAPIManager.getAllGroups();
                console.log('🔍 [Offline Debug] Current group list:', groups.map(g => ({ gid: g.gid, gname: g.gname })));

                let defaultGroup = groups.find(group => group.gname === '默认分组');

                if (!defaultGroup) {
                  console.log('🔍 [Offline Debug] Creating default group...');
                  const groupResult = await managers.groupAPIManager.createGroup('默认分组');
                  console.log('✅ [Offline Debug] Default group creation result:', groupResult);
                  defaultGroup = groupResult.data;
                } else {
                  console.log('✅ [Offline Debug] Default group already exists, skipping creation');
                }

                defaultGroupId = defaultGroup?.gid || defaultGroup?.groupId;
                console.log('🔍 [Offline Debug] Default group ID:', defaultGroupId);

                // 生成模拟设备数据
                if (defaultGroupId) {
                  await generateMockDevicesForAdmin(managers, defaultGroupId);
                }

                // 刷新分组统计信息
                console.log('🔍 [Offline Debug] Refreshing group statistics...');
                managers.groupAPIManager.refreshGroupStats();
              } catch (groupError) {
                console.warn('❌ [Offline Debug] Failed to create default group:', groupError);
              }
            }
          } catch (error) {
            console.warn('❌ [Offline Debug] Group manager initialization failed:', error);
          }

      console.log('✅ [Offline Debug] Admin account auto-login complete, no SSE connection required');
    } else {
      // 非admin账户的正常SSE连接流程
      if (sseConnectionId) {
        try {
          console.log('🔧 [Debug] Attempting to initialize device controller...');
          await deviceController.initialize(sseConnectionId);
          console.log('✅ [Debug] Device controller auto-initialization successful');

          // 确保默认分组存在
          try {
            console.log('🔍 [Debug] Checking for default group after auto-login...');
            const managers = accountManager.getDeviceManagers();
            const groups = managers.groupAPIManager.getAllGroups();
            console.log('🔍 [Debug] Current group list:', groups.map(g => ({ gid: g.gid, gname: g.gname })));

            const hasDefaultGroup = groups.some(group => group.gname === '默认分组');
            console.log('🔍 [Debug] Default group exists:', hasDefaultGroup);

            if (!hasDefaultGroup) {
              console.log('🔍 [Debug] Creating default group...');
              const groupResult = await managers.groupAPIManager.createGroup('默认分组');
              console.log('✅ [Debug] Default group creation result:', groupResult);
            } else {
              console.log('✅ [Debug] Default group already exists, skipping creation');
            }

            // 刷新分组统计信息
            console.log('🔍 [Debug] Refreshing group statistics...');
            managers.groupAPIManager.refreshGroupStats();
          } catch (error) {
            console.warn('❌ [Debug] Failed to create default group:', error);
          }
        } catch (error) {
          console.warn('❌ [Debug] Device controller auto-initialization failed:', error);
          console.error('❌ [Debug] SSE connection failed, please check network connection');
        }
      } else {
        console.log('🟡 [Debug] No SSE connection ID, skipping device controller initialization');
      }
    }

    return {
      success: true,
      autoLogin: true,
      user: {
        userId: currentUser?.getUserId()
      },
      token: token,
      sseConnectionId: sseConnectionId
    };
  }

  return { success: false, autoLogin: false };
});

// 登录 - 按照原始流程文档
ipcMain.handle('login', async (event, loginData) => {
  try {
    const { userId, password, rememberMe } = loginData;
    console.log('🔧 [Debug] Login request:', userId, password ? '***' : 'no_password', rememberMe);
    const { accountManager, deviceController } = require('../class');
    const result = await accountManager.login(userId, password, rememberMe);

    if (result.success) {
      // 检查是否为admin账户 - 完全跳过SSE连接
      if (userId === 'admin') {
        console.log('🟡 [Offline Debug] Admin account detected, enabling offline debug mode');
        console.log('🟡 [Offline Debug] Skipping SSE connection and device controller initialization entirely');

        result.offlineDebugMode = true;

        // 启用分组管理器的离线模式
        try {
          const managers = accountManager.getDeviceManagers();
          if (managers && managers.groupAPIManager) {
            managers.groupAPIManager.enableOfflineMode();
            console.log('🟡 [Offline Debug] Group manager offline mode enabled');

            // 确保默认分组存在（离线模式）
            let defaultGroupId = null;
            try {
              console.log('🔍 [Offline Debug] Checking for default group...');
              const groups = managers.groupAPIManager.getAllGroups();
              console.log('🔍 [Offline Debug] Current group list:', groups.map(g => ({ gid: g.gid, gname: g.gname })));

              let defaultGroup = groups.find(group => group.gname === '默认分组');

              if (!defaultGroup) {
                console.log('🔍 [Offline Debug] Creating default group...');
                const groupResult = await managers.groupAPIManager.createGroup('默认分组');
                console.log('✅ [Offline Debug] Default group creation result:', groupResult);
                defaultGroup = groupResult.data;
              } else {
                console.log('✅ [Offline Debug] Default group already exists, skipping creation');
              }

              defaultGroupId = defaultGroup?.gid || defaultGroup?.groupId;
              console.log('🔍 [Offline Debug] Default group ID:', defaultGroupId);

                              // 生成模拟设备数据
                if (defaultGroupId) {
                  await generateMockDevicesForAdmin(managers, defaultGroupId);
                }

              // 刷新分组统计信息
              console.log('🔍 [Offline Debug] Refreshing group statistics...');
              managers.groupAPIManager.refreshGroupStats();
            } catch (groupError) {
              console.warn('❌ [Offline Debug] Failed to create default group:', groupError);
            }
          }
        } catch (error) {
          console.warn('❌ [Offline Debug] Group manager initialization failed:', error);
        }

        console.log('✅ [Offline Debug] Admin account login complete, no SSE connection required');
        return result;
      }

      // 非admin账户的正常流程
      try {
        console.log('🔧 [Debug] Attempting to initialize device controller, user ID:', userId);
        await deviceController.initialize(userId);
        console.log('✅ [Debug] Device controller initialization successful');
        result.deviceControllerInitialized = true;

        // 确保默认分组存在
        try {
          console.log('🔍 [Debug] Checking for default group after login...');
          const managers = accountManager.getDeviceManagers();
          const groups = managers.groupAPIManager.getAllGroups();
          console.log('🔍 [Debug] Current group list:', groups.map(g => ({ gid: g.gid, gname: g.gname })));

          const hasDefaultGroup = groups.some(group => group.gname === '默认分组');
          console.log('🔍 [Debug] Default group exists:', hasDefaultGroup);

          if (!hasDefaultGroup) {
            console.log('🔍 [Debug] Creating default group...');
            const groupResult = await managers.groupAPIManager.createGroup('默认分组');
            console.log('✅ [Debug] Default group creation result:', groupResult);
          } else {
            console.log('✅ [Debug] Default group already exists, skipping creation');
          }

          // 刷新分组统计信息
          console.log('🔍 [Debug] Refreshing group statistics...');
          managers.groupAPIManager.refreshGroupStats();
        } catch (error) {
          console.warn('❌ [Debug] Failed to create default group:', error);
        }
      } catch (error) {
        console.warn('❌ [Debug] Device controller initialization failed:', error);
        result.deviceControllerInitialized = false;
        result.message = 'Device controller initialization failed, please check network connection';
      }
    }

    return result;
  } catch (error) {
    console.error('❌ [Debug] Login processing failed:', error);
    return { success: false, message: error.message || 'Login processing failed' };
  }
});

// 注册
ipcMain.handle('register', async (event, registerData) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.register(registerData.userId, registerData.password);
    return result;
  } catch (error) {
    console.error('Registration processing failed:', error);
    return { success: false, message: error.message || 'Registration processing failed' };
  }
});

// 登出
ipcMain.handle('logout', async () => {
  try {
    console.log('🔥 [MAIN LOGOUT] ==========================================');
    console.log('🔥 [MAIN LOGOUT] Received logout request from frontend...');
    console.log('🔥 [MAIN LOGOUT] Current process ID:', process.pid);
    console.log('🔥 [MAIN LOGOUT] Current working directory:', process.cwd());
    console.log('🔥 [MAIN LOGOUT] ==========================================');

    const { accountManager, deviceController } = require('../class');
    console.log('🔥 [MAIN LOGOUT] Loaded managers - accountManager:', !!accountManager, 'deviceController:', !!deviceController);

    try {
      console.log('🔥 [MAIN LOGOUT] Step 1: Cleaning up device controller...');
      await deviceController.logout();
      console.log('🔥 [MAIN LOGOUT] ✅ Device controller resources cleaned up successfully');
    } catch (error) {
      console.warn('🔥 [MAIN LOGOUT] ⚠️ Device controller resources cleanup failed:', error);
    }

    console.log('🔥 [MAIN LOGOUT] Step 2: Calling account manager logout...');
    const result = await accountManager.logout();
    console.log('🔥 [MAIN LOGOUT] Account manager logout result:', result);

    console.log('🔥 [MAIN LOGOUT] ==========================================');
    console.log('🔥 [MAIN LOGOUT] Logout process completed successfully');
    console.log('🔥 [MAIN LOGOUT] Final result:', result);
    console.log('🔥 [MAIN LOGOUT] ==========================================');

    return result;
  } catch (error) {
    console.error('🔥 [MAIN LOGOUT] ❌ Logout processing failed:', error);
    console.error('🔥 [MAIN LOGOUT] Error stack:', error.stack);
    return { success: false, message: error.message || 'Logout processing failed', stack: error.stack };
  }
});

// 强制清理所有本地数据（仅用于调试）
ipcMain.handle('force-cleanup-storage', async () => {
  try {
    console.log('🗑️ [IPC] Processing force cleanup storage request...');

    const { accountManager } = require('../class');
    const result = accountManager.forceCompleteCleanup();

    console.log('🗑️ [IPC] Force cleanup result:', result);
    return result;
  } catch (error) {
    console.error('🗑️ [IPC] Force cleanup failed:', error);
    return { success: false, message: error.message || 'Force cleanup failed' };
  }
});

// 获取存储状态（用于调试）
ipcMain.handle('get-storage-status', async () => {
  try {
    console.log('📊 [IPC] Getting storage status...');

    const { accountManager } = require('../class');
    const result = accountManager.getStorageStatus();

    console.log('📊 [IPC] Storage status:', result);
    return result;
  } catch (error) {
    console.error('📊 [IPC] Get storage status failed:', error);
    return { success: false, message: error.message || 'Get storage status failed' };
  }
});

// 第三方账号绑定
ipcMain.handle('bind-third-party', async (event, brandName, authCode) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.bindThirdPartyBrand(brandName, authCode);

    // 如果绑定成功，立即刷新绑定状态以确保前端数据一致性
    if (result.success) {
      console.log(`✅ [Debug] ${brandName} bind successful, refreshing binding status...`);

      // 重新加载绑定状态以确保数据一致性
      const refreshResult = await accountManager.loadUserBindings();
      if (refreshResult.success) {
        console.log('✅ [Debug] Binding status refreshed after bind');
      }
    }

    return result;
  } catch (error) {
    console.error('Third-party binding failed:', error);
    return { success: false, message: error.message || 'Third-party binding failed' };
  }
});

// 第三方账号解绑
ipcMain.handle('unbind-third-party', async (event, brandName) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.unbindThirdPartyBrand(brandName);

    // 如果解绑成功，立即刷新绑定状态以确保前端数据一致性
    if (result.success) {
      console.log(`✅ [Debug] ${brandName} unbind successful, refreshing binding status...`);

      // 重新加载绑定状态以确保数据一致性
      const refreshResult = await accountManager.loadUserBindings();
      if (refreshResult.success) {
        console.log('✅ [Debug] Binding status refreshed after unbind');
      }
    }

    return result;
  } catch (error) {
    console.error('Third-party unbinding failed:', error);
    return { success: false, message: error.message || 'Third-party unbinding failed' };
  }
});

// 获取已绑定的第三方账号
ipcMain.handle('get-bindings', async (event) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.loadUserBindings();

    if (result.success) {
      // 将绑定信息转换为前端需要的格式
      const bindings = {};

      if (result.bindings) {
        // 遍历所有支持的品牌
        Object.keys(result.bindings).forEach(brand => {
          const brandInfo = result.bindings[brand];
          // 只有当品牌已绑定且未过期时，才认为是绑定状态
          bindings[brand] = brandInfo.isBound && !brandInfo.isExpired;
        });
      }

      console.log('🔍 [Debug] Formatted bindings for frontend:', bindings);

      return { success: true, data: bindings };
    } else {
      return result;
    }
  } catch (error) {
    console.error('Getting bindings failed:', error);
    return { success: false, message: error.message || 'Getting bindings failed' };
  }
});

// 获取当前用户信息
ipcMain.handle('get-current-user', async (event) => {
  try {
    const { accountManager } = require('../class');
    const currentUser = accountManager.getCurrentUser();
    const isLoggedIn = accountManager.isLoggedIn();

    if (currentUser && isLoggedIn) {
      return {
        success: true,
        data: {
          userId: currentUser.getUserId(),
          isLoggedIn: true
        }
      };
    } else {
      return {
        success: true,
        data: {
          userId: '未登录',
          isLoggedIn: false
        }
      };
    }
  } catch (error) {
    console.error('Getting current user failed:', error);
    return {
      success: false,
      message: error.message || 'Getting current user failed',
      data: {
        userId: '未登录',
        isLoggedIn: false
      }
    };
  }
});

// 授权第三方品牌
ipcMain.handle('perform-third-party-authorization', async (event, brandName) => {
  try {
    const { accountManager } = require('../class');

    // 使用进度回调函数向渲染进程发送状态更新
    const progressCallback = (progress) => {
      event.sender.send('third-party-auth-progress', progress);
    };

    const result = await accountManager.performThirdPartyAuthorization(brandName, progressCallback);
    return result;
  } catch (error) {
    console.error('Third-party authorization failed:', error);
    return { success: false, message: error.message || 'Third-party authorization failed' };
  }
});

// 获取授权码
ipcMain.handle('get-authorization-code', async (event, userId, brandName) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.getAuthorizationCode(userId, brandName);
    return result;
  } catch (error) {
    console.error('Getting authorization code failed:', error);
    return { success: false, message: error.message || 'Getting authorization code failed' };
  }
});

// 使用授权码绑定
ipcMain.handle('bind-with-authorization-code', async (event, authCode, brandName) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.bindWithAuthorizationCode(authCode, brandName);

    // 如果绑定成功，立即刷新绑定状态以确保前端数据一致性
    if (result.success) {
      console.log(`✅ [Debug] ${brandName} bind with auth code successful, refreshing binding status...`);

      // 重新加载绑定状态以确保数据一致性
      const refreshResult = await accountManager.loadUserBindings();
      if (refreshResult.success) {
        console.log('✅ [Debug] Binding status refreshed after auth code bind');
      }
    }

    return result;
  } catch (error) {
    console.error('Binding with authorization code failed:', error);
    return { success: false, message: error.message || 'Binding with authorization code failed' };
  }
});

// 刷新token
ipcMain.handle('refresh-token', async () => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.refreshAccessToken();
    return result;
  } catch (error) {
    console.error('Refreshing token failed:', error);
    return { success: false, message: error.message || 'Refreshing token failed' };
  }
});

// 获取API baseURL
ipcMain.handle('get-api-base-url', async () => {
  try {
    const { accountManager } = require('../class');
    const baseURL = accountManager.apiRegistry.getBaseURL();
    return { success: true, baseURL: baseURL };
  } catch (error) {
    console.error('Getting API base URL failed:', error);
    return { success: false, message: error.message || 'Getting API base URL failed' };
  }
});

// ==================== 设备相关IPC处理器 ====================

// 获取所有设备
ipcMain.handle('get-all-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const devices = managers.storageManager.getAllDevices();
    return { success: true, data: devices };
  } catch (error) {
    console.error('Getting device list failed:', error);
    return { success: false, message: error.message || 'Getting device list failed' };
  }
});

// 根据品牌获取设备
ipcMain.handle('get-devices-by-brand', async (event, brand) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const devices = managers.storageManager.getDevicesByBrand(brand);
    return { success: true, data: devices };
  } catch (error) {
    console.error('Getting brand devices failed:', error);
    return { success: false, message: error.message || 'Getting brand devices failed' };
  }
});

// 根据分组获取设备
ipcMain.handle('get-devices-by-group', async (event, groupId) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const devices = managers.storageManager.getDevicesByGroup(groupId);
    return { success: true, data: devices };
  } catch (error) {
    console.error('Getting group devices failed:', error);
    return { success: false, message: error.message || 'Getting group devices failed' };
  }
});

// 获取可控制设备 (增强版本)
ipcMain.handle('get-controllable-devices', async (event) => {
  console.log('🎮 [IPC] Received get controllable devices request');

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const controlManager = managers.controlManager;

    if (!controlManager) {
      console.error('❌ [IPC] Control manager not available');
      return { success: false, message: '设备控制管理器未初始化' };
    }

    // 使用控制管理器获取可控制设备
    const controllableDevices = controlManager.getControllableDevices();

    console.log(`✅ [IPC] Found ${controllableDevices.length} controllable devices`);
    return { success: true, data: controllableDevices };

  } catch (error) {
    console.error('❌ [IPC] Getting controllable devices failed:', error);
    return { success: false, message: error.message || '获取可控制设备失败' };
  }
});

// 验证设备控制命令
ipcMain.handle('validate-device-control', async (event, validationData) => {
  console.log('🔧 [IPC] Received validate device control request:', validationData);

  try {
    const { did, operation, value } = validationData;
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const controlManager = managers.controlManager;

    if (!controlManager) {
      return { success: false, message: '设备控制管理器未初始化' };
    }

    // 获取设备信息
    const device = managers.storageManager.getDevice(did);
    if (!device) {
      return { valid: false, message: '设备不存在' };
    }

    // 验证控制命令
    const validation = controlManager.validateControlCommand(device, operation, value);
    console.log('🔧 [IPC] Validation result:', validation);

    return validation;

  } catch (error) {
    console.error('❌ [IPC] Control validation failed:', error);
    return { valid: false, message: error.message || '命令验证失败' };
  }
});

// 获取传感器设备
ipcMain.handle('get-sensor-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const allDevices = managers.storageManager.getAllDevices();
    const sensorDevices = allDevices.filter(device =>
      device.type === 'mi_temp_hum_sensor' ||
      device.type === 'mi_air_sensor' ||
      device.type === 'history'
    );
    return { success: true, data: sensorDevices };
  } catch (error) {
    console.error('Getting sensor devices failed:', error);
    return { success: false, message: error.message || 'Getting sensor devices failed' };
  }
});

// 获取设备控制选项 (增强版本)
ipcMain.handle('get-device-control-options', async (event, did) => {
  console.log('🎮 [IPC] Received get device control options request:', did);

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const controlManager = managers.controlManager;

    if (!controlManager) {
      console.error('❌ [IPC] Control manager not available');
      return { success: false, message: '设备控制管理器未初始化' };
    }

    // 使用控制管理器获取控制选项
    const options = controlManager.getDeviceControlOptions(did);

    if (!options) {
      console.log('❌ [IPC] Device not controllable or not found:', did);
      return { success: false, message: '设备不存在或不可控制' };
    }

    console.log('✅ [IPC] Control options retrieved:', options);
    return { success: true, data: options };

  } catch (error) {
    console.error('❌ [IPC] Getting device control options failed:', error);
    return { success: false, message: error.message || '获取设备控制选项失败' };
  }
});

// 控制设备 (增强版本)
ipcMain.handle('control-device', async (event, controlData) => {
  console.log('🎮 [IPC] Received device control request:', controlData);

  try {
    const { did, operation, value } = controlData;
    const { accountManager } = require('../class');

    // 获取设备控制管理器
    const managers = accountManager.getDeviceManagers();
    const controlManager = managers.controlManager;

    if (!controlManager) {
      console.error('❌ [IPC] Control manager not available');
      return { success: false, message: '设备控制管理器未初始化' };
    }

    // 使用控制管理器执行控制
    const controlResult = await controlManager.controlDevice(did, operation, value);
    console.log('🎮 [IPC] Control result:', controlResult);

    return controlResult;

  } catch (error) {
    console.error('❌ [IPC] Device control failed:', error);
    return { success: false, message: error.message || '设备控制失败' };
  }
});

// 刷新设备状态
ipcMain.handle('refresh-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const response = await accountManager.apiRegistry.callAPIGet('getDevicesStatus');
    if (response && response.code === 200 && response.data && response.data.devices) {
      const managers = accountManager.getDeviceManagers();
      const result = managers.storageManager.storeAllDevices(response.data.devices);
      return {
        success: result.success,
        message: result.message,
        deviceCount: response.data.devices.length
      };
    } else {
      return { success: false, message: 'Getting device data failed' };
    }
  } catch (error) {
    console.error('Refreshing device status failed:', error);
    return { success: false, message: error.message || 'Refreshing device status failed' };
  }
});

// 清理所有设备数据（仅用于admin调试）
ipcMain.handle('clear-all-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const currentUser = accountManager.getCurrentUser();

    // 仅允许admin用户清理数据
    if (currentUser?.getUserId() !== 'admin') {
      return { success: false, message: 'Only admin users can clear device data' };
    }

    console.log('🧹 [Admin Debug] Clearing all device data...');
    const managers = accountManager.getDeviceManagers();

    // 清除设备数据
    const result = managers.storageManager.clearAllDevices();

    // 清除传感器历史数据
    console.log('🧹 [Admin Debug] Clearing sensor history data...');
    managers.groupAPIManager.clearAllSensorHistory();
    console.log('✅ [Admin Debug] Sensor history data cleared');

    if (result.success) {
      console.log('✅ [Admin Debug] Device data cleared, regenerating mock devices...');

      // 重新生成模拟设备数据
      const groups = managers.groupAPIManager.getAllGroups();
      const defaultGroup = groups.find(g => g.gname === '默认分组');

      if (defaultGroup) {
        await generateMockDevicesForAdmin(managers, defaultGroup.gid);
        managers.groupAPIManager.refreshGroupStats();
        console.log('✅ [Admin Debug] Mock devices regenerated successfully');
      }

      return { success: true, message: 'Device data and sensor history cleared and regenerated successfully' };
    } else {
      return result;
    }
  } catch (error) {
    console.error('❌ [Admin Debug] Clear device data failed:', error);
    return { success: false, message: error.message || 'Clear device data failed' };
  }
});

// ==================== 分组管理相关IPC处理器 ====================

// 获取所有分组
ipcMain.handle('get-all-groups', async (event) => {
  console.log('🔍 [Debug] IPC call: get-all-groups');
  try {
    const { accountManager } = require('../class');
    console.log('🔍 [Debug] Successfully retrieved accountManager');

    const managers = accountManager.getDeviceManagers();
    console.log('🔍 [Debug] Successfully retrieved deviceManagers:', !!managers);
    console.log('🔍 [Debug] groupAPIManager exists:', !!managers.groupAPIManager);

    // 刷新分组统计信息以确保数据准确
    managers.groupAPIManager.refreshGroupStats();

    const groups = managers.groupAPIManager.getAllGroups();
    console.log('🔍 [Debug] Retrieved group data:', groups);
    console.log('🔍 [Debug] Number of groups:', Array.isArray(groups) ? groups.length : 'not an array');

    return { success: true, data: groups };
  } catch (error) {
    console.error('❌ [Debug] Getting group list failed:', error);
    console.error('❌ [Debug] Stack trace:', error.stack);
    return { success: false, message: error.message || 'Getting group list failed' };
  }
});

// 刷新分组统计信息
ipcMain.handle('refresh-group-stats', async (event) => {
  console.log('🔍 [Debug] IPC call: refresh-group-stats');
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // 刷新分组统计信息
    managers.groupAPIManager.refreshGroupStats();

    // 返回更新后的分组列表
    const groups = managers.groupAPIManager.getAllGroups();
    console.log('✅ [Debug] Group statistics refreshed, group count:', groups.length);

    return { success: true, data: groups, message: '分组统计信息已刷新' };
  } catch (error) {
    console.error('❌ [Debug] Refreshing group stats failed:', error);
    return { success: false, message: error.message || 'Refreshing group stats failed' };
  }
});

// 强制重新初始化分组和设备数据
ipcMain.handle('force-reinitialize-groups', async (event) => {
  console.log('🔄 [Debug] IPC call: force-reinitialize-groups');
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    console.log('🔄 [Debug] Re-fetching device list with status...');
    await managers.groupAPIManager.fetchDeviceListWithStatus();

    console.log('🔄 [Debug] Assigning ungrouped devices...');
    await managers.groupAPIManager.assignUngroupedDevices();

    console.log('🔄 [Debug] Refreshing group statistics...');
    managers.groupAPIManager.refreshGroupStats();

    // 返回更新后的分组列表
    const groups = managers.groupAPIManager.getAllGroups();
    console.log('✅ [Debug] Force reinitialization completed, group count:', groups.length);

    return {
      success: true,
      data: groups,
      message: '分组和设备数据已重新初始化'
    };
  } catch (error) {
    console.error('❌ [Debug] Force reinitializing groups failed:', error);
    return {
      success: false,
      message: error.message || 'Force reinitializing groups failed'
    };
  }
});

// 创建分组
ipcMain.handle('create-group', async (event, groupName) => {
  console.log('🔍 [Debug] IPC call: create-group, group name:', groupName);

  // 参数验证
  if (!groupName || typeof groupName !== 'string' || groupName.trim() === '') {
    console.log('❌ [Debug] Invalid group name:', groupName);
    throw new Error('Group name invalid');
  }

  try {
    const { accountManager } = require('../class');
    console.log('🔍 [Debug] Successfully retrieved accountManager');

    const managers = accountManager.getDeviceManagers();
    console.log('🔍 [Debug] Successfully retrieved deviceManagers');
    console.log('🔍 [Debug] groupAPIManager exists:', !!managers.groupAPIManager);

    console.log('🔍 [Debug] Calling createGroup method...');
    const result = await managers.groupAPIManager.createGroup(groupName.trim());
    console.log('✅ [Debug] Group created successfully:', result);

    return result;
  } catch (error) {
    console.error('❌ [Debug] Creating group failed:', error);
    console.error('❌ [Debug] Stack trace:', error.stack);
    return { success: false, message: error.message || 'Creating group failed' };
  }
});

// 删除分组
ipcMain.handle('delete-group', async (event, groupId) => {
  console.log('🔍 [Debug] IPC call: delete-group, group ID:', groupId);

  // 参数验证
  if (!groupId) {
    console.log('❌ [Debug] Invalid group ID:', groupId);
    throw new Error('Group ID invalid');
  }

  try {
    const { accountManager } = require('../class');
    console.log('🔍 [Debug] Successfully retrieved accountManager');

    const managers = accountManager.getDeviceManagers();
    console.log('🔍 [Debug] Successfully retrieved deviceManagers');
    console.log('🔍 [Debug] groupAPIManager exists:', !!managers.groupAPIManager);

    // 删除前先检查分组是否存在
    const groups = managers.groupAPIManager.getAllGroups();
    const targetGroup = groups.find(g => g.gid === groupId);
    console.log('🔍 [Debug] Group info to be deleted:', targetGroup);

    if (!targetGroup) {
      console.log('❌ [Debug] Group does not exist:', groupId);
      throw new Error('Group does not exist');
    }

    // 检查分组下的设备数量
    const devices = managers.storageManager.getAllDevices();
    const groupDevices = devices.filter(device => device.groupId === groupId);
    console.log('🔍 [Debug] Number of devices in group:', groupDevices.length);
    console.log('🔍 [Debug] Device list in group:', groupDevices.map(d => ({ did: d.did, name: d.name })));

    console.log('🔍 [Debug] Calling deleteGroup method...');
    const result = await managers.groupAPIManager.deleteGroup(groupId);
    console.log('✅ [Debug] Group deleted successfully:', result);

    return result;
  } catch (error) {
    console.error('❌ [Debug] Deleting group failed:', error);
    console.error('❌ [Debug] Stack trace:', error.stack);
    return { success: false, message: error.message || 'Deleting group failed' };
  }
});

// ==================== 设备分组移动相关IPC处理器 ====================

// 移动设备到指定分组
ipcMain.handle('move-device-to-group', async (event, deviceId, targetGroupId, targetGroupName) => {
  console.log('🔄 [Debug] IPC call: move-device-to-group');
  console.log('🔄 [Debug] Device ID:', deviceId);
  console.log('🔄 [Debug] Target Group ID:', targetGroupId);
  console.log('🔄 [Debug] Target Group Name:', targetGroupName);

  // 参数验证
  if (!deviceId || !targetGroupId) {
    console.log('❌ [Debug] Invalid parameters:', { deviceId, targetGroupId });
    return { success: false, message: '设备ID和目标分组ID不能为空' };
  }

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    console.log('🔄 [Debug] Calling moveDeviceToGroup...');
    const result = await managers.groupAPIManager.moveDeviceToGroup(deviceId, targetGroupId, targetGroupName);

    console.log('🔄 [Debug] Move result:', result);

    // 如果移动成功，刷新分组统计信息
    if (result.success) {
      console.log('🔄 [Debug] Refreshing group statistics...');
      managers.groupAPIManager.refreshGroupStats();
    }

    return result;
  } catch (error) {
    console.error('❌ [Debug] Moving device to group failed:', error);
    return { success: false, message: error.message || 'Moving device to group failed' };
  }
});

// 批量移动设备到分组
ipcMain.handle('batch-move-devices-to-group', async (event, deviceIds, targetGroupId) => {
  console.log('🔄 [Debug] IPC call: batch-move-devices-to-group');
  console.log('🔄 [Debug] Device IDs:', deviceIds);
  console.log('🔄 [Debug] Target Group ID:', targetGroupId);

  // 参数验证
  if (!Array.isArray(deviceIds) || deviceIds.length === 0 || !targetGroupId) {
    console.log('❌ [Debug] Invalid parameters');
    return { success: false, message: '设备ID列表和目标分组ID不能为空' };
  }

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    console.log('🔄 [Debug] Calling batchMoveDevicesToGroup...');
    const result = await managers.groupAPIManager.batchMoveDevicesToGroup(deviceIds, targetGroupId);

    console.log('🔄 [Debug] Batch move result:', result);

    // 刷新分组统计信息
    console.log('🔄 [Debug] Refreshing group statistics...');
    managers.groupAPIManager.refreshGroupStats();

    return result;
  } catch (error) {
    console.error('❌ [Debug] Batch moving devices to group failed:', error);
    return { success: false, message: error.message || 'Batch moving devices to group failed' };
  }
});

// 获取设备可移动的分组列表（排除当前分组）
ipcMain.handle('get-available-groups-for-device', async (event, deviceId) => {
  console.log('🔍 [Debug] IPC call: get-available-groups-for-device, device ID:', deviceId);

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // 获取设备信息
    const device = managers.storageManager.getDevice(deviceId);
    if (!device) {
      return { success: false, message: '设备不存在' };
    }

    // 获取所有分组
    const allGroups = managers.groupAPIManager.getAllGroups();
    const currentGroupId = device.groupId || device.group;

    // 过滤掉当前分组
    const availableGroups = allGroups.filter(group => group.gid !== currentGroupId);

    console.log('🔍 [Debug] Current group ID:', currentGroupId);
    console.log('🔍 [Debug] Available groups:', availableGroups.length);

    return {
      success: true,
      data: {
        device: {
          did: device.did,
          name: device.name,
          current_group_id: currentGroupId,
          current_group_name: allGroups.find(g => g.gid === currentGroupId)?.gname || '未分组'
        },
        available_groups: availableGroups.map(group => ({
          gid: group.gid,
          gname: group.gname,
          device_count: group.device_count || 0
        }))
      }
    };
  } catch (error) {
    console.error('❌ [Debug] Getting available groups for device failed:', error);
    return { success: false, message: error.message || 'Getting available groups for device failed' };
  }
});

// 验证分组名称是否存在
ipcMain.handle('validate-group-name', async (event, groupName) => {
  console.log('🔍 [Debug] IPC call: validate-group-name, group name:', groupName);

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!groupName || groupName.trim() === '') {
      return { success: false, message: '分组名称不能为空' };
    }

    const groups = managers.groupAPIManager.getAllGroups();
    const existingGroup = groups.find(g => g.gname === groupName.trim());

    if (existingGroup) {
      return {
        success: true,
        data: {
          exists: true,
          group: {
            gid: existingGroup.gid,
            gname: existingGroup.gname,
            device_count: existingGroup.device_count || 0
          }
        }
      };
    } else {
      return {
        success: true,
        data: {
          exists: false,
          message: '分组不存在'
        }
      };
    }
  } catch (error) {
    console.error('❌ [Debug] Validating group name failed:', error);
    return { success: false, message: error.message || 'Validating group name failed' };
  }
});

// 设置设备分组
ipcMain.handle('set-device-group', async (event, deviceId, groupId) => {
  console.log('🔍 [Debug] IPC call: set-device-group');
  console.log('🔍 [Debug] Device ID:', deviceId);
  console.log('🔍 [Debug] Target group ID:', groupId);

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // 验证设备是否存在
    const devices = managers.storageManager.getAllDevices();
    const device = devices.find(d => d.did === deviceId);
    console.log('🔍 [Debug] Device info:', device);

    if (!device) {
      console.log('❌ [Debug] Device does not exist:', deviceId);
      throw new Error('Device does not exist');
    }

    // 验证分组是否存在（如果groupId不为null）
    if (groupId) {
      const groups = managers.groupAPIManager.getAllGroups();
      const group = groups.find(g => g.gid === groupId);
      console.log('🔍 [Debug] Target group info:', group);

      if (!group) {
        console.log('❌ [Debug] Target group does not exist:', groupId);
        throw new Error('Target group does not exist');
      }
    }

    console.log('🔍 [Debug] Device current group:', device.groupId || 'No group');
    console.log('🔍 [Debug] Calling setDeviceGroup method...');

    const result = await managers.groupAPIManager.setDeviceGroup(deviceId, groupId);
    console.log('✅ [Debug] Device group set successfully:', result);

    return result;
  } catch (error) {
    console.error('❌ [Debug] Setting device group failed:', error);
    console.error('❌ [Debug] Stack trace:', error.stack);
    return { success: false, message: error.message || 'Setting device group failed' };
  }
});

// ==================== 传感器数据分析相关IPC处理器 ====================

// 分析分组传感器数据
ipcMain.handle('analyze-group-sensor-data', async (event, groupId) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const result = await managers.dataAnalyzer.analyzeGroupSensorData(groupId);
    return result;
  } catch (error) {
    console.error('Analyzing group sensor data failed:', error);
    return { success: false, message: error.message || 'Analyzing group sensor data failed' };
  }
});

// 分析多个分组数据（用于对比）
ipcMain.handle('analyze-multiple-groups', async (event, groupIds) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const result = await managers.dataAnalyzer.analyzeMultipleGroups(groupIds);
    return result;
  } catch (error) {
    console.error('Analyzing multiple groups failed:', error);
    return { success: false, message: error.message || 'Analyzing multiple groups failed' };
  }
});

// 获取支持的传感器类型
ipcMain.handle('get-supported-sensor-types', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const types = managers.dataAnalyzer.getSupportedSensorTypes();
    return { success: true, data: types };
  } catch (error) {
    console.error('Getting supported sensor types failed:', error);
    return { success: false, message: error.message || 'Getting supported sensor types failed' };
  }
});

// 导出分析结果
ipcMain.handle('export-analysis-result', async (event, analysisResult) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const exportData = managers.dataAnalyzer.exportAnalysisResult(analysisResult);
    return { success: true, data: exportData };
  } catch (error) {
    console.error('Exporting analysis result failed:', error);
    return { success: false, message: error.message || 'Exporting analysis result failed' };
  }
});


// 刷新所有数据
ipcMain.handle('refresh-all-data', async (event) => {
  try {
    const { accountManager } = require('../class');
    const response = await accountManager.apiRegistry.callAPIGet('getDevicesStatus');
    if (response && response.code === 200 && response.data && response.data.devices) {
      const managers = accountManager.getDeviceManagers();
      const result = managers.storageManager.storeAllDevices(response.data.devices);
      return {
        success: result.success,
        message: 'Data refresh completed',
        deviceCount: response.data.devices.length
      };
    } else {
      return { success: false, message: 'Getting device data failed' };
    }
  } catch (error) {
    console.error('Refreshing all data failed:', error);
    return { success: false, message: error.message || 'Refreshing all data failed' };
  }
});

// ==================== 系统状态相关IPC处理器 ====================

// 获取系统状态
ipcMain.handle('get-system-status', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const allDevices = managers.storageManager.getAllDevices();
    const stats = managers.storageManager.getDeviceStats();

    const status = {
      isInitialized: accountManager.isLoggedIn(),
      currentUserId: accountManager.getCurrentUser()?.getUserId(),
      deviceCount: allDevices.length,
      onlineDeviceCount: allDevices.filter(d => d.online).length,
      offlineDeviceCount: allDevices.filter(d => !d.online).length,
              sensorCount: allDevices.filter(d =>
          d.type === 'mi_temp_hum_sensor' ||
          d.type === 'mi_air_sensor' ||
          d.type === 'history'
        ).length,
      groupCount: managers.groupAPIManager.getAllGroups().length,
      sseStatus: managers.sseManager.getConnectionStatus(),
      stats: stats,
      lastUpdated: new Date().toISOString()
    };

    return { success: true, data: status };
  } catch (error) {
    console.error('Getting system status failed:', error);
    return { success: false, message: error.message || 'Getting system status failed' };
  }
});

// 重新连接SSE
ipcMain.handle('reconnect-sse', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const result = await managers.sseManager.reconnect();
    return result;
  } catch (error) {
    console.error('Reconnecting SSE failed:', error);
    return { success: false, message: error.message || 'Reconnecting SSE failed' };
  }
});

// ==================== 状态管理相关IPC处理器 ====================

// 获取当前状态
ipcMain.handle('get-current-state', async (event) => {
  try {
    const { stateManager } = require('../class');
    const state = stateManager.getCurrentState();
    return { success: true, data: state };
  } catch (error) {
    console.error('Getting current state failed:', error);
    return { success: false, message: error.message || 'Getting current state failed' };
  }
});

// 获取页面状态
ipcMain.handle('get-page-state', async (event, pageName) => {
  try {
    const { stateManager } = require('../class');
    const pageState = stateManager.getPageState(pageName);
    return { success: true, data: pageState };
  } catch (error) {
    console.error(`Getting page state failed (${pageName}):`, error);
    return { success: false, message: error.message || 'Getting page state failed' };
  }
});

// 保存页面状态
ipcMain.handle('save-page-state', async (event, pageName, pageState) => {
  try {
    const { stateManager } = require('../class');
    stateManager.updatePageState(pageName, pageState);
    return { success: true, message: 'Page state saved successfully' };
  } catch (error) {
    console.error(`Saving page state failed (${pageName}):`, error);
    return { success: false, message: error.message || 'Saving page state failed' };
  }
});

// 保存表单状态
ipcMain.handle('save-form-state', async (event, pageName, formName, formData) => {
  try {
    const { stateManager } = require('../class');
    stateManager.saveFormState(pageName, formName, formData);
    return { success: true, message: 'Form state saved successfully' };
  } catch (error) {
    console.error(`Saving form state failed (${pageName}/${formName}):`, error);
    return { success: false, message: error.message || 'Saving form state failed' };
  }
});

// 获取表单状态
ipcMain.handle('get-form-state', async (event, pageName, formName) => {
  try {
    const { stateManager } = require('../class');
    const formState = stateManager.getFormState(pageName, formName);
    return { success: true, data: formState };
  } catch (error) {
    console.error(`Getting form state failed (${pageName}/${formName}):`, error);
    return { success: false, message: error.message || 'Getting form state failed' };
  }
});

// 保存UI状态
ipcMain.handle('save-ui-state', async (event, pageName, uiState) => {
  try {
    const { stateManager } = require('../class');
    stateManager.saveUIState(pageName, uiState);
    return { success: true, message: 'UI state saved successfully' };
  } catch (error) {
    console.error(`Saving UI state failed (${pageName}):`, error);
    return { success: false, message: error.message || 'Saving UI state failed' };
  }
});

// 获取UI状态
ipcMain.handle('get-ui-state', async (event, pageName) => {
  try {
    const { stateManager } = require('../class');
    const uiState = stateManager.getUIState(pageName);
    return { success: true, data: uiState };
  } catch (error) {
    console.error(`Getting UI state failed (${pageName}):`, error);
    return { success: false, message: error.message || 'Getting UI state failed' };
  }
});

// 从存储同步状态
ipcMain.handle('sync-state-from-storage', async (event) => {
  try {
    const { stateManager } = require('../class');
    const result = stateManager.syncFromStorage();
    return { success: result, message: result ? 'State synchronization successful' : 'State synchronization failed' };
  } catch (error) {
    console.error('Synchronizing state failed:', error);
    return { success: false, message: error.message || 'Synchronizing state failed' };
  }
});

// 获取状态统计
ipcMain.handle('get-state-stats', async (event) => {
  try {
    const { stateManager } = require('../class');
    const stats = stateManager.getStateStats();
    return { success: true, data: stats };
  } catch (error) {
    console.error('Getting state stats failed:', error);
    return { success: false, message: error.message || 'Getting state stats failed' };
  }
});

// ==================== 预设策略相关IPC处理器 ====================

// 获取策略状态
ipcMain.handle('get-strategy-status', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // 从状态管理器获取策略状态
    const { stateManager } = require('../class');
    const strategyState = stateManager.getPageState('strategy') || {
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
      lastExecutionTime: null,
      executionCount: 0,
      affectedDevicesCount: 0
    };

    return { success: true, data: strategyState };
  } catch (error) {
    console.error('Getting strategy status failed:', error);
    return { success: false, message: error.message || 'Getting strategy status failed' };
  }
});

// 切换策略开关
ipcMain.handle('toggle-strategy', async (event, { enabled, strategy, config, currentGroup }) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const { stateManager } = require('../class');

    console.log(`🎯 [策略控制] ${enabled ? '启用' : '禁用'}策略:`, strategy.name);
    console.log('🎯 [策略控制] 策略配置:', config);
    console.log('🎯 [策略控制] 当前分组:', currentGroup);

    // 保存策略状态
    const strategyState = {
      enabled,
      strategy,
      config,
      currentGroup,
      lastExecutionTime: enabled ? new Date().toLocaleString() : null,
      executionCount: 0,
      affectedDevicesCount: 0
    };

    stateManager.updatePageState('strategy', strategyState);

    // 如果启用策略，立即执行一次
    if (enabled) {
      const executeResult = await executeStrategy(managers, strategy, config, currentGroup);
      strategyState.affectedDevicesCount = executeResult.affectedDevicesCount;
      strategyState.executionCount = 1;
      stateManager.updatePageState('strategy', strategyState);
    }

    return {
      success: true,
      message: `策略已${enabled ? '启用' : '禁用'}`,
      data: strategyState
    };
  } catch (error) {
    console.error('Toggling strategy failed:', error);
    return { success: false, message: error.message || 'Toggling strategy failed' };
  }
});

// 更新策略配置
ipcMain.handle('update-strategy-config', async (event, { strategy, config, currentGroup }) => {
  try {
    const { stateManager } = require('../class');

    console.log('🎯 [策略控制] 更新策略配置:', strategy.name);
    console.log('🎯 [策略控制] 新配置:', config);

    // 获取当前策略状态
    const currentState = stateManager.getPageState('strategy') || {};

    // 更新配置
    const updatedState = {
      ...currentState,
      strategy,
      config,
      currentGroup
    };

    stateManager.updatePageState('strategy', updatedState);

    return { success: true, message: '策略配置已更新' };
  } catch (error) {
    console.error('Updating strategy config failed:', error);
    return { success: false, message: error.message || 'Updating strategy config failed' };
  }
});

// 手动执行策略
ipcMain.handle('execute-strategy-manual', async (event, { strategy, config, currentGroup }) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const { stateManager } = require('../class');

    console.log('🎯 [策略控制] 手动执行策略:', strategy.name);

    // 执行策略
    const executeResult = await executeStrategy(managers, strategy, config, currentGroup);

    // 更新执行统计
    const currentState = stateManager.getPageState('strategy') || {};
    const updatedState = {
      ...currentState,
      lastExecutionTime: new Date().toLocaleString(),
      executionCount: (currentState.executionCount || 0) + 1,
      affectedDevicesCount: executeResult.affectedDevicesCount
    };

    stateManager.updatePageState('strategy', updatedState);

    return {
      success: true,
      message: '策略执行成功',
      data: {
        affectedDevicesCount: executeResult.affectedDevicesCount,
        executionDetails: executeResult.details
      }
    };
  } catch (error) {
    console.error('Manual strategy execution failed:', error);
    return { success: false, message: error.message || 'Manual strategy execution failed' };
  }
});

// ==================== 场景控制相关 IPC 处理器 ====================

// 获取场景列表
ipcMain.handle('get-scenes', async (event, groupId) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 获取场景列表, 分组ID:', groupId);

    const result = await managers.sceneManager.getScenes(groupId);

    if (result.success) {
      console.log('✅ [场景控制] 场景列表获取成功, 数量:', result.data.scenes.length);
    } else {
      console.error('❌ [场景控制] 场景列表获取失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Get scenes failed:', error);
    return { success: false, message: error.message || 'Get scenes failed' };
  }
});

// 获取场景详情
ipcMain.handle('get-scene-detail', async (event, sceneId) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 获取场景详情, 场景ID:', sceneId);

    const result = await managers.sceneManager.getSceneDetail(sceneId);

    if (result.success) {
      console.log('✅ [场景控制] 场景详情获取成功:', result.data.scene_name);
    } else {
      console.error('❌ [场景控制] 场景详情获取失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Get scene detail failed:', error);
    return { success: false, message: error.message || 'Get scene detail failed' };
  }
});

// 创建场景
ipcMain.handle('create-scene', async (event, sceneData) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 创建场景:', sceneData.scene_name);

    const result = await managers.sceneManager.createScene(sceneData);

    if (result.success) {
      console.log('✅ [场景控制] 场景创建成功, ID:', result.data.scene_id);
    } else {
      console.error('❌ [场景控制] 场景创建失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Create scene failed:', error);
    return { success: false, message: error.message || 'Create scene failed' };
  }
});

// 更新场景
ipcMain.handle('update-scene', async (event, sceneId, updateData) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 更新场景, ID:', sceneId);

    const result = await managers.sceneManager.updateScene(sceneId, updateData);

    if (result.success) {
      console.log('✅ [场景控制] 场景更新成功');
    } else {
      console.error('❌ [场景控制] 场景更新失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Update scene failed:', error);
    return { success: false, message: error.message || 'Update scene failed' };
  }
});

// 删除场景
ipcMain.handle('delete-scene', async (event, sceneId) => {
  try {
    // 参数验证
    if (!sceneId) {
      console.error('❌ [场景控制] 删除场景失败: 场景ID参数不完整');
      return { success: false, message: '参数不完整: 场景ID不能为空' };
    }

    if (typeof sceneId !== 'string') {
      console.error('❌ [场景控制] 删除场景失败: 场景ID参数类型错误');
      return { success: false, message: '参数不完整: 场景ID必须是字符串' };
    }

    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      console.error('❌ [场景控制] Scene manager 未初始化');
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 删除场景, ID:', sceneId);

    const result = await managers.sceneManager.deleteScene(sceneId);

    if (result.success) {
      console.log('✅ [场景控制] 场景删除成功');
    } else {
      console.error('❌ [场景控制] 场景删除失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Delete scene failed:', error);
    return { success: false, message: error.message || 'Delete scene failed' };
  }
});

// 执行场景
ipcMain.handle('execute-scene', async (event, sceneId) => {
  try {
    // 参数验证
    if (!sceneId) {
      console.error('❌ [场景控制] 执行场景失败: 场景ID参数不完整');
      return { success: false, message: '参数不完整: 场景ID不能为空' };
    }

    if (typeof sceneId !== 'string') {
      console.error('❌ [场景控制] 执行场景失败: 场景ID参数类型错误');
      return { success: false, message: '参数不完整: 场景ID必须是字符串' };
    }

    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      console.error('❌ [场景控制] Scene manager 未初始化');
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 执行场景, ID:', sceneId);

    const result = await managers.sceneManager.executeScene(sceneId);

    if (result.success) {
      console.log('✅ [场景控制] 场景执行成功, 统计:', result.data.summary);

      // 场景执行成功后，通知前端刷新设备状态
      console.log('🔄 [场景控制] 通知前端刷新设备状态...');
      event.sender.send('scene-executed-refresh-devices', {
        sceneId: sceneId,
        summary: result.data.summary
      });
    } else {
      console.error('❌ [场景控制] 场景执行失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('Execute scene failed:', error);
    return { success: false, message: error.message || 'Execute scene failed' };
  }
});

// 验证场景动作
ipcMain.handle('validate-scene-actions', async (event, actions) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 验证场景动作, 数量:', actions.length);

    const result = managers.sceneManager.validateSceneActions(actions);

    if (result.valid) {
      console.log('✅ [场景控制] 场景动作验证成功');
      return { success: true, message: result.message };
    } else {
      console.error('❌ [场景控制] 场景动作验证失败:', result.message);
      return { success: false, message: result.message };
    }
  } catch (error) {
    console.error('Validate scene actions failed:', error);
    return { success: false, message: error.message || 'Validate scene actions failed' };
  }
});

// 验证场景新动作添加（考虑已有动作）
ipcMain.handle('validate-scene-action-addition', async (event, newActions, existingActions) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 验证新动作添加, 新动作数量:', newActions.length, '已有动作数量:', existingActions.length);

    const result = managers.sceneManager.validateSceneActionAddition(newActions, existingActions);

    if (result.valid) {
      console.log('✅ [场景控制] 新动作添加验证成功');
      return { success: true, message: result.message };
    } else {
      console.error('❌ [场景控制] 新动作添加验证失败:', result.message);
      return { success: false, message: result.message };
    }
  } catch (error) {
    console.error('Validate scene action addition failed:', error);
    return { success: false, message: error.message || 'Validate scene action addition failed' };
  }
});

// 获取设备控制选项（统一处理器，支持手动控制和场景控制）
ipcMain.handle('get-device-control-options-for-scene', async (event, deviceId) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 获取设备控制选项, 设备ID:', deviceId);

    const options = managers.sceneManager.getDeviceControlOptions(deviceId);

    if (options) {
      console.log('✅ [场景控制] 设备控制选项获取成功, 属性数量:', options.controls.length);
      return { success: true, data: options };
    } else {
      console.error('❌ [场景控制] 设备控制选项获取失败');
      return { success: false, message: '无法获取设备控制选项' };
    }
  } catch (error) {
    console.error('Get device control options failed:', error);
    return { success: false, message: error.message || 'Get device control options failed' };
  }
});

// 获取设备属性选项
ipcMain.handle('get-property-options', async (event, deviceType, property) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    if (!managers.sceneManager) {
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [场景控制] 获取属性选项, 设备类型:', deviceType, '属性:', property);

    const options = managers.sceneManager.getPropertyOptions(deviceType, property);

    if (options) {
      console.log('✅ [场景控制] 属性选项获取成功');
      return { success: true, data: options };
    } else {
      console.error('❌ [场景控制] 属性选项获取失败');
      return { success: false, message: '无法获取属性选项' };
    }
  } catch (error) {
    console.error('Get property options failed:', error);
    return { success: false, message: error.message || 'Get property options failed' };
  }
});

// 获取分组可用设备（用于场景创建）
ipcMain.handle('get-group-devices-for-scene', async (event, groupId) => {
  try {
    console.log('🎬 [IPC] 收到获取分组设备请求, 分组ID:', groupId);

    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    console.log('🎬 [IPC] managers 状态:', {
      sceneManager: !!managers.sceneManager,
      storageManager: !!managers.storageManager,
      deviceControlManager: !!managers.deviceControlManager
    });

    if (!managers.sceneManager) {
      console.error('❌ [IPC] Scene manager 未初始化');
      return { success: false, message: 'Scene manager not initialized' };
    }

    console.log('🎬 [IPC] 调用 sceneManager.getGroupDevicesForScene...');
    const result = await managers.sceneManager.getGroupDevicesForScene(groupId);

    console.log('🎬 [IPC] SceneManager 返回结果:', {
      success: result.success,
      deviceCount: result.success ? result.data.devices.length : 0,
      message: result.message
    });

    if (result.success) {
      console.log('✅ [IPC] 分组设备获取成功, 数量:', result.data.devices.length);
      // 输出前3个设备的详细信息
      result.data.devices.slice(0, 3).forEach((device, index) => {
        console.log(`✅ [IPC] 设备${index + 1}: ${device.name || device.did} (${device.type})`);
      });
    } else {
      console.error('❌ [IPC] 分组设备获取失败:', result.message);
    }

    return result;
  } catch (error) {
    console.error('❌ [IPC] Get group devices for scene 异常:', error);
    return { success: false, message: error.message || 'Get group devices for scene failed' };
  }
});

// 策略执行函数
async function executeStrategy(managers, strategy, config, currentGroup) {
  console.log('🎯 [策略执行] 开始执行策略:', strategy.name);

  let targetDevices = [];
  let affectedCount = 0;
  const executionDetails = [];

  try {
    // 根据应用范围获取目标设备
    if (config.scope === 'current' && currentGroup) {
      targetDevices = managers.storageManager.getDevicesByGroup(currentGroup);
      console.log('🎯 [策略执行] 当前分组设备数量:', targetDevices.length);
    } else {
      targetDevices = managers.storageManager.getAllDevices();
      console.log('🎯 [策略执行] 所有设备数量:', targetDevices.length);
    }

    // 过滤在线且可控制的设备
    const controllableDevices = targetDevices.filter(device =>
      device.online &&
      !['mi_temp_hum_sensor', 'mi_air_sensor', 'history'].includes(device.type)
    );

    console.log('🎯 [策略执行] 可控制设备数量:', controllableDevices.length);

    // 根据策略类型执行不同的控制逻辑
    for (const device of controllableDevices) {
      try {
        const controlActions = generateControlActions(device, strategy, config);

        if (controlActions.length > 0) {
          for (const action of controlActions) {
            console.log(`🎯 [策略执行] 控制设备 ${device.name}: ${action.operation} = ${action.value}`);

            // 执行设备控制
            const controlResult = await managers.deviceControlManager.controlDevice(
              device.did,
              action.operation,
              action.value
            );

            if (controlResult.success) {
              affectedCount++;
              executionDetails.push({
                deviceId: device.did,
                deviceName: device.name,
                action: action.operation,
                value: action.value,
                success: true
              });
            } else {
              executionDetails.push({
                deviceId: device.did,
                deviceName: device.name,
                action: action.operation,
                value: action.value,
                success: false,
                error: controlResult.message
              });
            }
          }
        }
      } catch (deviceError) {
        console.error(`🎯 [策略执行] 控制设备失败 ${device.name}:`, deviceError);
        executionDetails.push({
          deviceId: device.did,
          deviceName: device.name,
          success: false,
          error: deviceError.message
        });
      }
    }

    console.log(`🎯 [策略执行] 策略执行完成，影响设备数: ${affectedCount}`);

    return {
      affectedDevicesCount: affectedCount,
      details: executionDetails
    };
  } catch (error) {
    console.error('🎯 [策略执行] 策略执行失败:', error);
    throw error;
  }
}

// 生成控制动作
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

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 调试设备分组信息
ipcMain.handle('debug-device-groups', async (event, groupId) => {
  console.log('🔍 [Debug] IPC call: debug-device-groups, groupId:', groupId);
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // 调用调试方法
    managers.storageManager.debugDeviceGroups(groupId);

    return { success: true, message: '调试信息已输出到控制台' };
  } catch (error) {
    console.error('❌ [Debug] Debug device groups failed:', error);
    return { success: false, message: error.message || 'Debug device groups failed' };
  }
});

// ==================== 数据分析相关IPC处理器 ====================

// 调试设备存储状态
ipcMain.handle('debug-device-storage', async (event) => {
  console.log('🔍 [Debug] IPC call: debug-device-storage');
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    const allDevices = managers.storageManager.getAllDevices();
    const deviceStats = managers.storageManager.getDeviceStats();

    console.log('🔍 [Debug] Device storage status:');
    console.log(`  - Total devices: ${allDevices.length}`);
    console.log(`  - Online devices: ${deviceStats.online}`);
    console.log(`  - Offline devices: ${deviceStats.offline}`);
    console.log(`  - Grouped devices: ${deviceStats.grouped}`);
    console.log(`  - Ungrouped devices: ${deviceStats.ungrouped}`);

    console.log('🔍 [Debug] First 5 devices:');
    allDevices.slice(0, 5).forEach((device, index) => {
      console.log(`  Device ${index + 1}:`);
      console.log(`    - did: ${device.did}`);
      console.log(`    - name: ${device.name}`);
      console.log(`    - type: ${device.type}`);
      console.log(`    - online: ${device.online}`);
      console.log(`    - groupId: ${device.groupId}`);
      console.log(`    - group: ${device.group}`);
      console.log(`    - gid: ${device.gid}`);
    });

    // 检查设备控制管理器状态
    const controlManager = managers.controlManager;
    console.log('🔍 [Debug] Device control manager status:');
    console.log(`  - Initialized: ${controlManager.isInitialized}`);
    console.log(`  - Has storage manager: ${!!controlManager.deviceStorageManager}`);
    console.log(`  - Has API registry: ${!!controlManager.apiRegistry}`);
    console.log(`  - Offline mode: ${controlManager.offlineMode}`);

    return {
      success: true,
      data: {
        deviceCount: allDevices.length,
        stats: deviceStats,
        controlManagerStatus: {
          initialized: controlManager.isInitialized,
          hasStorageManager: !!controlManager.deviceStorageManager,
          hasApiRegistry: !!controlManager.apiRegistry,
          offlineMode: controlManager.offlineMode
        }
      }
    };
  } catch (error) {
    console.error('❌ [Debug] Debug device storage failed:', error);
    return { success: false, message: error.message || 'Debug device storage failed' };
  }
});

// 测试API调用（调试用）
ipcMain.handle('debug-api-call', async (event, apiName, data) => {
  console.log('🔍 [Debug] IPC call: debug-api-call', apiName, data);
  try {
    const { accountManager } = require('../class');

    if (!accountManager.apiRegistry) {
      return { success: false, message: 'API Registry not available' };
    }

    console.log('🔍 [Debug] API Registry available, calling API...');
    const response = await accountManager.apiRegistry.callAPI(apiName, data);
    console.log('🔍 [Debug] API response:', response);

    return { success: true, data: response };
  } catch (error) {
    console.error('❌ [Debug] API call failed:', error);
    return { success: false, message: error.message || 'API call failed' };
  }
});

// 打开外部链接
ipcMain.handle('open-external-url', async (event, url) => {
  try {
    const { shell } = require('electron');
    await shell.openExternal(url);
    console.log(`🌐 [IPC] 打开外部链接: ${url}`);
    return { success: true };
  } catch (error) {
    console.error('❌ [IPC] 打开外部链接失败:', error);
    return { success: false, message: error.message || '打开链接失败' };
  }
});

// 综合刷新设备列表、状态和分组信息
ipcMain.handle('refresh-devices-and-groups', async (event) => {
  try {
    console.log('🔄 [IPC] 开始综合刷新设备和分组信息...');
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    let deviceCount = 0;
    let refreshSteps = [];

    // Step 1: 刷新设备列表
    console.log('🔄 [IPC] 步骤1: 获取设备列表...');
    try {
      const deviceListResponse = await accountManager.apiRegistry.getDeviceList();
      if (deviceListResponse && deviceListResponse.code === 200 && deviceListResponse.data && deviceListResponse.data.devices) {
        const storeResult = managers.storageManager.storeAllDevices(deviceListResponse.data.devices);
        if (storeResult.success) {
          deviceCount = deviceListResponse.data.devices.length;
          refreshSteps.push(`设备列表: ${deviceCount} 台设备`);
          console.log(`✅ [IPC] 设备列表刷新成功: ${deviceCount} 台设备`);
        } else {
          console.warn('⚠️ [IPC] 设备列表存储失败:', storeResult.message);
          refreshSteps.push('设备列表: 存储失败');
        }
      } else {
        console.warn('⚠️ [IPC] 获取设备列表失败或数据为空');
        refreshSteps.push('设备列表: 获取失败');
      }
    } catch (error) {
      console.error('❌ [IPC] 获取设备列表异常:', error);
      refreshSteps.push('设备列表: 请求异常');
    }

    // Step 2: 刷新设备状态
    console.log('🔄 [IPC] 步骤2: 获取设备状态...');
    try {
      const devicesStatusResponse = await accountManager.apiRegistry.callAPIGet('getDevicesStatus');
      if (devicesStatusResponse && devicesStatusResponse.code === 200 && devicesStatusResponse.data && devicesStatusResponse.data.devices) {
        const storeResult = managers.storageManager.storeAllDevices(devicesStatusResponse.data.devices);
        if (storeResult.success) {
          deviceCount = Math.max(deviceCount, devicesStatusResponse.data.devices.length);
          refreshSteps.push(`设备状态: ${devicesStatusResponse.data.devices.length} 台设备`);
          console.log(`✅ [IPC] 设备状态刷新成功: ${devicesStatusResponse.data.devices.length} 台设备`);
        } else {
          console.warn('⚠️ [IPC] 设备状态存储失败:', storeResult.message);
          refreshSteps.push('设备状态: 存储失败');
        }
      } else {
        console.warn('⚠️ [IPC] 获取设备状态失败或数据为空');
        refreshSteps.push('设备状态: 获取失败');
      }
    } catch (error) {
      console.error('❌ [IPC] 获取设备状态异常:', error);
      refreshSteps.push('设备状态: 请求异常');
    }

    // Step 3: 刷新分组信息
    console.log('🔄 [IPC] 步骤3: 刷新分组信息...');
    try {
      // 重新同步分组数据
      const groupSyncResult = await managers.groupAPIManager.syncGroupsFromServer();
      if (groupSyncResult.success) {
        refreshSteps.push('分组信息: 同步成功');
        console.log('✅ [IPC] 分组信息同步成功');
      } else {
        refreshSteps.push('分组信息: 同步失败');
        console.warn('⚠️ [IPC] 分组信息同步失败:', groupSyncResult.message);
      }

      // 刷新分组统计
      managers.groupAPIManager.refreshGroupStats();
      refreshSteps.push('分组统计: 已更新');
      console.log('✅ [IPC] 分组统计已更新');

      // 处理未分组设备
      await managers.groupAPIManager.assignUngroupedDevices();
      refreshSteps.push('未分组设备: 已处理');
      console.log('✅ [IPC] 未分组设备处理完成');

    } catch (error) {
      console.error('❌ [IPC] 刷新分组信息异常:', error);
      refreshSteps.push('分组信息: 处理异常');
    }

    // 获取最终统计信息
    const finalStats = managers.storageManager.getDeviceStats();
    const groupStats = managers.groupAPIManager.getGroupStats();

    console.log('✅ [IPC] 综合刷新完成');
    console.log(`📊 [IPC] 最终统计: 设备 ${finalStats.total} 台 (在线 ${finalStats.online}, 离线 ${finalStats.offline}), 分组 ${groupStats.totalGroups} 个`);

    return {
      success: true,
      message: '设备和分组信息刷新完成',
      deviceCount: finalStats.total,
      groupCount: groupStats.totalGroups,
      stats: finalStats,
      groupStats: groupStats,
      refreshSteps: refreshSteps,
      lastUpdated: new Date().toISOString()
    };

  } catch (error) {
    console.error('❌ [IPC] 综合刷新设备和分组失败:', error);
    return {
      success: false,
      message: error.message || '刷新设备和分组信息失败',
      refreshSteps: ['综合刷新: 发生异常']
    };
  }
});

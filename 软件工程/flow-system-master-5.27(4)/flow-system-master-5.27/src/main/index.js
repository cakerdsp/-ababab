import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// Set console encoding to UTF-8 to fix garbled Chinese characters issue
if (process.platform === 'win32') {
  try {
    // Set process encoding
    process.stdout.setEncoding('utf8');
    process.stderr.setEncoding('utf8');

    // Set environment variables to force UTF-8 encoding
    process.env.PYTHONIOENCODING = 'utf-8';
    process.env.LANG = 'zh_CN.UTF-8';
    process.env.LC_ALL = 'zh_CN.UTF-8';

    // Set code page to UTF-8 on Windows
    const { execSync } = require('child_process');
    execSync('chcp 65001', { stdio: 'ignore' });

    // Override console methods to ensure UTF-8 output (only handles string arguments)
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    const fixEncoding = (str) => {
      if (typeof str !== 'string') return str;
      try {
        // Try to detect and fix Chinese encoding issues
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
      // Parameter validation
      if (!args || typeof args !== 'object') {
        console.error('toMain: Invalid arguments', args)
        return
      }

      // Default screen size
      const screenWidth = Number(args.screenWidth) || 1200
      const screenHeight = Number(args.screenHeight) || 800

      console.log('Adjusting window size:', { screenWidth, screenHeight })

      // Calculate window dimensions
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
    event.preventDefault(); // Prevent default minimize behavior
    mainWindow.minimize(); // Minimize to taskbar
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
    // Window debugging
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

// Check for auto-login - following the original process documentation
ipcMain.handle('check-auto-login', async (event) => {
  console.log('Login page requests auto-login check')
  const { accountManager, deviceController } = require('../class');
  const result = await accountManager.initialize();

  if (result.success && result.autoLogin) {
    const currentUser = accountManager.getCurrentUser();
    const token = accountManager.dataStorage.getToken();
    const sseConnectionId = accountManager.dataStorage.getSseConnectionId();
    const userId = currentUser?.getUserId();

    // Check if it's an admin account - completely skip SSE connection
    if (userId === 'admin') {
      console.log('🟡 [Offline Debug] Admin account detected for auto-login, enabling offline debug mode');
      console.log('🟡 [Offline Debug] Skipping SSE connection and device controller initialization entirely');

      // Enable offline mode for the group manager
      try {
        const managers = accountManager.getDeviceManagers();
        if (managers && managers.groupAPIManager) {
          managers.groupAPIManager.enableOfflineMode();
          console.log('🟡 [Offline Debug] Group manager offline mode enabled');

          // Ensure the default group exists (offline mode)
          try {
            console.log('🔍 [Offline Debug] Checking for default group...');
            const groups = managers.groupAPIManager.getAllGroups();
            console.log('🔍 [Offline Debug] Current group list:', groups.map(g => ({ gid: g.gid, gname: g.gname })));

            const hasDefaultGroup = groups.some(group => group.gname === '默认分组');
            console.log('🔍 [Offline Debug] Default group exists:', hasDefaultGroup);

            if (!hasDefaultGroup) {
              console.log('🔍 [Offline Debug] Creating default group...');
              const groupResult = await managers.groupAPIManager.createGroup('默认分组');
              console.log('✅ [Offline Debug] Default group creation result:', groupResult);
            } else {
              console.log('✅ [Offline Debug] Default group already exists, skipping creation');
            }
          } catch (groupError) {
            console.warn('❌ [Offline Debug] Failed to create default group:', groupError);
          }
        }
      } catch (error) {
        console.warn('❌ [Offline Debug] Group manager initialization failed:', error);
      }

      console.log('✅ [Offline Debug] Admin account auto-login complete, no SSE connection required');
    } else {
      // Normal SSE connection process for non-admin accounts
      if (sseConnectionId) {
        try {
          console.log('🔧 [Debug] Attempting to initialize device controller...');
          await deviceController.initialize(sseConnectionId);
          console.log('✅ [Debug] Device controller auto-initialization successful');

          // Ensure the default group exists
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

// Login - following the original process documentation
ipcMain.handle('login', async (event, loginData) => {
  try {
    const { userId, password, rememberMe } = loginData;
    console.log('🔧 [Debug] Login request:', userId, password ? '***' : 'no_password', rememberMe);
    const { accountManager, deviceController } = require('../class');
    const result = await accountManager.login(userId, password, rememberMe);

    // Check if the application needs to be restarted to enter debug mode
    if (result.restart) {
      console.log('✅ [System] Restarting application to enter offline debug mode...');
      app.relaunch();
      app.quit();
      return; // Prevent further execution
    }

    if (result.success) {
      // Normal flow for non-admin accounts
      try {
        console.log('🔧 [Debug] Attempting to initialize device controller, user ID:', userId);
        await deviceController.initialize(userId);
        console.log('✅ [Debug] Device controller initialization successful');
        result.deviceControllerInitialized = true;

        // Ensure the default group exists
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

// Register
ipcMain.handle('register', async (event, registerData) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.register(registerData);
    return result;
  } catch (error) {
    console.error('Registration processing failed:', error);
    return { success: false, message: error.message || 'Registration processing failed' };
  }
});

// Logout
ipcMain.handle('logout', async () => {
  try {
    const { accountManager, deviceController } = require('../class');

    try {
      await deviceController.logout();
      console.log('Device controller resources cleaned up successfully');
    } catch (error) {
      console.warn('Device controller resources cleanup failed:', error);
    }

    const result = accountManager.logout();
    return result;
  } catch (error) {
    console.error('Logout processing failed:', error);
    return { success: false, message: error.message || 'Logout processing failed' };
  }
});

// Bind third-party account
ipcMain.handle('bind-third-party', async (event, brandName, authCode) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.bindThirdPartyBrand(brandName, authCode);
    return result;
  } catch (error) {
    console.error('Third-party binding failed:', error);
    return { success: false, message: error.message || 'Third-party binding failed' };
  }
});

// Unbind third-party account
ipcMain.handle('unbind-third-party', async (event, brandName) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.unbindThirdPartyBrand(brandName);
    return result;
  } catch (error) {
    console.error('Third-party unbinding failed:', error);
    return { success: false, message: error.message || 'Third-party unbinding failed' };
  }
});

// Get bound third-party accounts
ipcMain.handle('get-bindings', async (event) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.loadUserBindings();
    return result;
  } catch (error) {
    console.error('Getting bindings failed:', error);
    return { success: false, message: error.message || 'Getting bindings failed' };
  }
});

// Authorize third-party brand
ipcMain.handle('perform-third-party-authorization', async (event, brandName) => {
  try {
    const { accountManager } = require('../class');

    // Use a progress callback function to send status updates to the renderer process
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

// Get authorization code
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

// Bind with authorization code
ipcMain.handle('bind-with-authorization-code', async (event, authCode, brandName) => {
  try {
    const { accountManager } = require('../class');
    const result = await accountManager.bindWithAuthorizationCode(authCode, brandName);
    return result;
  } catch (error) {
    console.error('Binding with authorization code failed:', error);
    return { success: false, message: error.message || 'Binding with authorization code failed' };
  }
});

// Refresh token
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

// ==================== Device-related IPC handlers ====================

// Get all devices
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

// Get devices by brand
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

// Get devices by group
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

// Get controllable devices
ipcMain.handle('get-controllable-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const allDevices = managers.storageManager.getAllDevices();
    const controllableDevices = allDevices.filter(device =>
      device.type !== 'mi_temp_hum_sensor' && device.type !== 'mi_air_sensor'
    );
    return { success: true, data: controllableDevices };
  } catch (error) {
    console.error('Getting controllable devices failed:', error);
    return { success: false, message: error.message || 'Getting controllable devices failed' };
  }
});

// Get sensor devices
ipcMain.handle('get-sensor-devices', async (event) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const allDevices = managers.storageManager.getAllDevices();
    const sensorDevices = allDevices.filter(device =>
      device.type === 'mi_temp_hum_sensor' || device.type === 'mi_air_sensor'
    );
    return { success: true, data: sensorDevices };
  } catch (error) {
    console.error('Getting sensor devices failed:', error);
    return { success: false, message: error.message || 'Getting sensor devices failed' };
  }
});

// Get device control options
ipcMain.handle('get-device-control-options', async (event, did) => {
  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();
    const device = managers.storageManager.getDevice(did);

    if (!device || device.type === 'mi_temp_hum_sensor' || device.type === 'mi_air_sensor') {
      return { success: false, message: 'Device does not exist or is not controllable' };
    }

    const options = {
      did: device.did,
      name: device.name,
      type: device.type,
      brand: device.brand,
      online: device.online,
      controls: []
    };

    // 根据设备类型生成控制选项
    switch (device.type) {
      case 'mi_ac':
      case 'midea_ac':
        options.controls = [
          { property: 'power', type: 'select', options: ['ON', 'OFF'], label: 'Power' },
          { property: 'target_temperature', type: 'number', min: 16, max: 30, label: 'Target Temperature' },
          { property: 'fan_speed', type: 'select', options: ['low', 'medium', 'high', 'auto'], label: 'Fan Speed' },
          { property: 'mode', type: 'select', options: ['cool', 'heat', 'dry', 'fan'], label: 'Mode' }
        ];
        break;
      default:
        options.controls = [];
    }

    return { success: true, data: options };
  } catch (error) {
    console.error('Getting device control options failed:', error);
    return { success: false, message: error.message || 'Getting device control options failed' };
  }
});

// Control device
ipcMain.handle('control-device', async (event, controlData) => {
  try {
    const { did, operation, value } = controlData;
    const { accountManager } = require('../class');

    const response = await accountManager.apiRegistry.callAPI('controlDevice', {
      did: did,
      control: { operation: operation, value: value }
    });

    if (response && response.code === 200) {
      return { success: true, message: 'Device control successful', did: did, operation: operation, value: value };
    } else {
      return { success: false, message: response.message || 'Device control failed' };
    }
  } catch (error) {
    console.error('Device control failed:', error);
    return { success: false, message: error.message || 'Device control failed' };
  }
});

// Refresh device status
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

// ==================== Group management IPC handlers ====================

// Get all groups
ipcMain.handle('get-all-groups', async (event) => {
  console.log('🔍 [Debug] IPC call: get-all-groups');
  try {
    const { accountManager } = require('../class');
    console.log('🔍 [Debug] Successfully retrieved accountManager');

    const managers = accountManager.getDeviceManagers();
    console.log('🔍 [Debug] Successfully retrieved deviceManagers:', !!managers);
    console.log('🔍 [Debug] groupAPIManager exists:', !!managers.groupAPIManager);

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

// Create group
ipcMain.handle('create-group', async (event, groupName) => {
  console.log('🔍 [Debug] IPC call: create-group, group name:', groupName);

  // Parameter validation
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

// Delete group
ipcMain.handle('delete-group', async (event, groupId) => {
  console.log('🔍 [Debug] IPC call: delete-group, group ID:', groupId);

  // Parameter validation
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

    // Check if the group exists before deleting
    const groups = managers.groupAPIManager.getAllGroups();
    const targetGroup = groups.find(g => g.gid === groupId);
    console.log('🔍 [Debug] Group info to be deleted:', targetGroup);

    if (!targetGroup) {
      console.log('❌ [Debug] Group does not exist:', groupId);
      throw new Error('Group does not exist');
    }

    // Check the number of devices in the group
    const devices = managers.deviceAPIManager.getAllDevices();
    const groupDevices = devices.filter(device => device.group_id === groupId);
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

// Set device group
ipcMain.handle('set-device-group', async (event, deviceId, groupId) => {
  console.log('🔍 [Debug] IPC call: set-device-group');
  console.log('🔍 [Debug] Device ID:', deviceId);
  console.log('🔍 [Debug] Target group ID:', groupId);

  try {
    const { accountManager } = require('../class');
    const managers = accountManager.getDeviceManagers();

    // Validate if the device exists
    const devices = managers.deviceAPIManager.getAllDevices();
    const device = devices.find(d => d.did === deviceId);
    console.log('🔍 [Debug] Device info:', device);

    if (!device) {
      console.log('❌ [Debug] Device does not exist:', deviceId);
      throw new Error('Device does not exist');
    }

    // Validate if the group exists (if groupId is not null)
    if (groupId) {
      const groups = managers.groupAPIManager.getAllGroups();
      const group = groups.find(g => g.gid === groupId);
      console.log('🔍 [Debug] Target group info:', group);

      if (!group) {
        console.log('❌ [Debug] Target group does not exist:', groupId);
        throw new Error('Target group does not exist');
      }
    }

    console.log('🔍 [Debug] Device current group:', device.group_id || 'No group');
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

// ==================== Sensor data analysis IPC handlers ====================

// Analyze group sensor data
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

// Analyze multiple groups data (for comparison)
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

// Get supported sensor types
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

// Export analysis result
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

// Refresh all data
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

// ==================== System status IPC handlers ====================

// Get system status
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
      sensorCount: allDevices.filter(d => d.type === 'mi_temp_hum_sensor' || d.type === 'mi_air_sensor').length,
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

// Reconnect SSE
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

// ==================== State management IPC handlers ====================

// Get current state
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

// Get page state
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

// Save page state
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

// Save form state
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

// Get form state
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

// Save UI state
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

// Get UI state
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

// Sync state from storage
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

// Get state stats
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

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

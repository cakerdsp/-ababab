const UserAccount = require('../../domain/account/UserAccount');
const UnifiedStorage = require('../../services/storage/UnifiedStorage');
const AccountAPIRegistry = require('../../services/api/AccountAPIRegistry');
const DeviceSSEManager = require('../device/DeviceSSEManager');
const DeviceStorageManager = require('../device/DeviceStorageManager');
const DeviceGroupAPIManager = require('../device/DeviceGroupAPIManager');
const DeviceControlManager = require('../device/DeviceControlManager');
const SceneManager = require('../device/SceneManager');
const SceneStorageManager = require('../device/SceneStorageManager');
const SensorDataAnalyzer = require('../data/SensorDataAnalyzer');


class AccountManager {
  constructor() {
    this.dataStorage = new UnifiedStorage();
    this.apiRegistry = new AccountAPIRegistry(this.dataStorage); // 传递存储实例
    this.currentUser = null;
    this.supportedBrands = {}; // 存储支持的品牌
    this.isInitialized = false;

    // 设备管理相关组件
    this.deviceSSEManager = new DeviceSSEManager();
    this.deviceStorageManager = new DeviceStorageManager();
    this.deviceGroupAPIManager = new DeviceGroupAPIManager(this.apiRegistry, this.deviceStorageManager);
    this.deviceControlManager = new DeviceControlManager(this.apiRegistry, this.deviceStorageManager);
    this.sceneStorageManager = new SceneStorageManager();
    this.sceneManager = new SceneManager(this.apiRegistry, this.deviceStorageManager, this.deviceControlManager);
    this.sensorDataAnalyzer = new SensorDataAnalyzer(this.apiRegistry, this.deviceStorageManager);

    // (新增) 注入groupAPIManager到storageManager中，以实现自动分配默认分组
    this.deviceStorageManager.setGroupAPIManager(this.deviceGroupAPIManager);
  }

  // 初始化，检查自动登录
  async initialize() {
    if (this.isInitialized) {
      // 如果已经初始化，返回当前状态
      const isLoggedIn = this.isLoggedIn();
      return { success: isLoggedIn, autoLogin: isLoggedIn };
    }

    try {
      // 检查是否有有效的会话
      if (this.dataStorage.hasValidSession()) {
        const userData = this.dataStorage.getUserAccount();
        const settings = this.dataStorage.getAppSettings();

        if (userData && settings.autoLogin) {
          // 步骤2: 检查本地是否有有效的访问令牌
          const token = this.dataStorage.getToken();

          if (!token) {
            // 步骤3: 如果没有有效访问令牌，使用refreshToken请求新的token
            const refreshToken = this.dataStorage.getRefreshToken();
            if (refreshToken) {
              console.log('Access token does not exist, trying to get a new token with refreshToken');
              const refreshResult = await this.apiRegistry.refreshAccessToken(refreshToken);

              if (refreshResult.success) {
                // 步骤5: 收到新的访问令牌后，保存并使用它
                console.log('Successfully refreshed access token');
                this.currentUser = new UserAccount(userData.userId);

                // 获取绑定信息
                await this.loadUserBindings();

                // 确保存储结构完整
                const storageInitResult = this.dataStorage.initializeStorageStructure();
                if (!storageInitResult.success) {
                  console.warn('⚠️ Storage initialization failed during auto-login:', storageInitResult.message);
                }

                // 初始化设备管理功能
                await this.initializeDeviceManagement(userData.userId);

                console.log('Auto-login successful');
                this.isInitialized = true;
                return { success: true, autoLogin: true };
              } else {
                console.log('Failed to refresh token, please login again');
                // 清除无效的token信息
                this.dataStorage.clearUserData();
                this.isInitialized = true;
                return { success: false, autoLogin: false };
              }
            } else {
              console.log('No refreshToken, cannot auto-login');
              this.isInitialized = true;
              return { success: false, autoLogin: false };
            }
          } else {
                          // 有token，直接尝试验证token有效性
              // 特殊处理：如果是admin调试账户，跳过API验证
              if (userData.userId === 'admin') {
                console.log('Detected admin debug account, skipping token validation');
                this.currentUser = new UserAccount(userData.userId);

                // 加载调试账户的品牌绑定状态
                this.supportedBrands = this.dataStorage.getSupportedBrands() || {
                  'xiaomi': {
                    brandName: 'xiaomi',
                    isBound: true,
                    isExpired: false
                  },
                  'midea': {
                    brandName: 'midea',
                    isBound: true,
                    isExpired: false
                  }
                };

                // 确保存储结构完整
                const storageInitResult = this.dataStorage.initializeStorageStructure();
                if (!storageInitResult.success) {
                  console.warn('⚠️ Storage initialization failed during admin auto-login:', storageInitResult.message);
                }

                // 初始化设备管理功能
                await this.initializeDeviceManagement(userData.userId);

                console.log('Admin debug account auto-login successful');
                this.isInitialized = true;
                return { success: true, autoLogin: true };
              }

                          // 正常账户：通过调用一个需要认证的API来验证token是否有效
              try {
                await this.loadUserBindings(); // 这个API需要认证，会触发token验证
                this.currentUser = new UserAccount(userData.userId);

                // 确保存储结构完整
                const storageInitResult = this.dataStorage.initializeStorageStructure();
                if (!storageInitResult.success) {
                  console.warn('⚠️ Storage initialization failed during token auto-login:', storageInitResult.message);
                }

                // 初始化设备管理功能
                await this.initializeDeviceManagement(userData.userId);

                console.log('Auto-login successful with existing token');
                this.isInitialized = true;
                return { success: true, autoLogin: true };
              } catch (error) {
              // token无效，尝试使用refreshToken
              console.log('Existing token is invalid, trying to refresh with refreshToken');
              const refreshToken = this.dataStorage.getRefreshToken();
              if (refreshToken) {
                const refreshResult = await this.apiRegistry.refreshAccessToken(refreshToken);
                if (refreshResult.success) {
                  this.currentUser = new UserAccount(userData.userId);
                  await this.loadUserBindings();

                  // 确保存储结构完整
                  const storageInitResult = this.dataStorage.initializeStorageStructure();
                  if (!storageInitResult.success) {
                    console.warn('⚠️ Storage initialization failed during refresh auto-login:', storageInitResult.message);
                  }

                  // 初始化设备管理功能
                  await this.initializeDeviceManagement(userData.userId);

                  console.log('Auto-login successful after refreshing token');
                  this.isInitialized = true;
                  return { success: true, autoLogin: true };
                }
              }

              // 刷新失败，清除数据
              this.dataStorage.clearUserData();
              this.isInitialized = true;
              return { success: false, autoLogin: false };
            }
          }
        }
      }
    } catch (error) {
      console.error('Auto-login failed:', error);
    }

    this.isInitialized = true;
    return { success: false, autoLogin: false };
  }

  // 登录方法 - 根据接口文档更新
  async login(userId, password, rememberMe = false) {
    try {
      // ===== 特殊调试账户处理 =====
      // 当用户名和密码都是 "admin" 时，跳过服务器验证，直接登录
      if (userId === 'admin' && password === 'admin') {
        console.log('Detected admin debug account, enabling offline login mode');

        // 创建用户账户对象
        this.currentUser = new UserAccount(userId);

        // 生成模拟的token和数据
        const mockToken = 'admin-debug-token-' + Date.now();
        const mockRefreshToken = 'admin-debug-refresh-' + Date.now();

        // 存储登录状态
        this.dataStorage.saveUserAccount(this.currentUser);
        this.dataStorage.saveToken(mockToken);
        this.dataStorage.saveRefreshToken(mockRefreshToken);

        // 保存SSE连接ID（使用userId）
        this.dataStorage.saveSseConnectionId(userId);

        // 保存登录凭据用于自动登录
        this.dataStorage.saveLoginCredentials(userId, rememberMe);

        // 初始化存储结构和默认数据
        const storageInitResult = this.dataStorage.initializeStorageStructure();
        if (!storageInitResult.success) {
          console.warn('⚠️ Storage initialization failed:', storageInitResult.message);
        }

        // 保存应用设置
        const settings = this.dataStorage.getAppSettings();
        settings.rememberMe = rememberMe;
        settings.autoLogin = rememberMe;
        this.dataStorage.saveAppSettings(settings);

        // 为调试账户设置默认的品牌绑定状态
        this.supportedBrands = {
          'xiaomi': {
            brandName: 'xiaomi',
            isBound: true,
            isExpired: false
          },
          'midea': {
            brandName: 'midea',
            isBound: true,
            isExpired: false
          }
        };
        this.dataStorage.saveSupportedBrands(this.supportedBrands);

        console.log('Admin debug account logged in successfully');

        // 初始化设备管理功能
        await this.initializeDeviceManagement(userId);

        return {
          success: true,
          token: mockToken,
          refreshToken: mockRefreshToken,
          userId: userId,
          message: 'Admin debug account login successful',
          isDebugMode: true // 标识这是调试模式
        };
      }
      // ===== 正常登录流程 =====

      // 调用API进行登录验证 - 使用接口文档规定的参数名
      const response = await this.apiRegistry.callAPI('login', {
        userId: userId, // 接口文档要求的是userId，不是username
        password: password
      });

      if (response && response.status === 'success') {
        // 创建用户账户对象
        this.currentUser = new UserAccount(userId);

        // 存储登录状态
        this.dataStorage.saveUserAccount(this.currentUser);
        this.dataStorage.saveToken(response.data.token);

        // 存储refreshToken
        if (response.data.refreshToken) {
          this.dataStorage.saveRefreshToken(response.data.refreshToken);
        }

        // 保存SSE连接ID（使用userId）
        this.dataStorage.saveSseConnectionId(userId);

        // 保存登录凭据用于自动登录
        // 如果rememberMe为true，则保存30天的登录凭据，否则保存24小时
        this.dataStorage.saveLoginCredentials(userId, rememberMe);

        // 初始化存储结构和默认数据
        const storageInitResult = this.dataStorage.initializeStorageStructure();
        if (!storageInitResult.success) {
          console.warn('⚠️ Storage initialization failed:', storageInitResult.message);
        }

        // 保存应用设置
        const settings = this.dataStorage.getAppSettings();
        settings.rememberMe = rememberMe;
        settings.autoLogin = rememberMe; // 记住我的同时启用自动登录
        this.dataStorage.saveAppSettings(settings);

        // 加载用户绑定的品牌
        await this.loadUserBindings();

        // 初始化设备管理功能
        await this.initializeDeviceManagement(userId);

        return {
          success: true,
          token: response.data.token,
          refreshToken: response.data.refreshToken,
          userId: userId,
          message: 'Login successful'
        };
      } else {
        return {
          success: false,
          message: response.message || 'Login failed',
          errors: response.errors
        };
      }
    } catch (error) {
      console.error('Login error:', error);

      // 更详细的错误处理
      let errorMessage = 'Login request failed';

      if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to server, please check network connection';
      } else if (error.code === 'ETIMEDOUT') {
        errorMessage = 'Request timed out, please try again';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Network connection failed, please check server status';
      } else if (error.message) {
        errorMessage = error.message;
      }

      return {
        success: false,
        message: errorMessage,
        code: error.code || 'UNKNOWN_ERROR'
      };
    }
  }

  // 注册方法 - 根据接口文档更新
  async register(userId, password) {
    try {
      // 调用API进行注册 - 使用接口文档规定的参数名
      const response = await this.apiRegistry.callAPI('register', {
        userId: userId, // 接口文档要求的是userId
        password: password
      });

      if (response && response.status === 'success') {
        return { success: true, message: 'Registration successful' };
      } else {
        return {
          success: false,
          message: response.message || 'Registration failed',
          errors: response.errors
        };
      }
    } catch (error) {
      console.error('Registration error:', error);

      // 更详细的错误处理
      let errorMessage = 'Registration request failed';

      if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
        errorMessage = 'Cannot connect to server, please check network connection';
      } else if (error.code === 'ETIMEDOUT') {
        errorMessage = 'Request timed out, please try again';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Network connection failed, please check server status';
      } else if (error.message) {
        errorMessage = error.message;
      }

      return {
        success: false,
        message: errorMessage,
        code: error.code || 'UNKNOWN_ERROR'
      };
    }
  }

  // 加载用户绑定信息
  async loadUserBindings() {
    try {
      if (!this.currentUser) {
        return { success: false, message: 'User not logged in' };
      }

      // 特殊处理：admin调试账户跳过API调用
      if (this.currentUser.getUserId() === 'admin') {
        console.log('Admin debug account, using local binding information');

        // 使用默认的品牌绑定状态
        this.supportedBrands = {
          'xiaomi': {
            brandName: 'xiaomi',
            isBound: true,
            isExpired: false
          },
          'midea': {
            brandName: 'midea',
            isBound: true,
            isExpired: false
          }
        };

        // 保存到本地存储
        this.dataStorage.saveSupportedBrands(this.supportedBrands);

        return { success: true, bindings: this.supportedBrands };
      }

      // 正常用户：调用API获取绑定信息
      const response = await this.apiRegistry.callAPIGet('getBindings');

      if (response && response.status === 'success') {
        // 根据接口文档格式处理绑定信息
        this.supportedBrands = {};
        if (response.data && Array.isArray(response.data)) {
          response.data.forEach(binding => {
            this.supportedBrands[binding.brand] = {
              brandName: binding.brand,
              isBound: !binding.isExpired, // isExpired为false表示已绑定且有效
              isExpired: binding.isExpired
            };
          });
        }

        // 保存到本地存储
        this.dataStorage.saveSupportedBrands(this.supportedBrands);

        return { success: true, bindings: this.supportedBrands };
      } else {
        return { success: false, message: response.message || 'Failed to get binding information' };
      }
    } catch (error) {
      console.error('Error getting binding information:', error);
      return { success: false, message: error.message || 'Request to get binding information failed' };
    }
  }

  // 获取支持的品牌列表
  getSupportedBrands() {
    return this.supportedBrands;
  }

  // 绑定第三方品牌账户 - 根据接口文档更新
  async bindThirdPartyBrand(brandName, authCode) {
    try {
      if (!this.currentUser) {
        return { success: false, message: 'User not logged in' };
      }

      // 验证品牌名是否支持
      const supportedBrands = ['xiaomi', 'midea'];
      if (!supportedBrands.includes(brandName)) {
        return { success: false, message: 'Unsupported brand' };
      }

      // 调用API进行品牌绑定 - 根据接口文档使用code和brand参数
      const response = await this.apiRegistry.callAPI('bindThirdParty', {
        code: authCode,
        brand: brandName
      });

      if (response && response.status === 'success') {
        // 更新本地品牌状态
        if (!this.supportedBrands[brandName]) {
          this.supportedBrands[brandName] = {
            brandName: brandName,
            isBound: true,
            isExpired: false
          };
        } else {
          this.supportedBrands[brandName].isBound = true;
          this.supportedBrands[brandName].isExpired = false;
        }

        // 保存更新后的品牌状态
        this.dataStorage.saveSupportedBrands(this.supportedBrands);

        return { success: true, message: `${brandName} brand bound successfully` };
      } else {
        return {
          success: false,
          message: response.message || 'Brand binding failed',
          errors: response.errors
        };
      }
    } catch (error) {
      console.error('Brand binding error:', error);
      return { success: false, message: error.message || 'Brand binding request failed' };
    }
  }

  // 解绑第三方品牌账户 - 根据接口文档更新
  async unbindThirdPartyBrand(brandName) {
    try {
      if (!this.currentUser) {
        return { success: false, message: 'User not logged in' };
      }

      // 验证品牌名是否支持
      const supportedBrands = ['xiaomi', 'midea'];
      if (!supportedBrands.includes(brandName)) {
        return { success: false, message: 'Unsupported brand' };
      }

      // 调用API进行品牌解绑 - 根据接口文档使用brand参数
      const response = await this.apiRegistry.callAPI('unbindThirdParty', {
        brand: brandName
      });

      if (response && response.status === 'success') {
        // 更新本地品牌状态
        if (this.supportedBrands[brandName]) {
          this.supportedBrands[brandName].isBound = false;
          this.supportedBrands[brandName].isExpired = true;
        }

        // 保存更新后的品牌状态
        this.dataStorage.saveSupportedBrands(this.supportedBrands);

        return { success: true, message: `${brandName} brand unbound successfully` };
      } else {
        return {
          success: false,
          message: response.message || 'Brand unbinding failed',
          errors: response.errors
        };
      }
    } catch (error) {
      console.error('Brand unbinding error:', error);
      return { success: false, message: error.message || 'Brand unbinding request failed' };
    }
  }

    /**
   * 获取第三方品牌授权码 - 使用统一API调用方式
   * @param {string} userId - 用户ID
   * @param {string} brandName - 品牌名称 (xiaomi, midea)
   * @returns {Promise<Object>} 授权码获取结果
   */
  async getAuthorizationCode(userId, brandName) {
    try {
      console.log(`Getting authorization code for user ${userId} for brand ${brandName}...`);

      if (!userId || !brandName) {
        return { success: false, message: 'Missing required parameters: userId or brand' };
      }

      // 验证品牌名是否支持
      const supportedBrands = ['xiaomi', 'midea'];
      if (!supportedBrands.includes(brandName)) {
        return { success: false, message: `Brand '${brandName}' is not configured` };
      }

      // 特殊处理：admin调试账户生成模拟授权码
      if (userId === 'admin') {
        console.log('Admin debug account, generating mock authorization code');
        const mockAuthCode = `debug-auth-${brandName}-${Date.now()}`;
        return {
          success: true,
          authorizationCode: mockAuthCode,
          createdAt: new Date().toISOString()
        };
      }

      // 正常用户：使用统一的API调用方式
      const result = await this.apiRegistry.getAuthorizationCode({
        userId: userId,
        brand: brandName
      });

      if (result.status === 'success') {
        console.log(`Successfully obtained authorization code: ${result.data.authorizationCode}`);
        return {
          success: true,
          authorizationCode: result.data.authorizationCode,
          createdAt: result.data.createdAt
        };
      } else {
        return {
          success: false,
          message: result.message || 'Failed to get authorization code'
        };
      }
    } catch (error) {
      console.error('Failed to get authorization code:', error);
      return {
        success: false,
        message: `Failed to get authorization code: ${error.message}`
      };
    }
  }

    /**
   * 使用授权码绑定第三方品牌账号 - 使用统一API调用方式
   * @param {string} authCode - 授权码
   * @param {string} brandName - 品牌名称
   * @returns {Promise<Object>} 绑定结果
   */
  async bindWithAuthorizationCode(authCode, brandName) {
    try {
      console.log(`Binding brand ${brandName} with authorization code ${authCode}...`);

      if (!authCode || !brandName) {
        return { success: false, message: 'Missing required parameters: code or brand' };
      }

      // 验证品牌名是否支持
      const supportedBrands = ['xiaomi', 'midea'];
      if (!supportedBrands.includes(brandName)) {
        return { success: false, message: `Brand '${brandName}' is not configured` };
      }

      // 特殊处理：admin调试账户或调试授权码
      if (this.currentUser && this.currentUser.getUserId() === 'admin' || authCode.startsWith('debug-auth-')) {
        console.log('Admin debug account, simulating successful binding');

        // 更新本地绑定状态
        await this.updateLocalBindingStatus(brandName, true);

        return {
          success: true,
          message: `${brandName} brand bound successfully (debug mode)`
        };
      }

      // 正常用户：使用统一的API调用方式
      const result = await this.apiRegistry.bindWithAuthorizationCode({
        code: authCode,
        brand: brandName
      });

      if (result.status === 'success') {
        console.log(`${brandName} brand bound successfully`);

        // 更新本地绑定状态
        await this.updateLocalBindingStatus(brandName, true);

        return {
          success: true,
          message: result.message || 'Code exchanged successfully'
        };
      } else {
        return {
          success: false,
          message: result.message || 'Authorization code exchange failed'
        };
      }
    } catch (error) {
      console.error('Failed to bind third-party account:', error);
      return {
        success: false,
        message: `Binding failed: ${error.message}`
      };
    }
  }

  /**
   * 完整的第三方品牌授权流程 - 两步骤：获取授权码 → 绑定账号
   * @param {string} brandName - 品牌名称
   * @returns {Promise<Object>} 授权结果，包含进度回调
   */
  async performThirdPartyAuthorization(brandName, progressCallback) {
    try {
      console.log(`Starting authorization process for brand ${brandName}...`);

      if (!this.currentUser) {
        return { success: false, message: 'User not logged in' };
      }

      const userId = this.currentUser.getUserId();

      // 进度回调：开始授权
      if (progressCallback) {
        progressCallback({
          step: 'start',
          progress: 0,
          message: 'Starting authorization process...'
        });
      }

      // 第一步：获取授权码
      if (progressCallback) {
        progressCallback({
          step: 'getAuthCode',
          progress: 25,
          message: 'Getting authorization code...'
        });
      }

      const authCodeResult = await this.getAuthorizationCode(userId, brandName);
      if (!authCodeResult.success) {
        return authCodeResult;
      }

      // 第二步：使用授权码绑定
      if (progressCallback) {
        progressCallback({
          step: 'binding',
          progress: 75,
          message: 'Binding account...'
        });
      }

      const bindResult = await this.bindWithAuthorizationCode(authCodeResult.authorizationCode, brandName);

      if (bindResult.success) {
        // 进度回调：完成
        if (progressCallback) {
          progressCallback({
            step: 'complete',
            progress: 100,
            message: 'Authorization complete'
          });
        }
      }

      return bindResult;
    } catch (error) {
      console.error('Third-party brand authorization process error:', error);
      return {
        success: false,
        message: `Authorization failed: ${error.message}`
      };
    }
  }

  /**
   * 更新本地绑定状态
   * @param {string} brandName - 品牌名称
   * @param {boolean} isBound - 是否已绑定
   */
  async updateLocalBindingStatus(brandName, isBound) {
    try {
      if (!this.supportedBrands[brandName]) {
        this.supportedBrands[brandName] = {
          brandName: brandName,
          isBound: isBound,
          isExpired: !isBound
        };
      } else {
        this.supportedBrands[brandName].isBound = isBound;
        this.supportedBrands[brandName].isExpired = !isBound;
      }

      // 保存到本地存储
      this.dataStorage.saveSupportedBrands(this.supportedBrands);

      console.log(`Local binding status for brand ${brandName} has been updated to: ${isBound ? 'bound' : 'unbound'}`);
    } catch (error) {
      console.error('Failed to update local binding status:', error);
      throw error;
    }
  }

  // 刷新访问令牌
  async refreshAccessToken() {
    try {
      const refreshToken = this.dataStorage.getRefreshToken();
      if (!refreshToken) {
        return { success: false, message: 'No refresh token available' };
      }

      const response = await this.apiRegistry.refreshAccessToken(refreshToken);
      return response;
    } catch (error) {
      console.error('Error refreshing token:', error);
      return { success: false, message: error.message || 'Failed to refresh token' };
    }
  }

  // 检查用户是否已登录
  isLoggedIn() {
    return !!this.currentUser && this.dataStorage.hasValidSession();
  }

  // 获取当前用户
  getCurrentUser() {
    return this.currentUser;
  }

  // 获取应用设置
  getAppSettings() {
    return this.dataStorage.getAppSettings();
  }

  // 更新应用设置
  updateAppSettings(settings) {
    const currentSettings = this.dataStorage.getAppSettings();
    const newSettings = { ...currentSettings, ...settings };
    this.dataStorage.saveAppSettings(newSettings);
    return newSettings;
  }

  // 登出
  async logout() {
    try {
      console.log('🔥 [LOGOUT DEBUG] =================================');
      console.log('🔥 [LOGOUT DEBUG] Starting user logout process...');
      console.log('🔥 [LOGOUT DEBUG] Current user:', this.currentUser ? this.currentUser.getUserId() : 'No user');
      console.log('🔥 [LOGOUT DEBUG] Storage directory:', this.dataStorage ? this.dataStorage.getStorageDirectory() : 'No storage');
      console.log('🔥 [LOGOUT DEBUG] =================================');

      // 通知服务端关闭SSE连接
      try {
        console.log('🔥 [LOGOUT DEBUG] Step 1: Notifying SSE exit...');
        await this.deviceSSEManager.notifyExit(this.apiRegistry);
        console.log('🔥 [LOGOUT DEBUG] ✅ SSE exit notification sent');
      } catch (error) {
        console.error('🔥 [LOGOUT DEBUG] ❌ Failed to send SSE exit notification:', error);
      }

      // 断开SSE连接
      console.log('🔥 [LOGOUT DEBUG] Step 2: Disconnecting SSE...');
      this.deviceSSEManager.disconnect();
      console.log('🔥 [LOGOUT DEBUG] ✅ SSE disconnected');

      // 清理和重置设备管理组件
      console.log('🔥 [LOGOUT DEBUG] Step 3: Clearing and resetting device managers...');

      // 清理设备存储管理器数据
      if (this.deviceStorageManager) {
        console.log('🔥 [LOGOUT DEBUG] Clearing device storage data...');
        const deviceClearResult = this.deviceStorageManager.clearAllDevices();
        console.log('🔥 [LOGOUT DEBUG] Device storage clear result:', deviceClearResult);
      }

      // 清理分组API管理器数据
      if (this.deviceGroupAPIManager) {
        console.log('🔥 [LOGOUT DEBUG] Clearing device groups and sensor history...');
        this.deviceGroupAPIManager.clearLocalGroups();
        this.deviceGroupAPIManager.clearAllSensorHistory();
        console.log('🔥 [LOGOUT DEBUG] ✅ Device groups and sensor history cleared');
      }

      // 重置设备管理组件
      console.log('🔥 [LOGOUT DEBUG] Resetting device managers...');
      this.deviceSSEManager.reset();
      this.deviceStorageManager.reset();
      this.deviceGroupAPIManager.reset();
      this.deviceControlManager.reset();
      console.log('🔥 [LOGOUT DEBUG] ✅ Device managers cleared and reset');

      // 清理当前用户信息
      console.log('🔥 [LOGOUT DEBUG] Step 4: Clearing user state...');
      this.currentUser = null;
      this.supportedBrands = {};
      this.isInitialized = false;
      console.log('🔥 [LOGOUT DEBUG] ✅ User state cleared');

      // ===== 彻底清理所有本地存储文件 =====
      console.log('🔥 [LOGOUT DEBUG] Step 5: Starting complete storage cleanup...');
      console.log('🔥 [LOGOUT DEBUG] Storage object exists:', !!this.dataStorage);

      if (!this.dataStorage) {
        console.error('🔥 [LOGOUT DEBUG] ❌ CRITICAL: dataStorage is not available!');
        return {
          success: false,
          message: 'Storage system not available for cleanup',
          error: 'dataStorage is null or undefined'
        };
      }

      // 首先检查存储目录的当前状态
      console.log('🔥 [LOGOUT DEBUG] Checking current storage status before cleanup...');
      const preCleanupStats = this.dataStorage.getStorageStats();
      console.log('🔥 [LOGOUT DEBUG] Pre-cleanup storage stats:', preCleanupStats);

      // 获取实际的存储目录路径
      const storageDir = this.dataStorage.getStorageDirectory();
      console.log('🔥 [LOGOUT DEBUG] Actual storage directory path:', storageDir);

      // 检查目录是否存在
      const fs = require('fs');
      const dirExists = fs.existsSync(storageDir);
      console.log('🔥 [LOGOUT DEBUG] Storage directory exists:', dirExists);

      if (dirExists) {
        try {
          const files = fs.readdirSync(storageDir);
          console.log('🔥 [LOGOUT DEBUG] Files in storage directory:', files);
          console.log('🔥 [LOGOUT DEBUG] Total files found:', files.length);
        } catch (error) {
          console.error('🔥 [LOGOUT DEBUG] ❌ Failed to read storage directory:', error);
        }
      }

      // 1. 使用UnifiedStorage彻底清理所有数据文件和目录
      console.log('🔥 [LOGOUT DEBUG] Calling clearAllDataCompletely...');
      const clearResult = this.dataStorage.clearAllDataCompletely();
      console.log('🔥 [LOGOUT DEBUG] clearAllDataCompletely result:', clearResult);

      if (clearResult.success) {
        console.log(`🔥 [LOGOUT DEBUG] ✅ Local storage directory cleaned up successfully: deleted ${clearResult.deletedFiles} files/directories`);
        if (clearResult.failedFiles > 0) {
          console.warn(`🔥 [LOGOUT DEBUG] ⚠️ ${clearResult.failedFiles} files failed to delete`);
          console.warn('🔥 [LOGOUT DEBUG] Failed files details:', clearResult.details);
        }
      } else {
        console.error('🔥 [LOGOUT DEBUG] ❌ Failed to clean up local storage directory:', clearResult.message);
        console.error('🔥 [LOGOUT DEBUG] Cleanup error details:', clearResult);
      }

      // 验证清理结果
      console.log('🔥 [LOGOUT DEBUG] Step 6: Verifying cleanup results...');
      if (dirExists) {
        try {
          const postCleanupFiles = fs.readdirSync(storageDir);
          console.log('🔥 [LOGOUT DEBUG] Files remaining after cleanup:', postCleanupFiles);
          console.log('🔥 [LOGOUT DEBUG] Remaining files count:', postCleanupFiles.length);
        } catch (error) {
          console.log('🔥 [LOGOUT DEBUG] ✅ Storage directory no longer exists (expected)');
        }
      }

      // 2. 清理会话存储
      console.log('🔥 [LOGOUT DEBUG] Step 7: Clearing session storage...');
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.clear();
        console.log('🔥 [LOGOUT DEBUG] ✅ Session storage cleared');
      } else {
        console.log('🔥 [LOGOUT DEBUG] ⚠️ sessionStorage not available in this context');
      }

      // 3. 清理浏览器本地存储中的用户相关数据
      console.log('🔥 [LOGOUT DEBUG] Step 8: Clearing local storage...');
      if (typeof localStorage !== 'undefined') {
        const keysToRemove = [
          'userToken',
          'currentUser',
          'userBindings',
          'deviceData',
          'rememberMe',
          'bindingBrand',
          'lastLoginTime',
          'autoLogin',
          'sseConnectionId'
        ];

        keysToRemove.forEach(key => {
          localStorage.removeItem(key);
          console.log(`🔥 [LOGOUT DEBUG] Removed localStorage key: ${key}`);
        });
        console.log('🔥 [LOGOUT DEBUG] ✅ Browser local storage cleared');
      } else {
        console.log('🔥 [LOGOUT DEBUG] ⚠️ localStorage not available in this context');
      }

      // 4. 获取存储统计信息来验证清理结果
      console.log('🔥 [LOGOUT DEBUG] Step 9: Final verification...');
      const stats = this.dataStorage.getStorageStats();
      console.log('🔥 [LOGOUT DEBUG] Final storage stats:', stats);

      if (stats.totalFiles === 0) {
        console.log('🔥 [LOGOUT DEBUG] ✅ All local files have been successfully deleted');
      } else {
        console.warn(`🔥 [LOGOUT DEBUG] ⚠️ ${stats.totalFiles} files were not deleted, total size: ${stats.totalSize} bytes`);
        console.warn('🔥 [LOGOUT DEBUG] Remaining file statistics:', stats.categories);
      }

      console.log('🔥 [LOGOUT DEBUG] =================================');
      console.log('🔥 [LOGOUT DEBUG] User logout complete, all data cleared');
      console.log('🔥 [LOGOUT DEBUG] =================================');

      // 重新初始化存储结构，为下次登录做准备
      console.log('🔄 [LOGOUT DEBUG] Step 10: Reinitializing storage structure for future logins...');
      const reinitResult = this.dataStorage.reinitializeAfterCleanup();
      console.log('🔄 [LOGOUT DEBUG] Storage reinitialization result:', reinitResult);

      return {
        success: true,
        message: `Logout successful, deleted ${clearResult.deletedFiles} local files/directories`,
        filesDeleted: clearResult.deletedFiles,
        filesFailed: clearResult.failedFiles,
        filesRemaining: stats.totalFiles,
        clearDetails: clearResult,
        reinitResult: reinitResult,
        storageDirectory: storageDir,
        preCleanupStats: preCleanupStats,
        postCleanupStats: stats
      };
    } catch (error) {
      console.error('🔥 [LOGOUT DEBUG] ❌ An error occurred during logout:', error);
      console.error('🔥 [LOGOUT DEBUG] Error stack:', error.stack);
      return {
        success: false,
        message: `Logout failed: ${error.message}`,
        error: error.message,
        stack: error.stack
      };
    }
  }

  // 完全重置（用于测试或清理）
  reset() {
    this.logout();
    // 清除所有本地存储
    localStorage.clear();
    return { success: true, message: 'Reset successful' };
  }

  // 获取存储目录状态（用于调试和验证）
  getStorageStatus() {
    try {
      const stats = this.dataStorage.getStorageStats();
      const storageDir = this.dataStorage.storageDir;

      return {
        success: true,
        storageDirectory: storageDir,
        totalFiles: stats.totalFiles,
        totalSize: stats.totalSize,
        categories: stats.categories,
        isEmpty: stats.totalFiles === 0,
        message: stats.totalFiles === 0 ? 'Storage directory is empty' : `Storage directory contains ${stats.totalFiles} files`
      };
    } catch (error) {
      console.error('Failed to get storage status:', error);
      return {
        success: false,
        message: `Failed to get storage status: ${error.message}`,
        error: error.message
      };
    }
  }

  // 手动彻底清理存储目录（危险操作，仅用于调试）
  forceCompleteCleanup() {
    try {
      console.log('⚠️ Executing forced complete cleanup operation...');

      // 清理内存状态
      this.currentUser = null;
      this.supportedBrands = {};
      this.isInitialized = false;

      // 彻底清理存储目录
      const clearResult = this.dataStorage.clearAllDataCompletely();

      // 清理所有浏览器存储
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.clear();
      }
      if (typeof localStorage !== 'undefined') {
        localStorage.clear();
      }

      console.log('Forced complete cleanup operation finished');

      return {
        success: true,
        message: `Forced cleanup complete, deleted ${clearResult.deletedFiles} files/directories`,
        clearResult: clearResult
      };
    } catch (error) {
      console.error('Forced cleanup failed:', error);
      return {
        success: false,
        message: `Forced cleanup failed: ${error.message}`,
        error: error.message
      };
    }
  }

  // 初始化设备管理功能
  async initializeDeviceManagement(userId) {
    try {
      console.log('🔧 [Debug] Initializing device management features for user ID:', userId);
      console.log('🔧 [Debug] User ID type:', typeof userId);
      console.log('🔧 [Debug] User ID === "admin":', userId === 'admin');

      // 检查是否为admin账户 - 启用离线模式
      if (userId === 'admin') {
        console.log('🟡 [Offline Debug] Detected admin account, enabling offline device management mode');

        // 1. 初始化设备存储管理器
        const storageResult = await this.deviceStorageManager.initialize();
        if (!storageResult.success) {
          console.error('❌ [Offline Debug] Device storage manager initialization failed:', storageResult.message);
          return { success: false, message: 'Device storage initialization failed' };
        }

        // 2. 初始化分组API管理器并启用离线模式
        const groupResult = await this.deviceGroupAPIManager.initialize();
        if (!groupResult.success) {
          console.error('❌ [Offline Debug] Group API manager initialization failed:', groupResult.message);
          return { success: false, message: 'Group management initialization failed' };
        }

        // 启用分组管理器的离线模式
        this.deviceGroupAPIManager.enableOfflineMode();
        console.log('🟡 [Offline Debug] Group API manager offline mode enabled');

        // 3.5. 初始化设备控制管理器并启用离线模式
        const controlResult = await this.deviceControlManager.initialize();
        if (!controlResult.success) {
          console.error('❌ [Offline Debug] Device control manager initialization failed:', controlResult.message);
          return { success: false, message: 'Device control initialization failed' };
        }

        // 确保设备控制管理器有正确的设备存储管理器引用
        this.deviceControlManager.setDeviceStorageManager(this.deviceStorageManager);
        this.deviceControlManager.setApiRegistry(this.apiRegistry);
        console.log('🔧 [Debug] Device control manager initialized and references set');

        // 启用设备控制管理器的离线模式
        this.deviceControlManager.enableOfflineMode();
        console.log('🟡 [Offline Debug] Device control manager initialized and offline mode enabled');

        // 3.6. 初始化场景存储管理器
        const sceneStorageResult = await this.sceneStorageManager.initialize();
        if (!sceneStorageResult.success) {
          console.error('❌ [Offline Debug] Scene storage manager initialization failed:', sceneStorageResult.message);
          return { success: false, message: 'Scene storage initialization failed' };
        }
        console.log('🟡 [Offline Debug] Scene storage manager initialized');

        // 3.7. 初始化场景管理器并启用离线模式
        const sceneResult = await this.sceneManager.initialize();
        if (!sceneResult.success) {
          console.error('❌ [Offline Debug] Scene manager initialization failed:', sceneResult.message);
          return { success: false, message: 'Scene management initialization failed' };
        }

        // 启用场景管理器的离线模式
        this.sceneManager.enableOfflineMode();
        console.log('🟡 [Offline Debug] Scene manager initialized and offline mode enabled');

        // 3. 跳过设备状态获取和SSE连接
        console.log('🟡 [Offline Debug] Skipping device status retrieval and SSE connection');

        // 4. 初始化数据分析器（离线模式）
        this.sensorDataAnalyzer.setServices(this.apiRegistry, this.deviceStorageManager, this.deviceGroupAPIManager);
        console.log('🟡 [Offline Debug] Data analyzer initialized with GroupAPIManager (offline mode)');

        console.log('✅ [Offline Debug] Admin account device management features initialized successfully');
        return {
          success: true,
          message: 'Device management features initialized successfully (offline mode)',
          offlineMode: true,
          details: {
            storage: storageResult,
            groups: groupResult,
            sse: { success: false, message: 'SSE connection skipped for admin account' }
          }
        };
      }

      // 非admin账户的正常初始化流程
      console.log('🔧 [Debug] Normal user, executing full initialization process');

      // 1. 初始化设备存储管理器
      const storageResult = await this.deviceStorageManager.initialize();
      if (!storageResult.success) {
        console.error('❌ [Debug] Device storage manager initialization failed:', storageResult.message);
        return { success: false, message: 'Device storage initialization failed' };
      }

      // 2. (顺序调整) 初始化分组管理器，确保在处理设备前加载好分组信息
      try {
        await this.deviceGroupAPIManager.initialize();
      } catch (error) {
        console.error('❌ [Debug] Group API manager initialization failed:', error);
        return { success: false, message: 'Group management initialization failed' };
      }

      // 2.5. 初始化设备控制管理器
      const controlResult = await this.deviceControlManager.initialize();
      if (!controlResult.success) {
        console.error('❌ [Debug] Device control manager initialization failed:', controlResult.message);
        return { success: false, message: 'Device control initialization failed' };
      }

      // 确保设备控制管理器有正确的设备存储管理器引用
      this.deviceControlManager.setDeviceStorageManager(this.deviceStorageManager);
      this.deviceControlManager.setApiRegistry(this.apiRegistry);
      console.log('🔧 [Debug] Device control manager initialized and references set');

      // 2.6. 初始化场景存储管理器
      const sceneStorageResult = await this.sceneStorageManager.initialize();
      if (!sceneStorageResult.success) {
        console.error('❌ [Debug] Scene storage manager initialization failed:', sceneStorageResult.message);
        return { success: false, message: 'Scene storage initialization failed' };
      }
      console.log('🔧 [Debug] Scene storage manager initialized');

      // 2.7. 初始化场景管理器
      const sceneResult = await this.sceneManager.initialize();
      if (!sceneResult.success) {
        console.error('❌ [Debug] Scene manager initialization failed:', sceneResult.message);
        return { success: false, message: 'Scene management initialization failed' };
      }
      console.log('🔧 [Debug] Scene manager initialized');

      // 3. 获取设备列表和状态
      // Step 3a: Get device list
      console.log('🔧 [Debug] Getting device list...');
      const deviceListResponse = await this.apiRegistry.getDeviceList();
      if (deviceListResponse && deviceListResponse.code === 200 && deviceListResponse.data && deviceListResponse.data.devices) {
          const storeResult = this.deviceStorageManager.storeAllDevices(deviceListResponse.data.devices);
          if (storeResult.success) {
              console.log(`✅ [Debug] Successfully retrieved and stored ${deviceListResponse.data.devices.length} device basic info`);
          } else {
              console.error('❌ [Debug] Failed to store device list:', storeResult.message);
          }
      } else {
          console.warn('⚠️ [Debug] Failed to get device list or data is empty:', deviceListResponse?.message);
      }

      // Step 3b: Get device status
      console.log('🔧 [Debug] Getting device status...');
      const devicesStatusResponse = await this.apiRegistry.callAPIGet('getDevicesStatus');
      if (devicesStatusResponse && devicesStatusResponse.code === 200 && devicesStatusResponse.data && devicesStatusResponse.data.devices) {
          // 再次调用 storeAllDevices 会合并状态信息
          const storeResult = this.deviceStorageManager.storeAllDevices(devicesStatusResponse.data.devices);
          if (storeResult.success) {
              console.log(`✅ [Debug] Successfully retrieved and updated status for ${devicesStatusResponse.data.devices.length} devices`);
          } else {
              console.error('❌ [Debug] Failed to update device status:', storeResult.message);
          }
      } else {
          console.warn('⚠️ [Debug] Failed to get device status or data is empty:', devicesStatusResponse?.message);
      }

      // 4. (新增逻辑) 处理未分组的设备，将它们归入默认分组
      this.deviceGroupAPIManager.assignUngroupedDevices();

      // 5. 初始化SSE管理器
      const sseInitResult = await this.deviceSSEManager.initialize(userId, this.deviceStorageManager, this.deviceGroupAPIManager);
      if (!sseInitResult.success) {
        console.error('❌ [Debug] SSE manager initialization failed:', sseInitResult.message);
        return { success: false, message: 'SSE initialization failed' };
      }

      // 6. 初始化数据分析器
      this.sensorDataAnalyzer.setServices(this.apiRegistry, this.deviceStorageManager, this.deviceGroupAPIManager);

      // 7. 建立SSE连接
      const sseConnectResult = await this.deviceSSEManager.connect();
      if (sseConnectResult.success) {
        console.log('✅ [Debug] SSE connection established successfully');
      } else {
        console.error('❌ [Debug] SSE connection failed:', sseConnectResult.message);
        // SSE连接失败不影响整体初始化，只记录警告
      }

      console.log('✅ [Debug] Device management features initialized successfully');
      return {
        success: true,
        message: 'Device management features initialized successfully',
        details: {
          storage: storageResult,
          groups: this.deviceGroupAPIManager,
          sse: sseConnectResult
        }
      };
    } catch (error) {
      console.error('❌ [Debug] Device management features initialization failed:', error);
      return { success: false, message: 'Device management initialization failed: ' + error.message };
    }
  }

  // 获取设备管理相关组件（供外部访问）
  getDeviceManagers() {
    return {
      sseManager: this.deviceSSEManager,
      storageManager: this.deviceStorageManager,
      groupAPIManager: this.deviceGroupAPIManager,
      controlManager: this.deviceControlManager,
      sceneManager: this.sceneManager,
      sceneStorageManager: this.sceneStorageManager,
      dataAnalyzer: this.sensorDataAnalyzer,
      deviceAPIManager: this.deviceStorageManager // 使用storageManager作为deviceAPIManager
    };
  }
}

module.exports = AccountManager;


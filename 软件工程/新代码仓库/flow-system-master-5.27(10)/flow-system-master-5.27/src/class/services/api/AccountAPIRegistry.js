const axios = require('axios');

class AccountAPIRegistry {
  constructor(storage = null) {
    // API端点配置 - 根据接口文档更新
    this.apiConfig = {
      baseURL: 'http://192.168.99.56:3000', // 根据接口文档更新服务器地址
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    // API路径映射 - 根据接口文档更新
    this.apiPaths = {
      login: '/auth/login',
      register: '/auth/register',
      bindThirdParty: '/auth/code',
      unbindThirdParty: '/auth/unbind',
      getBindings: '/auth/bindings',
      refreshToken: '/auth/refresh-jwt',
      getAuthorizationCode: '/mockapi/auth/getAuthorizationCode', // 第三方授权码获取API
      bindWithAuthCode: '/auth/code', // 使用授权码绑定API
      // 设备相关API
      getDevicesStatus: '/devices/status',
      controlDevice: '/devices/control',
      getDeviceList: '/devices/getList',
      // 分组相关API
      createGroup: '/devices/createGroup',
      setGroup: '/devices/setGroup',
      deleteGroup: '/devices/deleteGroup',
      getGroups: '/devices/groups',
      // 传感器历史数据API
      getSensorHistory: '/api/sensor-data/last24h',
      getSensorData: '/api/sensor-data/device',
      // 场景相关API
      createScene: '/api/scenes',
      deleteScene: '/api/scenes',
      getScenes: '/api/scenes',
      getSceneDetail: '/api/scenes',
      updateScene: '/api/scenes',
      executeScene: '/api/scenes',
      // SSE相关API
      sseEvents: '/events',
      sseExit: '/api/sse/exit'
    };

    // 存储实例，用于获取token
    this.storage = storage;

    // 创建axios实例
    this.client = axios.create(this.apiConfig);

    // 添加请求拦截器
    this.client.interceptors.request.use(config => {
      // 从存储获取token
      if (this.storage) {
        const token = this.storage.getToken();
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
      }
      return config;
    }, error => {
      return Promise.reject(error);
    });

    // 添加响应拦截器处理token过期
    this.client.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401 && this.storage) {
          // token过期，尝试刷新
          const refreshToken = this.storage.getRefreshToken();
          if (refreshToken) {
            try {
              const refreshResponse = await this.refreshAccessToken(refreshToken);
              if (refreshResponse.success) {
                // 重新发送原请求
                error.config.headers['Authorization'] = `Bearer ${refreshResponse.data.token}`;
                return this.client.request(error.config);
              }
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError);
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // 设置存储实例
  setStorage(storage) {
    this.storage = storage;
  }

  // 调用API
  async callAPI(apiName, data) {
    if (!this.apiPaths[apiName]) {
      throw new Error(`Unknown API: ${apiName}`);
    }

    try {
      const response = await this.client.post(this.apiPaths[apiName], data);
      return response.data;
    } catch (error) {
      console.error(`API call error (${apiName}):`, error);

      // 处理错误响应
      if (error.response) {
        // 服务器返回了错误响应
        return {
          success: false,
          message: error.response.data.message || `${apiName} request failed`,
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        // 请求已发送但没有收到响应
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        // 请求设置时发生错误
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // GET请求方法
  async callAPIGet(apiName, params = {}) {
    if (!this.apiPaths[apiName]) {
      throw new Error(`Unknown API: ${apiName}`);
    }

    try {
      const response = await this.client.get(this.apiPaths[apiName], { params });
      return response.data;
    } catch (error) {
      console.error(`API call error (${apiName}):`, error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || `${apiName} request failed`,
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 刷新访问令牌
  async refreshAccessToken(refreshToken) {
    try {
      const response = await this.client.post(this.apiPaths.refreshToken, {
        refreshToken: refreshToken
      });

      if (response.data.status === 'success') {
        // 保存新的token
        if (this.storage) {
          this.storage.saveToken(response.data.data.token);
        }
        return {
          success: true,
          data: response.data.data
        };
      } else {
        return {
          success: false,
          message: response.data.message
        };
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
      return {
        success: false,
        message: 'Failed to refresh token'
      };
    }
  }

  // 配置API端点
  configureAPI(apiName, path) {
    if (!apiName || !path) return false;
    this.apiPaths[apiName] = path;
    return true;
  }

  // 设置基础URL
  setBaseURL(url) {
    if (!url) return false;
    this.apiConfig.baseURL = url;
    this.client = axios.create(this.apiConfig);
    return true;
  }

  // 获取基础URL
  getBaseURL() {
    return this.apiConfig.baseURL;
  }

  // 特殊方法：获取授权码 - 使用相对路径，不带基础URL
  async getAuthorizationCode(data) {
    try {
      const response = await this.client.post('/mockapi/auth/getAuthorizationCode', data, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
      return response.data;
    } catch (error) {
      console.error('Error calling get authorization code API:', error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Failed to get authorization code',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 特殊方法：使用授权码绑定 - 需要token认证
  async bindWithAuthorizationCode(data) {
    try {
      // 获取token
      const token = this.storage ? this.storage.getToken() : null;
      if (!token) {
        return {
          success: false,
          message: 'User not logged in, please log in first'
        };
      }

      const response = await this.client.post(this.apiPaths.bindWithAuthCode, data);
      return response.data;
    } catch (error) {
      console.error('Error binding with authorization code:', error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Failed to bind with authorization code',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 新增方法：获取设备列表
  async getDeviceList() {
    return this.callAPIGet('getDeviceList');
  }

  // 场景相关API方法

  // 创建场景
  async createScene(data) {
    return this.callAPI('createScene', data);
  }

  // 删除场景
  async deleteScene(sceneId) {
    try {
      const response = await this.client.delete(`${this.apiPaths.deleteScene}/${sceneId}`);
      return response.data;
    } catch (error) {
      console.error(`API call error (deleteScene):`, error);
      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Delete scene request failed',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 获取场景列表
  async getScenes() {
    return this.callAPIGet('getScenes');
  }

  // 获取场景详情
  async getSceneDetail(sceneId) {
    try {
      const response = await this.client.get(`${this.apiPaths.getSceneDetail}/${sceneId}`);
      return response.data;
    } catch (error) {
      console.error(`API call error (getSceneDetail):`, error);
      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Get scene detail request failed',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 更新场景
  async updateScene(sceneId, data) {
    try {
      console.log('[SCENE_UPDATE_API] Preparing to send scene update request to server');
      console.log('[SCENE_UPDATE_API] HTTP Method: PATCH');
      console.log('[SCENE_UPDATE_API] Request URL:', `${this.apiPaths.updateScene}/${sceneId}`);
      console.log('[SCENE_UPDATE_API] Full Server URL:', `${this.apiConfig.baseURL}${this.apiPaths.updateScene}/${sceneId}`);
      console.log('[SCENE_UPDATE_API] Target Scene ID:', sceneId);
      console.log('[SCENE_UPDATE_API] MESSAGE TO SERVER RAW:');
      console.log('[SCENE_UPDATE_API]', data);
      console.log('[SCENE_UPDATE_API] MESSAGE TO SERVER JSON:');
      console.log('[SCENE_UPDATE_API]', JSON.stringify(data, null, 2));

      // Check authentication token
      const token = this.storage ? this.storage.getToken() : null;
      console.log('[SCENE_UPDATE_API] Authentication token available:', !!token);
      if (token) {
        console.log('[SCENE_UPDATE_API] Token preview:', token.substring(0, 20) + '...');
      }

      console.log('[SCENE_UPDATE_API] Sending request to server...');
      const response = await this.client.patch(`${this.apiPaths.updateScene}/${sceneId}`, data);

      console.log('[SCENE_UPDATE_API] Scene update request successful');
      console.log('[SCENE_UPDATE_API] Server response status:', response.status);
      console.log('[SCENE_UPDATE_API] MESSAGE FROM SERVER:');
      console.log('[SCENE_UPDATE_API]', response.data);
      console.log('[SCENE_UPDATE_API] Server response headers:', response.headers);

      return response.data;
    } catch (error) {
      console.error('[SCENE_UPDATE_API] Scene update request failed');
      console.error('[SCENE_UPDATE_API] Error type:', error.name);
      console.error('[SCENE_UPDATE_API] Error message:', error.message);
      console.error('[SCENE_UPDATE_API] Server response status:', error.response?.status);
      console.error('[SCENE_UPDATE_API] Server response status text:', error.response?.statusText);
      console.error('[SCENE_UPDATE_API] ERROR MESSAGE FROM SERVER:');
      console.error('[SCENE_UPDATE_API]', error.response?.data);
      console.error('[SCENE_UPDATE_API] Server response headers:', error.response?.headers);
      console.error('[SCENE_UPDATE_API] Request config:', {
        method: error.config?.method,
        url: error.config?.url,
        data: error.config?.data,
        headers: error.config?.headers
      });
      console.error('[SCENE_UPDATE_API] Full error details:', error);
      throw new Error('Update scene request failed');
    }
  }

  // 执行场景
  async executeScene(sceneId) {
    try {
      const response = await this.client.post(`${this.apiPaths.executeScene}/${sceneId}/execute`);
      return response.data;
    } catch (error) {
      console.error(`API call error (executeScene):`, error);
      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Execute scene request failed',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // 设备控制
  async controlDevice(data) {
    try {
      console.log('🔗 [API] Preparing to send device control request');
      console.log('🔗 [API] Request method: POST');
      console.log('🔗 [API] Request URL:', this.apiPaths.controlDevice);
      console.log('🔗 [API] Full URL:', `${this.apiConfig.baseURL}${this.apiPaths.controlDevice}`);
      console.log('🔗 [API] Request data (raw):', data);
      console.log('🔗 [API] Request data (JSON string):', JSON.stringify(data, null, 2));

      // Check token
      const token = this.storage ? this.storage.getToken() : null;
      console.log('🔗 [API] Auth token exists:', !!token);
      if (token) {
        console.log('🔗 [API] Token prefix:', token.substring(0, 20) + '...');
      }

      const response = await this.client.post(this.apiPaths.controlDevice, data);

      console.log('🔗 [API] Device control request successful');
      console.log('🔗 [API] Response status:', response.status);
      console.log('🔗 [API] Response data:', response.data);

      return response.data;
    } catch (error) {
      console.error('❌ [API] Device control request failed');
      console.error('❌ [API] Error message:', error.message);
      console.error('❌ [API] Error status:', error.response?.status);
      console.error('❌ [API] Error response headers:', error.response?.headers);
      console.error('❌ [API] Error response data:', error.response?.data);
      console.error('❌ [API] Full error object:', error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Device control request failed',
          status: error.response.status,
          errors: error.response.data.errors,
          code: error.response.status
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'Server not responding',
          code: 500
        };
      } else {
        return {
          success: false,
          message: error.message,
          code: 500
        };
      }
    }
  }
}

module.exports = AccountAPIRegistry;

const axios = require('axios');

class AccountAPIRegistry {
  constructor(storage = null) {
    // API endpoint configuration - updated according to the API documentation
    this.apiConfig = {
      baseURL: 'http://192.168.58.56:3000', // Update server address according to the API documentation
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    // API path mapping - updated according to the API documentation
    this.apiPaths = {
      login: '/auth/login',
      register: '/auth/register',
      bindThirdParty: '/auth/code',
      unbindThirdParty: '/auth/unbind',
      getBindings: '/auth/bindings',
      refreshToken: '/auth/refresh-jwt',
      getAuthorizationCode: '/mockapi/auth/getAuthorizationCode', // Third-party authorization code acquisition API
      bindWithAuthCode: '/auth/code', // API for binding with authorization code
      // Device-related APIs
      getDevicesStatus: '/devices/status',
      controlDevice: '/device/control',
      getDeviceList: '/devices/getList',
      // Group-related APIs
      createGroup: '/devices/createGroup',
      setGroup: '/devices/setGroup',
      deleteGroup: '/devices/deleteGroup',
      getGroups: '/devices/groups',
      // Sensor history data API
      getSensorHistory: '/api/sensor-data/last24h',
      getSensorData: '/api/sensor-data/device',
      // SSE-related APIs
      sseEvents: '/events',
      sseExit: '/api/sse/exit'
    };

    // Storage instance for getting tokens
    this.storage = storage;

    // Create axios instance
    this.client = axios.create(this.apiConfig);

    // Add request interceptor
    this.client.interceptors.request.use(config => {
      // Get token from storage
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

    // Add response interceptor to handle token expiration
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

  // Set storage instance
  setStorage(storage) {
    this.storage = storage;
  }

  // Call API
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
          message: 'No response from server'
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

  // GET request method
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
          message: 'No response from server'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // Refresh access token
  async refreshAccessToken(refreshToken) {
    try {
      const response = await this.client.post(this.apiPaths.refreshToken, {
        refreshToken: refreshToken
      });

      if (response.data.status === 'success') {
        // Save the new token
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
      console.error('Token refresh failed:', error);
      return {
        success: false,
        message: 'Token refresh failed'
      };
    }
  }

  // Configure API endpoint
  configureAPI(apiName, path) {
    if (!apiName || !path) return false;
    this.apiPaths[apiName] = path;
    return true;
  }

  // Set base URL
  setBaseURL(url) {
    if (!url) return false;
    this.apiConfig.baseURL = url;
    this.client = axios.create(this.apiConfig);
    return true;
  }

  // Special method: Get authorization code - uses relative path, without base URL
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
      console.error('Get authorization code API call error:', error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Get authorization code request failed',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'No response from server'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // Special method: Bind with authorization code - requires token authentication
  async bindWithAuthorizationCode(data) {
    try {
      // Get token
      const token = this.storage ? this.storage.getToken() : null;
      if (!token) {
        return {
          success: false,
          message: '用户未登录，请先登录'
        };
      }

      const response = await this.client.post(this.apiPaths.bindWithAuthCode, data);
      return response.data;
    } catch (error) {
      console.error('Bind with authorization code API call error:', error);

      if (error.response) {
        return {
          success: false,
          message: error.response.data.message || 'Bind with authorization code request failed',
          status: error.response.status,
          errors: error.response.data.errors
        };
      } else if (error.request) {
        return {
          success: false,
          message: 'No response from server'
        };
      } else {
        return {
          success: false,
          message: error.message
        };
      }
    }
  }

  // New method: Get device list
  async getDeviceList() {
    return this.callAPIGet('getDeviceList');
  }
}

module.exports = AccountAPIRegistry;

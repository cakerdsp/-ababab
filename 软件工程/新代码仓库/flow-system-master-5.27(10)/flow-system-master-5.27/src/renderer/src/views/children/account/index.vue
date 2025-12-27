<template>
  <div class="user-info-container">
    <!-- 用户基本信息 -->
    <div class="user-basic-info">
      <div class="user-header">
        <h2>用户信息</h2>
      </div>
      <div class="user-details">
        <div class="detail-item">
          <span class="label">用户ID：</span>
          <span class="value">{{ userInfo.userId || '未登录' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">登录状态：</span>
          <span class="value" :class="userInfo.isLoggedIn ? 'status-online' : 'status-offline'">
            {{ userInfo.isLoggedIn ? '已登录' : '未登录' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 设备绑定管理 -->
    <div class="device-management">
      <div class="header">
        <h2>品牌设备绑定管理</h2>
        <div class="header-buttons">
          <button class="refresh-btn" @click="refreshBindings" :disabled="loading">
            {{ loading ? '刷新中...' : '刷新状态' }}
          </button>
          <button class="refresh-devices-btn" @click="refreshDevicesAndGroups" :disabled="refreshingDevices">
            {{ refreshingDevices ? '刷新设备中...' : '刷新设备' }}
          </button>
        </div>
      </div>

      <!-- 美的设备 -->
      <el-card class="device-card">
        <div class="brand-header">
          <img :src="getBrandLogo('midea')" class="brand-logo"/>
          <h3>美的品牌设备</h3>
        </div>
        <div class="device-status">
          <span>绑定状态：
            <span :class="getStatusClass(brandBindings.midea)">
              {{ getStatusText(brandBindings.midea) }}
            </span>
          </span>
          <el-button
            :type="brandBindings.midea ? 'danger' : 'primary'"
            @click="handleDeviceAction('midea')"
            :disabled="loading">
            {{ brandBindings.midea ? '解除绑定' : '立即绑定' }}
          </el-button>
        </div>
      </el-card>

      <!-- 小米设备 -->
      <el-card class="device-card">
        <div class="brand-header">
          <img :src="getBrandLogo('xiaomi')" class="brand-logo"/>
          <h3>小米品牌设备</h3>
        </div>
        <div class="device-status">
          <span>绑定状态：
            <span :class="getStatusClass(brandBindings.xiaomi)">
              {{ getStatusText(brandBindings.xiaomi) }}
            </span>
          </span>
          <el-button
            :type="brandBindings.xiaomi ? 'danger' : 'primary'"
            @click="handleDeviceAction('xiaomi')"
            :disabled="loading">
            {{ brandBindings.xiaomi ? '解除绑定' : '立即绑定' }}
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import mideaLogo from '@/assets/brands/midea.png'
import xiaomiLogo from '@/assets/brands/xiaomi.png'

// 使用预加载脚本暴露的ipcRenderer
const ipcRenderer = window.ipcRenderer;

export default {
  data() {
    return {
      loading: false,
      userInfo: {
        userId: '',
        isLoggedIn: false
      },
      brandBindings: {
        midea: false,
        xiaomi: false
      },
      brandLogos: {
        midea: mideaLogo,
        xiaomi: xiaomiLogo
      },
      refreshingDevices: false
    }
  },

  async mounted() {
    console.log('🎯 [账号中心] 页面已挂载，开始初始化数据');
    await this.initializeData();
    this.checkAuthCallback();
  },

  methods: {
    // 初始化页面数据
    async initializeData() {
      this.loading = true;
      try {
        await Promise.all([
          this.loadUserInfo(),
          this.loadBindings()
        ]);
        console.log('✅ [账号中心] 数据初始化完成');
      } catch (error) {
        console.error('❌ [账号中心] 数据初始化失败:', error);
        ElMessage.error('数据加载失败');
      } finally {
        this.loading = false;
      }
    },

    // 加载用户信息
    async loadUserInfo() {
      try {
        console.log('🔍 [账号中心] 加载用户信息...');
        const result = await ipcRenderer.invoke('get-current-user');
        if (result.success) {
          this.userInfo = result.data;
          console.log('✅ [账号中心] 用户信息加载成功:', this.userInfo);
        } else {
          console.error('❌ [账号中心] 获取用户信息失败:', result.message);
          this.userInfo = { userId: '未登录', isLoggedIn: false };
        }
      } catch (error) {
        console.error('❌ [账号中心] 加载用户信息异常:', error);
        this.userInfo = { userId: '未登录', isLoggedIn: false };
      }
    },

    // 加载绑定状态
    async loadBindings() {
      try {
        console.log('🔍 [账号中心] 加载绑定状态...');
        const result = await ipcRenderer.invoke('get-bindings');
        if (result.success) {
          console.log('✅ [账号中心] 绑定状态加载成功:', result.data);
          // 更新绑定状态
          this.brandBindings.midea = result.data.midea || false;
          this.brandBindings.xiaomi = result.data.xiaomi || false;
        } else {
          console.warn('⚠️ [账号中心] 获取绑定状态失败:', result.message);
          // 保持默认状态
        }
      } catch (error) {
        console.error('❌ [账号中心] 加载绑定状态异常:', error);
      }
    },

    // 刷新绑定状态
    async refreshBindings() {
      console.log('🔄 [账号中心] 手动刷新绑定状态');
      await this.loadBindings();
      ElMessage.success('绑定状态已刷新');
    },

    // 获取品牌logo
    getBrandLogo(brand) {
      return this.brandLogos[brand] || ''
    },

    // 获取状态文本
    getStatusText(isBound) {
      return isBound ? '已绑定' : '未绑定';
    },

    // 获取状态样式类
    getStatusClass(isBound) {
      return isBound ? 'status-bound' : 'status-unbound';
    },

    // 处理设备操作（绑定/解绑）
    async handleDeviceAction(brand) {
      const isBound = this.brandBindings[brand];

      if (!isBound) {
        // 绑定操作：打开外部授权网站并跳转到授权页面
        this.openAuthorizationWebsite(brand);

        // 存储品牌信息并跳转到授权页面
        sessionStorage.setItem('bindingBrand', brand);
        this.$router.push('/third-party-auth');
      } else {
        // 解绑操作
        await this.unbindDevice(brand);
      }
    },

    // 打开外部授权网站
    async openAuthorizationWebsite(brand) {
      try {
        // 从AccountAPIRegistry获取BASE_URL，实现统一管理
        const result = await window.api.getApiBaseUrl();

        if (!result.success) {
          console.error('❌ [账号中心] 获取API baseURL失败:', result.message);
          ElMessage.error('获取服务器地址失败，请重试');
          return;
        }

        const baseUrl = result.baseURL;
        const authUrl = `${baseUrl}/auth/auth-page?brand=${brand}`;

        console.log(`🌐 [账号中心] 打开 ${brand} 授权网站: ${authUrl}`);
        console.log(`🌐 [账号中心] 使用统一管理的BASE_URL: ${baseUrl}`);

        // 使用electron的shell.openExternal打开外部浏览器
        if (window.electronAPI && window.electronAPI.shell) {
          window.electronAPI.shell.openExternal(authUrl);
        } else if (window.ipcRenderer) {
          // 通过IPC调用主进程打开外部链接
          window.ipcRenderer.invoke('open-external-url', authUrl);
        } else {
          // 备用方案：在当前窗口打开
          window.open(authUrl, '_blank');
        }
      } catch (error) {
        console.error('❌ [账号中心] 打开授权网站异常:', error);
        ElMessage.error('打开授权网站失败，请重试');
      }
    },

    // 解绑设备
    async unbindDevice(brand) {
      try {
        const result = await ElMessageBox.confirm(
          `确定要解绑${brand}设备吗？`,
          '解绑确认',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消'
          }
        );

        this.loading = true;
        console.log(`🔧 [账号中心] 开始解绑 ${brand}...`);

        const unbindResult = await ipcRenderer.invoke('unbind-third-party', brand);

        if (unbindResult.success) {
          this.brandBindings[brand] = false;
          ElMessage.success(`${brand}设备解绑成功`);
          console.log(`✅ [账号中心] ${brand} 解绑成功`);
        } else {
          ElMessage.error(unbindResult.message || `${brand}设备解绑失败`);
          console.error(`❌ [账号中心] ${brand} 解绑失败:`, unbindResult.message);
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error(`❌ [账号中心] ${brand} 解绑异常:`, error);
          ElMessage.error('解绑操作失败');
        }
      } finally {
        this.loading = false;
      }
    },

    // 检查授权回调
    checkAuthCallback() {
      // 从URL参数中获取授权结果
      const success = this.$route.query.success === 'true';
      const brand = this.$route.query.brand || sessionStorage.getItem('bindingBrand');
      const message = this.$route.query.message;

      // 如果授权成功且品牌存在
      if (success && brand) {
        console.log(`✅ [账号中心] ${brand} 授权成功回调`);

        // 更新绑定状态
        this.brandBindings[brand] = true;

        // 显示成功消息
        const successMessage = message || `${brand}设备绑定成功`;
        this.$nextTick(() => {
          ElMessage.success(successMessage);
        });

        // 清除存储的品牌信息和URL参数
        sessionStorage.removeItem('bindingBrand');
        this.$router.replace({ query: {} });
      }

      // 处理授权失败的情况
      if (this.$route.query.error) {
        console.error('❌ [账号中心] 授权失败回调:', this.$route.query.message);
        const errorMessage = this.$route.query.message || '授权失败';
        this.$nextTick(() => {
          ElMessage.error(errorMessage);
        });
        this.$router.replace({ query: {} });
      }
    },

    // 刷新设备和分组信息
    async refreshDevicesAndGroups() {
      this.refreshingDevices = true;
      try {
        console.log('🔄 [账号中心] 开始刷新设备和分组信息...');

        const result = await ipcRenderer.invoke('refresh-devices-and-groups');

        if (result.success) {
          console.log('✅ [账号中心] 设备和分组刷新成功:', result);

          // 构建详细的成功消息
          const details = [
            `设备总数: ${result.deviceCount}`,
            `分组总数: ${result.groupCount}`
          ];

          if (result.stats) {
            details.push(`在线: ${result.stats.online}, 离线: ${result.stats.offline}`);
          }

          ElMessage.success({
            message: `设备和分组刷新成功！${details.join(' | ')}`,
            duration: 3000
          });

          // 发送全局事件通知其他组件更新
          this.$eventBus && this.$eventBus.emit('devices-refreshed', result);
          window.dispatchEvent(new CustomEvent('devices-refreshed', { detail: result }));

        } else {
          console.error('❌ [账号中心] 设备和分组刷新失败:', result.message);
          ElMessage.error(result.message || '刷新设备和分组失败');
        }

      } catch (error) {
        console.error('❌ [账号中心] 刷新设备和分组异常:', error);
        ElMessage.error('刷新过程中发生错误: ' + (error.message || '未知错误'));
      } finally {
        this.refreshingDevices = false;
      }
    }
  }
}
</script>

<style scoped>
.user-info-container {
  padding: 30px;
  max-width: 800px;
  margin: 0 auto;
}

.user-basic-info {
  margin-bottom: 40px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.user-header h2 {
  color: #303133;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.user-details {
  display: grid;
  gap: 15px;
}

.detail-item {
  display: flex;
  align-items: center;
  font-size: 16px;
}

.label {
  color: #606266;
  min-width: 100px;
}

.value {
  color: #303133;
  font-weight: 500;
}

.status-online {
  color: #67c23a;
}

.status-offline {
  color: #f56c6c;
}

.device-management {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #303133;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.refresh-btn {
  padding: 8px 16px;
  background: #409EFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.refresh-btn:hover:not(:disabled) {
  background: #337ecc;
}

.refresh-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.refresh-devices-btn {
  padding: 8px 16px;
  background: #409EFF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.refresh-devices-btn:hover:not(:disabled) {
  background: #337ecc;
}

.refresh-devices-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.device-card {
  margin: 20px 0;
}

.brand-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.brand-logo {
  width: 60px;
  height: 40px;
  margin-right: 15px;
}

.device-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.status-bound {
  color: #67c23a;
  font-weight: 600;
}

.status-unbound {
  color: #f56c6c;
  font-weight: 600;
}

.el-button {
  min-width: 100px;
}
</style>

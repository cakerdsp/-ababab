<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <div class="auth-header">
        <div class="app-logo">
          <div class="logo-circle">APP</div>
        </div>
        <h2>授权请求</h2>
      </div>

      <div class="auth-content" v-if="!isProcessing">
        <p>请为应用程序授权访问您的 {{ brandName }} 设备数据</p>

        <div class="permissions-list">
          <div class="permission-item">
            <el-icon><View /></el-icon>
            <span>查看设备信息</span>
          </div>
          <div class="permission-item">
            <el-icon><Setting /></el-icon>
            <span>控制设备状态</span>
          </div>
          <div class="permission-item">
            <el-icon><Bell /></el-icon>
            <span>接收设备通知</span>
          </div>
        </div>

        <div class="auth-buttons">
          <el-button type="info" @click="cancelAuth" :disabled="isProcessing">取消</el-button>
          <el-button type="primary" @click="confirmAuth" :disabled="isProcessing">授权</el-button>
        </div>
      </div>

      <!-- 授权处理中的状态 -->
      <div class="auth-processing" v-if="isProcessing">
        <div class="loading-container">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <h3>{{ processingStatus }}</h3>
          <p class="processing-desc">{{ processingDesc }}</p>
        </div>

        <!-- 进度条 -->
        <el-progress :percentage="progressPercentage" :show-text="false" class="progress-bar"></el-progress>

        <!-- 错误状态 -->
        <div v-if="hasError" class="error-container">
          <el-icon class="error-icon"><WarningFilled /></el-icon>
          <p class="error-message">{{ errorMessage }}</p>
          <div class="error-buttons">
            <el-button type="info" @click="cancelAuth">返回</el-button>
            <el-button type="primary" @click="retryAuth">重试</el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { View, Setting, Bell, Loading, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  components: { View, Setting, Bell, Loading, WarningFilled },

  data() {
    return {
      isProcessing: false,
      hasError: false,
      errorMessage: '',
      processingStatus: '',
      processingDesc: '',
      progressPercentage: 0,
      brandName: ''
    }
  },

  mounted() {
    // 获取要授权的品牌名称
    this.brandName = sessionStorage.getItem('bindingBrand') || '未知品牌';

    // 监听主进程发送的授权进度更新
    window.ipcRenderer.on('third-party-auth-progress', this.handleProgressUpdate);
  },

  beforeUnmount() {
    // 清理IPC监听器
    window.ipcRenderer.off('third-party-auth-progress', this.handleProgressUpdate);
  },

    methods: {
    // 确认授权 - 通过IPC调用主进程业务逻辑
    async confirmAuth() {
      this.isProcessing = true;
      this.hasError = false;
      this.progressPercentage = 0;

      try {
        console.log(`开始 ${this.brandName} 品牌授权流程...`);

        // 通过IPC调用主进程的完整授权流程
        const result = await window.ipcRenderer.invoke('perform-third-party-authorization', this.brandName);

        if (result.success) {
          this.handleAuthSuccess();
        } else {
          throw new Error(result.message || '授权失败');
        }

      } catch (error) {
        this.handleAuthError(error);
      }
        },

    // 处理来自主进程的进度更新
    handleProgressUpdate(event, progress) {
      console.log('收到授权进度更新:', progress);

      switch (progress.step) {
        case 'start':
          this.processingStatus = '开始授权流程...';
          this.processingDesc = '正在初始化授权流程';
          this.progressPercentage = progress.progress;
          break;

        case 'getAuthCode':
          this.processingStatus = '获取授权码中...';
          this.processingDesc = '正在为您生成授权码，请稍候';
          this.progressPercentage = progress.progress;
          break;

        case 'binding':
          this.processingStatus = '绑定账号中...';
          this.processingDesc = '正在使用授权码绑定您的设备账号';
          this.progressPercentage = progress.progress;
          break;

        case 'complete':
          this.processingStatus = '授权完成';
          this.processingDesc = '授权流程已成功完成';
          this.progressPercentage = progress.progress;
          break;

        default:
          this.processingStatus = progress.message || '处理中...';
          this.processingDesc = '正在处理您的请求';
          this.progressPercentage = progress.progress || 0;
      }
    },

    // 授权成功处理
    handleAuthSuccess() {
      setTimeout(() => {
        ElMessage.success(`${this.brandName} 设备授权成功！`);

        // 跳转回用户绑定页面，携带成功参数
        this.$router.replace({
          path: '/account',
          query: {
            success: 'true',
            brand: this.brandName,
            message: '授权绑定成功'
          }
        });
      }, 500);
    },

    // 授权错误处理
    handleAuthError(error) {
      console.error('授权流程错误:', error);
      this.hasError = true;
      this.errorMessage = error.message || '授权过程中发生未知错误';
      this.processingStatus = '授权失败';
      this.processingDesc = '请检查网络连接后重试';

      ElMessage.error(this.errorMessage);
    },

    // 重试授权
    retryAuth() {
      this.hasError = false;
      this.errorMessage = '';
      this.confirmAuth();
    },

    // 取消授权
    cancelAuth() {
      // 清除存储的品牌信息
      sessionStorage.removeItem('bindingBrand');

      // 返回账号中心页面
      this.$router.replace('/account');
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.auth-card {
  width: 500px;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.app-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.logo-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.auth-content {
  padding: 0 20px;
}

.auth-content p {
  text-align: center;
  color: #606266;
  margin-bottom: 25px;
  font-size: 16px;
}

.permissions-list {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
}

.permission-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  font-size: 15px;
}

.permission-item:last-child {
  margin-bottom: 0;
}

.permission-item .el-icon {
  margin-right: 10px;
  color: #409EFF;
  font-size: 18px;
}

.auth-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.auth-buttons .el-button {
  width: 120px;
}

/* 授权处理中的样式 */
.auth-processing {
  text-align: center;
  padding: 20px;
}

.loading-container {
  margin-bottom: 30px;
}

.loading-icon {
  font-size: 48px;
  color: #409EFF;
  animation: rotate 2s linear infinite;
  margin-bottom: 20px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-container h3 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 20px;
}

.processing-desc {
  color: #909399;
  font-size: 14px;
  margin-bottom: 0;
}

.progress-bar {
  margin: 20px 0;
}

/* 错误状态样式 */
.error-container {
  margin-top: 20px;
  padding: 20px;
  background: #fef0f0;
  border-radius: 8px;
  border: 1px solid #fde2e2;
}

.error-icon {
  font-size: 32px;
  color: #f56c6c;
  margin-bottom: 10px;
}

.error-message {
  color: #f56c6c;
  font-size: 14px;
  margin-bottom: 15px;
}

.error-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.error-buttons .el-button {
  width: 100px;
}
</style>

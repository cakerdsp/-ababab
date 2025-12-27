<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <div class="auth-header">
        <div class="app-logo">
          <div class="logo-circle">APP</div>
        </div>
        <h2>授权请求</h2>
      </div>
      
      <div class="auth-content">
        <p>请为应用程序授权访问您的 {{ brandName }} 数据</p>
        
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
        
        <!-- 新增授权码输入区域 -->
        <div class="auth-code-section">
          <div class="auth-code-label">授权码</div>
          <el-input 
            v-model="authCode" 
            placeholder="请输入8位大写字母和数字组合"
            maxlength="8"
            show-word-limit
            @input="validateAuthCode"
          />
          <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        </div>
        
        <div class="auth-buttons">
          <el-button type="info" @click="cancelAuth">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmAuth"
            :disabled="!isAuthCodeValid"
          >授权</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { View, Setting, Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  components: { View, Setting, Bell },
  data() {
    return {
      brandName: '', // 品牌名称
      authCode: '', // 存储用户输入的授权码
      errorMessage: '', // 错误提示信息
      isAuthCodeValid: false // 授权码是否有效
    }
  },

  mounted() {
    // 获取要授权的品牌名称
    this.brandName = sessionStorage.getItem('bindingBrand') || '未知品牌';
    console.log(`📋 [第三方授权] 初始化授权页面，品牌: ${this.brandName}`);
  },

  methods: {
    // 确认授权
    async confirmAuth() {
      if (this.isAuthCodeValid) {
        try {
          console.log(`🔧 [第三方授权] 开始使用授权码绑定 ${this.brandName}...`);
          
          // 调用后端绑定接口
          const result = await window.ipcRenderer.invoke('bind-with-authorization-code', this.authCode, this.brandName);
          
          if (result && result.success) {
            console.log(`✅ [第三方授权] ${this.brandName} 绑定成功`);
            // 显示成功消息
            ElMessage.success({
              message: `${this.brandName} 授权成功！`,
              duration: 1500,
              onClose: () => {
                // 跳转回用户绑定页面，携带成功参数
                this.$router.replace({
                  path: '/account',
                  query: { 
                    success: 'true',
                    brand: this.brandName 
                  }
                });
              }
            });
          } else {
            throw new Error(result?.message || '授权绑定失败');
          }
        } catch (error) {
          console.error(`❌ [第三方授权] ${this.brandName} 绑定失败:`, error);
          ElMessage.error(error.message || '授权过程中发生错误');
          this.errorMessage = error.message || '授权失败，请检查授权码是否正确';
        }
      }
    },
    
    // 取消授权
    cancelAuth() {
      // 清除存储的品牌信息
      sessionStorage.removeItem('bindingBrand');
      
      // 直接返回原页面
      this.$router.back();
    },
    
    // 验证授权码格式
    validateAuthCode() {
      // 清空错误信息
      this.errorMessage = '';
      
      // 空值检查
      if (!this.authCode) {
        this.isAuthCodeValid = false;
        return;
      }
      
      // 长度检查
      if (this.authCode.length !== 8) {
        this.errorMessage = '授权码必须为8位字符';
        this.isAuthCodeValid = false;
        return;
      }
      
      // 格式检查：仅允许大写字母和数字
      const isValid = /^[A-Z0-9]{8}$/.test(this.authCode);
      
      if (!isValid) {
        this.errorMessage = '授权码只能包含大写字母和数字';
        this.isAuthCodeValid = false;
        return;
      }
      
      // 验证通过
      this.isAuthCodeValid = true;
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

/* 新增授权码输入区域样式 */
.auth-code-section {
  margin-bottom: 30px;
}

.auth-code-label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #606266;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
  height: 20px;
}

.auth-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.auth-buttons .el-button {
  width: 120px;
}
</style>

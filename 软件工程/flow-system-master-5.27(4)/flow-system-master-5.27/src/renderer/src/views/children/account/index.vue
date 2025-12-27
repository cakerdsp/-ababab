<template>
  <div class="user-info-container">
    <!-- 用户基本信息 -->
    <div class="user-basic-info">
      <div class="user-header">
        <h2>用户信息</h2>
      </div>
      <div class="user-details">
        <div class="detail-item">
          <span class="label">用户名：</span>
          <span class="value">李四</span>
        </div>
        <div class="detail-item">
          <span class="label">用户ID：</span>
          <span class="value">123456789</span>
        </div>
      </div>
    </div>

    <!-- 设备绑定管理 -->
    <div class="device-management">
      <div class="header">
        <h2>品牌设备绑定管理</h2>
      </div>

      <!-- 美的设备 -->
      <el-card class="device-card">
        <div class="brand-header">
          <img :src="getBrandLogo('midea')" class="brand-logo"/>
          <h3>美的品牌设备</h3>
        </div>
        <div class="device-status">
          <span>绑定状态：{{ mideaStatus }}</span>
          <el-button
            :type="mideaStatus === '未绑定' ? 'primary' : 'danger'"
            @click="handleDeviceAction('midea')">
            {{ mideaStatus === '未绑定' ? '立即绑定' : '解除绑定' }}
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
          <span>绑定状态：{{ xiaomiStatus }}</span>
          <el-button
            :type="xiaomiStatus === '未绑定' ? 'primary' : 'danger'"
            @click="handleDeviceAction('xiaomi')">
            {{ xiaomiStatus === '未绑定' ? '立即绑定' : '解除绑定' }}
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

export default {
  data() {
    return {
      mideaStatus: '未绑定',
      xiaomiStatus: '已绑定',
      totalDevices: 1,
      brandLogos: {
        midea: mideaLogo,
        xiaomi: xiaomiLogo
      }
    }
  },
  mounted() {
    // 检查URL参数中是否有授权成功的标志
    this.checkAuthCallback();
  },
  methods: {
    // 获取品牌logo
    getBrandLogo(brand) {
      return this.brandLogos[brand] || ''
    },

    // 处理设备操作（绑定/解绑）
    handleDeviceAction(brand) {
      const isBind = this[`${brand}Status`] === '未绑定'

      if (isBind) {
        // 存储当前操作品牌
        sessionStorage.setItem('bindingBrand', brand);

        // 绑定操作：跳转到通用第三方授权页面
        this.$router.push('/third-party-auth');
      } else {
        // 解绑操作：保持原有逻辑
        this.unbindDevice(brand);
      }
    },

    // 解绑设备
    unbindDevice(brand) {
      ElMessageBox.confirm(
        `确定要解绑${brand}设备吗？`,
        '解绑确认',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消'
        }
      ).then(() => {
        this[`${brand}Status`] = '未绑定';
        this.totalDevices -= 1;
        ElMessage.success(`${brand}设备解绑成功`);
      }).catch(() => {});
    },

    // 检查授权回调
    checkAuthCallback() {
      // 从URL参数中获取授权结果
      const success = this.$route.query.success === 'true';
      const brand = this.$route.query.brand || sessionStorage.getItem('bindingBrand');
      const message = this.$route.query.message;

      // 如果授权成功且品牌存在
      if (success && brand) {
        // 检查当前状态，只有未绑定的才更新设备总数
        const currentStatus = this[`${brand}Status`];

        // 更新绑定状态
        this[`${brand}Status`] = '已绑定';

        // 更新设备总数（只有之前是未绑定状态才增加）
        if (currentStatus === '未绑定') {
          this.totalDevices += 1;
        }

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
        const errorMessage = this.$route.query.message || '授权失败';
        this.$nextTick(() => {
          ElMessage.error(errorMessage);
        });
        this.$router.replace({ query: {} });
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
  min-width: 80px;
}

.value {
  color: #303133;
  font-weight: 500;
}

.device-management {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
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

.el-button {
  min-width: 100px;
}
</style>

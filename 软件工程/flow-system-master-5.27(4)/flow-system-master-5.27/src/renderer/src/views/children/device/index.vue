<template>
  <div class="brand-device-setting">
    <!-- 品牌设备列表 -->
    <div class="brand-section" v-for="brand in brandList" :key="brand.name">
      <el-card class="brand-card">
        <!-- 品牌标题 -->
        <div slot="header" class="brand-header">
          <img :src="brand.logo" class="brand-logo" />
          <span class="brand-name">{{ brand.name }}设备列表</span>
        </div>

        <!-- 设备列表 -->
        <div class="device-list">
          <div v-for="device in brand.devices" :key="device.id" class="device-item">
            <div class="device-info">
              <span class="device-name">{{ device.name }}</span>
              <span class="device-id">ID: {{ device.id }}</span>
            </div>

            <!-- 分组选择器 -->
            <el-select
              v-model="device.group"
              size="small"
              @change="(val) => handleGroupChange(device, val)"
            >
              <el-option
                v-for="group in availableGroups"
                :key="group.id"
                :label="group.name"
                :value="group.id"
              />
            </el-select>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
// 示例品牌logo（需替换为实际路径）
import midLogo from '@/assets/brands/midea.png'
// const midLogo = require('@/assets/brands/midea.png')
// import { useRouter } from 'vue-router'
import miLogo from '@/assets/brands/xiaomi.png'
// const miLogo = require('@/assets/brands/xiaomi.png')

export default {
  data() {
    return {
      // 可用分组列表
      availableGroups: [
        { id: 'default', name: '默认分组' },
        { id: 'office', name: '办公区' },
        { id: 'home', name: '家庭区' }
      ],

      // 品牌设备数据
      brandList: [
        {
          name: '美的',
          logo: midLogo,
          devices: [
            { id: 'M-001', name: '空调X1', group: 'default' },
            { id: 'M-002', name: '冰箱T3', group: 'default' },
            { id: 'M-003', name: '洗衣机Z7', group: 'default' }
          ]
        },
        {
          name: '小米',
          logo: miLogo,
          devices: [
            { id: 'MI-001', name: '智能灯', group: 'default' },
            { id: 'MI-002', name: '摄像头', group: 'default' },
            { id: 'MI-003', name: '空气净化器', group: 'default' }
          ]
        }
      ]
    }
  },

  methods: {
    // 处理分组变更
    // setting/index.vue 修改部分
    handleGroupChange(device, newGroupId) {
      const group = this.availableGroups.find((g) => g.id === newGroupId)
      this.$confirm(`确认将设备 ${device.name} 分配到 ${group.name} 吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {
          this.$set(device, 'group', newGroupId) // 使用响应式更新
          this.$message.success('分组更新成功')
        })
        .catch(() => {
          const originalGroup = this.availableGroups.find((g) => g.id === device.group)
          this.$set(device, 'group', originalGroup.id) // 恢复时也使用响应式更新
        })
    }
  }
}
</script>

<style scoped>
.brand-device-setting {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.brand-section {
  margin-bottom: 30px;
}

.brand-card {
  margin-bottom: 20px;
}

.brand-header {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.brand-logo {
  width: 40px;
  height: 40px;
  margin-right: 15px;
}

.brand-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.device-list {
  padding: 10px 0;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.device-item:last-child {
  border-bottom: none;
}

.device-info {
  display: flex;
  flex-direction: column;
}

.device-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.device-id {
  font-size: 12px;
  color: #909399;
}

/* 选择器宽度 */
.el-select {
  width: 150px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .device-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .el-select {
    margin-top: 10px;
    width: 100%;
  }
}
</style>
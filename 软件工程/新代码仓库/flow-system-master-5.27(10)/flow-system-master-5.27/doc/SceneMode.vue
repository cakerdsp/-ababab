<template>
  <Layout>
    <div class="device-manager">
      <!-- 场景模式内容区 -->
      <div class="scene-content">
        <h2 class="scene-title">可用场景</h2>
        <div class="scene-list">
          <!-- 场景卡片 - 点击显示详情 -->
          <div
            v-for="(scene, index) in sceneList"
            :key="index"
            class="scene-card"
            @click="openSceneDetail(scene)"
          >
            <h3>{{ scene.name }}</h3>
            <p>{{ scene.description }}</p>
            <div class="scene-device-count">包含 {{ scene.devices.length }} 个设备</div>
            <button class="apply-scene" @click="applyScene(scene)">应用场景</button>
          </div>
        </div>

        <!-- 新增场景按钮 -->
        <div class="add-scene-btn-container">
          <button class="add-scene-btn" @click="showCreateSceneDialog">
            <i class="icon-plus"></i> 新建场景
          </button>
        </div>
      </div>

      <!-- 场景详情模态框 -->
      <div v-if="showSceneDetail" class="scene-detail-modal">
        <div class="modal-content">
          <div class="modal-header">
            <h3 class="modal-title">{{ currentScene.name }} - 场景详情</h3>
            <button class="close-btn" @click="showSceneDetail = false">×</button>
          </div>
          <div class="modal-body">
            <h3 class="sub-title">场景中的设备</h3>
            <div class="scene-devices">
              <div v-if="currentScene.devices.length === 0" class="empty-tip">
                该场景暂无设备，点击"添加设备"按钮进行添加
              </div>
              <div
                v-for="(device, index) in currentScene.devices"
                :key="index"
                class="scene-device-card"
              >
                <div class="device-header">
                  <span>{{ device.id }}</span>
                  <span class="device-status" :class="'status-' + device.status">
                    {{ statusMap[device.status] }}
                  </span>
                </div>
                <div class="device-props">
                  <div class="prop-item">
                    <span>电量：</span>
                    <input
                      type="number"
                      v-model.number="device.battery"
                      min="0"
                      max="100"
                      @change="updateDeviceProperty(device, 'battery')"
                      class="prop-input"
                    />
                    <span>%</span>
                  </div>
                  <div class="prop-item" v-if="device.temperature !== undefined">
                    <span>温度：</span>
                    <input
                      type="number"
                      v-model.number="device.temperature"
                      min="-20"
                      max="80"
                      @change="updateDeviceProperty(device, 'temperature')"
                      class="prop-input"
                    />
                    <span>℃</span>
                  </div>
                  <div class="prop-item">
                    <span>状态：</span>
                    <select
                      v-model="device.status"
                      @change="updateDeviceProperty(device, 'status')"
                      class="status-select"
                    >
                      <option value="normal">正常</option>
                      <option value="standby">待机</option>
                      <option value="offline">离线</option>
                    </select>
                  </div>
                </div>
                <button class="remove-device" @click.stop="removeDeviceFromScene(device.id)">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
            </div>
            <h3 class="sub-title mt-4">添加设备到场景</h3>
            <div class="add-devices-section">
              <div v-for="device in allDevices" :key="device.id" class="device-option">
                <label class="device-checkbox">
                  <input
                    type="checkbox"
                    :checked="isDeviceInScene(device.id)"
                    @change="toggleDeviceInScene(device.id)"
                  />
                  <span>{{ device.id }} - {{ device.name }}</span>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showSceneDetail = false">关闭</button>
            <button class="btn-confirm" @click="saveSceneChanges">保存更改</button>
          </div>
        </div>
      </div>

      <!-- 新建场景对话框（居中显示） -->
      <div v-if="showCreateScene" class="create-scene-modal">
        <div class="modal-content center-modal">
          <h3 class="modal-title">新建场景</h3>
          <div class="modal-form">
            <div class="form-group">
              <label for="scene-name">场景名称</label>
              <input
                type="text"
                id="scene-name"
                v-model="newSceneForm.name"
                :class="{ 'form-error': sceneErrors.name }"
                placeholder="请输入场景名称"
              />
              <div v-if="sceneErrors.name" class="error-message">{{ sceneErrors.name }}</div>
            </div>
            <div class="form-group">
              <label for="scene-desc">场景描述</label>
              <textarea
                id="scene-desc"
                v-model="newSceneForm.description"
                :class="{ 'form-error': sceneErrors.description }"
                placeholder="请输入场景描述"
                rows="3"
              ></textarea>
              <div v-if="sceneErrors.description" class="error-message">
                {{ sceneErrors.description }}
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="showCreateScene = false">取消</button>
            <button class="btn-confirm" @click="confirmCreateScene">确认创建</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script>
import Layout from './Layout.vue'

export default {
  data() {
    return {
      // 场景相关数据
      sceneList: [
        {
          id: 'work',
          name: '工作模式',
          description: '开启办公设备，调整至高效工作状态',
          createTime: '2025-06-10',
          devices: [
            { id: 'T-001', status: 'normal', battery: 80, temperature: 25 },
            { id: 'L-002', status: 'normal', battery: 90 }
          ]
        },
        {
          id: 'meeting',
          name: '会议模式',
          description: '关闭不必要设备，开启会议系统',
          createTime: '2025-06-10',
          devices: [
            { id: 'T-001', status: 'standby', battery: 70, temperature: 26 },
            { id: 'P-003', status: 'normal', battery: 85 }
          ]
        }
      ],
      showCreateScene: false,
      newSceneForm: {
        name: '',
        description: ''
      },
      sceneErrors: {
        name: '',
        description: ''
      },
      showSceneDetail: false,
      currentScene: null,

      // 所有设备列表（用于场景添加设备）
      allDevices: [
        { id: 'T-001', name: '温度传感器1' },
        { id: 'L-002', name: '灯光控制器2' },
        { id: 'P-003', name: '投影仪3' },
        { id: 'S-004', name: '音响4' },
        { id: 'D-005', name: '显示屏5' }
      ],

      // 传感器数据
      sensorDevices: {
        temperature: [
          { id: 'T-001', currentValue: '22℃', updateTime: '10:30:21' },
          { id: 'T-003', currentValue: '24℃', updateTime: '10:29:55' }
        ],
        humidity: [
          { id: 'H-002', currentValue: '50%', updateTime: '10:30:15' },
          { id: 'H-004', currentValue: '48%', updateTime: '10:29:45' }
        ]
      },
      selectedSensors: {
        temperature: 'T-001',
        humidity: 'H-002'
      }
    }
  },

  computed: {
    statusMap() {
      return {
        normal: '正常',
        standby: '待机',
        offline: '离线'
      }
    }
  },

  methods: {
    // 场景相关方法
    openSceneDetail(scene) {
      // 使用深拷贝避免直接修改原数据
      this.currentScene = JSON.parse(JSON.stringify(scene))
      this.showSceneDetail = true
    },

    isDeviceInScene(deviceId) {
      return this.currentScene.devices.some((device) => device.id === deviceId)
    },

    toggleDeviceInScene(deviceId) {
      const deviceIndex = this.currentScene.devices.findIndex((device) => device.id === deviceId)

      if (deviceIndex > -1) {
        // 从场景中移除设备
        this.currentScene.devices.splice(deviceIndex, 1)
      } else {
        // 添加设备到场景，使用预设值
        const currentDevice = this.getAllDeviceDetails(deviceId)
        if (currentDevice) {
          this.currentScene.devices.push({
            id: currentDevice.id,
            status: currentDevice.preset.status,
            battery: currentDevice.preset.battery,
            temperature: currentDevice.preset.temperature || null
          })
        } else {
          console.error('设备数据不存在:', deviceId)
        }
      }
    },

    // 获取设备完整信息
    getAllDeviceDetails(deviceId) {
      // 补充所有设备的预设数据
      const mockDevices = [
        { id: 'T-001', preset: { status: 'normal', battery: 80, temperature: 25 } },
        { id: 'L-002', preset: { status: 'normal', battery: 90 } },
        { id: 'P-003', preset: { status: 'standby', battery: 70 } },
        { id: 'S-004', preset: { status: 'normal', battery: 85 } },
        { id: 'D-005', preset: { status: 'offline', battery: 30, temperature: 30 } }
      ]
      return mockDevices.find((d) => d.id === deviceId)
    },

    removeDeviceFromScene(deviceId) {
      this.currentScene.devices = this.currentScene.devices.filter(
        (device) => device.id !== deviceId
      )
    },

    saveSceneChanges() {
      // 找到场景在列表中的索引并更新
      const sceneIndex = this.sceneList.findIndex((scene) => scene.id === this.currentScene.id)
      if (sceneIndex > -1) {
        this.sceneList[sceneIndex] = this.currentScene
        this.$message.success('场景配置已保存')
        this.showSceneDetail = false
      }
    },

    // 新建场景相关方法
    showCreateSceneDialog() {
      this.newSceneForm = {
        name: '',
        description: ''
      }
      this.sceneErrors = { name: '', description: '' }
      this.showCreateScene = true
    },

    confirmCreateScene() {
      this.validateSceneForm()
      if (!this.sceneErrors.name && !this.sceneErrors.description) {
        // 创建新场景
        const newScene = {
          id: `scene${this.sceneList.length + 1}`,
          name: this.newSceneForm.name,
          description: this.newSceneForm.description,
          createTime: this.formatDate(new Date()),
          devices: [] // 初始化空设备列表
        }
        this.sceneList.push(newScene)
        this.showCreateScene = false
        this.$message.success('场景创建成功')
      }
    },

    validateSceneForm() {
      this.sceneErrors.name = ''
      this.sceneErrors.description = ''

      if (!this.newSceneForm.name) {
        this.sceneErrors.name = '请输入场景名称'
      } else if (this.newSceneForm.name.length < 2 || this.newSceneForm.name.length > 16) {
        this.sceneErrors.name = '长度应在2到16个字符之间'
      }

      if (!this.newSceneForm.description) {
        this.sceneErrors.description = '请输入场景描述'
      } else if (this.newSceneForm.description.length < 10) {
        this.sceneErrors.description = '描述至少需要10个字符'
      }
    },

    // 应用场景
    applyScene(scene) {
      this.$message({
        type: 'success',
        message: `已应用「${scene.name}」场景`
      })
      console.log('应用场景配置:', scene)
    },

    // 日期格式化工具方法
    formatDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },

    // 设备属性更新方法
    updateDeviceProperty(device, prop) {
      // 设备参数修改时触发，可在此处添加数据验证或同步逻辑
      console.log(`修改设备 ${device.id} 的 ${prop} 属性为: ${device[prop]}`)
      // 实际项目中可添加防抖或API请求
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Arial', sans-serif;
}

.device-manager {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

/* 场景内容区样式 */
.scene-content {
  margin-top: 30px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.scene-title {
  font-size: 18px;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.scene-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.scene-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.scene-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.scene-card h3 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 16px;
}

.scene-card p {
  color: #606266;
  font-size: 14px;
  margin-bottom: 15px;
  line-height: 1.5;
}

.scene-device-count {
  color: #909399;
  font-size: 12px;
  margin-bottom: 15px;
}

.apply-scene {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  width: 100%;
}

.apply-scene:hover {
  background-color: #368ee0;
}
/* 场景内容区样式（续） */
.add-scene-btn-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
}

.add-scene-btn {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.add-scene-btn:hover {
  background-color: #38a169;
}

.prop-input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
  margin: 0 5px;
}

.status-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

/* 场景详情模态框样式 */
.scene-detail-modal,
.create-scene-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  max-width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-title {
  font-size: 18px;
  color: #303133;
  /* 关键：调整标题的位置 */
  margin: 10px 0 0 10px;
}

.center-modal {
  max-width: 400px;
  width: 90%;
  /* 新增以下样式确保垂直居中 */
  transform: translateY(0);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #909399;
}

.modal-body {
  padding: 20px;
}

.scene-basic-info {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #eee;
}

.scene-basic-info p {
  margin-bottom: 8px;
  font-size: 14px;
}

.sub-title {
  font-size: 16px;
  color: #303133;
  margin: 20px 0 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.mt-4 {
  margin-top: 20px;
}

.scene-devices {
  margin-bottom: 20px;
}

.scene-device-card {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.device-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.device-header span:first-child {
  font-weight: bold;
  color: #303133;
}

.device-status {
  margin-left: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-normal {
  background-color: #67c23a;
  color: white;
}

.status-standby {
  background-color: #e6a23c;
  color: white;
}

.status-offline {
  background-color: #f56c6c;
  color: white;
}

.device-props {
  flex: 1;
  margin-right: 15px;
}

.prop-item {
  display: flex;
  font-size: 14px;
  margin-bottom: 5px;
}

.prop-item span:first-child {
  color: #909399;
  min-width: 60px;
}

.remove-device {
  background: none;
  border: none;
  color: #f56c6c;
  cursor: pointer;
  font-size: 16px;
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: #909399;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.add-devices-section {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.device-option {
  margin-bottom: 10px;
  font-size: 14px;
}

.device-checkbox input {
  margin-right: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: 15px 20px;
  border-top: 1px solid #eee;
}

/* 新建场景对话框样式 */
.create-scene-modal .modal-form {
  padding: 20px;
}

.create-scene-modal .form-group {
  margin-bottom: 20px;
}

.modal-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #42b983;
}

.form-error {
  border-color: #f56c6c !important;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  padding: 15px 20px;
  border-top: 1px solid #eee;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: none;
  margin-left: 10px;
}

.btn-cancel {
  background-color: #fff;
  color: #606266;
  border: 1px solid #ddd;
}

.btn-confirm {
  background-color: #42b983;
  color: white;
}

.btn-cancel:hover,
.btn-confirm:hover {
  opacity: 0.9;
}
</style>
<template>
  <div class="device-manager">
    <!-- 设备信息展示 - 仅在非预设策略模式下显示 -->
    <div v-if="currentMode !== 'smart'" class="device-panels">
      <div v-for="device in currentDevices" :key="device.id" class="device-card">
        <h3 class="device-title">设备 {{ device.id }}</h3>
        <div class="device-status">
          <div class="status-item">
            <span class="label">状态：</span>
            <span class="value">
              <span class="current-value" :class="device.status">
                {{ getStatusText(device.status) }}
              </span>
              <span class="preset-value">(预设: {{ getStatusText(device.preset.status) }})</span>
            </span>
          </div>
          <div class="status-item">
            <span class="label">电量：</span>
            <span class="value">
              <span class="current-value">{{ device.battery }}%</span>
              <span class="preset-value">(预设: {{ device.preset.battery }}%)</span>
            </span>
          </div>
          <div v-if="device.showTemperature" class="status-item">
            <span class="label">温度：</span>
            <span class="value">
              <span class="current-value">{{ device.temperature }}℃</span>
              <span class="preset-value">(预设: {{ device.preset.temperature }}℃)</span>
            </span>
          </div>
        </div>
        <div class="device-id">编号：{{ device.id }}</div>
        <button v-if="currentMode !== 'smart'" class="modify-btn" @click="showModifyDialog(device)">
          修改预设参数
        </button>
      </div>
    </div>

    <!-- 预设策略控制开关 - 仅在预设策略模式下显示 -->
    <div v-if="currentMode === 'smart'" class="strategy-control">
      <div class="strategy-card">
        <h3 class="strategy-title">预设策略控制</h3>
        <div class="strategy-switch">
          <label class="switch">
            <input type="checkbox" v-model="strategyEnabled" @change="toggleStrategy" />
            <span class="slider round"></span>
          </label>
          <span class="switch-label">{{ strategyEnabled ? '策略已启用' : '策略已禁用' }}</span>
        </div>
        <div v-if="strategyEnabled" class="strategy-settings">
          <div class="setting-item">
            <span class="setting-label">温度阈值：</span>
            <span class="setting-value">{{ temperatureThreshold }}℃</span>
          </div>
          <div class="setting-item">
            <span class="setting-label">电量阈值：</span>
            <span class="setting-value">{{ batteryThreshold }}%</span>
          </div>
          <button class="setting-btn" @click="showStrategySettings">修改策略设置</button>
        </div>
      </div>
    </div>

    <!-- 传感器面板 - 仅在非预设策略模式下显示 -->
    <div v-if="currentMode !== 'smart'" class="sensor-panels">
      <div v-for="(sensor, type) in sensorData" :key="type" class="sensor-card">
        <div class="sensor-header">
          <div class="sensor-title">{{ getSensorTypeText(type) }}</div>
          <select
            v-model="selectedSensors[type]"
            @change="handleSensorChange(type)"
            class="sensor-dropdown"
          >
            <option v-for="device in sensorDevices[type]" :key="device.id" :value="device.id">
              {{ device.id }}
            </option>
          </select>
        </div>
        <div class="sensor-value">
          {{ sensor.currentValue }}
        </div>
        <div class="sensor-info">最新更新：{{ sensor.updateTime }}</div>
      </div>
    </div>

    <!-- 模态框 - 统一管理所有模态框显示 -->
    <div v-if="showModal" class="modal-backdrop">
      <div class="modal-content">
        <h3 class="modal-title">{{ modalTitle }}</h3>
        <div class="modal-body">
          <slot name="modal-body"></slot>
          <div v-if="modalType === 'createGroup'">
            <div class="form-group">
              <label for="group-name">分组名称</label>
              <input
                type="text"
                id="group-name"
                v-model="newGroupForm.name"
                :class="{ 'form-error': groupErrors.name }"
                placeholder="请输入分组名称"
              />
              <div v-if="groupErrors.name" class="error-message">{{ groupErrors.name }}</div>
            </div>
          </div>
          <div v-if="modalType === 'deleteGroup'">
            <div class="form-group">
              <p>
                确定要删除
                <span class="delete-group-name">{{ currentGroupInfo.name }}</span> 分组吗？
              </p>
              <p class="form-note">该分组下的所有设备将移至默认分组。</p>
            </div>
          </div>
          <div v-if="modalType === 'modifyParams' && currentMode !== 'smart'">
            <div class="form-group">
              <label>设备状态</label>
              <div class="status-radio-group">
                <label class="status-radio">
                  <input type="radio" v-model="deviceParams.status" value="normal" />
                  <span class="status-radio-text normal">正常</span>
                </label>
                <label class="status-radio">
                  <input type="radio" v-model="deviceParams.status" value="standby" />
                  <span class="status-radio-text standby">待机</span>
                </label>
                <label class="status-radio">
                  <input type="radio" v-model="deviceParams.status" value="offline" />
                  <span class="status-radio-text offline">离线</span>
                </label>
              </div>
            </div>

            <div class="form-group">
              <label>预设电量 (%)</label>
              <input
                type="number"
                v-model.number="deviceParams.battery"
                min="0"
                max="100"
                :class="{ 'form-error': batteryError }"
              />
              <div v-if="batteryError" class="error-message">{{ batteryError }}</div>
            </div>

            <div class="form-group" v-if="deviceParams.showTemperature">
              <label>预设温度 (℃)</label>
              <input
                type="number"
                v-model.number="deviceParams.temperature"
                :class="{ 'form-error': temperatureError }"
              />
              <div v-if="temperatureError" class="error-message">{{ temperatureError }}</div>
            </div>

            <div class="form-note">
              <p>提示：修改预设参数不会立即影响当前设备状态，需通过系统同步后生效。</p>
            </div>
          </div>
          <div v-if="modalType === 'strategySettings'">
            <div class="form-group">
              <label>温度阈值 (℃)</label>
              <input
                type="number"
                v-model.number="temperatureThreshold"
                min="-20"
                max="80"
                :class="{ 'form-error': temperatureThresholdError }"
              />
              <div v-if="temperatureThresholdError" class="error-message">
                {{ temperatureThresholdError }}
              </div>
            </div>

            <div class="form-group">
              <label>电量阈值 (%)</label>
              <input
                type="number"
                v-model.number="batteryThreshold"
                min="0"
                max="100"
                :class="{ 'form-error': batteryThresholdError }"
              />
              <div v-if="batteryThresholdError" class="error-message">
                {{ batteryThresholdError }}
              </div>
            </div>

            <div class="form-note">
              <p>提示：设置策略阈值后，系统将根据传感器数据自动调整设备状态。</p>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-confirm" @click="confirmModal">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      // 分组相关
      groupList: [
        { id: 'default', name: '默认分组' },
        { id: 'group1', name: '办公区设备' }
      ],
      currentGroup: 'default',
      showModal: false,
      modalType: '',
      modalTitle: '',
      newGroupForm: { name: '' },
      groupErrors: { name: '' },

      // 模式相关
      currentMode: 'manual',
      modes: [
        { value: 'manual', label: '手动模式' },
        { value: 'auto', label: '场景模式' },
        { value: 'smart', label: '预设策略控制' }
      ],
      sceneModeUrl: '/scene-mode',

      // 预设策略控制相关
      strategyEnabled: false,
      temperatureThreshold: 26,
      batteryThreshold: 20,
      temperatureThresholdError: '',
      batteryThresholdError: '',

      // 设备数据
      currentDevices: [
        {
          id: 'T-001',
          status: 'normal',
          battery: 75,
          temperature: 22,
          showTemperature: true,
          preset: {
            status: 'normal',
            battery: 80,
            temperature: 25
          }
        },
        {
          id: 'H-002',
          status: 'standby',
          battery: 60,
          showTemperature: false,
          preset: {
            status: 'normal',
            battery: 90
          }
        }
      ],
      currentDevice: null,
      deviceParams: {
        status: 'normal',
        battery: 100,
        temperature: 25,
        showTemperature: true
      },
      batteryError: '',
      temperatureError: '',

      // 传感器相关
      sensorDevices: {
        temperature: [
          { id: 'T-001', currentValue: '22℃', updateTime: '10:30:21' },
          { id: 'T-003', currentValue: '24℃', updateTime: '10:29:55' }
        ],
        humidity: [
          { id: 'H-002', currentValue: '50%', updateTime: '10:30:15' },
          { id: 'H-004', currentValue: '48%', updateTime: '10:29:45' }
        ],
        pm25: [
          { id: 'PM-003', currentValue: '15μg/m³', updateTime: '10:30:05' },
          { id: 'PM-005', currentValue: '18μg/m³', updateTime: '10:29:35' }
        ]
      },
      selectedSensors: {
        temperature: 'T-001',
        humidity: 'H-002',
        pm25: 'PM-003'
      }
    }
  },

  computed: {
    currentGroupInfo() {
      return this.groupList.find((group) => group.id === this.currentGroup) || {}
    },
    sensorData() {
      return Object.keys(this.selectedSensors).reduce((acc, type) => {
        const device = this.sensorDevices[type].find((d) => d.id === this.selectedSensors[type])
        acc[type] = device
        return acc
      }, {})
    }
  },

  methods: {
    // 状态文本转换
    getStatusText(status) {
      const statusMap = {
        normal: '正常',
        standby: '待机',
        offline: '离线'
      }
      return statusMap[status] || status
    },

    // 传感器类型文本转换
    getSensorTypeText(type) {
      const sensorTypeMap = {
        temperature: '温度传感器',
        humidity: '湿度传感器',
        pm25: 'PM2.5传感器'
      }
      return sensorTypeMap[type] || type
    },

    // 模式切换
    switchMode(mode) {
      if (mode === 'auto') {
        this.openSceneModePage()
      } else {
        if (this.currentMode === 'smart' && mode !== 'smart') {
          this.strategyEnabled = false
        }
        this.currentMode = mode
      }
    },

    openSceneModePage() {
      sessionStorage.setItem('currentGroupForScene', this.currentGroup)
      this.$router.push({
        path: this.sceneModeUrl,
        query: { currentGroup: this.currentGroup }
      })
    },

    // 分组管理
    showCreateDialog() {
      this.modalType = 'createGroup'
      this.modalTitle = '新建分组'
      this.newGroupForm.name = ''
      this.groupErrors.name = ''
      this.showModal = true
    },

    showDeleteDialog() {
      if (this.currentGroup === 'default') {
        this.$message.error('默认分组不允许删除')
        return
      }
      this.modalType = 'deleteGroup'
      this.modalTitle = '删除分组'
      this.showModal = true
    },

    showModifyDialog(device) {
      this.currentDevice = device
      this.deviceParams = {
        status: device.preset.status,
        battery: device.preset.battery,
        temperature: device.preset.temperature || 25,
        showTemperature: device.showTemperature
      }
      this.batteryError = ''
      this.temperatureError = ''
      this.modalType = 'modifyParams'
      this.modalTitle = `修改预设参数 - ${device.id}`
      this.showModal = true
    },

    showStrategySettings() {
      this.modalType = 'strategySettings'
      this.modalTitle = '预设策略设置'
      this.temperatureThresholdError = ''
      this.batteryThresholdError = ''
      this.showModal = true
    },

    closeModal() {
      this.showModal = false
      this.resetModalErrors()
    },

    resetModalErrors() {
      this.groupErrors = { name: '' }
      this.temperatureThresholdError = ''
      this.batteryThresholdError = ''
      this.batteryError = ''
      this.temperatureError = ''
    },

    confirmModal() {
      switch (this.modalType) {
        case 'createGroup':
          if (this.validateGroupForm()) {
            this.groupList.push({
              id: `group${this.groupList.length + 1}`,
              name: this.newGroupForm.name
            })
            this.currentGroup = `group${this.groupList.length}`
            this.closeModal()
            this.$message.success('分组创建成功')
          }
          break

        case 'deleteGroup':
          this.groupList = this.groupList.filter((group) => group.id !== this.currentGroup)
          this.currentGroup = 'default'
          this.closeModal()
          this.$message.success('分组删除成功')
          break

        case 'modifyParams':
          if (this.validateDeviceParams()) {
            this.currentDevice.preset = { ...this.deviceParams }
            this.closeModal()
            this.$message.success('预设参数已保存，等待系统同步')
          }
          break

        case 'strategySettings':
          if (this.validateStrategySettings()) {
            this.closeModal()
            this.$message.success('策略设置已保存')
            if (this.strategyEnabled) {
              this.checkStrategyConditions()
            }
          }
          break
      }
    },

    validateGroupForm() {
      this.groupErrors.name = ''
      if (!this.newGroupForm.name) {
        this.groupErrors.name = '请输入分组名称'
        return false
      } else if (this.newGroupForm.name.length < 2 || this.newGroupForm.name.length > 8) {
        this.groupErrors.name = '长度应在2到8个字符之间'
        return false
      }
      return true
    },

    validateDeviceParams() {
      this.batteryError = ''
      this.temperatureError = ''

      if (
        isNaN(this.deviceParams.battery) ||
        this.deviceParams.battery < 0 ||
        this.deviceParams.battery > 100
      ) {
        this.batteryError = '请输入0-100之间的数字'
        return false
      }

      if (
        this.deviceParams.showTemperature &&
        (isNaN(this.deviceParams.temperature) ||
          this.deviceParams.temperature < -20 ||
          this.deviceParams.temperature > 80)
      ) {
        this.temperatureError = '请输入-20-80之间的数字'
        return false
      }
      return true
    },

    validateStrategySettings() {
      this.temperatureThresholdError = ''
      this.batteryThresholdError = ''

      if (
        isNaN(this.temperatureThreshold) ||
        this.temperatureThreshold < -20 ||
        this.temperatureThreshold > 80
      ) {
        this.temperatureThresholdError = '请输入-20-80之间的数字'
        return false
      }

      if (
        isNaN(this.batteryThreshold) ||
        this.batteryThreshold < 0 ||
        this.batteryThreshold > 100
      ) {
        this.batteryThresholdError = '请输入0-100之间的数字'
        return false
      }
      return true
    },

    // 策略控制
    toggleStrategy() {
      if (this.strategyEnabled) {
        if (!this.validateStrategySettings()) {
          this.strategyEnabled = false
          this.$message.error('请先设置有效的策略阈值')
        }
      }
    },

    checkStrategyConditions() {
      const temperatureSensor = this.sensorData.temperature
      const batterySensor = this.sensorData.pm25

      if (temperatureSensor && batterySensor) {
        const currentTemperature = parseFloat(temperatureSensor.currentValue)
        const currentBattery = parseFloat(batterySensor.currentValue.replace('%', ''))

        if (currentTemperature > this.temperatureThreshold) {
          this.applyStrategy('temperatureHigh')
        }

        if (currentBattery < this.batteryThreshold) {
          this.applyStrategy('batteryLow')
        }
      }
    },

    applyStrategy(strategyType) {
      this.$message({
        type: 'info',
        message: `策略触发: ${strategyType}`
      })
    },

    handleSensorChange(type) {
      if (this.strategyEnabled) {
        this.checkStrategyConditions()
      }
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
}

.device-manager {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.sensor-dropdown,
.group-dropdown {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.modify-btn,
.new-group-btn,
.setting-btn,
.apply-scene {
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

.delete-group-btn {
  padding: 8px 16px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.delete-group-btn:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.mode-radio {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.mode-radio-active {
  background-color: #42b983;
  color: white;
  border-color: #42b983;
}

/* 设备卡片 */
.device-panels,
.sensor-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.device-card,
.sensor-card,
.strategy-card,
.scene-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.device-title,
.sensor-title,
.strategy-title,
.scene-card h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.status-item,
.setting-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.label,
.setting-label {
  color: #909399;
}

.value,
.setting-value {
  color: #606266;
}

.current-value {
  font-weight: bold;
}

.current-value.normal {
  color: #67c23a;
}

.current-value.standby {
  color: #e6a23c;
}

.current-value.offline {
  color: #f56c6c;
}

.preset-value {
  font-size: 12px;
  color: #909399;
}

.device-id,
.sensor-info,
.delete-note {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}

.sensor-value {
  font-size: 24px;
  color: #303133;
  margin: 20px 0;
  text-align: center;
}

/* 策略控制 */
.strategy-control {
  max-width: 500px;
  margin: 0 auto 30px;
}

.strategy-switch {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  justify-content: center;
}

.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
  margin-right: 10px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: '';
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #42b983;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.switch-label {
  font-size: 16px;
  color: #303133;
  font-weight: bold;
}

/* 模态框 */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal-title {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  font-size: 16px;
  color: #303133;
}

.modal-body {
  padding: 20px;
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

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus {
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

.form-note {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

/* 状态选择器 */
.status-radio-group {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.status-radio {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.status-radio input {
  margin-right: 5px;
}

.status-radio-text {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
}

.status-radio-text.normal {
  color: #67c23a;
  border: 1px solid #67c23a;
}

.status-radio-text.standby {
  color: #e6a23c;
  border: 1px solid #e6a23c;
}

.status-radio-text.offline {
  color: #f56c6c;
  border: 1px solid #f56c6c;
}

.status-radio input:checked + .status-radio-text.normal {
  background-color: #67c23a;
  color: white;
}

.status-radio input:checked + .status-radio-text.standby {
  background-color: #e6a23c;
  color: white;
}

.status-radio input:checked + .status-radio-text.offline {
  background-color: #f56c6c;
  color: white;
}
</style>
<template>
  <div class="strategy-control">
    <div class="strategy-container">
      <div class="strategy-header">
        <h2>预设策略控制</h2>
        <label class="strategy-switch">
          <input type="checkbox" v-model="strategyEnabled" @change="handleStrategyToggle" />
          <span class="strategy-slider"></span>
        </label>
      </div>

      <div class="strategy-status">
        <p>
          当前状态: <span class="status-text" :class="{ 'disabled': !strategyEnabled }">
            {{ strategyEnabled ? '开启' : '关闭' }}
          </span>
        </p>
        <p v-if="strategyEnabled">{{ currentStrategy.name }}已开启</p>
        <p v-if="strategyEnabled">策略描述: {{ currentStrategy.description }}</p>
        <p v-else>预设策略已关闭</p>
      </div>

      <!-- 策略详细配置 -->
      <div v-if="strategyEnabled" class="strategy-config">
        <div class="config-section">
          <h3>策略配置</h3>
          <div class="config-item">
            <label>策略类型:</label>
            <select v-model="currentStrategy.id" @change="handleStrategyChange" class="strategy-select">
              <option v-for="strategy in availableStrategies" :key="strategy.id" :value="strategy.id">
                {{ strategy.name }}
              </option>
            </select>
          </div>
          <div class="config-item">
            <label>执行频率:</label>
            <select v-model="strategyConfig.frequency" class="strategy-select">
              <option value="realtime">实时</option>
              <option value="5min">每5分钟</option>
              <option value="15min">每15分钟</option>
              <option value="30min">每30分钟</option>
            </select>
          </div>
          <div class="config-item">
            <label>应用范围:</label>
            <select v-model="strategyConfig.scope" class="strategy-select">
              <option value="current">当前分组</option>
              <option value="all">所有设备</option>
            </select>
          </div>
        </div>

        <!-- 策略参数配置 -->
        <div class="config-section" v-if="currentStrategy.parameters">
          <h3>参数设置</h3>
          <div v-for="param in currentStrategy.parameters" :key="param.key" class="config-item">
            <label>{{ param.label }}:</label>
            <input
              v-if="param.type === 'number'"
              type="number"
              v-model.number="strategyConfig.parameters[param.key]"
              :min="param.min"
              :max="param.max"
              :step="param.step || 1"
              class="strategy-input"
            />
            <select
              v-else-if="param.type === 'select'"
              v-model="strategyConfig.parameters[param.key]"
              class="strategy-select"
            >
              <option v-for="option in param.options" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <input
              v-else
              type="text"
              v-model="strategyConfig.parameters[param.key]"
              class="strategy-input"
            />
          </div>
        </div>

        <!-- 策略执行状态 -->
        <div class="strategy-execution">
          <h3>执行状态</h3>
          <div class="execution-info">
            <div class="info-item">
              <span class="label">上次执行:</span>
              <span class="value">{{ lastExecutionTime || '未执行' }}</span>
            </div>
            <div class="info-item">
              <span class="label">执行次数:</span>
              <span class="value">{{ executionCount }}</span>
            </div>
            <div class="info-item">
              <span class="label">影响设备:</span>
              <span class="value">{{ affectedDevicesCount }} 个</span>
            </div>
          </div>
          <button class="manual-execute-btn" @click="manualExecuteStrategy" :disabled="loading">
            {{ loading ? '执行中...' : '立即执行' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PresetStrategyControl',
  props: {
    currentGroup: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      strategyEnabled: false,
      loading: false,
      currentStrategy: {
        id: 'smart_comfort',
        name: '智能舒适策略',
        description: '根据环境数据自动调节设备参数以优化舒适度'
      },
      availableStrategies: [
        {
          id: 'smart_comfort',
          name: '智能舒适策略',
          description: '根据环境数据自动调节设备参数以优化舒适度',
          parameters: [
            {
              key: 'target_temperature',
              label: '目标温度',
              type: 'number',
              min: 16,
              max: 30,
              step: 0.5
            },
            {
              key: 'target_humidity',
              label: '目标湿度',
              type: 'number',
              min: 30,
              max: 80,
              step: 1
            }
          ]
        },
        {
          id: 'energy_saving',
          name: '节能策略',
          description: '优化设备运行以降低能耗',
          parameters: [
            {
              key: 'max_power_level',
              label: '最大功率等级',
              type: 'select',
              options: [
                { value: 'low', label: '低' },
                { value: 'medium', label: '中' },
                { value: 'high', label: '高' }
              ]
            }
          ]
        },
        {
          id: 'air_quality',
          name: '空气质量策略',
          description: '根据空气质量数据自动调节净化设备',
          parameters: [
            {
              key: 'pm25_threshold',
              label: 'PM2.5阈值',
              type: 'number',
              min: 10,
              max: 100,
              step: 5
            }
          ]
        }
      ],
      strategyConfig: {
        frequency: 'realtime',
        scope: 'current',
        parameters: {
          target_temperature: 24,
          target_humidity: 50,
          max_power_level: 'medium',
          pm25_threshold: 35
        }
      },
      lastExecutionTime: null,
      executionCount: 0,
      affectedDevicesCount: 0
    }
  },
  computed: {
    selectedStrategy() {
      return this.availableStrategies.find(s => s.id === this.currentStrategy.id) || this.availableStrategies[0];
    }
  },
  methods: {
    // 策略开关切换 - 纯前端逻辑
    handleStrategyToggle() {
      console.log('🔄 [预设策略] 策略开关切换:', this.strategyEnabled);

      if (this.strategyEnabled) {
        this.$message({
          message: '预设策略已开启',
          type: 'success',
          duration: 2000
        });
        // 模拟初始化执行状态
        this.lastExecutionTime = new Date().toLocaleString();
        this.executionCount = 1;
        this.affectedDevicesCount = Math.floor(Math.random() * 5) + 1;
      } else {
        this.$message({
          message: '预设策略已关闭',
          type: 'info',
          duration: 2000
        });
        // 重置执行状态
        this.lastExecutionTime = null;
        this.executionCount = 0;
        this.affectedDevicesCount = 0;
      }

      // 触发事件给父组件
      this.$emit('strategy-changed', {
        enabled: this.strategyEnabled,
        strategy: this.currentStrategy,
        config: this.strategyConfig
      });
    },

    // 策略类型变更
    handleStrategyChange() {
      const strategy = this.availableStrategies.find(s => s.id === this.currentStrategy.id);
      if (strategy) {
        this.currentStrategy = { ...strategy };
        console.log('🔄 [预设策略] 策略类型变更:', this.currentStrategy.name);

        this.$message({
          message: `已切换到${this.currentStrategy.name}`,
          type: 'success',
          duration: 2000
        });
      }
    },

    // 手动执行策略 - 纯前端模拟
    manualExecuteStrategy() {
      console.log('🚀 [预设策略] 手动执行策略');

      this.loading = true;

      // 模拟执行过程
      setTimeout(() => {
        this.loading = false;
        this.lastExecutionTime = new Date().toLocaleString();
        this.executionCount += 1;
        this.affectedDevicesCount = Math.floor(Math.random() * 8) + 1;

        this.$message({
          message: `策略执行完成，影响了 ${this.affectedDevicesCount} 个设备`,
          type: 'success',
          duration: 3000
        });

        // 触发事件给父组件
        this.$emit('strategy-executed', {
          strategy: this.currentStrategy,
          config: this.strategyConfig,
          result: {
            success: true,
            affectedDevices: this.affectedDevicesCount,
            executionTime: this.lastExecutionTime
          }
        });
      }, 2000);
    }
  },

  watch: {
    // 监听策略配置变化
    strategyConfig: {
      handler(newConfig) {
        console.log('🔧 [预设策略] 配置更新:', newConfig);
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.strategy-control {
  margin-top: 20px;
}

.strategy-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  border: 1px solid #ebeef5;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.strategy-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.strategy-switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 30px;
}

.strategy-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.strategy-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 30px;
}

.strategy-slider:before {
  position: absolute;
  content: '';
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .strategy-slider {
  background-color: #409eff;
}

input:checked + .strategy-slider:before {
  transform: translateX(30px);
}

.strategy-status {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.strategy-status p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.strategy-status p:last-child {
  margin-bottom: 0;
}

.status-text {
  font-weight: bold;
  color: #409eff;
}

.status-text.disabled {
  color: #909399;
}

.strategy-config {
  margin-top: 20px;
}

.config-section {
  margin-bottom: 25px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.config-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.config-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-item label {
  min-width: 120px;
  font-size: 14px;
  color: #606266;
  margin-right: 15px;
}

.strategy-select,
.strategy-input {
  flex: 1;
  max-width: 200px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.strategy-select:focus,
.strategy-input:focus {
  outline: none;
  border-color: #409eff;
}

.strategy-execution {
  background-color: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  padding: 20px;
}

.strategy-execution h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.execution-info {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .label {
  color: #606266;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.manual-execute-btn {
  width: 100%;
  padding: 10px 20px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.manual-execute-btn:hover:not(:disabled) {
  background-color: #337ecc;
}

.manual-execute-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}
</style>

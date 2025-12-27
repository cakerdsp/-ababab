<template>
  <div class="device-manager">
    <!-- 标题控制栏 -->
    <div class="control-bar">
      <div class="group-selector">
        <select v-model="currentGroup" @change="handleGroupChange" class="group-dropdown">
          <option v-for="(group, index) in groupList" :key="index" :value="group.id">
            {{ group.name }}
          </option>
        </select>
        <button class="new-group-btn" @click="showCreateDialog">
          <i class="fa fa-plus"></i> 新建分组
        </button>
        <button
          class="delete-group-btn"
          @click="showDeleteDialog"
          :disabled="groupList.length <= 1"
        >
          <i class="fa fa-trash"></i> 删除分组
        </button>
      </div>

      <div class="mode-switch">
        <div
          class="mode-radio"
          v-for="mode in modes"
          :key="mode.value"
          :class="{ 'mode-radio-active': currentMode === mode.value }"
          @click="switchMode(mode.value)"
        >
          {{ mode.label }}
        </div>
      </div>
    </div>

    <!-- 修改这里：动态渲染组件 -->
    <div class="main-content">
      <component :is="getComponentByMode(currentMode)"></component>
    </div>

    <!-- 新建分组对话框 -->
    <div v-if="showCreateGroup" class="create-group-modal">
      <div class="modal-content">
        <h3 class="modal-title">新建分组</h3>
        <div class="modal-form">
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
        <div class="modal-actions">
          <button class="btn-cancel" @click="showCreateGroup = false">取消</button>
          <button class="btn-confirm" @click="confirmCreateGroup">确认</button>
        </div>
      </div>
    </div>

    <!-- 删除分组对话框 -->
    <div v-if="showDeleteGroup" class="delete-group-modal">
      <div class="modal-content">
        <h3 class="modal-title">删除分组</h3>
        <div class="modal-form">
          <div class="form-group">
            <p>
              确定要删除 <span class="delete-group-name">{{ currentGroupInfo.name }}</span> 分组吗？
            </p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showDeleteGroup = false">取消</button>
          <button class="btn-confirm" @click="confirmDeleteGroup">确认删除</button>
        </div>
      </div>
    </div>

    <!-- 预设策略控制组件 -->
    <div v-if="currentMode === 'smart'" class="strategy-control">
      <div class="strategy-container">
        <div class="strategy-header">
          <h2>预设策略控制</h2>
          <label class="strategy-switch">
            <!-- 修改：移除@change事件，仅依赖v-model -->
            <input type="checkbox" v-model="strategyEnabled" />
            <span class="strategy-slider"></span>
          </label>
        </div>

        <div class="strategy-status">
          <p>
            当前状态: <span class="status-text">{{ strategyEnabled ? '开启' : '关闭' }}</span>
          </p>
          <p v-if="strategyEnabled">预设策略已开启</p>
          <p v-if="strategyEnabled">策略描述: 自动调节设备参数以优化性能</p>
          <p v-else>预设策略已关闭</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 导入组件
import ManualStrategyMode from './ManualStrategyMode.vue'
import SceneMode from './SceneMode.vue'

export default {
  name: 'Layout',
  components: {
    ManualStrategyMode,
    SceneMode
  },
  data() {
    return {
      // 预设策略控制相关数据
      strategyEnabled: false, // 初始状态为禁用
      // 分组相关数据
      groupList: [
        { id: 'default', name: '默认分组' },
        { id: 'group1', name: '办公区设备' }
      ],
      currentGroup: 'default',
      showCreateGroup: false,
      newGroupForm: { name: '' },
      groupErrors: { name: '' },

      // 模式相关数据
      currentMode: 'manual',
      modes: [
        { value: 'manual', label: '手动模式' },
        { value: 'auto', label: '场景模式' },
        { value: 'smart', label: '预设策略控制' }
      ],
      sceneModeUrl: '/scene',

      showDeleteGroup: false,
      currentGroupInfo: null,

      // 预设策略控制相关数据
      strategyEnabled: false,
      currentStrategy: {
        id: 'default',
        name: '智能策略',
        description: '自动调节设备参数以优化性能'
      }
    }
  },

  // 添加方法来映射模式到组件
  methods: {
    getComponentByMode(mode) {
      switch (mode) {
        case 'manual':
          return 'ManualStrategyMode'
        case 'auto':
          return 'SceneMode'
        case 'smart':
          // 直接在主模板中实现，不需要单独组件
          return null
        default:
          return 'ManualStrategyMode'
      }
    },

    switchMode(mode) {
      this.currentMode = mode
      // 修改路径与路由配置一致
      if (mode === 'auto' && this.$router) {
        sessionStorage.setItem('currentGroupForScene', this.currentGroup)
        this.$router.push({
          path: '/group/scene',
          query: { currentGroup: this.currentGroup }
        })
      } else {
        // 对于其他模式，移除场景相关的查询参数
        if (this.$router) {
          this.$router.push({
            path: '/group',
            query: {}
          })
        }
      }
    },

    // 分组管理方法
    handleGroupChange(val) {
      console.log('分组变更:', val)
    },

    showCreateDialog() {
      this.showCreateGroup = true
      this.newGroupForm.name = ''
      this.groupErrors.name = ''
    },

    confirmCreateGroup() {
      this.validateGroupForm()
      if (!this.groupErrors.name) {
        this.groupList.push({
          id: `group${this.groupList.length + 1}`,
          name: this.newGroupForm.name
        })
        this.showCreateGroup = false
        this.currentGroup = `group${this.groupList.length}`
      }
    },

    validateGroupForm() {
      this.groupErrors.name = ''
      if (!this.newGroupForm.name) {
        this.groupErrors.name = '请输入分组名称'
      } else if (this.newGroupForm.name.length < 2 || this.newGroupForm.name.length > 8) {
        this.groupErrors.name = '长度应在2到8个字符之间'
      }
    },

    showDeleteDialog() {
      this.currentGroupInfo = this.groupList.find((group) => group.id === this.currentGroup)
      this.showDeleteGroup = true
    },

    confirmDeleteGroup() {
      if (!this.currentGroupInfo) return
      if (this.currentGroup === 'default') {
        this.$message.error('默认分组不允许删除')
        this.showDeleteGroup = false
        return
      }
      this.groupList = this.groupList.filter((group) => group.id !== this.currentGroup)
      this.currentGroup = 'default'
      this.showDeleteGroup = false
      this.$message.success('分组删除成功')
    },

    // 预设策略控制方法
    toggleStrategy() {
      // 修改：添加实际状态切换逻辑
      this.strategyEnabled = !this.strategyEnabled

      if (this.strategyEnabled) {
        console.log('启用预设策略')
        // 这里可以添加实际启用策略的API调用
      } else {
        console.log('禁用预设策略')
        // 这里可以添加实际禁用策略的API调用
      }
    }
  }
}
</script>

<style scoped>
/* 布局样式 */
.device-manager {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.group-selector {
  display: flex;
  align-items: center;
}

.group-dropdown {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
  font-size: 14px;
}

.new-group-btn,
.delete-group-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.new-group-btn {
  background-color: #42b983;
  color: white;
}

.new-group-btn:hover {
  background-color: #38a169;
}

.delete-group-btn {
  background-color: #e74c3c;
  color: white;
  margin-left: 10px;
}

.delete-group-btn:hover {
  background-color: #c0392b;
}

.delete-group-btn:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.mode-switch {
  display: flex;
  gap: 15px;
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

.main-content {
  margin-top: 20px;
}

/* 对话框样式 */
.delete-group-modal,
.create-group-modal {
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
  padding: 0;
}

.modal-title {
  font-size: 16px;
  color: #303133;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  margin: 0;
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

.form-group input {
  width: 80%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
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

/* 预设策略控制样式 */
.strategy-control {
  margin-top: 20px;
}

.strategy-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.strategy-header h2 {
  font-size: 18px;
  color: #303133;
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
  background-color: #42b983;
}

input:focus + .strategy-slider {
  box-shadow: 0 0 1px #42b983;
}

input:checked + .strategy-slider:before {
  transform: translateX(30px);
}

.strategy-status {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.strategy-status p {
  margin-bottom: 8px;
  font-size: 14px;
}

.strategy-status .status-text {
  font-weight: bold;
  color: #42b983;
}

.strategy-status .status-text.disabled {
  color: #909399;
}
</style>
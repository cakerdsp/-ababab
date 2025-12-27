<template>
  <div class="scene-mode">
    <div class="scene-header">
      <h2>场景模式</h2>
      <p class="scene-subtitle">根据预设场景自动调节设备状态</p>
      <button class="new-scene-btn" @click="showCreateSceneDialog">
        + 新建场景
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>正在加载场景数据...</p>
    </div>

    <!-- 场景列表 -->
    <div v-else class="scene-list">
      <div v-if="sceneList.length === 0" class="empty-scenes">
        <p>暂无场景，点击"新建场景"开始创建</p>
      </div>
      <div v-for="scene in sceneList" :key="scene.scene_id" class="scene-card" @click="openSceneDetail(scene)">
        <div class="scene-card-header">
          <h3 class="scene-name">{{ scene.scene_name }}</h3>
          <div class="scene-actions">
            <button class="apply-scene-btn" @click.stop="executeScene(scene)" :disabled="executing">
              {{ executing && executingSceneId === scene.scene_id ? '执行中...' : '应用场景' }}
            </button>
            <button class="delete-scene-btn" @click.stop="confirmDeleteScene(scene)">
              删除
            </button>
          </div>
        </div>
        <p class="scene-description">{{ scene.description || '暂无描述' }}</p>
        <div class="scene-info">
          <span class="device-count">{{ scene.actions ? scene.actions.length : 0 }} 个动作</span>
          <span class="scene-date">{{ formatDate(scene.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 场景详情对话框 -->
    <div v-if="showSceneDetail" class="modal-overlay" @click="closeSceneDetail">
      <div class="modal-content scene-detail-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ currentScene.scene_name }} - 场景详情</h3>
          <button class="close-btn" @click="closeSceneDetail">×</button>
        </div>
        <div class="modal-body">
          <div class="scene-basic-info">
            <p><strong>场景名称:</strong> {{ currentScene.scene_name }}</p>
            <p><strong>场景描述:</strong> {{ currentScene.description || '暂无描述' }}</p>
            <p><strong>创建时间:</strong> {{ formatDate(currentScene.created_at) }}</p>
            <p><strong>所属分组:</strong> {{ getGroupName(currentScene.gid) }}</p>
          </div>

          <h4 class="section-title">场景动作</h4>
          <div class="scene-actions-list">
            <div v-if="!currentScene.actions || currentScene.actions.length === 0" class="empty-tip">
              该场景暂无动作，点击下方"添加动作"进行配置
            </div>
            <div v-for="(action, index) in currentScene.actions" :key="action.action_id || index" class="scene-action-item">
              <div class="action-info">
                <span class="device-name">{{ getDeviceName(action.did) }}</span>
                <span class="action-detail">{{ getActionDescription(action) }}</span>
              </div>
              <button class="remove-action-btn" @click="removeActionFromScene(index)">
                删除动作
              </button>
            </div>
          </div>

          <h4 class="section-title">添加设备动作</h4>
          <div class="add-actions-section">
            <div class="device-selector">
              <label>选择设备:</label>
              <select v-model="selectedDeviceForAction" @change="loadDeviceControlOptions" class="device-select">
                <option value="">请选择设备</option>
                <option v-for="device in availableDevices" :key="device.did" :value="device.did">
                  {{ device.name }} ({{ device.type }})
                </option>
              </select>
            </div>

            <div v-if="selectedDeviceForAction && deviceControlOptions.length > 0" class="control-options">
              <div v-for="control in deviceControlOptions" :key="control.property" class="control-option">
                <label>{{ control.label }}:</label>
                <select v-if="control.type === 'select'" v-model="newAction[control.property]" class="control-select">
                  <option value="">请选择</option>
                  <option v-for="option in control.options" :key="option" :value="option">
                    {{ formatOptionLabel(control.property, option) }}
                  </option>
                </select>
                <input v-else-if="control.type === 'number'"
                       type="number"
                       v-model.number="newAction[control.property]"
                       :min="control.min"
                       :max="control.max"
                       :step="control.step"
                       class="control-input" />
                <input v-else
                       type="text"
                       v-model="newAction[control.property]"
                       class="control-input" />
              </div>
              <button class="add-action-btn" @click="addActionToScene" :disabled="!canAddAction">
                添加动作
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeSceneDetail">关闭</button>
          <button class="btn-confirm" @click="saveSceneChanges" :disabled="saving">
            {{ saving ? '保存中...' : '保存更改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 新建场景对话框 -->
    <div v-if="showCreateScene" class="modal-overlay" @click="closeCreateDialog">
      <div class="modal-content create-scene-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">新建场景</h3>
          <button class="close-btn" @click="closeCreateDialog">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="scene-name">场景名称</label>
            <input
              type="text"
              id="scene-name"
              v-model="newSceneForm.scene_name"
              :class="{ 'form-error': sceneErrors.scene_name }"
              placeholder="请输入场景名称"
            />
            <div v-if="sceneErrors.scene_name" class="error-message">{{ sceneErrors.scene_name }}</div>
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
            <div v-if="sceneErrors.description" class="error-message">{{ sceneErrors.description }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeCreateDialog">取消</button>
          <button class="btn-confirm" @click="confirmCreateScene" :disabled="creating">
            {{ creating ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="closeDeleteConfirm">
      <div class="modal-content delete-confirm-modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">确认删除</h3>
          <button class="close-btn" @click="closeDeleteConfirm">×</button>
        </div>
        <div class="modal-body">
          <p>确定要删除场景 <strong>{{ sceneToDelete?.scene_name }}</strong> 吗？</p>
          <p class="warning-text">此操作不可撤销！</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeDeleteConfirm">取消</button>
          <button class="btn-confirm btn-danger" @click="deleteScene" :disabled="deleting">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SceneModeControl',
  props: {
    currentGroup: {
      type: String,
      default: 'default'
    }
  },
  data() {
    return {
      // 场景列表
      sceneList: [],

      // 可用设备列表
      availableDevices: [],

      // 分组信息
      groupList: [],

      // 加载状态
      loading: false,
      creating: false,
      saving: false,
      deleting: false,
      executing: false,
      executingSceneId: null,

      // 对话框状态
      showSceneDetail: false,
      showCreateScene: false,
      showDeleteConfirm: false,
      currentScene: null,
      sceneToDelete: null,

      // 新建场景表单
      newSceneForm: {
        scene_name: '',
        description: '',
        gid: ''
      },
      sceneErrors: {
        scene_name: '',
        description: ''
      },

      // 设备控制相关
      selectedDeviceForAction: '',
      deviceControlOptions: [],
      newAction: {},

      // 消息提示
      message: null
    }
  },
  computed: {
    canAddAction() {
      if (!this.selectedDeviceForAction) return false;

      // 检查是否至少设置了一个控制属性
      return this.deviceControlOptions.some(control =>
        this.newAction[control.property] !== undefined &&
        this.newAction[control.property] !== ''
      );
    }
  },
  async mounted() {
    console.log('🔍 [场景调试] SceneModeControl 组件挂载');
    console.log('🔍 [场景调试] 接收到的 currentGroup prop:', this.currentGroup);
    await this.initializeData();
  },
  watch: {
    currentGroup: {
      handler: 'loadScenes',
      immediate: false
    },
    selectedDeviceForAction: {
      handler: 'loadDeviceControlOptions',
      immediate: false
    }
  },
  methods: {
    // 初始化数据
    async initializeData() {
      this.loading = true;
      try {
        await Promise.all([
          this.loadScenes(),
          this.loadAvailableDevices(),
          this.loadGroups()
        ]);
      } catch (error) {
        console.error('初始化数据失败:', error);
        this.showMessage('初始化数据失败: ' + error.message, 'error');
      } finally {
        this.loading = false;
      }
    },

    // 加载场景列表
    async loadScenes() {
      try {
        const result = await window.electronAPI.invoke('get-scenes', this.currentGroup);
        if (result.success) {
          this.sceneList = result.data.scenes || [];
          console.log('场景列表加载成功:', this.sceneList.length);
        } else {
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('加载场景列表失败:', error);
        this.showMessage('加载场景列表失败: ' + error.message, 'error');
      }
    },

    // 加载可用设备
    async loadAvailableDevices() {
      console.log('🔍 [场景调试] 开始加载可用设备...');
      console.log('🔍 [场景调试] 当前分组ID:', this.currentGroup);

      try {
        const result = await window.electronAPI.invoke('get-group-devices-for-scene', this.currentGroup);
        console.log('🔍 [场景调试] API调用结果:', result);

        if (result.success) {
          this.availableDevices = result.data.devices || [];
          console.log('✅ [场景调试] 可用设备加载成功, 数量:', this.availableDevices.length);
          console.log('🔍 [场景调试] 设备列表详情:', this.availableDevices);

          // 详细输出每个设备信息
          this.availableDevices.forEach((device, index) => {
            console.log(`🔍 [场景调试] 设备${index + 1}: ${device.name || device.did} (${device.type}) - 在线:${device.online}`);
          });
        } else {
          console.error('❌ [场景调试] 加载设备失败:', result.message);
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('❌ [场景调试] 加载可用设备异常:', error);
        this.showMessage('加载可用设备失败: ' + error.message, 'error');
      }
    },

    // 加载分组信息
    async loadGroups() {
      try {
        const result = await window.electronAPI.invoke('get-all-groups');
        if (result.success) {
          this.groupList = result.data || [];
        }
      } catch (error) {
        console.error('加载分组信息失败:', error);
      }
    },

    // 显示新建场景对话框
    showCreateSceneDialog() {
      this.newSceneForm = {
        scene_name: '',
        description: '',
        gid: this.currentGroup
      };
      this.sceneErrors = { scene_name: '', description: '' };
      this.showCreateScene = true;
    },

    // 关闭新建场景对话框
    closeCreateDialog() {
      this.showCreateScene = false;
    },

    // 确认创建场景
    async confirmCreateScene() {
      if (!this.validateSceneForm()) return;

      this.creating = true;
      try {
        console.log('🎬 [场景调试] 创建场景:', this.newSceneForm.scene_name);

        // 将响应式对象转换为纯JavaScript对象，避免IPC传递问题
        const sceneData = JSON.parse(JSON.stringify({
          ...this.newSceneForm,
          actions: []
        }));

        console.log('🎬 [场景调试] 场景数据:', sceneData);

        const result = await window.electronAPI.invoke('create-scene', sceneData);
        if (result.success) {
          this.showMessage('场景创建成功', 'success');
          this.showCreateScene = false;
          await this.loadScenes(); // 重新加载场景列表
        } else {
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('创建场景失败:', error);
        this.showMessage('创建场景失败: ' + error.message, 'error');
      } finally {
        this.creating = false;
      }
    },

    // 验证场景表单
    validateSceneForm() {
      this.sceneErrors.scene_name = '';
      this.sceneErrors.description = '';

      let isValid = true;

      if (!this.newSceneForm.scene_name) {
        this.sceneErrors.scene_name = '请输入场景名称';
        isValid = false;
      } else if (this.newSceneForm.scene_name.length < 2 || this.newSceneForm.scene_name.length > 16) {
        this.sceneErrors.scene_name = '长度应在2到16个字符之间';
        isValid = false;
      }

      if (!this.newSceneForm.description) {
        this.sceneErrors.description = '请输入场景描述';
        isValid = false;
      } else if (this.newSceneForm.description.length < 5) {
        this.sceneErrors.description = '描述至少需要5个字符';
        isValid = false;
      }

      return isValid;
    },

    // 打开场景详情
    async openSceneDetail(scene) {
      console.log('🔍 [场景调试] 打开场景详情:', scene.scene_name);
      console.log('🔍 [场景调试] 场景ID:', scene.scene_id);

      try {
        // 获取完整的场景详情
        const result = await window.electronAPI.invoke('get-scene-detail', scene.scene_id);
        console.log('🔍 [场景调试] 场景详情API结果:', result);

        if (result.success) {
          this.currentScene = { ...result.data };
          console.log('🔍 [场景调试] 当前场景数据:', this.currentScene);

          // 确保设备列表是最新的
          console.log('🔍 [场景调试] 重新加载设备列表...');
          await this.loadAvailableDevices();

          this.showSceneDetail = true;
          console.log('✅ [场景调试] 场景详情对话框已打开');
        } else {
          console.error('❌ [场景调试] 获取场景详情失败:', result.message);
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('❌ [场景调试] 获取场景详情异常:', error);
        this.showMessage('获取场景详情失败: ' + error.message, 'error');
      }
    },

    // 关闭场景详情
    closeSceneDetail() {
      this.showSceneDetail = false;
      this.currentScene = null;
      this.selectedDeviceForAction = '';
      this.deviceControlOptions = [];
      this.newAction = {};
    },

    // 保存场景更改
    async saveSceneChanges() {
      this.saving = true;
      try {
        console.log('🎬 [场景调试] 保存场景更改, 场景ID:', this.currentScene.scene_id);

        // 将响应式对象转换为纯JavaScript对象，避免IPC传递问题
        const currentActions = JSON.parse(JSON.stringify(this.currentScene.actions || []));

        console.log('🎬 [场景调试] 当前动作列表:', currentActions);

        // 直接用当前的动作列表替换整个场景的动作
        // 这样可以正确处理添加和删除的动作
        const updateData = {
          replaceActions: currentActions // 使用新的字段名表示完全替换
        };

        console.log('🎬 [场景调试] 更新数据:', updateData);

        const result = await window.electronAPI.invoke('update-scene', this.currentScene.scene_id, updateData);
        if (result.success) {
          this.showMessage('场景配置已保存', 'success');
          this.showSceneDetail = false;
          await this.loadScenes(); // 重新加载场景列表
        } else {
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('保存场景失败:', error);
        this.showMessage('保存场景失败: ' + error.message, 'error');
      } finally {
        this.saving = false;
      }
    },

    // 执行场景
    async executeScene(scene) {
      // 参数验证
      if (!scene) {
        this.showMessage('执行场景失败: 场景参数不完整', 'error');
        return;
      }

      if (!scene.scene_id) {
        this.showMessage('执行场景失败: 场景ID不完整', 'error');
        return;
      }

      this.executing = true;
      this.executingSceneId = scene.scene_id;

      try {
        console.log('🎬 [场景执行] 开始执行场景:', scene.scene_name, '(ID:', scene.scene_id, ')');

        const result = await window.electronAPI.invoke('execute-scene', scene.scene_id);

        console.log('🎬 [场景执行] 后端返回结果:', result);

        if (result.success) {
          const summary = result.data.summary;
          this.showMessage(
            `场景执行完成！成功: ${summary.success}, 失败: ${summary.failed}, 跳过: ${summary.skipped}`,
            summary.failed > 0 ? 'warning' : 'success'
          );
        } else {
          throw new Error(result.message || '场景执行失败');
        }
      } catch (error) {
        console.error('执行场景失败:', error);
        this.showMessage('执行场景失败: ' + error.message, 'error');
      } finally {
        this.executing = false;
        this.executingSceneId = null;
      }
    },

    // 确认删除场景
    confirmDeleteScene(scene) {
      this.sceneToDelete = scene;
      this.showDeleteConfirm = true;
    },

    // 关闭删除确认对话框
    closeDeleteConfirm() {
      this.showDeleteConfirm = false;
      this.sceneToDelete = null;
    },

    // 删除场景
    async deleteScene() {
      // 参数验证
      if (!this.sceneToDelete) {
        this.showMessage('删除场景失败: 场景参数不完整', 'error');
        return;
      }

      if (!this.sceneToDelete.scene_id) {
        this.showMessage('删除场景失败: 场景ID不完整', 'error');
        return;
      }

      this.deleting = true;
      try {
        console.log('🎬 [场景删除] 开始删除场景:', this.sceneToDelete.scene_name, '(ID:', this.sceneToDelete.scene_id, ')');

        const result = await window.electronAPI.invoke('delete-scene', this.sceneToDelete.scene_id);

        console.log('🎬 [场景删除] 后端返回结果:', result);

        if (result.success) {
          this.showMessage('场景删除成功', 'success');
          this.showDeleteConfirm = false;
          await this.loadScenes(); // 重新加载场景列表
        } else {
          throw new Error(result.message || '场景删除失败');
        }
      } catch (error) {
        console.error('删除场景失败:', error);
        this.showMessage('删除场景失败: ' + error.message, 'error');
      } finally {
        this.deleting = false;
      }
    },

    // 加载设备控制选项
    async loadDeviceControlOptions() {
      if (!this.selectedDeviceForAction) {
        this.deviceControlOptions = [];
        return;
      }

      try {
        console.log('🎬 [场景调试] 加载设备控制选项, 设备ID:', this.selectedDeviceForAction);

        const result = await window.electronAPI.invoke('get-device-control-options-for-scene', this.selectedDeviceForAction);
        console.log('🎬 [场景调试] 设备控制选项结果:', result);

        if (result.success) {
          this.deviceControlOptions = result.data.controls || [];
          this.newAction = {}; // 重置新动作

          console.log('✅ [场景调试] 设备控制选项加载成功, 数量:', this.deviceControlOptions.length);
          this.deviceControlOptions.forEach((control, index) => {
            console.log(`🎬 [场景调试] 控制选项${index + 1}: ${control.label} (${control.property}) - 类型: ${control.type}`);
            if (control.options) {
              console.log(`🎬 [场景调试] 可选值:`, control.options);
            }
          });
        } else {
          throw new Error(result.message);
        }
      } catch (error) {
        console.error('加载设备控制选项失败:', error);
        this.showMessage('加载设备控制选项失败: ' + error.message, 'error');
      }
    },

    // 添加动作到场景
    async addActionToScene() {
      if (!this.canAddAction) return;

      // 构建新动作列表
      const newActions = [];
      for (const control of this.deviceControlOptions) {
        const value = this.newAction[control.property];
        if (value !== undefined && value !== '') {
          newActions.push({
            did: this.selectedDeviceForAction,
            operation: control.property,
            value: value
          });
        }
      }

      if (newActions.length === 0) return;

      try {
        console.log('🎬 [场景调试] 新增动作:', newActions);

        // 构建完整的动作列表（包括已有动作和新动作）
        const existingActions = this.currentScene.actions || [];
        const allActions = [...existingActions, ...newActions];

        console.log('🎬 [场景调试] 完整动作列表:', allActions);

        // 将动作转换为纯JavaScript对象，避免IPC传递问题
        const pureActions = JSON.parse(JSON.stringify(allActions));

        // 验证完整的动作列表
        const validateResult = await window.electronAPI.invoke('validate-scene-actions', pureActions);
        if (!validateResult.success) {
          throw new Error(validateResult.message);
        }

        console.log('✅ [场景调试] 动作验证成功');

        // 添加到当前场景
        if (!this.currentScene.actions) {
          this.currentScene.actions = [];
        }
        this.currentScene.actions.push(...newActions);

        // 重置表单
        this.selectedDeviceForAction = '';
        this.deviceControlOptions = [];
        this.newAction = {};

        this.showMessage('动作添加成功', 'success');
      } catch (error) {
        console.error('添加动作失败:', error);
        this.showMessage('添加动作失败: ' + error.message, 'error');
      }
    },

    // 从场景中移除动作
    removeActionFromScene(index) {
      if (this.currentScene.actions && index >= 0 && index < this.currentScene.actions.length) {
        this.currentScene.actions.splice(index, 1);
      }
    },

    // 获取设备名称
    getDeviceName(deviceId) {
      const device = this.availableDevices.find(d => d.did === deviceId);
      return device ? device.name : deviceId;
    },

    // 获取动作描述
    getActionDescription(action) {
      return `${action.operation}: ${action.value}`;
    },

    // 获取分组名称
    getGroupName(groupId) {
      const group = this.groupList.find(g => g.gid === groupId);
      return group ? group.gname : groupId;
    },

    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return '未知';
      try {
        return new Date(dateString).toLocaleDateString();
      } catch {
        return dateString;
      }
    },

    // 格式化选项标签
    formatOptionLabel(property, option) {
      // 为不同属性的选项提供中文标签
      const labelMaps = {
        power: {
          'ON': '开启',
          'OFF': '关闭'
        },
        mode: {
          'cool': '制冷',
          'heat': '制热',
          'dry': '除湿',
          'fan': '送风',
          'auto': '自动',
          'sleep': '睡眠',
          'strong': '强力',
          'silent': '静音'
        },
        fan_speed: {
          'low': '低速',
          'medium': '中速',
          'high': '高速',
          'auto': '自动'
        },
        status: {
          'running': '运行中',
          'paused': '暂停',
          'off': '关闭'
        },
        fan_level: {
          1: '1档',
          2: '2档',
          3: '3档'
        }
      };

      const propertyLabels = labelMaps[property];
      if (propertyLabels && propertyLabels[option]) {
        return propertyLabels[option];
      }

      return option;
    },

    // 显示消息
    showMessage(message, type = 'info') {
      // 这里可以集成具体的消息提示组件
      console.log(`[${type.toUpperCase()}] ${message}`);

      // 简单的消息提示实现
      if (this.$message) {
        this.$message({
          message: message,
          type: type,
          duration: 3000
        });
      } else {
        // 备用提示方式
        alert(message);
      }
    }
  }
}
</script>

<style scoped>
.scene-mode {
  padding: 20px;
}

.scene-header {
  margin-bottom: 30px;
  text-align: center;
}

.scene-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.scene-subtitle {
  color: #909399;
  font-size: 14px;
  margin-bottom: 20px;
}

.new-scene-btn {
  padding: 10px 20px;
  background-color: #67c23a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.new-scene-btn:hover {
  background-color: #5daf34;
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-scenes {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.scene-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.scene-card {
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.scene-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.scene-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.scene-name {
  font-size: 16px;
  color: #303133;
  margin: 0;
}

.scene-actions {
  display: flex;
  gap: 8px;
}

.apply-scene-btn {
  padding: 6px 12px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.apply-scene-btn:hover:not(:disabled) {
  background-color: #337ecc;
}

.apply-scene-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.delete-scene-btn {
  padding: 6px 12px;
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.delete-scene-btn:hover {
  background-color: #f24c4c;
}

.scene-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.4;
}

.scene-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

/* 模态框样式 */
.modal-overlay {
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
  max-height: 90%;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.scene-detail-modal {
  width: 800px;
}

.create-scene-modal,
.delete-confirm-modal {
  width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  font-size: 18px;
  color: #303133;
  margin: 0;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: 15px 20px;
  border-top: 1px solid #eee;
  gap: 10px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: none;
}

.btn-cancel {
  background-color: #fff;
  color: #606266;
  border: 1px solid #ddd;
}

.btn-confirm {
  background-color: #409eff;
  color: white;
}

.btn-confirm:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.btn-danger {
  background-color: #f56c6c;
}

.btn-danger:hover:not(:disabled) {
  background-color: #f24c4c;
}

/* 表单样式 */
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
  border-color: #409eff;
}

.form-error {
  border-color: #f56c6c !important;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

/* 场景详情样式 */
.scene-basic-info {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #eee;
}

.scene-basic-info p {
  margin-bottom: 8px;
  font-size: 14px;
}

.section-title {
  font-size: 16px;
  color: #303133;
  margin: 20px 0 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: #909399;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.scene-actions-list {
  margin-bottom: 20px;
}

.scene-action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
}

.action-info {
  flex: 1;
}

.device-name {
  font-weight: bold;
  color: #303133;
  margin-right: 10px;
}

.action-detail {
  color: #606266;
  font-size: 14px;
}

.remove-action-btn {
  padding: 4px 8px;
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.add-actions-section {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.device-selector {
  margin-bottom: 15px;
}

.device-selector label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.device-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.control-options {
  margin-top: 15px;
}

.control-option {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.control-option label {
  min-width: 80px;
  font-size: 14px;
  color: #606266;
}

.control-select,
.control-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.add-action-btn {
  padding: 8px 16px;
  background-color: #67c23a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.add-action-btn:hover:not(:disabled) {
  background-color: #5daf34;
}

.add-action-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.warning-text {
  color: #f56c6c;
  font-size: 14px;
  margin-top: 10px;
}
</style>

<template>
  <div class="device-manager">
    <!-- 标题控制栏 -->
    <div class="control-bar">
      <div class="group-selector">
        <select v-model="currentGroup" @change="handleGroupChange" class="group-dropdown">
          <option v-for="group in groupList" :key="group.gid" :value="group.gid">
            {{ group.gname }}
          </option>
        </select>
        <button class="new-group-btn" @click="showCreateDialog">
          <i class="icon-plus"></i> 新建分组
        </button>
        <!-- 删除分组按钮 -->
        <button
          class="delete-group-btn"
          @click="showDeleteDialog"
          :disabled="!canDeleteCurrentGroup"
        >
          <i class="icon-trash"></i> 删除分组
        </button>
      </div>

      <div class="info-panel">
        <span class="info-item">总设备数: {{ totalDeviceCount }}</span>
        <span class="info-item">当前分组: {{ currentDeviceCount }} 个设备</span>
        <span class="info-item">传感器数: {{ sensorDeviceCount }}</span>
      </div>
    </div>

    <!-- 设备信息展示 -->
    <div class="device-panels">
      <div v-for="device in currentDevices" :key="device.did" class="device-card">
        <h3 class="device-title">{{ device.name }}</h3>
        <div class="device-status">
          <div class="status-item">
            <span class="label">状态：</span>
            <span class="value">
              <span class="current-value" :class="device.online ? 'online' : 'offline'">
                {{ device.online ? '在线' : '离线' }}
              </span>
            </span>
          </div>
          <div class="status-item">
            <span class="label">类型：</span>
            <span class="value">{{ getDeviceTypeName(device.type) }}</span>
          </div>
          <div class="status-item">
            <span class="label">品牌：</span>
            <span class="value">{{ device.brand }}</span>
          </div>
          <!-- 传感器数据显示 -->
          <div v-if="isSensorDevice(device)" class="sensor-data">
            <div v-if="device.status.temperature" class="status-item">
              <span class="label">温度：</span>
              <span class="value">{{ device.status.temperature }}℃</span>
            </div>
            <div v-if="device.status.humidity" class="status-item">
              <span class="label">湿度：</span>
              <span class="value">{{ device.status.humidity }}%</span>
            </div>
            <div v-if="device.status.pm25" class="status-item">
              <span class="label">PM2.5：</span>
              <span class="value">{{ device.status.pm25 }}μg/m³</span>
            </div>
          </div>
          <!-- 可控制设备状态显示 -->
          <div v-else class="control-data">
            <div v-for="(value, key) in device.status" :key="key" class="status-item">
              <span class="label">{{ getStatusLabel(key) }}：</span>
              <span class="value">{{ formatStatusValue(key, value) }}</span>
            </div>
          </div>
        </div>
        <div class="device-id">设备ID：{{ device.did }}</div>
        <div class="device-actions">
          <button 
            v-if="!isSensorDevice(device)" 
            class="control-btn" 
            @click="showControlDialog(device)"
            :disabled="!device.online"
          >
            设备控制
          </button>
          <button 
            class="move-btn" 
            @click="showMoveDialog(device)"
          >
            移动分组
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态显示 -->
    <div v-if="currentDevices.length === 0" class="empty-state">
      <p>当前分组没有设备</p>
      <button class="refresh-btn" @click="refreshData">刷新数据</button>
    </div>

    <!-- 新建分组对话框 -->
    <div v-if="showCreateGroup" class="modal-overlay" @click="closeCreateDialog">
      <div class="modal-content" @click.stop>
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
              @keyup.enter="confirmCreateGroup"
            />
            <div v-if="groupErrors.name" class="error-message">{{ groupErrors.name }}</div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeCreateDialog">取消</button>
          <button class="btn-confirm" @click="confirmCreateGroup" :disabled="loading">
            {{ loading ? '创建中...' : '确认' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除分组对话框 -->
    <div v-if="showDeleteGroup" class="modal-overlay" @click="closeDeleteDialog">
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">删除分组</h3>
        <div class="modal-form">
          <div class="form-group">
            <p>
              确定要删除 <span class="delete-group-name">{{ currentGroupInfo?.gname }}</span> 分组吗？
            </p>
            <p class="form-note">该分组下的所有设备将移至默认分组。</p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeDeleteDialog">取消</button>
          <button class="btn-confirm" @click="confirmDeleteGroup" :disabled="loading">
            {{ loading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 设备控制对话框 -->
    <div v-if="showControlDevice" class="modal-overlay" @click="closeControlDialog">
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">设备控制 - {{ currentDevice?.name }}</h3>
        <div class="modal-form">
          <div v-for="control in deviceControls" :key="control.property" class="form-group">
            <label>{{ control.label }}</label>
            <select 
              v-if="control.type === 'select'" 
              v-model="controlParams[control.property]"
              class="form-control"
            >
              <option v-for="option in control.options" :key="option" :value="option">
                {{ formatControlOption(control.property, option) }}
              </option>
            </select>
            <input 
              v-else-if="control.type === 'number'" 
              type="number"
              v-model.number="controlParams[control.property]"
              :min="control.min"
              :max="control.max"
              :step="control.step || 1"
              class="form-control"
            />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeControlDialog">取消</button>
          <button class="btn-confirm" @click="confirmControlDevice" :disabled="loading">
            {{ loading ? '控制中...' : '执行控制' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 移动设备对话框 -->
    <div v-if="showMoveDevice" class="modal-overlay" @click="closeMoveDialog">
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">移动设备 - {{ currentDevice?.name }}</h3>
        <div class="modal-form">
          <div class="form-group">
            <label>目标分组</label>
            <select v-model="targetGroupId" class="form-control">
              <option v-for="group in groupList" :key="group.gid" :value="group.gid">
                {{ group.gname }}
              </option>
            </select>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeMoveDialog">取消</button>
          <button class="btn-confirm" @click="confirmMoveDevice" :disabled="loading">
            {{ loading ? '移动中...' : '确认移动' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 使用预加载脚本暴露的ipcRenderer
const ipcRenderer = window.ipcRenderer;

export default {
  name: 'GroupManagement',
  data() {
    return {
      // 分组相关
      groupList: [],
      currentGroup: null,
      showCreateGroup: false,
      newGroupForm: { name: '' },
      groupErrors: { name: '' },
      
      // 设备数据
      allDevices: [],
      currentDevices: [],
      
      // 状态管理
      loading: false,
      totalDeviceCount: 0,
      currentDeviceCount: 0,
      sensorDeviceCount: 0,
      
      // 对话框状态
      showDeleteGroup: false,
      currentGroupInfo: null,
      showControlDevice: false,
      showMoveDevice: false,
      currentDevice: null,
      
      // 设备控制相关
      deviceControls: [],
      controlParams: {},
      targetGroupId: null,
      
      // 设备类型映射
      deviceTypeMap: {
        'mi_temp_hum_sensor': '小米温湿度计',
        'mi_air_sensor': '青萍空气质量检测仪',
        'mi_ac': '小米空调',
        'midea_ac': '美的空调',
        'mi_humidifier': '小米加湿器',
        'midea_humidifier': '美的加湿器'
      },
      
      // 状态标签映射
      statusLabelMap: {
        'power': '电源',
        'target_temperature': '目标温度',
        'mode': '模式',
        'fan_speed': '风速',
        'target_humidity': '目标湿度'
      }
    }
  },

  computed: {
    canDeleteCurrentGroup() {
      const currentGroupObj = this.groupList.find(g => g.gid === this.currentGroup);
      return currentGroupObj && currentGroupObj.gname !== '默认分组' && this.groupList.length > 1;
    }
  },

  async mounted() {
    console.log('🎯 [前端调试] 分组管理页面已挂载');
    console.log('🎯 [前端调试] 开始初始化数据...');
    
    // 检查是否为离线调试模式
    this.checkOfflineDebugMode();
    
    await this.initializeData();
    console.log('🎯 [前端调试] 页面初始化完成');
  },

  methods: {
    // 检查离线调试模式
    checkOfflineDebugMode() {
      // 检查当前用户是否为admin或者localStorage中是否有离线标记
      const currentUser = localStorage.getItem('currentUser');
      const isOfflineMode = localStorage.getItem('offlineDebugMode');
      
      if (currentUser === 'admin' || isOfflineMode === 'true') {
        console.log('🟡 [前端调试] 检测到离线调试模式');
        this.$nextTick(() => {
          this.$message({
            message: '当前为离线调试模式，分组功能使用本地数据',
            type: 'info',
            duration: 3000,
            showClose: true
          });
        });
      }
    },

    // 初始化数据
    async initializeData() {
      console.log('🎯 [前端调试] 开始初始化数据流程');
      this.loading = true;
      try {
        console.log('🎯 [前端调试] 并行加载分组和设备数据...');
        await Promise.all([
          this.loadGroups(),
          this.loadDevices()
        ]);
        
        console.log('🎯 [前端调试] 数据加载完成，设置默认分组...');
        console.log('🎯 [前端调试] 分组列表长度:', this.groupList.length);
        console.log('🎯 [前端调试] 当前选中分组:', this.currentGroup);
        
        // 设置默认分组
        if (this.groupList.length > 0 && !this.currentGroup) {
          const defaultGroup = this.groupList.find(g => g.gname === '默认分组');
          console.log('🎯 [前端调试] 找到的默认分组:', defaultGroup);
          this.currentGroup = defaultGroup ? defaultGroup.gid : this.groupList[0].gid;
          console.log('🎯 [前端调试] 设置当前分组为:', this.currentGroup);
        }
        
        console.log('🎯 [前端调试] 更新当前设备和统计信息...');
        this.updateCurrentDevices();
        this.updateStatistics();
        
        console.log('✅ [前端调试] 数据初始化完成');
      } catch (error) {
        console.error('❌ [前端调试] 初始化数据失败:', error);
        this.$message.error('初始化数据失败');
      } finally {
        this.loading = false;
        console.log('🎯 [前端调试] 初始化流程结束，loading状态已清除');
      }
    },

    // 加载分组列表
    async loadGroups() {
      console.log('🔍 [前端调试] 开始加载分组列表');
      try {
        console.log('🔍 [前端调试] 调用electron API: get-all-groups');
        const result = await ipcRenderer.invoke('get-all-groups');
        console.log('🔍 [前端调试] API返回结果:', result);
        
        if (result.success) {
          this.groupList = result.data;
          console.log('✅ [前端调试] 分组列表加载成功, 数量:', this.groupList.length);
          console.log('🔍 [前端调试] 分组列表详情:', this.groupList);
        } else {
          console.error('❌ [前端调试] 加载分组失败:', result.message);
        }
      } catch (error) {
        console.error('❌ [前端调试] 加载分组列表失败:', error);
      }
    },

    // 加载设备列表
    async loadDevices() {
      try {
        const result = await ipcRenderer.invoke('get-all-devices');
        if (result.success) {
          this.allDevices = result.data;
          this.totalDeviceCount = this.allDevices.length;
          console.log('设备列表加载成功:', this.allDevices);
        } else {
          console.error('加载设备失败:', result.message);
        }
      } catch (error) {
        console.error('加载设备列表失败:', error);
      }
    },

    // 更新当前分组设备
    async updateCurrentDevices() {
      if (!this.currentGroup) {
        this.currentDevices = [];
        return;
      }

      try {
        const result = await ipcRenderer.invoke('get-devices-by-group', this.currentGroup);
        if (result.success) {
          this.currentDevices = result.data;
        } else {
          this.currentDevices = [];
        }
      } catch (error) {
        console.error('获取分组设备失败:', error);
        this.currentDevices = [];
      }
    },

    // 更新统计信息
    updateStatistics() {
      this.currentDeviceCount = this.currentDevices.length;
      this.sensorDeviceCount = this.currentDevices.filter(device => 
        this.isSensorDevice(device)
      ).length;
    },

    // 分组变更处理
    async handleGroupChange() {
      console.log('分组变更:', this.currentGroup);
      await this.updateCurrentDevices();
      this.updateStatistics();
    },

    // 刷新数据
    async refreshData() {
      await this.initializeData();
      this.$message.success('数据刷新成功');
    },

    // ==================== 分组管理相关方法 ====================
    
    // 显示创建分组对话框
    showCreateDialog() {
      this.showCreateGroup = true;
      this.newGroupForm.name = '';
      this.groupErrors.name = '';
    },

    // 关闭创建分组对话框
    closeCreateDialog() {
      this.showCreateGroup = false;
    },

    // 确认创建分组
    async confirmCreateGroup() {
      console.log('🔍 [前端调试] 开始创建分组');
      console.log('🔍 [前端调试] 分组名称:', this.newGroupForm.name);
      
      if (!this.validateGroupForm()) {
        console.log('❌ [前端调试] 表单验证失败');
        return;
      }

      this.loading = true;
      try {
        console.log('🔍 [前端调试] 调用electron API: create-group');
        const result = await ipcRenderer.invoke('create-group', this.newGroupForm.name);
        console.log('🔍 [前端调试] 创建分组API返回:', result);
        
        if (result.success) {
          console.log('✅ [前端调试] 分组创建成功, 新分组信息:', result.data);
          this.$message.success('分组创建成功');
          
          console.log('🔍 [前端调试] 重新加载分组列表...');
          await this.loadGroups();
          
          this.currentGroup = result.data.gid;
          console.log('🔍 [前端调试] 切换到新创建的分组:', this.currentGroup);
          
          await this.updateCurrentDevices();
          this.closeCreateDialog();
        } else {
          console.log('❌ [前端调试] 分组创建失败:', result.message);
          this.$message.error(result.message || '创建分组失败');
        }
      } catch (error) {
        console.error('❌ [前端调试] 创建分组异常:', error);
        this.$message.error('创建分组失败');
      } finally {
        this.loading = false;
        console.log('🔍 [前端调试] 创建分组流程结束');
      }
    },

    // 验证分组表单
    validateGroupForm() {
      this.groupErrors.name = '';

      if (!this.newGroupForm.name) {
        this.groupErrors.name = '请输入分组名称';
        return false;
      }
      
      if (this.newGroupForm.name.length < 2 || this.newGroupForm.name.length > 20) {
        this.groupErrors.name = '分组名称长度应在2到20个字符之间';
        return false;
      }

      if (this.groupList.some(group => group.gname === this.newGroupForm.name)) {
        this.groupErrors.name = '分组名称已存在';
        return false;
      }

      return true;
    },

    // 显示删除分组对话框
    showDeleteDialog() {
      this.currentGroupInfo = this.groupList.find(group => group.gid === this.currentGroup);
      this.showDeleteGroup = true;
    },

    // 关闭删除分组对话框
    closeDeleteDialog() {
      this.showDeleteGroup = false;
    },

    // 确认删除分组
    async confirmDeleteGroup() {
      console.log('🔍 [前端调试] 开始删除分组');
      console.log('🔍 [前端调试] 当前分组信息:', this.currentGroupInfo);
      console.log('🔍 [前端调试] 要删除的分组ID:', this.currentGroup);
      
      if (!this.currentGroupInfo || this.currentGroupInfo.gname === '默认分组') {
        console.log('❌ [前端调试] 默认分组不允许删除');
        this.$message.error('默认分组不允许删除');
        return;
      }

      this.loading = true;
      try {
        console.log('🔍 [前端调试] 调用electron API: delete-group');
        const result = await ipcRenderer.invoke('delete-group', this.currentGroup);
        console.log('🔍 [前端调试] 删除分组API返回:', result);
        
        if (result.success) {
          console.log('✅ [前端调试] 分组删除成功');
          this.$message.success('分组删除成功');
          
          console.log('🔍 [前端调试] 重新加载分组列表...');
          await this.loadGroups();
          
          // 切换到默认分组
          const defaultGroup = this.groupList.find(g => g.gname === '默认分组');
          console.log('🔍 [前端调试] 查找默认分组:', defaultGroup);
          
          this.currentGroup = defaultGroup ? defaultGroup.gid : this.groupList[0]?.gid;
          console.log('🔍 [前端调试] 切换到分组:', this.currentGroup);
          
          await this.updateCurrentDevices();
          this.closeDeleteDialog();
        } else {
          console.log('❌ [前端调试] 分组删除失败:', result.message);
          this.$message.error(result.message || '删除分组失败');
        }
      } catch (error) {
        console.error('❌ [前端调试] 删除分组异常:', error);
        this.$message.error('删除分组失败');
      } finally {
        this.loading = false;
        console.log('🔍 [前端调试] 删除分组流程结束');
      }
    },

    // ==================== 设备控制相关方法 ====================
    
    // 显示设备控制对话框
    async showControlDialog(device) {
      this.currentDevice = device;
      
      try {
        const result = await ipcRenderer.invoke('get-device-control-options', device.did);
        if (result.success) {
          this.deviceControls = result.data.controls;
          this.controlParams = {};
          
          // 初始化控制参数
          this.deviceControls.forEach(control => {
            this.controlParams[control.property] = device.status[control.property] || 
              (control.type === 'select' ? control.options[0] : control.min || 0);
          });
          
          this.showControlDevice = true;
        } else {
          this.$message.error('获取设备控制选项失败');
        }
      } catch (error) {
        console.error('获取设备控制选项失败:', error);
        this.$message.error('获取设备控制选项失败');
      }
    },

    // 关闭设备控制对话框
    closeControlDialog() {
      this.showControlDevice = false;
    },

    // 确认设备控制
    async confirmControlDevice() {
      if (!this.currentDevice) return;

      this.loading = true;
      try {
        const controlPromises = Object.entries(this.controlParams).map(([operation, value]) => {
          return ipcRenderer.invoke('control-device', {
            did: this.currentDevice.did,
            operation,
            value
          });
        });

        const results = await Promise.all(controlPromises);
        const successCount = results.filter(r => r.success).length;
        
        if (successCount > 0) {
          this.$message.success(`设备控制成功 (${successCount}/${results.length})`);
          await this.loadDevices();
          await this.updateCurrentDevices();
          this.closeControlDialog();
        } else {
          this.$message.error('设备控制失败');
        }
      } catch (error) {
        console.error('设备控制失败:', error);
        this.$message.error('设备控制失败');
      } finally {
        this.loading = false;
      }
    },

    // 显示移动设备对话框
    showMoveDialog(device) {
      this.currentDevice = device;
      this.targetGroupId = this.currentGroup;
      this.showMoveDevice = true;
    },

    // 关闭移动设备对话框
    closeMoveDialog() {
      this.showMoveDevice = false;
    },

    // 确认移动设备
    async confirmMoveDevice() {
      if (!this.currentDevice || !this.targetGroupId) return;

      this.loading = true;
      try {
        const result = await ipcRenderer.invoke('set-device-group', this.currentDevice.did, this.targetGroupId);
        if (result.success) {
          this.$message.success('设备移动成功');
          await this.updateCurrentDevices();
          this.closeMoveDialog();
        } else {
          this.$message.error(result.message || '设备移动失败');
        }
      } catch (error) {
        console.error('设备移动失败:', error);
        this.$message.error('设备移动失败');
      } finally {
        this.loading = false;
      }
    },

    // ==================== 工具方法 ====================
    
    // 判断是否为传感器设备
    isSensorDevice(device) {
      return device.type === 'mi_temp_hum_sensor' || device.type === 'mi_air_sensor';
    },

    // 获取设备类型名称
    getDeviceTypeName(type) {
      return this.deviceTypeMap[type] || type;
    },

    // 获取状态标签
    getStatusLabel(key) {
      return this.statusLabelMap[key] || key;
    },

    // 格式化状态值
    formatStatusValue(key, value) {
      switch (key) {
        case 'power':
          return value === 'ON' ? '开启' : '关闭';
        case 'mode':
          const modeMap = { 'cool': '制冷', 'heat': '制热', 'dry': '除湿', 'fan': '送风' };
          return modeMap[value] || value;
        case 'fan_speed':
          const speedMap = { 'low': '低速', 'medium': '中速', 'high': '高速', 'auto': '自动' };
          return speedMap[value] || value;
        case 'target_temperature':
          return `${value}℃`;
        case 'target_humidity':
          return `${value}%`;
        default:
          return value;
      }
    },

    // 格式化控制选项
    formatControlOption(property, option) {
      return this.formatStatusValue(property, option);
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
.device-manager {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

/* 控制栏样式 */
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
  gap: 10px;
}

.group-dropdown {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
}

.new-group-btn, .delete-group-btn {
  padding: 8px 16px;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.new-group-btn {
  background-color: #42b983;
}

.new-group-btn:hover {
  background-color: #38a169;
}

.delete-group-btn {
  background-color: #e53e3e;
}

.delete-group-btn:hover:not(:disabled) {
  background-color: #c53030;
}

.delete-group-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.icon-plus::before {
  content: '+';
}

.icon-trash::before {
  content: '🗑';
}

.info-panel {
  display: flex;
  gap: 20px;
}

.info-item {
  color: #666;
  font-size: 14px;
}

/* 设备卡片样式 */
.device-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.device-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.device-title {
  color: #303133;
  margin-bottom: 15px;
  font-size: 16px;
  font-weight: 600;
}

.device-status {
  margin-bottom: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.label {
  color: #606266;
  font-weight: 500;
}

.value {
  color: #303133;
}

.current-value.online {
  color: #67c23a;
}

.current-value.offline {
  color: #f56c6c;
}

.device-id {
  color: #909399;
  font-size: 12px;
  margin-bottom: 15px;
}

.device-actions {
  display: flex;
  gap: 10px;
}

.control-btn, .move-btn {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  flex: 1;
}

.control-btn {
  color: #409eff;
  border-color: #409eff;
}

.control-btn:hover:not(:disabled) {
  background: #409eff;
  color: white;
}

.control-btn:disabled {
  color: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.move-btn {
  color: #67c23a;
  border-color: #67c23a;
}

.move-btn:hover {
  background: #67c23a;
  color: white;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.refresh-btn {
  margin-top: 15px;
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  min-width: 400px;
  max-width: 500px;
}

.modal-title {
  color: #303133;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
}

.modal-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #606266;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-control:focus {
  outline: none;
  border-color: #409eff;
}

.form-error {
  border-color: #f56c6c !important;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.form-note {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}

.delete-group-name {
  color: #f56c6c;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel {
  background: #fff;
  color: #606266;
}

.btn-cancel:hover {
  background: #f5f7fa;
}

.btn-confirm {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.btn-confirm:hover:not(:disabled) {
  background: #337ecc;
}

.btn-confirm:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}
</style>

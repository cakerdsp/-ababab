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

      <!-- 模式切换按钮 -->
      <div class="mode-switch">
        <div
          class="mode-radio"
          :class="{ 'mode-radio-active': currentMode === 'manual' }"
          @click="switchMode('manual')"
        >
          手动模式
        </div>
        <div
          class="mode-radio"
          :class="{ 'mode-radio-active': currentMode === 'scene' }"
          @click="switchMode('scene')"
        >
          场景模式
        </div>
        <div
          class="mode-radio"
          :class="{ 'mode-radio-active': currentMode === 'preset' }"
          @click="switchMode('preset')"
        >
          预设策略
        </div>
      </div>

      <div class="info-panel">
        <span class="info-item">总设备数: {{ totalDeviceCount }}</span>
        <span class="info-item">当前分组: {{ currentDeviceCount }} 个设备</span>
        <span class="info-item">传感器数: {{ sensorDeviceCount }}</span>
        <span class="info-item refresh-status" :class="{ 'refreshing': isAutoRefreshing }">
          {{ refreshStatusText }}
        </span>
        <button
          class="debug-btn"
          @click="debugDeviceStorage"
          title="调试设备存储状态（输出到控制台）"
        >
          🔍 调试
        </button>
      </div>
    </div>

    <!-- 设备信息展示 - 仅在手动模式下显示 -->
    <div v-if="currentMode === 'manual'" class="device-panels">
      <div v-for="device in currentDevices" :key="device.did" class="device-card">
        <div class="device-header">
          <h3 class="device-title">{{ device.name }}</h3>
          <span class="device-online-indicator" :class="device.online ? 'online' : 'offline'">
            {{ device.online ? '●' : '●' }}
          </span>
        </div>
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
          <div class="status-item">
            <span class="label">最后更新：</span>
            <span class="value">{{ getLastUpdatedDisplay(device) }}</span>
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
            :disabled="false"
          >
            设备控制
          </button>
          <button
            v-if="!isSensorDevice(device)"
            class="test-api-btn"
            @click="testControlAPI(device)"
            title="测试控制API（调试用）"
          >
            测试API
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

    <!-- 空状态显示 - 仅在手动模式下显示 -->
    <div v-if="currentMode === 'manual' && currentDevices.length === 0 && !loading" class="empty-state">
      <p>当前分组没有设备</p>
              <button class="refresh-btn" @click="refreshData" :disabled="loading">
          {{ loading ? '刷新中...' : '刷新数据' }}
        </button>
        <button v-if="isAdminDebugMode" class="clear-devices-btn" @click="clearAndRegenerateDevices" :disabled="loading">
          {{ loading ? '重新生成中...' : '重新生成设备数据' }}
        </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>数据加载中...</p>
    </div>

    <!-- 场景模式内容 -->
    <div v-if="currentMode === 'scene'">
      <SceneModeControl :current-group="currentGroup" />
    </div>

    <!-- 预设策略控制 - 仅在预设策略模式下显示 -->
    <div v-if="currentMode === 'preset'">
      <PresetStrategyControl
        :current-group="currentGroup"
        @strategy-changed="handleStrategyChanged"
        @strategy-executed="handleStrategyExecuted"
      />
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
      <div class="modal-content move-device-dialog" @click.stop>
        <h3 class="modal-title">移动设备 - {{ currentDevice?.name }}</h3>
        <div class="modal-form">
          <div class="form-group">
            <label>当前分组</label>
            <div class="current-group-info">
              {{ getCurrentGroupName() }}
              <span class="device-count">(共 {{ getCurrentGroupDeviceCount() }} 个设备)</span>
            </div>
          </div>

          <div class="form-group">
            <label>选择移动方式</label>
            <div class="move-mode-selector">
              <label class="radio-option">
                <input type="radio" v-model="moveDeviceMode" value="select" />
                <span>从列表选择</span>
              </label>
              <label class="radio-option">
                <input type="radio" v-model="moveDeviceMode" value="input" />
                <span>手动输入分组名</span>
              </label>
            </div>
          </div>

          <!-- 下拉选择模式 -->
          <div v-if="moveDeviceMode === 'select'" class="form-group">
            <label>可移动的分组</label>
            <select v-model="targetGroupId" class="form-control" :class="{ 'form-error': moveDeviceErrors.select }">
              <option value="">请选择目标分组</option>
              <option v-for="group in availableGroups" :key="group.gid" :value="group.gid">
                {{ group.gname }} ({{ group.device_count }} 个设备)
              </option>
            </select>
            <div v-if="moveDeviceErrors.select" class="error-message">{{ moveDeviceErrors.select }}</div>
            <div v-if="availableGroups.length === 0" class="info-message">
              没有可移动的分组，设备已在所有分组中或只有一个分组
            </div>
          </div>

          <!-- 手动输入模式 -->
          <div v-if="moveDeviceMode === 'input'" class="form-group">
            <label>分组名称</label>
            <input
              type="text"
              v-model="targetGroupName"
              @blur="validateGroupNameInput"
              @input="clearGroupNameError"
              class="form-control"
              :class="{ 'form-error': moveDeviceErrors.groupName }"
              placeholder="请输入已存在的分组名称"
            />
            <div v-if="moveDeviceErrors.groupName" class="error-message">{{ moveDeviceErrors.groupName }}</div>
            <div v-if="!moveDeviceErrors.groupName && targetGroupName && targetGroupId" class="success-message">
              ✓ 找到分组"{{ targetGroupName }}"
            </div>
          </div>

          <!-- 移动预览 -->
          <div v-if="targetGroupId" class="form-group move-preview">
            <label>移动预览</label>
            <div class="preview-info">
              将设备"{{ currentDevice?.name }}"从"{{ getCurrentGroupName() }}"移动到"{{ getTargetGroupName() }}"
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeMoveDialog">取消</button>
          <button class="btn-confirm" @click="confirmMoveDevice" :disabled="loading || !targetGroupId">
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
import PresetStrategyControl from '../../../components/PresetStrategyControl.vue';
import SceneModeControl from '../../../components/SceneModeControl.vue';

export default {
  name: 'GroupManagement',
  components: {
    PresetStrategyControl,
    SceneModeControl
  },
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

      // 设备移动相关
      targetGroupId: null,
      targetGroupName: '',
      moveDeviceMode: 'select', // 'select' 或 'input'
      availableGroups: [],
      moveDeviceErrors: {},

      // 自动刷新相关
      autoRefreshTimer: null,
      autoRefreshInterval: 30000, // 30秒自动刷新
      lastRefreshTime: null,
      isAutoRefreshing: false,

      // 设备类型映射
      deviceTypeMap: {
        'mi_temp_hum_sensor': '小米温湿度计',
        'mi_air_sensor': '青萍空气质量检测仪',
        'mi_ac': '小米空调',
        'midea_ac': '美的空调',
        'mi_humidifier': '小米加湿器',
        'midea_humidifier': '美的加湿器',
        'midea_dehumidifier': '美的除湿器',
        'midea_air_purifier': '美的空气净化器',
        'mi_air_purifier': '小米空气净化器',
        'history': '传感器设备'
      },

      // 状态标签映射
      statusLabelMap: {
        'power': '电源',
        'target_temperature': '目标温度',
        'mode': '模式',
        'fan_speed': '风速',
        'target_humidity': '目标湿度'
      },

      // 模式切换相关
      currentMode: 'manual', // 默认为手动模式

      // 场景执行监听器
      sceneExecutionHandler: null
    }
  },

      computed: {
    canDeleteCurrentGroup() {
      const currentGroupObj = this.groupList.find(g => g.gid === this.currentGroup);
      return currentGroupObj && currentGroupObj.gname !== '默认分组' && this.groupList.length > 1;
    },

    // 计算刷新状态文本
    refreshStatusText() {
      if (this.isAutoRefreshing) {
        return '自动刷新中...';
      }
      if (this.lastRefreshTime) {
        const now = new Date();
        const diff = Math.floor((now - this.lastRefreshTime) / 1000);
        if (diff < 60) {
          return `${diff}秒前刷新`;
        } else {
          return `${Math.floor(diff / 60)}分钟前刷新`;
        }
      }
      return '未刷新';
    },

    // 检查是否为admin调试模式
    isAdminDebugMode() {
      const currentUser = localStorage.getItem('currentUser');
      return currentUser === 'admin';
    }
  },

  async mounted() {
    console.log('🎯 [前端调试] 分组管理页面已挂载');
    console.log('🎯 [前端调试] 开始初始化数据...');

    // 检查是否为离线调试模式
    this.checkOfflineDebugMode();

    await this.initializeData();

    // 启动自动刷新定时器
    this.startAutoRefresh();

    // 监听场景执行后的设备状态刷新事件
    this.setupSceneExecutionListener();

    console.log('🎯 [前端调试] 页面初始化完成');
  },

  beforeUnmount() {
    // 清理定时器
    this.stopAutoRefresh();

    // 移除场景执行监听器
    this.removeSceneExecutionListener();

    console.log('🎯 [前端调试] 分组管理页面已卸载，定时器已清理');
  },

  methods: {
    // 模式切换
    switchMode(mode) {
      console.log('🔄 [前端调试] 切换模式:', mode);
      this.currentMode = mode;

      // 根据模式显示不同的提示信息
      switch (mode) {
        case 'manual':
          this.$message({
            message: '已切换到手动模式',
            type: 'success',
            duration: 2000
          });
          break;
        case 'scene':
          this.$message({
            message: '已切换到场景模式',
            type: 'success',
            duration: 2000
          });
          break;
        case 'preset':
          this.$message({
            message: '预设策略模式已激活',
            type: 'success',
            duration: 2000
          });
          break;
      }
    },

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
        await this.updateCurrentDevices();
        this.updateStatistics();
        this.lastRefreshTime = new Date();

        console.log('✅ [前端调试] 数据初始化完成');
      } catch (error) {
        console.error('❌ [前端调试] 初始化数据失败:', error);
        this.$message.error('初始化数据失败');
      } finally {
        this.loading = false;
        console.log('🎯 [前端调试] 初始化流程结束，loading状态已清除');
      }
    },

    // 启动自动刷新
    startAutoRefresh() {
      console.log('🔄 [前端调试] 启动自动刷新定时器');
      this.autoRefreshTimer = setInterval(async () => {
        if (!this.loading && !this.showControlDevice && !this.showMoveDevice && !this.showCreateGroup && !this.showDeleteGroup) {
          console.log('🔄 [前端调试] 执行自动刷新');
          this.isAutoRefreshing = true;
          await this.refreshDeviceData();
          this.isAutoRefreshing = false;
        }
      }, this.autoRefreshInterval);
    },

    // 停止自动刷新
    stopAutoRefresh() {
      if (this.autoRefreshTimer) {
        clearInterval(this.autoRefreshTimer);
        this.autoRefreshTimer = null;
        console.log('🔄 [前端调试] 自动刷新定时器已停止');
      }
    },

    // 刷新设备数据（不刷新分组列表）
    async refreshDeviceData() {
      try {
        await this.loadDevices();
        await this.updateCurrentDevices();
        this.updateStatistics();
        this.lastRefreshTime = new Date();
      } catch (error) {
        console.error('❌ [前端调试] 刷新设备数据失败:', error);
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

    // 刷新分组统计信息
    async refreshGroupStats() {
      console.log('🔍 [前端调试] 刷新分组统计信息');
      try {
        const result = await ipcRenderer.invoke('refresh-group-stats');
        if (result.success) {
          this.groupList = result.data;
          console.log('✅ [前端调试] 分组统计信息刷新成功');
        }
      } catch (error) {
        console.error('❌ [前端调试] 刷新分组统计失败:', error);
      }
    },

    // 加载设备列表
    async loadDevices() {
      try {
        const result = await ipcRenderer.invoke('get-all-devices');
        if (result.success) {
          this.allDevices = result.data;
          this.totalDeviceCount = this.allDevices.length;
          console.log('🔍 [前端调试] 设备列表加载成功，总数:', this.allDevices.length);

          // 输出设备状态统计
          const onlineCount = this.allDevices.filter(d => d.online).length;
          const offlineCount = this.allDevices.length - onlineCount;
          console.log('🔍 [前端调试] 设备状态统计 - 在线:', onlineCount, '离线:', offlineCount);
        } else {
          console.error('❌ [前端调试] 加载设备失败:', result.message);
        }
      } catch (error) {
        console.error('❌ [前端调试] 加载设备列表失败:', error);
      }
    },

    // 更新当前分组设备
    async updateCurrentDevices() {
      if (!this.currentGroup) {
        this.currentDevices = [];
        return;
      }

      try {
        console.log('🔍 [前端调试] 更新当前分组设备，分组ID:', this.currentGroup);
        const result = await ipcRenderer.invoke('get-devices-by-group', this.currentGroup);
        if (result.success) {
          this.currentDevices = result.data;
          console.log('🔍 [前端调试] 当前分组设备加载成功，数量:', this.currentDevices.length);

          // 输出设备详细状态
          this.currentDevices.forEach(device => {
            console.log(`🔍 [设备状态] ${device.name} (${device.did}) - 在线:${device.online}, 类型:${device.type}, 品牌:${device.brand}`);
            if (device.status) {
              console.log(`🔍 [设备状态] ${device.name} 状态数据:`, device.status);
            }
          });
        } else {
          console.error('❌ [前端调试] 获取分组设备失败:', result.message);
          this.currentDevices = [];
        }
      } catch (error) {
        console.error('❌ [前端调试] 获取分组设备失败:', error);
        this.currentDevices = [];
      }
    },

    // 更新统计信息
    updateStatistics() {
      this.currentDeviceCount = this.currentDevices.length;
      this.sensorDeviceCount = this.currentDevices.filter(device =>
        this.isSensorDevice(device)
      ).length;

      console.log('🔍 [前端调试] 统计信息更新 - 当前分组设备数:', this.currentDeviceCount, '传感器设备数:', this.sensorDeviceCount);
    },

    // 分组变更处理
    async handleGroupChange() {
      console.log('🔍 [前端调试] 分组变更:', this.currentGroup);
      await this.updateCurrentDevices();
      this.updateStatistics();
    },

    // 手动刷新所有数据
    async manualRefresh() {
      console.log('🔄 [前端调试] 手动刷新所有数据');
      this.loading = true;
      try {
        await this.initializeData();
        this.$message.success('数据刷新成功');
      } catch (error) {
        console.error('❌ [前端调试] 手动刷新失败:', error);
        this.$message.error('数据刷新失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },

    // 调试设备存储状态
    async debugDeviceStorage() {
      console.log('🔍 [Debug] 检查设备存储状态');
      try {
        const result = await ipcRenderer.invoke('debug-device-storage');
        if (result.success) {
          console.log('✅ [Debug] 设备存储状态检查完成，详情已输出到控制台');
          this.$message.success('设备存储状态已输出到控制台');
        } else {
          console.error('❌ [Debug] 设备存储状态检查失败:', result.message);
          this.$message.error('设备存储状态检查失败: ' + result.message);
        }
      } catch (error) {
        console.error('❌ [Debug] 设备存储状态检查异常:', error);
        this.$message.error('设备存储状态检查异常');
      }
    },

    // 测试API调用（调试用）
    async testControlAPI(device) {
      console.log('🔍 [Debug] 测试控制API调用:', device.name);
      try {
        const result = await ipcRenderer.invoke('debug-api-call', 'controlDevice', {
          did: device.did,
          control: {
            operation: 'power',
            value: 'OFF'
          }
        });

        if (result.success) {
          console.log('✅ [Debug] API调用成功:', result.data);
          this.$message.success('API调用成功，详情已输出到控制台');
        } else {
          console.error('❌ [Debug] API调用失败:', result.message);
          this.$message.error('API调用失败: ' + result.message);
        }
      } catch (error) {
        console.error('❌ [Debug] API调用异常:', error);
        this.$message.error('API调用异常');
      }
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
      console.log('🎮 [设备控制] 显示控制对话框:', device.name);
      console.log('🎮 [设备控制] 设备信息:', device);

      this.currentDevice = device;

      try {
        const result = await ipcRenderer.invoke('get-device-control-options', device.did);
        console.log('🎮 [设备控制] 获取控制选项结果:', result);

        if (result.success) {
          this.deviceControls = result.data.controls;
          this.controlParams = {};

          console.log('🎮 [设备控制] 可用控制选项:', this.deviceControls);

          // 初始化控制参数，使用后端标准化的设备状态作为默认值
          this.deviceControls.forEach(control => {
            // 优先使用后端返回的标准化currentValue
            const backendCurrentValue = control.currentValue;
            const frontendCurrentValue = device.status?.[control.property];
            let defaultValue;

            if (backendCurrentValue !== undefined && backendCurrentValue !== null) {
              // 使用后端标准化的当前值（推荐）
              defaultValue = backendCurrentValue;
              console.log(`🎮 [设备控制] 使用标准化值: ${control.property}=${defaultValue}`);
            } else if (frontendCurrentValue !== undefined && frontendCurrentValue !== null) {
              // 兜底：使用前端设备状态值
              defaultValue = frontendCurrentValue;
              console.log(`🎮 [设备控制] 使用前端值: ${control.property}=${defaultValue}`);
            } else if (control.type === 'select' && control.options?.length > 0) {
              // 选择类型控件使用第一个选项
              defaultValue = control.options[0];
              console.log(`🎮 [设备控制] 使用默认选项: ${control.property}=${defaultValue}`);
            } else if (control.type === 'number' && control.min !== undefined) {
              // 数值类型控件使用最小值
              defaultValue = control.min;
              console.log(`🎮 [设备控制] 使用最小值: ${control.property}=${defaultValue}`);
            } else {
              // 兜底默认值
              defaultValue = control.type === 'select' ? '' : 0;
              console.log(`🎮 [设备控制] 使用兜底值: ${control.property}=${defaultValue}`);
            }

            this.controlParams[control.property] = defaultValue;
            console.log(`🎮 [设备控制] 最终参数: ${control.property}=${defaultValue} (后端: ${backendCurrentValue}, 前端: ${frontendCurrentValue})`);
          });

          console.log('🎮 [设备控制] 初始化控制参数:', this.controlParams);
          this.showControlDevice = true;
        } else {
          console.error('❌ [设备控制] 获取设备控制选项失败:', result.message);
          this.$message.error(result.message || '获取设备控制选项失败');
        }
      } catch (error) {
        console.error('❌ [设备控制] 获取设备控制选项异常:', error);
        this.$message.error('获取设备控制选项失败: ' + error.message);
      }
    },

    // 关闭设备控制对话框
    closeControlDialog() {
      this.showControlDevice = false;
    },

    // 检测实际发生变化的操作
    getChangedOperations() {
      const changedOps = [];

      this.deviceControls.forEach(control => {
        const property = control.property;
        const currentValue = control.currentValue; // 后端标准化的原始值
        const newValue = this.controlParams[property]; // 用户设置的新值

        // 比较值是否发生变化
        if (this.hasValueChanged(currentValue, newValue)) {
          changedOps.push({
            operation: property,
            value: newValue,
            oldValue: currentValue
          });
          console.log(`🔧 [设备控制] 属性变化: ${property}: ${currentValue} -> ${newValue}`);
        } else {
          console.log(`🔧 [设备控制] 属性无变化: ${property}: ${currentValue}`);
        }
      });

      return changedOps;
    },

    // 检查值是否发生变化（处理不同数据类型的比较）
    hasValueChanged(oldValue, newValue) {
      // 处理null/undefined情况
      if (oldValue == null && newValue == null) return false;
      if (oldValue == null || newValue == null) return true;

      // 字符串类型比较
      if (typeof oldValue === 'string' && typeof newValue === 'string') {
        return oldValue !== newValue;
      }

      // 数值类型比较（考虑精度）
      if (typeof oldValue === 'number' && typeof newValue === 'number') {
        return Math.abs(oldValue - newValue) > 0.001;
      }

      // 其他类型严格比较
      return oldValue !== newValue;
    },

    // 确认设备控制
    async confirmControlDevice() {
      if (!this.currentDevice) return;

      console.log('🎮 [设备控制] 开始执行设备控制:', this.currentDevice.name);
      console.log('🎮 [设备控制] 控制参数:', this.controlParams);

      this.loading = true;
      const controlResults = [];

      try {
        // 检测实际发生变化的属性（只控制变化的属性）
        const changedOperations = this.getChangedOperations();
        console.log('🔧 [设备控制] 检测到变化的属性:', changedOperations);

        if (changedOperations.length === 0) {
          this.$message.info('没有检测到任何变化');
          this.loading = false;
          return;
        }

        // 逐个验证和执行变化的控制命令
        for (const { operation, value } of changedOperations) {
          console.log(`🔧 [设备控制] 验证命令: ${operation}=${value}`);

          // 先验证命令
          const validation = await ipcRenderer.invoke('validate-device-control', {
            did: this.currentDevice.did,
            operation,
            value
          });

          if (!validation.valid) {
            console.error(`❌ [设备控制] 命令验证失败 ${operation}=${value}:`, validation.message);
            this.$message.error(`${operation} 设置失败: ${validation.message}`);
            controlResults.push({
              operation,
              value,
              success: false,
              message: validation.message
            });
            continue;
          }

          console.log(`✅ [设备控制] 命令验证通过: ${operation}=${value}`);

          // 执行控制命令
          const controlResult = await ipcRenderer.invoke('control-device', {
            did: this.currentDevice.did,
            operation,
            value
          });

          console.log(`🎮 [设备控制] 控制结果 ${operation}=${value}:`, controlResult);
          controlResults.push({
            operation,
            value,
            success: controlResult.success,
            message: controlResult.message
          });

          if (controlResult.success) {
            console.log(`✅ [设备控制] ${operation} 控制成功`);
          } else {
            console.error(`❌ [设备控制] ${operation} 控制失败:`, controlResult.message);
          }
        }

        // 统计结果
        const successCount = controlResults.filter(r => r.success).length;
        const totalCount = controlResults.length;

        console.log(`🎮 [设备控制] 控制完成: ${successCount}/${totalCount} 成功`);

        if (successCount > 0) {
          this.$message.success(`设备控制成功 (${successCount}/${totalCount})`);

          // 显示详细控制结果
          const successOps = controlResults.filter(r => r.success).map(r => `${r.operation}=${r.value}`);
          console.log('✅ [设备控制] 成功的操作:', successOps);

          // 立即刷新设备数据以显示最新状态
          console.log('🔄 [设备控制] 刷新设备数据以显示最新状态');
          await this.forceRefreshDeviceStates();

          // 强制刷新当前设备对象（如果对话框仍然打开）
          if (this.currentDevice && this.showControlDevice) {
            // 重新获取最新的设备数据
            await this.loadDevices();
            await this.updateCurrentDevices();

            const updatedDevice = this.currentDevices.find(d => d.did === this.currentDevice.did);
            if (updatedDevice) {
              this.currentDevice = { ...updatedDevice }; // 创建新对象引用以确保响应式更新
              console.log('🔄 [设备控制] 已更新当前设备对象:', updatedDevice);
              console.log('🔄 [设备控制] 设备当前状态:', {
                name: updatedDevice.name,
                online: updatedDevice.online,
                power: updatedDevice.status?.power
              });
            }
          }

          this.closeControlDialog();
        } else {
          const errorMessages = controlResults.map(r => `${r.operation}: ${r.message}`).join('; ');
          this.$message.error(`设备控制失败: ${errorMessages}`);
        }

        // 输出失败的操作详情
        const failedOps = controlResults.filter(r => !r.success);
        if (failedOps.length > 0) {
          console.error('❌ [设备控制] 失败的操作:', failedOps);
        }

      } catch (error) {
        console.error('❌ [设备控制] 设备控制异常:', error);
        this.$message.error('设备控制失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },

    // 显示移动设备对话框
    async showMoveDialog(device) {
      console.log('🔄 [前端调试] 显示移动设备对话框:', device.name);
      this.currentDevice = device;
      this.targetGroupId = null; // 重置目标分组
      this.availableGroups = []; // 重置可用分组列表
      this.moveDeviceErrors = {}; // 重置错误信息

      // 获取可移动的分组列表
      try {
        const result = await ipcRenderer.invoke('get-available-groups-for-device', device.did);
        if (result.success) {
          this.availableGroups = result.data.available_groups;
          console.log('🔄 [前端调试] 可用分组数量:', this.availableGroups.length);
        } else {
          console.error('❌ [前端调试] 获取可用分组失败:', result.message);
          this.$message.error(result.message || '获取分组列表失败');
          return;
        }
      } catch (error) {
        console.error('❌ [前端调试] 获取可用分组异常:', error);
        this.$message.error('获取分组列表失败');
        return;
      }

      this.showMoveDevice = true;
    },

    // 关闭移动设备对话框
    closeMoveDialog() {
      this.showMoveDevice = false;
      this.currentDevice = null;
      this.targetGroupId = null;
      this.availableGroups = [];
      this.moveDeviceErrors = {};
    },

    // 验证分组名称输入
    async validateGroupNameInput() {
      const groupName = this.targetGroupName;

      if (!groupName || groupName.trim() === '') {
        this.moveDeviceErrors.groupName = '分组名称不能为空';
        return false;
      }

      try {
        const result = await ipcRenderer.invoke('validate-group-name', groupName.trim());
        if (result.success && result.data.exists) {
          this.targetGroupId = result.data.group.gid;
          this.moveDeviceErrors.groupName = '';
          return true;
        } else {
          this.moveDeviceErrors.groupName = '分组不存在';
          this.targetGroupId = null;
          return false;
        }
      } catch (error) {
        console.error('验证分组名称失败:', error);
        this.moveDeviceErrors.groupName = '验证分组名称失败';
        return false;
      }
    },

    // 确认移动设备
    async confirmMoveDevice() {
      if (!this.currentDevice) {
        this.$message.error('未选择设备');
        return;
      }

      // 验证目标分组
      let targetGroupId = this.targetGroupId;
      let targetGroupName = null;

      // 如果使用的是下拉选择
      if (this.moveDeviceMode === 'select' && targetGroupId) {
        const selectedGroup = this.availableGroups.find(g => g.gid === targetGroupId);
        targetGroupName = selectedGroup?.gname;
      }
      // 如果使用的是手动输入
      else if (this.moveDeviceMode === 'input' && this.targetGroupName) {
        const isValid = await this.validateGroupNameInput();
        if (!isValid) {
          return;
        }
        targetGroupId = this.targetGroupId;
        targetGroupName = this.targetGroupName.trim();
      } else {
        this.$message.error('请选择或输入目标分组');
        return;
      }

      if (!targetGroupId) {
        this.$message.error('请选择有效的目标分组');
        return;
      }

      console.log('🔄 [前端调试] 开始移动设备');
      console.log('🔄 [前端调试] 设备:', this.currentDevice.name, this.currentDevice.did);
      console.log('🔄 [前端调试] 目标分组:', targetGroupName, targetGroupId);

      this.loading = true;
      try {
        const result = await ipcRenderer.invoke('move-device-to-group', this.currentDevice.did, targetGroupId, targetGroupName);

        if (result.success) {
          console.log('✅ [前端调试] 设备移动成功:', result);
          this.$message.success(result.message || '设备移动成功');

          // 刷新数据
          await this.initializeData();
          this.closeMoveDialog();
        } else {
          console.error('❌ [前端调试] 设备移动失败:', result.message);
          this.$message.error(result.message || '设备移动失败');
        }
      } catch (error) {
        console.error('❌ [前端调试] 设备移动异常:', error);
        this.$message.error('设备移动失败');
      } finally {
        this.loading = false;
      }
    },

    // ==================== 设备移动辅助方法 ====================

    // 获取当前设备所在分组名称
    getCurrentGroupName() {
      if (!this.currentDevice) return '未知';
      const currentGroupId = this.currentDevice.groupId || this.currentDevice.group;
      const currentGroup = this.groupList.find(g => g.gid === currentGroupId);
      return currentGroup ? currentGroup.gname : '未分组';
    },

    // 获取当前分组的设备数量
    getCurrentGroupDeviceCount() {
      if (!this.currentDevice) return 0;
      const currentGroupId = this.currentDevice.groupId || this.currentDevice.group;
      const currentGroup = this.groupList.find(g => g.gid === currentGroupId);
      return currentGroup ? (currentGroup.device_count || 0) : 0;
    },

    // 获取目标分组名称
    getTargetGroupName() {
      if (this.moveDeviceMode === 'select' && this.targetGroupId) {
        const targetGroup = this.availableGroups.find(g => g.gid === this.targetGroupId);
        return targetGroup ? targetGroup.gname : '';
      } else if (this.moveDeviceMode === 'input' && this.targetGroupName) {
        return this.targetGroupName;
      }
      return '';
    },

    // 清除分组名称错误
    clearGroupNameError() {
      if (this.moveDeviceErrors.groupName) {
        this.moveDeviceErrors.groupName = '';
      }
      // 当用户修改输入时，重置目标分组ID
      if (this.moveDeviceMode === 'input') {
        this.targetGroupId = null;
      }
    },

    // ==================== 工具方法 ====================

    // 判断是否为传感器设备
    isSensorDevice(device) {
      return device.type === 'mi_temp_hum_sensor' ||
             device.type === 'mi_air_sensor' ||
             device.type === 'history';
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
        case 'status':
          const statusMap = {
            'on': '开启',
            'off': '关闭',
            'running': '运行中',
            'paused': '暂停',
            'idle': '待机'
          };
          return statusMap[value] || value;
        default:
          return value;
      }
    },

    // 格式化控制选项
    formatControlOption(property, option) {
      return this.formatStatusValue(property, option);
    },

        // 获取设备最后更新时间显示
    getLastUpdatedDisplay(device) {
      if (!device.lastUpdated) return '未知';
      try {
        const updateTime = new Date(device.lastUpdated);
        const now = new Date();
        const diff = Math.floor((now - updateTime) / 1000);

        if (diff < 60) return `${diff}秒前`;
        if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
        return updateTime.toLocaleDateString();
      } catch (error) {
        return '未知';
      }
    },

    // 清理并重新生成设备数据（仅admin可用）
    async clearAndRegenerateDevices() {
      if (!this.isAdminDebugMode) {
        this.$message.error('仅管理员可以使用此功能');
        return;
      }

      try {
        const result = await this.$confirm(
          '确定要清理所有设备数据并重新生成模拟数据吗？此操作不可撤销！',
          '警告',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
          }
        );

        this.loading = true;
        console.log('🧹 [Admin Debug] 开始清理并重新生成设备数据...');

        const clearResult = await ipcRenderer.invoke('clear-all-devices');

        if (clearResult.success) {
          this.$message.success('设备数据已清理并重新生成');
          console.log('✅ [Admin Debug] 设备数据重新生成成功');

          // 刷新页面数据
          await this.initializeData();
        } else {
          this.$message.error(clearResult.message || '设备数据重新生成失败');
          console.error('❌ [Admin Debug] 设备数据重新生成失败:', clearResult.message);
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('❌ [Admin Debug] 重新生成设备数据异常:', error);
          this.$message.error('重新生成设备数据失败');
        }
      } finally {
        this.loading = false;
      }
    },

    // 强制刷新设备状态
    async forceRefreshDeviceStates() {
      try {
        console.log('🔄 [设备控制] 开始强制刷新设备状态...');
        await this.loadDevices();
        await this.updateCurrentDevices();
        this.updateStatistics();
        this.lastRefreshTime = new Date();
        console.log('✅ [设备控制] 设备状态刷新完成');
      } catch (error) {
        console.error('❌ [前端调试] 强制刷新设备状态失败:', error);
      }
    },

    // 处理策略状态变更
    handleStrategyChanged(data) {
      console.log('🎯 [策略控制] 策略状态变更:', data);
      this.$message({
        type: 'info',
        message: `预设策略已${data.enabled ? '开启' : '关闭'}: ${data.strategy.name}`
      });

      // 如果策略开启，可能需要刷新设备状态以反映策略执行结果
      if (data.enabled) {
        setTimeout(() => {
          this.forceRefreshDeviceStates();
        }, 2000);
      }
    },

    // 处理策略执行完成
    handleStrategyExecuted(data) {
      console.log('🎯 [策略控制] 策略执行完成:', data);

      // 刷新设备状态以显示策略执行结果
      this.forceRefreshDeviceStates();

      // 显示执行结果通知
      if (data.affectedDevicesCount > 0) {
        this.$message({
          type: 'success',
          message: `策略执行成功，已调整 ${data.affectedDevicesCount} 个设备`,
          duration: 5000
        });
      }
    },

    // 设置场景执行监听器
    setupSceneExecutionListener() {
      console.log('🎬 [场景监听] 设置场景执行监听器');

      // 监听场景执行后的设备状态刷新事件
      this.sceneExecutionHandler = (event, data) => {
        console.log('🎬 [场景监听] 收到场景执行完成通知:', data);

        // 显示场景执行结果
        if (data.summary) {
          const { success, failed, skipped } = data.summary;
          const message = `场景执行完成！成功: ${success}, 失败: ${failed}, 跳过: ${skipped}`;

          this.$message({
            type: failed > 0 ? 'warning' : 'success',
            message: message,
            duration: 4000
          });
        }

        // 刷新手动模式页面的设备状态
        if (this.currentMode === 'manual') {
          console.log('🔄 [场景监听] 当前为手动模式，刷新设备状态...');
          this.forceRefreshDeviceStates();
        }
      };

      // 注册监听器
      ipcRenderer.on('scene-executed-refresh-devices', this.sceneExecutionHandler);
    },

    // 移除场景执行监听器
    removeSceneExecutionListener() {
      console.log('🎬 [场景监听] 移除场景执行监听器');

      if (this.sceneExecutionHandler) {
        ipcRenderer.removeListener('scene-executed-refresh-devices', this.sceneExecutionHandler);
        this.sceneExecutionHandler = null;
      }
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

.refresh-status {
  color: #909399;
  font-style: italic;
}

.refresh-status.refreshing {
  color: #409eff;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.debug-btn {
  padding: 4px 8px;
  background-color: #909399;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-left: 10px;
}

.debug-btn:hover {
  background-color: #73767a;
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
  transition: box-shadow 0.3s ease;
}

.device-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.device-title {
  color: #303133;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.device-online-indicator {
  font-size: 12px;
  margin-left: 10px;
}

.device-online-indicator.online {
  color: #67c23a;
  animation: blink-online 2s infinite;
}

.device-online-indicator.offline {
  color: #f56c6c;
}

@keyframes blink-online {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
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

.control-btn, .move-btn, .test-api-btn {
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

.test-api-btn {
  color: #e6a23c;
  border-color: #e6a23c;
  font-size: 10px;
}

.test-api-btn:hover {
  background: #e6a23c;
  color: white;
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

.loading-state {
  text-align: center;
  padding: 40px;
  color: #409eff;
  font-style: italic;
}

.refresh-btn {
  margin-top: 15px;
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #3a8ee6;
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.clear-devices-btn {
  margin-top: 15px;
  margin-left: 10px;
  padding: 8px 16px;
  background: #e53e3e;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.clear-devices-btn:hover:not(:disabled) {
  background-color: #c53030;
}

.clear-devices-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
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

/* 移动设备对话框特殊样式 */
.move-device-dialog {
  min-width: 500px;
  max-width: 600px;
}

.current-group-info {
  padding: 8px 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  font-weight: 500;
  color: #495057;
}

.device-count {
  color: #6c757d;
  font-weight: normal;
  font-size: 0.9em;
}

.move-mode-selector {
  display: flex;
  gap: 20px;
  margin-top: 8px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
}

.radio-option input[type="radio"] {
  margin: 0;
}

.move-preview {
  border: 1px solid #28a745;
  border-radius: 4px;
  background-color: #f8fff9;
}

.preview-info {
  padding: 8px 12px;
  color: #155724;
  font-size: 14px;
  line-height: 1.4;
}

.info-message {
  margin-top: 4px;
  padding: 6px 8px;
  background-color: #e3f2fd;
  border: 1px solid #bbdefb;
  border-radius: 3px;
  color: #1565c0;
  font-size: 12px;
}

.success-message {
  margin-top: 4px;
  padding: 4px 8px;
  background-color: #f8fff9;
  border: 1px solid #28a745;
  border-radius: 3px;
  color: #155724;
  font-size: 12px;
}

/* 模式切换样式 */
.mode-switch {
  display: flex;
  gap: 15px;
}

.mode-radio {
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  background: white;
  color: #606266;
}

.mode-radio:hover {
  border-color: #409eff;
  color: #409eff;
}

.mode-radio-active {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}

.mode-radio-active:hover {
  background-color: #337ecc;
  border-color: #337ecc;
}

.debug-btn {
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s ease;
}

.debug-btn:hover:not(:disabled) {
  background-color: #337ecc;
}

.debug-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

</style>

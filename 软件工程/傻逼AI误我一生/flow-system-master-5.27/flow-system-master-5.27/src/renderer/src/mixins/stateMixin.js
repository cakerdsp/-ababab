// stateMixin.js - Vue组件状态管理Mixin

export default {
  data() {
    return {
      // 本地状态缓存
      localState: {},
      // 状态加载状态
      stateLoading: false,
      // 页面名称（由组件定义）
      pageName: this.$options.name || 'unknown'
    }
  },

  async created() {
    // 组件创建时自动加载状态
    await this.loadPageState();
    await this.loadUIState();
  },

  async beforeUnmount() {
    // 组件销毁前保存状态
    await this.saveCurrentState();
  },

  methods: {
    // ==================== 状态加载方法 ====================

    // 加载页面状态
    async loadPageState() {
      try {
        this.stateLoading = true;
        const result = await window.electronAPI.invoke('get-page-state', this.pageName);

        if (result.success && result.data) {
          this.localState = { ...this.localState, ...result.data };
          // 触发状态恢复钩子
          if (this.onStateLoaded) {
            this.onStateLoaded(result.data);
          }
        }
      } catch (error) {
        console.error(`加载页面状态失败 (${this.pageName}):`, error);
      } finally {
        this.stateLoading = false;
      }
    },

    // 加载UI状态
    async loadUIState() {
      try {
        const result = await window.electronAPI.invoke('get-ui-state', this.pageName);

        if (result.success && result.data) {
          // 应用UI状态
          this.applyUIState(result.data);
        }
      } catch (error) {
        console.error(`加载UI状态失败 (${this.pageName}):`, error);
      }
    },

    // 加载表单状态
    async loadFormState(formName) {
      try {
        const result = await window.electronAPI.invoke('get-form-state', this.pageName, formName);

        if (result.success && result.data) {
          return result.data;
        }
        return null;
      } catch (error) {
        console.error(`加载表单状态失败 (${this.pageName}/${formName}):`, error);
        return null;
      }
    },

    // ==================== 状态保存方法 ====================

    // 保存页面状态
    async savePageState(state = null) {
      try {
        const stateToSave = state || this.getPageStateToSave();
        if (!stateToSave) return;

        const result = await window.electronAPI.invoke('save-page-state', this.pageName, stateToSave);

        if (!result.success) {
          console.error(`保存页面状态失败 (${this.pageName}):`, result.message);
        }
      } catch (error) {
        console.error(`保存页面状态失败 (${this.pageName}):`, error);
      }
    },

    // 保存UI状态
    async saveUIState(uiState = null) {
      try {
        const stateToSave = uiState || this.getUIStateToSave();
        if (!stateToSave) return;

        const result = await window.electronAPI.invoke('save-ui-state', this.pageName, stateToSave);

        if (!result.success) {
          console.error(`保存UI状态失败 (${this.pageName}):`, result.message);
        }
      } catch (error) {
        console.error(`保存UI状态失败 (${this.pageName}):`, error);
      }
    },

    // 保存表单状态
    async saveFormState(formName, formData) {
      try {
        const result = await window.electronAPI.invoke('save-form-state', this.pageName, formName, formData);

        if (!result.success) {
          console.error(`保存表单状态失败 (${this.pageName}/${formName}):`, result.message);
        }
      } catch (error) {
        console.error(`保存表单状态失败 (${this.pageName}/${formName}):`, error);
      }
    },

    // ==================== 状态同步方法 ====================

    // 同步状态从存储
    async syncStateFromStorage() {
      try {
        const result = await window.electronAPI.invoke('sync-state-from-storage');

        if (result.success) {
          // 重新加载状态
          await this.loadPageState();
          await this.loadUIState();
        }

        return result.success;
      } catch (error) {
        console.error('同步状态失败:', error);
        return false;
      }
    },

    // ==================== 辅助方法 ====================

    // 获取要保存的页面状态（由组件重写）
    getPageStateToSave() {
      return this.localState;
    },

    // 获取要保存的UI状态（由组件重写）
    getUIStateToSave() {
      // 默认保存一些常见的UI状态
      return {
        scrollPosition: window.pageYOffset || document.documentElement.scrollTop,
        timestamp: new Date().toISOString()
      };
    },

    // 应用UI状态（由组件重写）
    applyUIState(uiState) {
      // 默认恢复滚动位置
      if (uiState.scrollPosition !== undefined) {
        this.$nextTick(() => {
          window.scrollTo(0, uiState.scrollPosition);
        });
      }
    },

    // 保存当前状态（组件销毁前调用）
    async saveCurrentState() {
      await Promise.all([
        this.savePageState(),
        this.saveUIState()
      ]);
    },

    // ==================== 便捷方法 ====================

    // 自动保存表单数据（可以在表单字段变化时调用）
    debounceFormSave: null,

    autoSaveForm(formName, formData, delay = 2000) {
      // 防抖保存
      if (this.debounceFormSave) {
        clearTimeout(this.debounceFormSave);
      }

      this.debounceFormSave = setTimeout(() => {
        this.saveFormState(formName, formData);
      }, delay);
    },

    // 获取全局应用状态
    async getAppState() {
      try {
        const result = await window.electronAPI.invoke('get-current-state');
        return result.success ? result.data : {};
      } catch (error) {
        console.error('获取应用状态失败:', error);
        return {};
      }
    },

    // 检查用户登录状态
    async checkLoginState() {
      try {
        const appState = await this.getAppState();
        return !!(appState.user && appState.user.userId);
      } catch (error) {
        console.error('检查登录状态失败:', error);
        return false;
      }
    },

    // 获取设备列表状态
    async getDevicesState() {
      try {
        const appState = await this.getAppState();
        return appState.devices || [];
      } catch (error) {
        console.error('获取设备状态失败:', error);
        return [];
      }
    },

    // 获取应用设置
    async getAppSettings() {
      try {
        const appState = await this.getAppState();
        return appState.appSettings || { autoLogin: false, rememberMe: false };
      } catch (error) {
        console.error('获取应用设置失败:', error);
        return { autoLogin: false, rememberMe: false };
      }
    }
  },

  // ==================== 生命周期钩子 ====================

  // 状态加载完成钩子（由组件实现）
  onStateLoaded(state) {
    // 默认实现：合并到组件数据
    Object.keys(state).forEach(key => {
      if (this.$data.hasOwnProperty(key)) {
        this[key] = state[key];
      }
    });
  }
};

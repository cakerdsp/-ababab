const UnifiedStorage = require('../../services/storage/UnifiedStorage');

/**
 * 场景管理器
 * 负责场景的创建、删除、更新、执行等核心业务逻辑
 * 包括智能电源补齐、动作冲突检测和属性值校验
 */
class SceneManager {
  constructor(apiRegistry = null, deviceStorageManager = null, deviceControlManager = null) {
    this.apiRegistry = apiRegistry;
    this.deviceStorageManager = deviceStorageManager;
    this.deviceControlManager = deviceControlManager;
    this.storage = new UnifiedStorage();
    this.isInitialized = false;
    this.offlineMode = false;

    // 场景缓存 - Map<sceneId, scene>
    this.scenes = new Map();

    // 需要开机的属性列表
    this.POWER_DEPENDENT_PROPS = {
      'mi_ac': ['mode', 'fan_speed', 'target_temperature'],
      'midea_ac': ['mode', 'fan_speed', 'target_temperature'],
      'mi_humidifier': ['target_humidity', 'mode'],
      'midea_humidifier': ['target_humidity', 'mode'],
      'mi_dehumidifier': ['target_humidity', 'mode'],
      'midea_dehumidifier': ['target_humidity', 'mode'],
      'mi_air_purifier': ['mode', 'fan_level'],
      'midea_air_purifier': ['mode', 'fan_level']
    };

    // 动作冲突规则表
    this.CONFLICT_RULES = {
      'mi_ac': {
        'fan_speed': ['dry'], // dry模式下不可调风速
        'target_temperature': ['fan'] // fan模式下不可调温度
      },
      'midea_ac': {
        'fan_speed': ['dry'],
        'target_temperature': ['fan']
      },
      'mi_humidifier': {
        'target_humidity': ['auto'] // auto模式下不可调湿度
      },
      'midea_humidifier': {
        'target_humidity': ['auto']
      },
      'mi_air_purifier': {
        'fan_level': ['auto'] // auto模式下不可调风扇等级
      },
      'midea_air_purifier': {
        'fan_level': ['auto']
      }
    };
  }

  // 设置依赖项
  setApiRegistry(apiRegistry) {
    this.apiRegistry = apiRegistry;
  }

  setDeviceStorageManager(deviceStorageManager) {
    this.deviceStorageManager = deviceStorageManager;
  }

  setDeviceControlManager(deviceControlManager) {
    this.deviceControlManager = deviceControlManager;
  }

  // 初始化场景管理器
  async initialize() {
    if (this.isInitialized) {
      return { success: true, message: '场景管理器已初始化' };
    }

    try {
      // 从本地存储加载场景数据
      await this.loadScenesFromStorage();

      // 从服务端同步场景数据
      const syncResult = await this.syncScenesFromServer();

      this.isInitialized = true;
      console.log('Scene manager initialized successfully');
      return {
        success: true,
        message: '场景管理器初始化成功',
        sceneCount: this.scenes.size,
        syncResult: syncResult
      };
    } catch (error) {
      console.error('Scene manager initialization failed:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 从本地存储加载场景数据
  async loadScenesFromStorage() {
    try {
      const scenesData = this.storage.getItem('scenes') || [];
      if (Array.isArray(scenesData)) {
        scenesData.forEach(scene => {
          this.scenes.set(scene.scene_id, scene);
        });
        console.log(`Loaded ${scenesData.length} scenes from local storage`);
      }
    } catch (error) {
      console.error('Failed to load scenes from local storage:', error);
    }
  }

  // 从服务端同步场景数据
  async syncScenesFromServer() {
    try {
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Scene] Skip server sync: API registry not set or offline mode');

        // 离线模式下生成一些模拟场景数据
        if (this.offlineMode) {
          await this.generateMockScenesForOffline();
        }

        return { success: false, message: 'API注册器未设置或处于离线模式' };
      }

      console.log('🔄 [Scene] 开始从服务端同步场景数据...');

      // 第一步：获取场景列表（简略信息）
      const listResponse = await this.apiRegistry.callAPIGet('getScenes');

      if (!listResponse || listResponse.code !== 200 || !listResponse.data) {
        return {
          success: false,
          message: listResponse?.message || '获取场景列表失败'
        };
      }

      console.log(`📋 [Scene] 获取到 ${listResponse.data.scenes.length} 个场景的简略信息`);

      // 清空本地场景缓存
      this.scenes.clear();

      // 第二步：获取每个场景的详细信息
      const sceneDetails = [];
      for (const sceneInfo of listResponse.data.scenes) {
        try {
          console.log(`🔍 [Scene] 获取场景详情: ${sceneInfo.scene_name} (${sceneInfo.scene_id})`);

          const detailResponse = await this.apiRegistry.getSceneDetail(sceneInfo.scene_id);

          if (detailResponse && detailResponse.code === 200 && detailResponse.data) {
            sceneDetails.push(detailResponse.data);
            console.log(`✅ [Scene] 场景详情获取成功: ${detailResponse.data.scene_name}`);
          } else {
            console.warn(`⚠️ [Scene] 场景详情获取失败: ${sceneInfo.scene_name} - ${detailResponse?.message}`);
            // 如果获取详情失败，使用简略信息
            sceneDetails.push({
              ...sceneInfo,
              actions: [] // 没有详情时设置空动作列表
            });
          }
        } catch (detailError) {
          console.error(`❌ [Scene] 获取场景详情异常: ${sceneInfo.scene_name}`, detailError);
          // 异常时也使用简略信息
          sceneDetails.push({
            ...sceneInfo,
            actions: []
          });
        }
      }

      // 存储完整的场景数据
      sceneDetails.forEach(scene => {
        this.scenes.set(scene.scene_id, scene);
      });

      // 保存到本地存储
      this.saveScenesToStorage();

      console.log(`✅ [Scene] 场景数据同步完成，共 ${sceneDetails.length} 个场景`);
      return {
        success: true,
        message: '场景数据同步成功',
        sceneCount: sceneDetails.length,
        detailsCount: sceneDetails.filter(s => s.actions && s.actions.length > 0).length
      };

    } catch (error) {
      console.error('❌ [Scene] 场景数据同步失败:', error);
      return { success: false, message: '同步失败：' + error.message };
    }
  }

  // 为离线模式生成模拟场景数据
  async generateMockScenesForOffline() {
    console.log('🎭 [Scene] 生成离线模式模拟场景数据...');

    const mockScenes = [
      {
        scene_id: 'scene_mock_1',
        scene_name: '回家模式',
        description: '回家时自动开启设备',
        gid: 'group_1749872371525_ibx2uutu4',
        actions: [
          {
            action_id: 'action_mock_1_1',
            did: 'midea_midea_ac_gf6s1k',
            operation: 'power',
            value: 'ON'
          },
          {
            action_id: 'action_mock_1_2',
            did: 'midea_midea_ac_gf6s1k',
            operation: 'target_temperature',
            value: 24
          }
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        scene_id: 'scene_mock_2',
        scene_name: '离家模式',
        description: '离家时关闭所有设备',
        gid: 'group_1749872371525_ibx2uutu4',
        actions: [
          {
            action_id: 'action_mock_2_1',
            did: 'midea_midea_ac_gf6s1k',
            operation: 'power',
            value: 'OFF'
          }
        ],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ];

    // 存储模拟场景
    mockScenes.forEach(scene => {
      this.scenes.set(scene.scene_id, scene);
    });

    this.saveScenesToStorage();
    console.log(`✅ [Scene] 生成了 ${mockScenes.length} 个模拟场景`);
  }

  // 保存场景到本地存储
  saveScenesToStorage() {
    try {
      const scenesArray = Array.from(this.scenes.values());
      this.storage.setItem('scenes', scenesArray);
      console.log(`Saved ${scenesArray.length} scenes to local storage`);
    } catch (error) {
      console.error('Failed to save scenes to local storage:', error);
    }
  }

  // 创建新场景
  async createScene(sceneDataOrName, gid, actions = []) {
    // 支持两种调用方式：对象参数或独立参数
    let sceneName, sceneGid, sceneActions, sceneDescription;

    if (typeof sceneDataOrName === 'object' && sceneDataOrName !== null) {
      // 对象参数方式
      sceneName = sceneDataOrName.scene_name;
      sceneGid = sceneDataOrName.gid;
      sceneActions = sceneDataOrName.actions || [];
      sceneDescription = sceneDataOrName.description;
    } else {
      // 独立参数方式
      sceneName = sceneDataOrName;
      sceneGid = gid;
      sceneActions = actions;
    }

    console.log('🔧 [Scene] Creating scene:', { sceneName, gid: sceneGid, actions: sceneActions });

    try {
      if (!sceneName || sceneName.trim() === '') {
        return { success: false, message: '场景名称不能为空' };
      }

      const trimmedName = sceneName.trim();

      // 检查同一分组内是否有重名场景
      const existingScene = Array.from(this.scenes.values()).find(
        scene => scene.gid === sceneGid && scene.scene_name === trimmedName
      );
      if (existingScene) {
        return { success: false, message: '同一分组内场景名称已存在' };
      }

      // 验证和处理动作
      const processedActions = await this.processSceneActions(sceneActions, sceneGid);
      if (!processedActions.success) {
        return processedActions;
      }

      // 检查是否为离线模式
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Scene] Offline mode: creating scene locally');

        const mockSceneId = 'scene_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const newScene = {
          scene_id: mockSceneId,
          scene_name: trimmedName,
          description: sceneDescription || '',
          gid: sceneGid,
          actions: processedActions.data.map((action, index) => ({
            action_id: `action_${mockSceneId}_${index}`,
            ...action
          })),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };

        this.scenes.set(mockSceneId, newScene);
        this.saveScenesToStorage();

        console.log('✅ [Scene] Scene created successfully in offline mode:', newScene);
        return {
          success: true,
          message: '场景创建成功（离线模式）',
          data: {
            scene_id: mockSceneId,
            scene_name: trimmedName
          }
        };
      }

      // 调用服务端API创建场景
      const response = await this.apiRegistry.callAPI('createScene', {
        scene_name: trimmedName,
        description: sceneDescription || '',
        gid: sceneGid,
        actions: processedActions.data
      });

      if (response && response.code === 200) {
        // 添加到本地缓存
        const newScene = {
          scene_id: response.scene_id,
          scene_name: trimmedName,
          description: sceneDescription || '',
          gid: sceneGid,
          actions: processedActions.data.map((action, index) => ({
            action_id: `action_${response.scene_id}_${index}`,
            ...action
          })),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };

        this.scenes.set(response.scene_id, newScene);
        this.saveScenesToStorage();

        console.log('✅ [Scene] Scene created successfully:', newScene);
        return {
          success: true,
          message: '场景创建成功',
          data: {
            scene_id: response.scene_id,
            scene_name: trimmedName
          }
        };
      } else {
        return {
          success: false,
          message: response.message || '场景创建失败'
        };
      }
    } catch (error) {
      console.error('Failed to create scene:', error);
      return { success: false, message: '创建失败：' + error.message };
    }
  }

  // 删除场景
  async deleteScene(sceneId) {
    console.log('🔧 [Scene] Deleting scene:', sceneId);

    try {
      // Parameter validation
      if (!sceneId) {
        console.error('❌ [Scene] Delete scene failed: Scene ID parameter incomplete');
        return { success: false, message: 'Parameter incomplete: Scene ID cannot be empty' };
      }

      if (typeof sceneId !== 'string') {
        console.error('❌ [Scene] Delete scene failed: Scene ID parameter type error');
        return { success: false, message: 'Parameter incomplete: Scene ID must be string' };
      }

      if (!this.scenes.has(sceneId)) {
        console.error('❌ [Scene] Delete scene failed: Scene does not exist, ID:', sceneId);
        return { success: false, message: 'Scene does not exist' };
      }

      const scene = this.scenes.get(sceneId);
      console.log('🎬 [Scene] Preparing to delete scene:', {
        scene_id: scene.scene_id,
        scene_name: scene.scene_name
      });

      // Add offline mode status debugging
      console.log('🔍 [Scene] Offline mode status check:', {
        hasApiRegistry: !!this.apiRegistry,
        offlineMode: this.offlineMode,
        shouldUseOfflineMode: !this.apiRegistry || this.offlineMode
      });

      // Check if offline mode
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Scene] Offline mode: deleting scene locally');

        this.scenes.delete(sceneId);
        this.saveScenesToStorage();

        console.log('✅ [Scene] Scene deleted successfully in offline mode');
        return {
          success: true,
          message: 'Scene deleted successfully (offline mode)'
        };
      }

      console.log('🌐 [Scene] Online mode: calling server API');
      // 调用服务端API删除场景
      const response = await this.apiRegistry.deleteScene(sceneId);

      if (response && response.code === 200) {
        // 从本地缓存删除
        this.scenes.delete(sceneId);
        this.saveScenesToStorage();

        console.log('✅ [Scene] Scene deleted successfully');
        return {
          success: true,
          message: '场景删除成功'
        };
      } else {
        return {
          success: false,
          message: response.message || '场景删除失败'
        };
      }
    } catch (error) {
      console.error('Failed to delete scene:', error);
      return { success: false, message: '删除失败：' + error.message };
    }
  }

  // 更新场景
  async updateScene(sceneId, updateDataOrAddActions = [], removeActionIds = []) {
    console.log('[SCENE_UPDATE] Starting scene update process');
    console.log('[SCENE_UPDATE] Scene ID:', sceneId);
    console.log('[SCENE_UPDATE] Update data type:', typeof updateDataOrAddActions);

    // 支持三种调用方式：对象参数（增量更新）、对象参数（完全替换）或独立参数
    let addActions, removeActions, replaceActions;

    if (typeof updateDataOrAddActions === 'object' && updateDataOrAddActions !== null) {
      if (updateDataOrAddActions.replaceActions) {
        // 完全替换模式
        replaceActions = updateDataOrAddActions.replaceActions;
        console.log('[SCENE_UPDATE] Mode: Full replacement');
        console.log('[SCENE_UPDATE] Replace actions count:', replaceActions.length);
      } else if (updateDataOrAddActions.actions) {
        // 增量更新模式
        addActions = updateDataOrAddActions.actions.add || [];
        removeActions = updateDataOrAddActions.actions.remove || [];
        console.log('[SCENE_UPDATE] Mode: Incremental update');
        console.log('[SCENE_UPDATE] Add actions count:', addActions.length);
        console.log('[SCENE_UPDATE] Remove actions count:', removeActions.length);
      }
    } else {
      // 独立参数方式（向后兼容）
      addActions = updateDataOrAddActions;
      removeActions = removeActionIds;
      console.log('[SCENE_UPDATE] Mode: Legacy parameters');
    }

    try {
      // Parameter validation
      if (!sceneId) {
        console.error('[SCENE_UPDATE] ERROR: Scene ID parameter incomplete');
        return { success: false, message: 'Parameter incomplete: Scene ID cannot be empty' };
      }

      if (typeof sceneId !== 'string') {
        console.error('[SCENE_UPDATE] ERROR: Scene ID parameter type error');
        return { success: false, message: 'Parameter incomplete: Scene ID must be string' };
      }

      if (!this.scenes.has(sceneId)) {
        console.error('[SCENE_UPDATE] ERROR: Scene does not exist, ID:', sceneId);
        return { success: false, message: 'Scene does not exist' };
      }

      const scene = this.scenes.get(sceneId);
      console.log('[SCENE_UPDATE] Target scene info:');
      console.log('[SCENE_UPDATE] - Scene ID:', scene.scene_id);
      console.log('[SCENE_UPDATE] - Scene name:', scene.scene_name);
      console.log('[SCENE_UPDATE] - Current actions count:', scene.actions ? scene.actions.length : 0);

      // 检查离线模式状态
      console.log('[SCENE_UPDATE] Checking offline mode status:');
      console.log('[SCENE_UPDATE] - Has API registry:', !!this.apiRegistry);
      console.log('[SCENE_UPDATE] - Offline mode flag:', this.offlineMode);
      console.log('[SCENE_UPDATE] - Should use offline mode:', !this.apiRegistry || this.offlineMode);

      // 处理完全替换模式
      if (replaceActions !== undefined) {
        console.log('[SCENE_UPDATE] Processing full replacement mode');

        // 验证替换的动作
        if (replaceActions.length > 0) {
          console.log('[SCENE_UPDATE] Validating replacement actions');
          const processedActions = await this.processSceneActions(replaceActions, scene.gid);
          if (!processedActions.success) {
            console.error('[SCENE_UPDATE] ERROR: Action validation failed:', processedActions.message);
            return processedActions;
          }
          replaceActions = processedActions.data;
          console.log('[SCENE_UPDATE] Action validation passed');
        }

        // 检查是否为离线模式
        if (!this.apiRegistry || this.offlineMode) {
          console.log('[SCENE_UPDATE] Offline mode: replacing scene actions locally');

          // 完全替换动作列表
          scene.actions = replaceActions.map((action, index) => ({
            action_id: `action_${sceneId}_${Date.now()}_${index}`,
            ...action
          }));
          scene.updated_at = new Date().toISOString();

          this.scenes.set(sceneId, scene);
          this.saveScenesToStorage();

          console.log('[SCENE_UPDATE] SUCCESS: Scene actions replaced successfully in offline mode');
          return {
            success: true,
            message: 'Scene actions replaced successfully in offline mode'
          };
        }

        console.log('[SCENE_UPDATE] Online mode: preparing API call for replacement');

        // 在线模式：计算真正的差异，只发送需要添加和删除的动作
        const existingActions = scene.actions || [];
        const newActions = replaceActions || [];

        console.log('[SCENE_UPDATE] Calculating differences between existing and new actions');
        console.log('[SCENE_UPDATE] Existing actions count:', existingActions.length);
        console.log('[SCENE_UPDATE] New actions count:', newActions.length);

        // 找出需要删除的动作（存在于现有动作中，但不存在于新动作中）
        const actionsToRemove = [];
        existingActions.forEach(existingAction => {
          if (!existingAction.action_id) return; // 跳过没有ID的动作

          // 检查这个动作是否在新动作列表中存在（通过内容比较）
          const foundInNew = newActions.some(newAction =>
            newAction.did === existingAction.did &&
            newAction.operation === existingAction.operation &&
            JSON.stringify(newAction.value) === JSON.stringify(existingAction.value)
          );

          if (!foundInNew) {
            actionsToRemove.push(existingAction.action_id);
          }
        });

        // 找出需要添加的动作（存在于新动作中，但不存在于现有动作中）
        const actionsToAdd = [];
        newActions.forEach(newAction => {
          // 检查这个动作是否在现有动作列表中存在（通过内容比较）
          const foundInExisting = existingActions.some(existingAction =>
            existingAction.did === newAction.did &&
            existingAction.operation === newAction.operation &&
            JSON.stringify(existingAction.value) === JSON.stringify(newAction.value)
          );

          if (!foundInExisting) {
            // 移除action_id字段，因为这是新增动作
            const { action_id, ...actionWithoutId } = newAction;
            actionsToAdd.push(actionWithoutId);
          }
        });

        console.log('[SCENE_UPDATE] Actions to remove count:', actionsToRemove.length);
        console.log('[SCENE_UPDATE] Actions to add count:', actionsToAdd.length);
        console.log('[SCENE_UPDATE] Actions to remove IDs:', actionsToRemove);
        console.log('[SCENE_UPDATE] Actions to add:', actionsToAdd);

        const apiData = {
          actions: {
            add: actionsToAdd,     // 始终包含add数组，即使为空
            remove: actionsToRemove // 始终包含remove数组，即使为空
          }
        };

        // 如果既没有要添加的也没有要删除的，仍然发送请求（因为可能是无变化的保存操作）
        if (actionsToAdd.length === 0 && actionsToRemove.length === 0) {
          console.log('[SCENE_UPDATE] No changes detected, but still sending API request with empty arrays');
        }

        console.log('[SCENE_UPDATE] API call data for replacement:');
        console.log('[SCENE_UPDATE] - Actions to add count:', actionsToAdd.length);
        console.log('[SCENE_UPDATE] - Action IDs to remove count:', actionsToRemove.length);
        console.log('[SCENE_UPDATE] - API data structure:', JSON.stringify(apiData, null, 2));

        console.log('[SCENE_UPDATE] Calling server API for scene update');
        const response = await this.apiRegistry.updateScene(sceneId, apiData);

        console.log('[SCENE_UPDATE] Server API response received');
        console.log('[SCENE_UPDATE] Response code:', response?.code);
        console.log('[SCENE_UPDATE] Response message:', response?.message);

        if (response && response.code === 200) {
          console.log('[SCENE_UPDATE] API call successful, refreshing scene data from server');

          // API调用成功后，重新获取场景完整信息
          try {
            const detailResponse = await this.apiRegistry.getSceneDetail(sceneId);
            console.log('[SCENE_UPDATE] Scene detail API response:', detailResponse?.code);

            if (detailResponse && detailResponse.code === 200 && detailResponse.data) {
              console.log('[SCENE_UPDATE] Updating local cache with fresh scene data');
              console.log('[SCENE_UPDATE] Fresh scene actions count:', detailResponse.data.actions ? detailResponse.data.actions.length : 0);

              // 更新本地缓存为服务端返回的最新数据
              this.scenes.set(sceneId, detailResponse.data);
              this.saveScenesToStorage();

              console.log('[SCENE_UPDATE] SUCCESS: Scene replacement completed with fresh data from server');
              return {
                success: true,
                message: 'Scene actions replaced successfully',
                data: detailResponse.data
              };
            } else {
              console.error('[SCENE_UPDATE] ERROR: Failed to get fresh scene data after update');
              return {
                success: false,
                message: 'Scene update succeeded but failed to refresh data'
              };
            }
          } catch (detailError) {
            console.error('[SCENE_UPDATE] ERROR: Exception while getting fresh scene data:', detailError);
            return {
              success: false,
              message: 'Scene update succeeded but failed to refresh data due to exception'
            };
          }
        } else {
          console.error('[SCENE_UPDATE] ERROR: API call failed');
          console.error('[SCENE_UPDATE] Error response:', response);
          return {
            success: false,
            message: response?.message || 'Scene replacement failed'
          };
        }
      }

      // 处理增量更新模式
      console.log('[SCENE_UPDATE] Processing incremental update mode');

      // 验证新增动作
      if (addActions && addActions.length > 0) {
        console.log('[SCENE_UPDATE] Validating add actions');
        const processedActions = await this.processSceneActions(addActions, scene.gid);
        if (!processedActions.success) {
          console.error('[SCENE_UPDATE] ERROR: Add action validation failed:', processedActions.message);
          return processedActions;
        }
        addActions = processedActions.data;
        console.log('[SCENE_UPDATE] Add action validation passed');
      }

      // 检查是否为离线模式（增量更新）
      if (!this.apiRegistry || this.offlineMode) {
        console.log('[SCENE_UPDATE] Offline mode: updating scene locally');

        // 本地更新场景
        const updatedActions = [...scene.actions];

        // 删除指定动作
        if (removeActions && removeActions.length > 0) {
          console.log('[SCENE_UPDATE] Removing actions locally:', removeActions);
          removeActions.forEach(actionId => {
            const index = updatedActions.findIndex(action => action.action_id === actionId);
            if (index > -1) {
              updatedActions.splice(index, 1);
              console.log('[SCENE_UPDATE] Removed action:', actionId);
            }
          });
        }

        // 添加新动作
        if (addActions && addActions.length > 0) {
          console.log('[SCENE_UPDATE] Adding new actions locally');
          addActions.forEach((action, index) => {
            const newAction = {
              action_id: `action_${sceneId}_${Date.now()}_${index}`,
              ...action
            };
            updatedActions.push(newAction);
            console.log('[SCENE_UPDATE] Added action:', newAction.action_id);
          });
        }

        scene.actions = updatedActions;
        scene.updated_at = new Date().toISOString();

        this.scenes.set(sceneId, scene);
        this.saveScenesToStorage();

        console.log('[SCENE_UPDATE] SUCCESS: Scene updated successfully in offline mode');
        return {
          success: true,
          message: 'Scene updated successfully in offline mode'
        };
      }

      console.log('[SCENE_UPDATE] Online mode: preparing API call for incremental update');

      // 准备API数据：新增动作不包含action_id字段
      const actionsToAdd = (addActions && addActions.length > 0)
        ? addActions.map(action => {
            const { action_id, ...actionWithoutId } = action;
            return actionWithoutId;
          })
        : [];

      const actionsToRemove = (removeActions && removeActions.length > 0)
        ? removeActions
        : [];

      const apiData = {
        actions: {
          add: actionsToAdd,     // 始终包含add数组，即使为空
          remove: actionsToRemove // 始终包含remove数组，即使为空
        }
      };

      // 如果既没有要添加的也没有要删除的，仍然发送请求
      if (actionsToAdd.length === 0 && actionsToRemove.length === 0) {
        console.log('[SCENE_UPDATE] No changes detected, but still sending API request with empty arrays');
      }

      console.log('[SCENE_UPDATE] API call data for incremental update:');
      console.log('[SCENE_UPDATE] - Actions to add count:', actionsToAdd.length);
      console.log('[SCENE_UPDATE] - Action IDs to remove count:', actionsToRemove.length);
      console.log('[SCENE_UPDATE] - API data structure:', JSON.stringify(apiData, null, 2));

      console.log('[SCENE_UPDATE] Calling server API for incremental scene update');
      const response = await this.apiRegistry.updateScene(sceneId, apiData);

      console.log('[SCENE_UPDATE] Server API response received');
      console.log('[SCENE_UPDATE] Response code:', response?.code);
      console.log('[SCENE_UPDATE] Response message:', response?.message);

      if (response && response.code === 200) {
        console.log('[SCENE_UPDATE] API call successful, refreshing scene data from server');

        // API调用成功后，重新获取场景完整信息
        try {
          const detailResponse = await this.apiRegistry.getSceneDetail(sceneId);
          console.log('[SCENE_UPDATE] Scene detail API response:', detailResponse?.code);

          if (detailResponse && detailResponse.code === 200 && detailResponse.data) {
            console.log('[SCENE_UPDATE] Updating local cache with fresh scene data');
            console.log('[SCENE_UPDATE] Fresh scene actions count:', detailResponse.data.actions ? detailResponse.data.actions.length : 0);

            // 更新本地缓存为服务端返回的最新数据
            this.scenes.set(sceneId, detailResponse.data);
            this.saveScenesToStorage();

            console.log('[SCENE_UPDATE] SUCCESS: Scene incremental update completed with fresh data from server');
            return {
              success: true,
              message: 'Scene updated successfully',
              data: detailResponse.data
            };
          } else {
            console.error('[SCENE_UPDATE] ERROR: Failed to get fresh scene data after update');
            return {
              success: false,
              message: 'Scene update succeeded but failed to refresh data'
            };
          }
        } catch (detailError) {
          console.error('[SCENE_UPDATE] ERROR: Exception while getting fresh scene data:', detailError);
          return {
            success: false,
            message: 'Scene update succeeded but failed to refresh data due to exception'
          };
        }
      } else {
        console.error('[SCENE_UPDATE] ERROR: API call failed');
        console.error('[SCENE_UPDATE] Error response:', response);
        return {
          success: false,
          message: response?.message || 'Scene update failed'
        };
      }
    } catch (error) {
      console.error('[SCENE_UPDATE] ERROR: Exception during scene update:', error);
      return { success: false, message: 'Update failed: ' + error.message };
    }
  }

  // 执行场景
  async executeScene(sceneId) {
    console.log('🔧 [Scene] Executing scene:', sceneId);

    try {
      // Parameter validation
      if (!sceneId) {
        console.error('❌ [Scene] Execute scene failed: Scene ID parameter incomplete');
        return { success: false, message: 'Parameter incomplete: Scene ID cannot be empty' };
      }

      if (typeof sceneId !== 'string') {
        console.error('❌ [Scene] Execute scene failed: Scene ID parameter type error');
        return { success: false, message: 'Parameter incomplete: Scene ID must be string' };
      }

      if (!this.scenes.has(sceneId)) {
        console.error('❌ [Scene] Execute scene failed: Scene does not exist, ID:', sceneId);
        return { success: false, message: 'Scene does not exist' };
      }

      const scene = this.scenes.get(sceneId);

      // Validate scene data integrity
      if (!scene.actions || !Array.isArray(scene.actions)) {
        console.error('❌ [Scene] Execute scene failed: Scene action data incomplete');
        return { success: false, message: 'Scene action data incomplete' };
      }

      console.log('🎬 [Scene] Scene info:', {
        scene_id: scene.scene_id,
        scene_name: scene.scene_name,
        actionCount: scene.actions.length
      });

      // Add offline mode status debugging
      console.log('🔍 [Scene] Offline mode status check:', {
        hasApiRegistry: !!this.apiRegistry,
        offlineMode: this.offlineMode,
        shouldUseOfflineMode: !this.apiRegistry || this.offlineMode
      });

      // Check if offline mode
      if (!this.apiRegistry || this.offlineMode) {
        console.log('🟡 [Scene] Offline mode: executing scene locally');

        // In offline mode, directly apply actions to local device state
        const result = await this.executeSceneLocally(scene);
        return result;
      }

      console.log('🌐 [Scene] Online mode: calling server API');
      // Call server API to execute scene
      const response = await this.apiRegistry.executeScene(sceneId);

      if (response && (response.code === 1007 || response.code === 1008)) {
        // 场景执行成功或部分成功
        console.log('✅ [Scene] Scene executed:', response.summary);

        // 如果有失败的动作，也要应用成功的动作到本地
        if (response.code === 1007 || response.summary.success > 0) {
          await this.executeSceneLocally(scene);
        }

        return {
          success: true,
          message: response.code === 1007 ? '场景执行成功' : '场景执行部分成功',
          data: {
            summary: response.summary
          },
          failedActions: response.failed_actions || []
        };
      } else {
        return {
          success: false,
          message: response.message || '场景执行失败'
        };
      }
    } catch (error) {
      console.error('Failed to execute scene:', error);
      return { success: false, message: '执行失败：' + error.message };
    }
  }

  // 本地执行场景（离线模式或同步本地状态）
  async executeSceneLocally(scene) {
    console.log('🔧 [Scene] Executing scene locally:', scene.scene_name);

    const results = {
      total: scene.actions.length,
      success: 0,
      failed: 0,
      skipped: 0
    };

    const failedActions = [];

    for (const action of scene.actions) {
      try {
        if (this.deviceControlManager) {
          // 使用设备控制管理器执行动作
          const controlResult = await this.deviceControlManager.controlDevice(
            action.did,
            action.operation,
            action.value
          );

          if (controlResult.success) {
            results.success++;
          } else {
            results.failed++;
            failedActions.push({
              action_id: action.action_id,
              error: controlResult.message
            });
          }
        } else {
          // 直接更新设备状态（简化版本）
          if (this.deviceStorageManager) {
            const device = this.deviceStorageManager.getDevice(action.did);
            if (device) {
              device.status = device.status || {};
              device.status[action.operation] = action.value;
              this.deviceStorageManager.updateDevice(device);
              results.success++;
            } else {
              results.failed++;
              failedActions.push({
                action_id: action.action_id,
                error: 'DEVICE_NOT_FOUND'
              });
            }
          }
        }
      } catch (error) {
        console.error('Failed to execute action:', action, error);
        results.failed++;
        failedActions.push({
          action_id: action.action_id,
          error: error.message
        });
      }
    }

    console.log('✅ [Scene] Local execution completed:', results);

    return {
      success: true,
      message: '场景执行完成（离线模式）',
      data: {
        summary: results
      },
      failedActions: failedActions
    };
  }

  // 获取场景列表（按分组过滤）
  getScenesByGroup(gid) {
    const groupScenes = Array.from(this.scenes.values()).filter(scene => scene.gid === gid);
    return groupScenes.map(scene => ({
      scene_id: scene.scene_id,
      scene_name: scene.scene_name,
      gid: scene.gid,
      created: scene.created,
      updated: scene.updated,
      actionCount: scene.actions ? scene.actions.length : 0
    }));
  }

  // 获取场景列表（主进程调用的方法）
  async getScenes(gid) {
    try {
      const groupScenes = this.getScenesByGroup(gid);
      return {
        success: true,
        data: {
          scenes: groupScenes,
          total: groupScenes.length
        }
      };
    } catch (error) {
      console.error('Failed to get scenes:', error);
      return { success: false, message: '获取场景列表失败：' + error.message };
    }
  }

  // 获取分组可用设备（用于场景创建）
  async getGroupDevicesForScene(gid) {
    console.log('🔧 [SceneManager] 获取分组可用设备, 分组ID:', gid);

    try {
      const groupDevices = await this.getGroupDevices(gid);
      console.log('🔧 [SceneManager] 分组内所有设备数量:', groupDevices.length);

      // 详细输出所有设备信息
      groupDevices.forEach((device, index) => {
        console.log(`🔧 [SceneManager] 设备${index + 1}: ${device.name || device.did} (类型:${device.type}, 分组:${device.group || device.gid || device.groupId || 'default'})`);
      });

      // 过滤出可控制的设备（排除传感器设备）
      const controllableDevices = groupDevices.filter(device => {
        // 传感器设备类型通常包含 sensor 或 history
        const deviceType = device.type || '';
        const isControllable = !deviceType.includes('sensor') &&
                              !deviceType.includes('history') &&
                              device !== 'history';

        console.log(`🔧 [SceneManager] 设备过滤: ${device.name || device.did} (${deviceType}) - 可控制: ${isControllable}`);
        return isControllable;
      });

      console.log('✅ [SceneManager] 可控制设备数量:', controllableDevices.length);

      // 详细输出可控制设备
      controllableDevices.forEach((device, index) => {
        console.log(`✅ [SceneManager] 可控制设备${index + 1}: ${device.name || device.did} (${device.type})`);
      });

      return {
        success: true,
        data: {
          devices: controllableDevices,
          total: controllableDevices.length
        }
      };
    } catch (error) {
      console.error('❌ [SceneManager] 获取分组设备失败:', error);
      return { success: false, message: '获取分组设备失败：' + error.message };
    }
  }

  // 获取场景详细信息
  getSceneDetail(sceneId) {
    const scene = this.scenes.get(sceneId);
    if (scene) {
      return {
        success: true,
        data: scene
      };
    } else {
      return { success: false, message: '场景不存在' };
    }
  }

  // 获取所有场景
  getAllScenes() {
    return Array.from(this.scenes.values());
  }

  // 处理场景动作（智能电源补齐、冲突检测、属性值校验）
  async processSceneActions(actions, gid) {
    console.log('🔧 [Scene] Processing scene actions:', actions);

    try {
      if (!Array.isArray(actions) || actions.length === 0) {
        return { success: true, data: [] };
      }

      // 获取分组内的设备列表
      const groupDevices = await this.getGroupDevices(gid);
      const deviceMap = new Map(groupDevices.map(device => [device.did, device]));

      // 验证设备存在性
      for (const action of actions) {
        if (!deviceMap.has(action.did)) {
          return { success: false, message: `设备 ${action.did} 不存在于当前分组` };
        }
      }

      // 按设备分组动作
      const deviceActions = new Map();
      actions.forEach(action => {
        if (!deviceActions.has(action.did)) {
          deviceActions.set(action.did, []);
        }
        deviceActions.get(action.did).push(action);
      });

      const processedActions = [];

      // 处理每个设备的动作
      for (const [deviceId, deviceActionList] of deviceActions) {
        const device = deviceMap.get(deviceId);

        // 验证属性值
        const validationResult = this.validateActionValues(device, deviceActionList);
        if (!validationResult.success) {
          return validationResult;
        }

        // 检查动作冲突
        const conflictResult = this.checkActionConflicts(device, deviceActionList);
        if (!conflictResult.success) {
          return conflictResult;
        }

        // 智能电源补齐
        const fixedActions = this.autoFixPowerActions(device, deviceActionList);
        processedActions.push(...fixedActions);
      }

      console.log('✅ [Scene] Actions processed successfully:', processedActions);
      return { success: true, data: processedActions };

    } catch (error) {
      console.error('Failed to process scene actions:', error);
      return { success: false, message: '动作处理失败：' + error.message };
    }
  }

  // 验证动作属性值 - 支持场景级动作验证（考虑已有动作和新动作）
  validateActionValues(device, actions, existingActions = []) {
    if (!this.deviceControlManager) {
      console.log('🟡 [Scene] Device control manager not available, skipping validation');
      return { success: true };
    }

    // 创建一个包含当前动作的虚拟设备状态，用于验证（深拷贝避免修改原始设备）
    const virtualDeviceState = JSON.parse(JSON.stringify(device));

    // 合并已有动作和新动作，检查场景中是否包含开机指令
    const allActions = [...existingActions, ...actions];

    const hasPowerOnAction = allActions.some(action =>
      action.operation === 'power' &&
      (action.value === 'ON' || action.value === true || action.value === 1)
    );

    // 检查是否有需要开机的操作
    const deviceType = device.type;
    const powerDependentProps = this.POWER_DEPENDENT_PROPS[deviceType] || [];
    const hasPowerDependentAction = actions.some(action =>
      powerDependentProps.includes(action.operation)
    );

    console.log(`🔍 [Scene] 动作验证 - 设备: ${device.name}, 已有动作: ${existingActions.length}, 新动作: ${actions.length}`);
    console.log(`🔍 [Scene] 场景中包含开机动作: ${hasPowerOnAction}, 需要开机的操作: ${hasPowerDependentAction}`);

    // 如果场景中有开机动作（包括已有的和新添加的），临时设置设备为开机状态进行验证
    if (hasPowerOnAction) {
      if (!virtualDeviceState.status) {
        virtualDeviceState.status = {};
      }
      virtualDeviceState.status.power = 'ON';
      virtualDeviceState.online = true;

      // 对于加湿器，同时更新status字段以避免约束冲突
      if (deviceType === 'mi_humidifier' || deviceType === 'midea_humidifier') {
        virtualDeviceState.status.status = deviceType === 'midea_humidifier' ? 'on' : 'running';
      }

      console.log(`🔧 [Scene] 场景包含开机动作，虚拟设置设备为开机状态用于验证`);
    } else if (hasPowerDependentAction) {
      // 如果有需要开机的操作但场景中没有开机动作，检查设备当前是否为开机状态
      const currentPowerState = device.status?.power;
      const isCurrentlyOn = currentPowerState === 'ON' || currentPowerState === true || currentPowerState === 1;

      if (!isCurrentlyOn) {
        return {
          success: false,
          message: `设备 ${device.name || device.did} 当前为关机状态，无法执行需要开机的操作。请先添加开机动作。`
        };
      }
    }

    // 验证每个新动作
    for (const action of actions) {
      const validation = this.deviceControlManager.validateControlCommand(
        virtualDeviceState,
        action.operation,
        action.value
      );

      if (!validation.valid) {
        return {
          success: false,
          message: `设备 ${device.name || device.did} 的动作验证失败: ${validation.message}`
        };
      }
    }

    return { success: true };
  }

  // 检查动作冲突
  checkActionConflicts(device, actions) {
    const deviceType = device.type;
    const rules = this.CONFLICT_RULES[deviceType] || {};

    // 检查重复属性设置
    const propertySet = new Set();
    for (const action of actions) {
      if (propertySet.has(action.operation)) {
        return {
          success: false,
          message: `设备 ${device.did} 不能在同一场景中重复设置属性 ${action.operation}`
        };
      }
      propertySet.add(action.operation);
    }

    // 检查属性冲突
    const actionMap = new Map(actions.map(action => [action.operation, action.value]));

    for (const action of actions) {
      const conflictRules = rules[action.operation];
      if (conflictRules) {
        // 检查是否有冲突的模式设置
        if (actionMap.has('mode')) {
          const modeValue = actionMap.get('mode');
          if (conflictRules.includes(modeValue)) {
            return {
              success: false,
              message: `设备 ${device.did} 在 ${modeValue} 模式下不能设置 ${action.operation}`
            };
          }
        }
      }
    }

    return { success: true };
  }

  // 智能电源补齐
  autoFixPowerActions(device, actions) {
    const deviceType = device.type;
    const powerDependentProps = this.POWER_DEPENDENT_PROPS[deviceType] || [];

    const actionMap = new Map(actions.map(action => [action.operation, action]));
    const fixedActions = [...actions];

    // 检查是否需要补开机指令
    const needsPower = actions.some(action =>
      powerDependentProps.includes(action.operation)
    );
    const hasPower = actionMap.has('power');

    if (needsPower && !hasPower) {
      // 在动作列表开头插入开机指令
      fixedActions.unshift({
        did: device.did,
        operation: 'power',
        value: 'ON'
      });
    }

    // 如果有关机指令，移除其他无效设置
    const hasPowerOff = actionMap.has('power') &&
      (actionMap.get('power').value === 'OFF' || actionMap.get('power').value === false);

    if (hasPowerOff) {
      return fixedActions.filter(action =>
        action.operation === 'power' ||
        !powerDependentProps.includes(action.operation)
      );
    }

    return fixedActions;
  }

  // 获取分组内的设备列表
  async getGroupDevices(gid) {
    console.log('🔧 [SceneManager] getGroupDevices 调用, 分组ID:', gid);
    console.log('🔧 [SceneManager] deviceStorageManager 状态:', !!this.deviceStorageManager);

    if (this.deviceStorageManager) {
      const allDevices = this.deviceStorageManager.getAllDevices();
      console.log('🔧 [SceneManager] 所有设备总数:', allDevices.length);

      // 详细输出前5个设备的分组信息
      allDevices.slice(0, 5).forEach((device, index) => {
        console.log(`🔧 [SceneManager] 设备${index + 1}分组信息: ${device.name || device.did} - group:${device.group}, gid:${device.gid}, groupId:${device.groupId}`);
      });

      // 支持多种分组字段名称：group, gid, groupId
      const filteredDevices = allDevices.filter(device => {
        const matchesGroup = device.group === gid ||
                           device.gid === gid ||
                           device.groupId === gid ||
                           (gid === 'default' && (!device.group && !device.gid && !device.groupId));

        if (matchesGroup) {
          console.log(`✅ [SceneManager] 匹配设备: ${device.name || device.did} (分组匹配)`);
        }

        return matchesGroup;
      });

      console.log('✅ [SceneManager] 分组内设备数量:', filteredDevices.length);
      return filteredDevices;
    } else {
      console.error('❌ [SceneManager] deviceStorageManager 未初始化');
      return [];
    }
  }

  // 启用离线模式
  enableOfflineMode() {
    this.offlineMode = true;
    console.log('Scene manager offline mode enabled');
  }

  // 禁用离线模式
  disableOfflineMode() {
    this.offlineMode = false;
    console.log('Scene manager offline mode disabled');
  }

  // 检查是否为离线模式
  isOfflineMode() {
    return this.offlineMode;
  }

  // 重置场景管理器
  reset() {
    this.scenes.clear();
    this.isInitialized = false;
    console.log('Scene manager has been reset');
  }

  // 导出场景数据
  exportSceneData() {
    return {
      success: true,
      data: {
        scenes: Array.from(this.scenes.values()),
        sceneCount: this.scenes.size
      }
    };
  }

  /**
   * 验证场景中添加新动作（支持考虑已有动作）
   * @param {Array} newActions - 新添加的动作列表
   * @param {Array} existingActions - 已有的动作列表
   * @returns {object} 验证结果
   */
  validateSceneActionAddition(newActions, existingActions = []) {
    if (!Array.isArray(newActions)) {
      return { valid: false, message: '新动作列表必须是数组' };
    }

    if (newActions.length === 0) {
      return { valid: false, message: '至少需要添加一个动作' };
    }

    const errors = [];
    const allActions = [...existingActions, ...newActions]; // 合并所有动作

    // 按设备分组所有动作
    const deviceActionGroups = new Map();

    for (const action of allActions) {
      if (!deviceActionGroups.has(action.did)) {
        deviceActionGroups.set(action.did, []);
      }
      deviceActionGroups.get(action.did).push(action);
    }

    // 对每个设备进行验证
    for (const [deviceId, deviceActions] of deviceActionGroups) {
      const device = this.deviceStorageManager?.getDevice(deviceId);
      if (!device) {
        errors.push(`设备不存在: ${deviceId}`);
        continue;
      }

      // 过滤出这个设备的新动作和已有动作
      const deviceExistingActions = existingActions.filter(action => action.did === deviceId);
      const deviceNewActions = newActions.filter(action => action.did === deviceId);

      if (deviceNewActions.length === 0) continue; // 如果这个设备没有新动作，跳过

      // 检查设备是否可控制
      if (this.deviceControlManager) {
        const controllableCheck = this.deviceControlManager.validateDeviceControllable(device);
        if (!controllableCheck.valid) {
          errors.push(`设备 ${device.name}: ${controllableCheck.message}`);
          continue;
        }

        // 智能验证：传入已有动作和新动作
        const actionValidation = this.validateActionValues(device, deviceNewActions, deviceExistingActions);
        if (!actionValidation.success) {
          errors.push(`设备 ${device.name}: ${actionValidation.message}`);
          continue;
        }

        // 检查所有动作（包括已有的）的冲突
        const conflictCheck = this.checkActionConflicts(device, deviceActions);
        if (!conflictCheck.success) {
          errors.push(`设备 ${device.name}: ${conflictCheck.message}`);
          continue;
        }
      }
    }

    if (errors.length > 0) {
      return { valid: false, message: errors.join('; ') };
    }

    return { valid: true, message: '新动作验证通过' };
  }

  /**
   * 验证场景动作列表
   * @param {Array} actions - 动作列表
   * @returns {object} 验证结果
   */
  validateSceneActions(actions) {
    if (!Array.isArray(actions)) {
      return { valid: false, message: '动作列表必须是数组' };
    }

    if (actions.length === 0) {
      return { valid: false, message: '场景至少需要包含一个动作' };
    }

    const errors = [];
    const deviceActions = new Map(); // 用于检测同设备同属性的重复动作

    // 按设备分组动作，以便进行智能验证
    const deviceActionGroups = new Map();

    for (let i = 0; i < actions.length; i++) {
      const action = actions[i];

      // 基础字段验证
      if (!action.did) {
        errors.push(`动作${i + 1}: 缺少设备ID`);
        continue;
      }

      if (!action.operation) {
        errors.push(`动作${i + 1}: 缺少操作属性`);
        continue;
      }

      if (action.value === undefined || action.value === null) {
        errors.push(`动作${i + 1}: 缺少操作值`);
        continue;
      }

      // 检查重复动作（同一设备的同一属性）
      const actionKey = `${action.did}_${action.operation}`;
      if (deviceActions.has(actionKey)) {
        const device = this.deviceStorageManager?.getDevice(action.did);
        const deviceName = device ? device.name : action.did;
        errors.push(`动作${i + 1}: 重复设置设备 ${deviceName} 的 ${action.operation} 属性`);
        continue;
      } else {
        deviceActions.set(actionKey, true);
      }

      // 按设备分组
      if (!deviceActionGroups.has(action.did)) {
        deviceActionGroups.set(action.did, []);
      }
      deviceActionGroups.get(action.did).push(action);
    }

    // 对每个设备的动作进行验证
    for (const [deviceId, deviceActions] of deviceActionGroups) {
      // 获取设备信息
      const device = this.deviceStorageManager?.getDevice(deviceId);
      if (!device) {
        errors.push(`设备不存在: ${deviceId}`);
        continue;
      }

      // 检查设备是否可控制
      if (this.deviceControlManager) {
        const controllableCheck = this.deviceControlManager.validateDeviceControllable(device);
        if (!controllableCheck.valid) {
          errors.push(`设备 ${device.name}: ${controllableCheck.message}`);
          continue;
        }

        // 使用智能验证（考虑设备动作组合） - 传入空的existingActions因为在这里验证的就是完整的actions
        const actionValidation = this.validateActionValues(device, deviceActions, []);
        if (!actionValidation.success) {
          errors.push(`设备 ${device.name}: ${actionValidation.message}`);
          continue;
        }

        // 检查动作冲突
        const conflictCheck = this.checkActionConflicts(device, deviceActions);
        if (!conflictCheck.success) {
          errors.push(`设备 ${device.name}: ${conflictCheck.message}`);
          continue;
        }
      }
    }

    if (errors.length > 0) {
      return { valid: false, message: errors.join('; ') };
    }

    return { valid: true, message: '场景动作验证通过' };
  }

  /**
   * 获取设备的可控制属性选项
   * @param {string} did - 设备ID
   * @returns {object|null} 设备控制选项
   */
  getDeviceControlOptions(did) {
    if (!this.deviceControlManager) {
      console.error('❌ [Scene] DeviceControlManager not available');
      return null;
    }

    return this.deviceControlManager.getDeviceControlOptions(did);
  }

  /**
   * 获取设备属性的可选值
   * @param {string} deviceType - 设备类型
   * @param {string} property - 属性名
   * @returns {Array|null} 可选值列表
   */
  getPropertyOptions(deviceType, property) {
    if (!this.deviceControlManager) {
      return null;
    }

    const deviceLimits = this.deviceControlManager.deviceLimits[deviceType];
    if (!deviceLimits || !deviceLimits[property]) {
      return null;
    }

    const config = deviceLimits[property];
    if (config.values) {
      return config.values;
    } else if (config.min !== undefined && config.max !== undefined) {
      // 对于数值范围，返回范围信息
      return {
        type: 'range',
        min: config.min,
        max: config.max,
        step: config.precision || 1
      };
    }

    return null;
  }

  /**
   * 获取属性的显示标签
   * @param {string} property - 属性名
   * @returns {string} 显示标签
   */
  getPropertyLabel(property) {
    if (this.deviceControlManager) {
      return this.deviceControlManager.getPropertyLabel(property);
    }

    // 兜底标签
    const labels = {
      power: '电源',
      target_temperature: '目标温度',
      fan_speed: '风速',
      mode: '模式',
      status: '状态',
      target_humidity: '目标湿度',
      fan_level: '风扇等级'
    };
    return labels[property] || property;
  }
}

module.exports = SceneManager;

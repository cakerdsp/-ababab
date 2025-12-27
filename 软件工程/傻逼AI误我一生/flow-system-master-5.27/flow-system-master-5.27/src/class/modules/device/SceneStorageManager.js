const UnifiedStorage = require('../../services/storage/UnifiedStorage');
const fs = require('fs');
const path = require('path');

/**
 * 场景存储管理器
 * 专门负责场景数据的本地存储和管理
 */
class SceneStorageManager {
  constructor() {
    this.storage = new UnifiedStorage();
    this.scenesFilePath = path.join(process.cwd(), 'data', 'scenes.json');
    this.isInitialized = false;

    // 确保数据目录存在
    this.ensureDataDirectory();
  }

  // 确保数据目录存在
  ensureDataDirectory() {
    const dataDir = path.dirname(this.scenesFilePath);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
      console.log('Created scenes data directory:', dataDir);
    }
  }

  // 初始化存储管理器
  async initialize() {
    if (this.isInitialized) {
      return { success: true, message: '场景存储管理器已初始化' };
    }

    try {
      // 确保场景文件存在
      if (!fs.existsSync(this.scenesFilePath)) {
        await this.saveScenesToFile([]);
      }

      this.isInitialized = true;
      console.log('Scene storage manager initialized successfully');
      return {
        success: true,
        message: '场景存储管理器初始化成功'
      };
    } catch (error) {
      console.error('Scene storage manager initialization failed:', error);
      return { success: false, message: '初始化失败：' + error.message };
    }
  }

  // 保存场景到文件
  async saveScenesToFile(scenes) {
    try {
      const scenesData = {
        version: '1.0',
        timestamp: new Date().toISOString(),
        scenes: scenes
      };

      fs.writeFileSync(this.scenesFilePath, JSON.stringify(scenesData, null, 2), 'utf8');
      console.log(`Saved ${scenes.length} scenes to file:`, this.scenesFilePath);
      return { success: true };
    } catch (error) {
      console.error('Failed to save scenes to file:', error);
      return { success: false, message: error.message };
    }
  }

  // 从文件加载场景
  async loadScenesFromFile() {
    try {
      if (!fs.existsSync(this.scenesFilePath)) {
        console.log('Scenes file does not exist, returning empty array');
        return { success: true, data: [] };
      }

      const fileContent = fs.readFileSync(this.scenesFilePath, 'utf8');
      const scenesData = JSON.parse(fileContent);

      const scenes = scenesData.scenes || [];
      console.log(`Loaded ${scenes.length} scenes from file:`, this.scenesFilePath);

      return { success: true, data: scenes };
    } catch (error) {
      console.error('Failed to load scenes from file:', error);
      return { success: false, message: error.message, data: [] };
    }
  }

  // 保存单个场景
  async saveScene(scene) {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      // 查找是否已存在该场景
      const existingIndex = scenes.findIndex(s => s.scene_id === scene.scene_id);

      if (existingIndex >= 0) {
        // 更新现有场景
        scenes[existingIndex] = { ...scene, updated: new Date().toISOString() };
      } else {
        // 添加新场景
        scenes.push({ ...scene, created: new Date().toISOString() });
      }

      const saveResult = await this.saveScenesToFile(scenes);
      if (saveResult.success) {
        console.log('Scene saved successfully:', scene.scene_id);
        return { success: true, message: '场景保存成功' };
      } else {
        return saveResult;
      }
    } catch (error) {
      console.error('Failed to save scene:', error);
      return { success: false, message: error.message };
    }
  }

  // 删除场景
  async deleteScene(sceneId) {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      const filteredScenes = scenes.filter(scene => scene.scene_id !== sceneId);

      if (filteredScenes.length === scenes.length) {
        return { success: false, message: '场景不存在' };
      }

      const saveResult = await this.saveScenesToFile(filteredScenes);
      if (saveResult.success) {
        console.log('Scene deleted successfully:', sceneId);
        return { success: true, message: '场景删除成功' };
      } else {
        return saveResult;
      }
    } catch (error) {
      console.error('Failed to delete scene:', error);
      return { success: false, message: error.message };
    }
  }

  // 获取场景
  async getScene(sceneId) {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      const scene = scenes.find(s => s.scene_id === sceneId);
      return { success: true, data: scene || null };
    } catch (error) {
      console.error('Failed to get scene:', error);
      return { success: false, message: error.message, data: null };
    }
  }

  // 获取分组的场景列表
  async getScenesByGroup(gid) {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      const groupScenes = scenes.filter(scene => scene.gid === gid);
      return { success: true, data: groupScenes };
    } catch (error) {
      console.error('Failed to get scenes by group:', error);
      return { success: false, message: error.message, data: [] };
    }
  }

  // 获取所有场景
  async getAllScenes() {
    try {
      const loadResult = await this.loadScenesFromFile();
      return loadResult;
    } catch (error) {
      console.error('Failed to get all scenes:', error);
      return { success: false, message: error.message, data: [] };
    }
  }

  // 批量保存场景
  async batchSaveScenes(scenes) {
    try {
      const saveResult = await this.saveScenesToFile(scenes);
      if (saveResult.success) {
        console.log('Batch save scenes successfully:', scenes.length);
        return { success: true, message: '批量保存场景成功' };
      } else {
        return saveResult;
      }
    } catch (error) {
      console.error('Failed to batch save scenes:', error);
      return { success: false, message: error.message };
    }
  }

  // 清空所有场景
  async clearAllScenes() {
    try {
      const saveResult = await this.saveScenesToFile([]);
      if (saveResult.success) {
        console.log('All scenes cleared successfully');
        return { success: true, message: '所有场景已清空' };
      } else {
        return saveResult;
      }
    } catch (error) {
      console.error('Failed to clear all scenes:', error);
      return { success: false, message: error.message };
    }
  }

  // 备份场景数据
  async backupScenes() {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupPath = path.join(
        path.dirname(this.scenesFilePath),
        `scenes_backup_${timestamp}.json`
      );

      if (fs.existsSync(this.scenesFilePath)) {
        fs.copyFileSync(this.scenesFilePath, backupPath);
        console.log('Scenes backup created:', backupPath);
        return { success: true, message: '场景数据备份成功', backupPath };
      } else {
        return { success: false, message: '场景文件不存在' };
      }
    } catch (error) {
      console.error('Failed to backup scenes:', error);
      return { success: false, message: error.message };
    }
  }

  // 恢复场景数据
  async restoreScenes(backupPath) {
    try {
      if (!fs.existsSync(backupPath)) {
        return { success: false, message: '备份文件不存在' };
      }

      fs.copyFileSync(backupPath, this.scenesFilePath);
      console.log('Scenes restored from backup:', backupPath);
      return { success: true, message: '场景数据恢复成功' };
    } catch (error) {
      console.error('Failed to restore scenes:', error);
      return { success: false, message: error.message };
    }
  }

  // 获取存储统计信息
  async getStorageStats() {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      const stats = {
        totalScenes: scenes.length,
        scenesByGroup: {},
        fileSize: 0,
        lastModified: null
      };

      // 按分组统计
      scenes.forEach(scene => {
        const gid = scene.gid || 'unknown';
        stats.scenesByGroup[gid] = (stats.scenesByGroup[gid] || 0) + 1;
      });

      // 文件信息
      if (fs.existsSync(this.scenesFilePath)) {
        const fileStats = fs.statSync(this.scenesFilePath);
        stats.fileSize = fileStats.size;
        stats.lastModified = fileStats.mtime.toISOString();
      }

      return { success: true, data: stats };
    } catch (error) {
      console.error('Failed to get storage stats:', error);
      return { success: false, message: error.message };
    }
  }

  // 验证场景数据完整性
  async validateScenesData() {
    try {
      const loadResult = await this.loadScenesFromFile();
      const scenes = loadResult.data || [];

      const validationResults = {
        totalScenes: scenes.length,
        validScenes: 0,
        invalidScenes: 0,
        errors: []
      };

      scenes.forEach((scene, index) => {
        const errors = [];

        // 检查必需字段
        if (!scene.scene_id) errors.push('缺少 scene_id');
        if (!scene.scene_name) errors.push('缺少 scene_name');
        if (!scene.gid) errors.push('缺少 gid');
        if (!Array.isArray(scene.actions)) errors.push('actions 不是数组');

        // 检查动作格式
        if (Array.isArray(scene.actions)) {
          scene.actions.forEach((action, actionIndex) => {
            if (!action.did) errors.push(`动作 ${actionIndex} 缺少 did`);
            if (!action.operation) errors.push(`动作 ${actionIndex} 缺少 operation`);
            if (action.value === undefined) errors.push(`动作 ${actionIndex} 缺少 value`);
          });
        }

        if (errors.length === 0) {
          validationResults.validScenes++;
        } else {
          validationResults.invalidScenes++;
          validationResults.errors.push({
            sceneIndex: index,
            sceneId: scene.scene_id,
            errors: errors
          });
        }
      });

      return { success: true, data: validationResults };
    } catch (error) {
      console.error('Failed to validate scenes data:', error);
      return { success: false, message: error.message };
    }
  }

  // 重置存储管理器
  reset() {
    this.isInitialized = false;
    console.log('Scene storage manager has been reset');
  }
}

module.exports = SceneStorageManager;

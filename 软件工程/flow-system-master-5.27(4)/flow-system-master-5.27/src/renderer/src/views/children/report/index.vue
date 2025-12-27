<template>
  <div class="environment-monitor">
    <!-- 顶部控制面板 -->
    <div class="control-panel">
      <div class="group-select">
        <span>选择分组:</span>
        <select 
          v-model="selectedGroupId" 
          @change="onGroupChange" 
          class="group-dropdown"
        >
          <option value="" disabled>请选择分组</option>
          <option v-for="group in groupList" :key="group.gid" :value="group.gid">
            {{ group.gname }}
          </option>
        </select>
      </div>
      
      <div class="controls">
        <button 
          class="refresh-btn" 
          @click="refreshAnalysis" 
          :disabled="loading || !selectedGroupId"
        >
          <span class="btn-icon">🔄</span>
          {{ loading ? '分析中...' : '刷新分析' }}
        </button>
        
        <button 
          class="export-btn" 
          @click="exportReport" 
          :disabled="!analysisResult || loading"
        >
          <span class="btn-icon">📊</span>
          导出报告
        </button>
      </div>
    </div>

    <!-- 分析结果展示 -->
    <div v-if="selectedGroupId && analysisResult" class="analysis-container">
      <!-- 概览卡片 -->
      <div class="overview-cards">
        <div class="overview-card" v-for="metric in overviewMetrics" :key="metric.type">
          <div class="card-header">
            <span class="card-icon">{{ metric.icon }}</span>
            <span class="card-title">{{ metric.title }}</span>
          </div>
          <div class="card-content">
            <div class="metric-value">{{ getMetricValue(metric.type) }}</div>
            <div class="metric-status" :class="getMetricStatus(metric.type)">
              {{ getMetricStatusText(metric.type) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 详细分析 -->
      <div class="detailed-analysis">
        <div class="analysis-section">
          <h3 class="section-title">温度分析</h3>
          <div class="analysis-grid">
            <div class="analysis-item">
              <span class="item-label">平均温度</span>
              <span class="item-value">{{ formatTemperature(analysisResult.temperature?.average) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最高温度</span>
              <span class="item-value">{{ formatTemperature(analysisResult.temperature?.max?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最低温度</span>
              <span class="item-value">{{ formatTemperature(analysisResult.temperature?.min?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">温度趋势</span>
              <span class="item-value" :class="getTrendClass(analysisResult.temperature?.trend)">
                {{ formatTrend(analysisResult.temperature?.trend) }}
              </span>
            </div>
          </div>
          <div class="analysis-details">
            <p><strong>建议：</strong>{{ analysisResult.temperature?.recommendation || '暂无建议' }}</p>
          </div>
        </div>

        <div class="analysis-section">
          <h3 class="section-title">湿度分析</h3>
          <div class="analysis-grid">
            <div class="analysis-item">
              <span class="item-label">平均湿度</span>
              <span class="item-value">{{ formatHumidity(analysisResult.humidity?.average) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最高湿度</span>
              <span class="item-value">{{ formatHumidity(analysisResult.humidity?.max?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最低湿度</span>
              <span class="item-value">{{ formatHumidity(analysisResult.humidity?.min?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">湿度趋势</span>
              <span class="item-value" :class="getTrendClass(analysisResult.humidity?.trend)">
                {{ formatTrend(analysisResult.humidity?.trend) }}
              </span>
            </div>
          </div>
          <div class="analysis-details">
            <p><strong>建议：</strong>{{ analysisResult.humidity?.recommendation || '暂无建议' }}</p>
          </div>
        </div>

        <div v-if="analysisResult.pm25" class="analysis-section">
          <h3 class="section-title">空气质量分析</h3>
          <div class="analysis-grid">
            <div class="analysis-item">
              <span class="item-label">平均PM2.5</span>
              <span class="item-value">{{ formatPM25(analysisResult.pm25?.average) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最高PM2.5</span>
              <span class="item-value">{{ formatPM25(analysisResult.pm25?.max?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">最低PM2.5</span>
              <span class="item-value">{{ formatPM25(analysisResult.pm25?.min?.value) }}</span>
            </div>
            <div class="analysis-item">
              <span class="item-label">空气质量等级</span>
              <span class="item-value" :class="getAirQualityClass(analysisResult.pm25?.average)">
                {{ getAirQualityLevel(analysisResult.pm25?.average) }}
              </span>
            </div>
          </div>
          <div class="analysis-details">
            <p><strong>建议：</strong>{{ analysisResult.pm25?.recommendation || '暂无建议' }}</p>
          </div>
        </div>

        <!-- 综合评估 -->
        <div class="analysis-section">
          <h3 class="section-title">综合评估</h3>
          <div class="comprehensive-assessment">
            <div class="comfort-score">
              <span class="score-label">舒适度评分</span>
              <span class="score-value" :class="getComfortScoreClass(analysisResult.overallScore)">
                {{ analysisResult.overallScore || 'N/A' }}/10
              </span>
            </div>
            <div class="assessment-text">
              <p>{{ analysisResult.overallAssessment || '暂无评估' }}</p>
            </div>
            <div class="recommendations">
              <h4>改善建议</h4>
              <ul v-if="analysisResult.recommendations && analysisResult.recommendations.length > 0">
                <li v-for="(rec, index) in analysisResult.recommendations" :key="index">
                  {{ rec }}
                </li>
              </ul>
              <p v-else>当前环境状况良好，无需特别改善。</p>
            </div>
          </div>
        </div>

        <!-- 数据统计 -->
        <div class="analysis-section">
          <h3 class="section-title">数据统计</h3>
          <div class="statistics">
            <div class="stat-item">
              <span class="stat-label">分析时间范围</span>
              <span class="stat-value">{{ formatTimeRange() }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">传感器设备数量</span>
              <span class="stat-value">{{ analysisResult.deviceCount || 0 }} 个</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">数据样本数</span>
              <span class="stat-value">{{ analysisResult.sampleCount || 0 }} 条</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">分析完成时间</span>
              <span class="stat-value">{{ formatAnalysisTime() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!selectedGroupId" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">请选择一个分组开始环境数据分析</div>
    </div>

    <div v-else-if="!analysisResult && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">点击"刷新分析"按钮开始分析</div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在分析传感器数据，请稍候...</div>
    </div>

    <!-- 错误状态 -->
    <div v-if="errorMessage" class="error-state">
      <div class="error-icon">⚠️</div>
      <div class="error-text">{{ errorMessage }}</div>
      <button class="retry-btn" @click="refreshAnalysis">重试</button>
    </div>
  </div>
</template>

<script>
// 使用预加载脚本暴露的ipcRenderer
const ipcRenderer = window.ipcRenderer;

export default {
  name: 'EnvironmentReport',
  data() {
    return {
      // 分组列表
      groupList: [],
      selectedGroupId: '',
      
      // 状态管理
      loading: false,
      errorMessage: '',
      
      // 分析结果
      analysisResult: null,
      
      // 概览指标配置
      overviewMetrics: [
        {
          type: 'temperature',
          title: '温度',
          icon: '🌡️'
        },
        {
          type: 'humidity',
          title: '湿度',
          icon: '💧'
        },
        {
          type: 'pm25',
          title: 'PM2.5',
          icon: '🌫️'
        },
        {
          type: 'comfort',
          title: '舒适度',
          icon: '😊'
        }
      ]
    }
  },

  async mounted() {
    console.log('环境报告页面已挂载');
    await this.initializeData();
  },

  methods: {
    // 初始化数据
    async initializeData() {
      this.loading = true;
      this.errorMessage = '';
      
      try {
        await this.loadGroups();
        
        // 如果有分组，自动选择第一个
        if (this.groupList.length > 0) {
          this.selectedGroupId = this.groupList[0].gid;
          await this.performAnalysis();
        }
      } catch (error) {
        console.error('初始化数据失败:', error);
        this.errorMessage = '初始化数据失败，请刷新页面重试';
      } finally {
        this.loading = false;
      }
    },

    // 加载分组列表
    async loadGroups() {
      try {
        const result = await ipcRenderer.invoke('get-all-groups');
        if (result.success) {
          this.groupList = result.data;
          console.log('分组列表加载成功:', this.groupList);
        } else {
          throw new Error(result.message || '加载分组失败');
        }
      } catch (error) {
        console.error('加载分组列表失败:', error);
        this.errorMessage = '加载分组列表失败';
      }
    },

    // 分组变更处理
    async onGroupChange() {
      if (this.selectedGroupId) {
        await this.performAnalysis();
      }
    },

    // 刷新分析
    async refreshAnalysis() {
      if (!this.selectedGroupId) {
        this.$message.warning('请先选择一个分组');
        return;
      }
      await this.performAnalysis();
    },

    // 执行数据分析
    async performAnalysis() {
      if (!this.selectedGroupId) return;

      this.loading = true;
      this.errorMessage = '';
      
      try {
        const result = await ipcRenderer.invoke('analyze-group-sensor-data', this.selectedGroupId);
        
        if (result.success) {
          this.analysisResult = result.data;
          console.log('分析结果:', this.analysisResult);
          this.$message.success('数据分析完成');
        } else {
          this.errorMessage = result.message || '数据分析失败';
          this.$message.error(this.errorMessage);
        }
      } catch (error) {
        console.error('数据分析失败:', error);
        this.errorMessage = '数据分析失败，请重试';
        this.$message.error(this.errorMessage);
      } finally {
        this.loading = false;
      }
    },

    // 导出报告
    async exportReport() {
      if (!this.analysisResult) {
        this.$message.warning('没有可导出的分析结果');
        return;
      }

      try {
        const result = await ipcRenderer.invoke('export-analysis-result', this.analysisResult);
        
        if (result.success) {
          // 创建下载链接
          const blob = new Blob([result.data], { type: 'application/json' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          
          link.href = url;
          link.download = `环境分析报告_${this.getSelectedGroupName()}_${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          this.$message.success('报告导出成功');
        } else {
          this.$message.error(result.message || '导出失败');
        }
      } catch (error) {
        console.error('导出报告失败:', error);
        this.$message.error('导出报告失败');
      }
    },

    // ==================== 格式化方法 ====================
    
    // 获取选中分组名称
    getSelectedGroupName() {
      const group = this.groupList.find(g => g.gid === this.selectedGroupId);
      return group ? group.gname : '';
    },

    // 获取指标值
    getMetricValue(type) {
      if (!this.analysisResult) return 'N/A';
      
      switch (type) {
        case 'temperature':
          return this.formatTemperature(this.analysisResult.temperature?.average);
        case 'humidity':
          return this.formatHumidity(this.analysisResult.humidity?.average);
        case 'pm25':
          return this.formatPM25(this.analysisResult.pm25?.average);
        case 'comfort':
          return this.analysisResult.overallScore ? `${this.analysisResult.overallScore}/10` : 'N/A';
        default:
          return 'N/A';
      }
    },

    // 获取指标状态
    getMetricStatus(type) {
      if (!this.analysisResult) return 'unknown';
      
      switch (type) {
        case 'temperature':
          const temp = this.analysisResult.temperature?.average;
          if (temp >= 20 && temp <= 26) return 'good';
          if (temp >= 18 && temp <= 28) return 'normal';
          return 'poor';
        case 'humidity':
          const humidity = this.analysisResult.humidity?.average;
          if (humidity >= 40 && humidity <= 60) return 'good';
          if (humidity >= 30 && humidity <= 70) return 'normal';
          return 'poor';
        case 'pm25':
          const pm25 = this.analysisResult.pm25?.average;
          if (pm25 <= 35) return 'good';
          if (pm25 <= 75) return 'normal';
          return 'poor';
        case 'comfort':
          const score = this.analysisResult.overallScore;
          if (score >= 8) return 'good';
          if (score >= 6) return 'normal';
          return 'poor';
        default:
          return 'unknown';
      }
    },

    // 获取指标状态文本
    getMetricStatusText(type) {
      const status = this.getMetricStatus(type);
      const statusMap = {
        'good': '优秀',
        'normal': '正常',
        'poor': '需改善',
        'unknown': '未知'
      };
      return statusMap[status] || '未知';
    },

    // 格式化温度
    formatTemperature(value) {
      return value !== undefined && value !== null ? `${value.toFixed(1)}℃` : 'N/A';
    },

    // 格式化湿度
    formatHumidity(value) {
      return value !== undefined && value !== null ? `${value.toFixed(1)}%` : 'N/A';
    },

    // 格式化PM2.5
    formatPM25(value) {
      return value !== undefined && value !== null ? `${value.toFixed(1)}μg/m³` : 'N/A';
    },

    // 格式化趋势
    formatTrend(trend) {
      const trendMap = {
        'rising': '上升 ↗️',
        'falling': '下降 ↘️',
        'stable': '稳定 ➡️',
        'fluctuating': '波动 ↕️'
      };
      return trendMap[trend] || 'N/A';
    },

    // 获取趋势样式类
    getTrendClass(trend) {
      return {
        'trend-rising': trend === 'rising',
        'trend-falling': trend === 'falling',
        'trend-stable': trend === 'stable',
        'trend-fluctuating': trend === 'fluctuating'
      };
    },

    // 获取空气质量等级
    getAirQualityLevel(pm25Value) {
      if (pm25Value === undefined || pm25Value === null) return 'N/A';
      
      if (pm25Value <= 35) return '优';
      if (pm25Value <= 75) return '良';
      if (pm25Value <= 115) return '轻度污染';
      if (pm25Value <= 150) return '中度污染';
      if (pm25Value <= 250) return '重度污染';
      return '严重污染';
    },

    // 获取空气质量样式类
    getAirQualityClass(pm25Value) {
      const level = this.getAirQualityLevel(pm25Value);
      return {
        'air-excellent': level === '优',
        'air-good': level === '良',
        'air-light': level === '轻度污染',
        'air-moderate': level === '中度污染',
        'air-heavy': level === '重度污染',
        'air-severe': level === '严重污染'
      };
    },

    // 获取舒适度评分样式类
    getComfortScoreClass(score) {
      if (!score) return '';
      if (score >= 8) return 'score-excellent';
      if (score >= 6) return 'score-good';
      if (score >= 4) return 'score-normal';
      return 'score-poor';
    },

    // 格式化时间范围
    formatTimeRange() {
      if (!this.analysisResult || !this.analysisResult.timeRange) return 'N/A';
      
      const { start, end } = this.analysisResult.timeRange;
      const startDate = new Date(start).toLocaleDateString();
      const endDate = new Date(end).toLocaleDateString();
      
      return startDate === endDate ? startDate : `${startDate} - ${endDate}`;
    },

    // 格式化分析时间
    formatAnalysisTime() {
      if (!this.analysisResult || !this.analysisResult.analysisTime) return 'N/A';
      return new Date(this.analysisResult.analysisTime).toLocaleString();
    }
  }
}
</script>

<style scoped>
/* 基础样式 */
.environment-monitor {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

/* 控制面板样式 */
.control-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.group-select {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-select span {
  font-weight: 500;
  color: #495057;
}

.group-dropdown {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  min-width: 200px;
  background: white;
}

.controls {
  display: flex;
  gap: 12px;
}

.refresh-btn, .export-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.refresh-btn {
  background: #007bff;
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background: #0056b3;
}

.export-btn {
  background: #28a745;
  color: white;
}

.export-btn:hover:not(:disabled) {
  background: #1e7e34;
}

.refresh-btn:disabled, .export-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 16px;
}

/* 概览卡片样式 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.overview-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.card-icon {
  font-size: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #495057;
}

.card-content {
  text-align: center;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #212529;
  margin-bottom: 8px;
}

.metric-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.metric-status.good {
  background: #d4edda;
  color: #155724;
}

.metric-status.normal {
  background: #fff3cd;
  color: #856404;
}

.metric-status.poor {
  background: #f8d7da;
  color: #721c24;
}

/* 详细分析样式 */
.detailed-analysis {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.analysis-section {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #212529;
  margin-bottom: 20px;
  border-bottom: 2px solid #007bff;
  padding-bottom: 8px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.analysis-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-label {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.item-value {
  font-size: 18px;
  font-weight: 600;
  color: #212529;
}

.analysis-details {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

/* 趋势样式 */
.trend-rising {
  color: #dc3545;
}

.trend-falling {
  color: #007bff;
}

.trend-stable {
  color: #28a745;
}

.trend-fluctuating {
  color: #ffc107;
}

/* 空气质量样式 */
.air-excellent {
  color: #28a745;
}

.air-good {
  color: #20c997;
}

.air-light {
  color: #ffc107;
}

.air-moderate {
  color: #fd7e14;
}

.air-heavy {
  color: #dc3545;
}

.air-severe {
  color: #6f42c1;
}

/* 综合评估样式 */
.comprehensive-assessment {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comfort-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.score-label {
  font-size: 18px;
  font-weight: 600;
  color: #495057;
}

.score-value {
  font-size: 32px;
  font-weight: 700;
}

.score-excellent {
  color: #28a745;
}

.score-good {
  color: #20c997;
}

.score-normal {
  color: #ffc107;
}

.score-poor {
  color: #dc3545;
}

.assessment-text {
  padding: 16px;
  background: #e3f2fd;
  border-radius: 4px;
  border-left: 4px solid #2196f3;
}

.recommendations h4 {
  margin-bottom: 12px;
  color: #495057;
}

.recommendations ul {
  padding-left: 20px;
}

.recommendations li {
  margin-bottom: 8px;
  color: #6c757d;
}

/* 统计信息样式 */
.statistics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-label {
  font-weight: 500;
  color: #6c757d;
}

.stat-value {
  font-weight: 600;
  color: #212529;
}

/* 状态样式 */
.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #6c757d;
}

.empty-icon, .error-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text, .loading-text, .error-text {
  font-size: 18px;
  margin-bottom: 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: #0056b3;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-panel {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
  
  .comfort-score {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .statistics {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>
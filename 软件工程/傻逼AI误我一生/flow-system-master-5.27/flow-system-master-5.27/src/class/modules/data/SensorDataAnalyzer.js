const UnifiedStorage = require('../../services/storage/UnifiedStorage');

class SensorDataAnalyzer {
  constructor(apiRegistry = null, deviceStorageManager = null, groupAPIManager = null) {
    this.apiRegistry = apiRegistry;
    this.deviceStorageManager = deviceStorageManager;
    this.groupAPIManager = groupAPIManager; // 新增：分组API管理器
    this.storage = new UnifiedStorage();

    // 传感器类型定义（根据传感器说明.md）
    this.sensorTypes = {
      'mi_temp_hum_sensor': {
        name: '小米温湿度计',
        properties: ['temperature', 'humidity', 'time']
      },
      'mi_air_sensor': {
        name: '青萍空气质量检测仪',
        properties: ['pm25', 'temperature', 'humidity', 'time']
      }
    };

    // 空气质量评级标准（中国标准）
    this.airQualityLevels = [
      { max: 35, level: '优', description: '空气质量令人满意，基本无空气污染' },
      { max: 75, level: '良', description: '空气质量可接受，但某些污染物可能对极少数异常敏感人群健康有较弱影响' },
      { max: 115, level: '轻度污染', description: '易感人群症状有轻度加剧，健康人群出现刺激症状' },
      { max: 150, level: '中度污染', description: '进一步加剧易感人群症状，可能对健康人群心脏、呼吸系统有影响' },
      { max: 250, level: '重度污染', description: '心脏病和肺病患者症状显著加剧，运动耐受力降低，健康人群普遍出现症状' },
      { max: Infinity, level: '严重污染', description: '健康人群运动耐受力降低，有明显强烈症状，提前出现某些疾病' }
    ];

    // 舒适度评级标准
    this.comfortLevels = {
      temperature: {
        optimal: { min: 20, max: 26 },
        good: { min: 18, max: 28 },
        fair: { min: 16, max: 30 }
      },
      humidity: {
        optimal: { min: 40, max: 60 },
        good: { min: 30, max: 70 },
        fair: { min: 20, max: 80 }
      },
      pm25: {
        optimal: { max: 35 },
        good: { max: 75 },
        fair: { max: 115 }
      }
    };
  }

  // 设置依赖服务
  setServices(apiRegistry, deviceStorageManager, groupAPIManager = null) {
    this.apiRegistry = apiRegistry;
    this.deviceStorageManager = deviceStorageManager;
    this.groupAPIManager = groupAPIManager;
  }

  // 分析指定分组的传感器数据
  async analyzeGroupSensorData(groupId) {
    try {
      if (!this.deviceStorageManager) {
        return { success: false, message: '设备存储管理器未设置' };
      }

      // 获取分组中的设备
      const groupDevices = this.deviceStorageManager.getDevicesByGroup(groupId);

      // 筛选出传感器设备
      const sensorDevices = groupDevices.filter(device =>
        this.isSensorDevice(device.type)
      );

      if (sensorDevices.length === 0) {
        return {
          success: true,
          message: '该分组中没有传感器设备',
          data: this.getEmptyAnalysisResult()
        };
      }

      // 获取每个传感器的24小时数据
      const sensorDataPromises = sensorDevices.map(device =>
        this.getSensor24HourData(device.did)
      );

      const sensorDataResults = await Promise.all(sensorDataPromises);

      // 合并所有传感器数据
      const allSensorData = this.mergeSensorData(sensorDataResults, sensorDevices);

      // 进行数据分析
      const analysisResult = this.performDataAnalysis(allSensorData);

      return {
        success: true,
        message: '数据分析完成',
        data: {
          ...analysisResult,
          groupId: groupId,
          sensorCount: sensorDevices.length,
          deviceCount: sensorDevices.length,
          dataPoints: allSensorData.length,
          sampleCount: allSensorData.length,
          timeRange: this.getTimeRange(allSensorData),
          analysisTime: new Date().toISOString(),
          analyzedAt: new Date().toISOString(),
          // 为了兼容环境报告页面的格式，添加这些字段
          overallScore: analysisResult.comfort ? analysisResult.comfort.score / 10 : null,
          overallAssessment: this.getOverallAssessment(analysisResult),
          recommendations: this.generateRecommendations(analysisResult)
        }
      };
    } catch (error) {
      console.error('Failed to analyze group sensor data:', error);
      return { success: false, message: '数据分析失败：' + error.message };
    }
  }

  // 获取单个传感器的24小时数据
  async getSensor24HourData(deviceId) {
    try {
      // 优先从GroupAPIManager获取历史数据
      if (this.groupAPIManager) {
        const historyData = this.groupAPIManager.getSensorHistory(deviceId, 24);
        if (historyData && historyData.length > 0) {
          console.log(`[SENSOR_DATA] Retrieved ${historyData.length} history points from GroupAPIManager for device ${deviceId}`);

          // 转换数据格式以确保兼容性
          const formattedData = historyData.map(point => ({
            time: point.timestamp || point.time,
            timestamp: point.timestamp || point.time,
            deviceId: deviceId,
            deviceName: point.deviceName || deviceId,
            temperature: point.temperature,
            humidity: point.humidity,
            pm25: point.pm25,
            source: point.source || 'history'
          }));

          return formattedData;
        }
      }

      // 如果GroupAPIManager没有数据，尝试调用API
      if (this.apiRegistry) {
        console.log(`[SENSOR_DATA] Attempting to fetch data from API for device ${deviceId}`);
        const response = await this.apiRegistry.callAPIGet('getSensorData', {
          deviceId: deviceId,
          hours: 24
        });

        if (response && response.code === 200 && response.data) {
          console.log(`[SENSOR_DATA] Retrieved ${response.data.length} data points from API for device ${deviceId}`);
          return response.data;
        }
      }

      // 最后尝试从本地存储获取
      console.warn(`[SENSOR_DATA] Failed to get historical data for device ${deviceId}, trying local data`);
      return this.getLocalSensorData(deviceId);
    } catch (error) {
      console.error(`[SENSOR_DATA] Failed to get historical data for device ${deviceId}:`, error);
      return this.getLocalSensorData(deviceId);
    }
  }

  // 从本地存储获取传感器数据
  getLocalSensorData(deviceId) {
    try {
      // 首先尝试从传感器历史获取
      const sensorHistory = this.storage.getSensorHistory(deviceId, 'all');
      if (sensorHistory && sensorHistory.length > 0) {
        console.log(`[SENSOR_DATA] Retrieved ${sensorHistory.length} points from sensor history for device ${deviceId}`);

        // 过滤最近24小时的数据
        const now = new Date();
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        const recentData = sensorHistory.filter(data => {
          const dataTime = new Date(data.time || data.timestamp);
          return dataTime >= yesterday;
        });

        console.log(`[SENSOR_DATA] Filtered to ${recentData.length} recent data points for device ${deviceId}`);
        return recentData;
      }

      // 如果没有传感器历史，尝试从设备本身获取历史数据
      const device = this.storage.getDevice(deviceId);
      if (device && device.data && Array.isArray(device.data)) {
        console.log(`[SENSOR_DATA] Retrieved history data from device object for device ${deviceId}`);
        return device.data;
      }

      // 如果设备有当前状态且是传感器，生成单个数据点
      if (device && this.isSensorDevice(device.type)) {
        console.log(`[SENSOR_DATA] Generating current state data point for sensor device ${deviceId}`);
        const currentData = {
          time: new Date().toISOString(),
          timestamp: new Date().toISOString(),
          deviceId: device.did,
          deviceName: device.name,
          source: 'current_status'
        };

        // 根据设备状态添加传感器数据
        if (device.status) {
          if (device.status.temperature !== undefined) {
            currentData.temperature = parseFloat(device.status.temperature);
          }
          if (device.status.humidity !== undefined) {
            currentData.humidity = parseFloat(device.status.humidity);
          }
          if (device.status.pm25 !== undefined) {
            currentData.pm25 = parseFloat(device.status.pm25);
          }
        }

        return [currentData];
      }

      console.warn(`[SENSOR_DATA] No sensor data found for device ${deviceId}`);
      return [];
    } catch (error) {
      console.error(`[SENSOR_DATA] Error getting local sensor data for device ${deviceId}:`, error);
      return [];
    }
  }

  // 合并多个传感器的数据
  mergeSensorData(sensorDataResults, sensorDevices) {
    const mergedData = [];

    sensorDataResults.forEach((data, index) => {
      const device = sensorDevices[index];
      if (data && Array.isArray(data)) {
        data.forEach(dataPoint => {
          mergedData.push({
            ...dataPoint,
            deviceId: device.did,
            deviceName: device.name,
            deviceType: device.type,
            sensorType: this.sensorTypes[device.type]
          });
        });
      }
    });

    // 按时间排序
    return mergedData.sort((a, b) => {
      const timeA = new Date(a.time || a.timestamp);
      const timeB = new Date(b.time || b.timestamp);
      return timeA - timeB;
    });
  }

  // 执行数据分析
  performDataAnalysis(sensorData) {
    if (!sensorData || sensorData.length === 0) {
      return this.getEmptyAnalysisResult();
    }

    const analysis = {
      temperature: this.analyzeTemperature(sensorData),
      humidity: this.analyzeHumidity(sensorData),
      pm25: this.analyzePM25(sensorData),
      airQuality: null,
      comfort: null
    };

    // 计算空气质量评级
    analysis.airQuality = this.calculateAirQuality(analysis.pm25);

    // 计算综合舒适度
    analysis.comfort = this.calculateComfort(analysis);

    return analysis;
  }

  // 分析温度数据
  analyzeTemperature(sensorData) {
    const temperatureData = sensorData
      .filter(d => d.temperature !== undefined && d.temperature !== null)
      .map(d => parseFloat(d.temperature));

    if (temperatureData.length === 0) {
      return { avg: null, max: null, min: null, trend: 'stable', dataCount: 0 };
    }

    const avg = temperatureData.reduce((sum, temp) => sum + temp, 0) / temperatureData.length;
    const max = Math.max(...temperatureData);
    const min = Math.min(...temperatureData);
    const trend = this.calculateTrend(temperatureData);

    return {
      avg: Number(avg.toFixed(1)),
      max: Number(max.toFixed(1)),
      min: Number(min.toFixed(1)),
      trend: trend,
      dataCount: temperatureData.length,
      unit: '°C'
    };
  }

  // 分析湿度数据
  analyzeHumidity(sensorData) {
    const humidityData = sensorData
      .filter(d => d.humidity !== undefined && d.humidity !== null)
      .map(d => parseFloat(d.humidity));

    if (humidityData.length === 0) {
      return { avg: null, max: null, min: null, trend: 'stable', dataCount: 0 };
    }

    const avg = humidityData.reduce((sum, hum) => sum + hum, 0) / humidityData.length;
    const max = Math.max(...humidityData);
    const min = Math.min(...humidityData);
    const trend = this.calculateTrend(humidityData);

    return {
      avg: Number(avg.toFixed(1)),
      max: Number(max.toFixed(1)),
      min: Number(min.toFixed(1)),
      trend: trend,
      dataCount: humidityData.length,
      unit: '%'
    };
  }

  // 分析PM2.5数据
  analyzePM25(sensorData) {
    const pm25Data = sensorData
      .filter(d => d.pm25 !== undefined && d.pm25 !== null)
      .map(d => parseFloat(d.pm25));

    if (pm25Data.length === 0) {
      return { avg: null, max: null, min: null, dataCount: 0 };
    }

    const avg = pm25Data.reduce((sum, pm) => sum + pm, 0) / pm25Data.length;
    const max = Math.max(...pm25Data);
    const min = Math.min(...pm25Data);

    return {
      avg: Number(avg.toFixed(1)),
      max: Number(max.toFixed(1)),
      min: Number(min.toFixed(1)),
      dataCount: pm25Data.length,
      unit: 'μg/m³'
    };
  }

  // 计算趋势
  calculateTrend(dataArray) {
    if (dataArray.length < 2) return 'stable';

    const firstHalf = dataArray.slice(0, Math.floor(dataArray.length / 2));
    const secondHalf = dataArray.slice(Math.floor(dataArray.length / 2));

    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;

    const diff = secondAvg - firstAvg;
    const threshold = Math.abs(firstAvg) * 0.05; // 5%的变化阈值

    if (Math.abs(diff) < threshold) return 'stable';
    return diff > 0 ? 'rising' : 'falling';
  }

  // 计算空气质量评级
  calculateAirQuality(pm25Analysis) {
    if (!pm25Analysis || pm25Analysis.avg === null) {
      return { level: '未知', description: '无PM2.5数据', color: '#999999' };
    }

    const avgPM25 = pm25Analysis.avg;

    for (const level of this.airQualityLevels) {
      if (avgPM25 <= level.max) {
        return {
          level: level.level,
          description: level.description,
          pm25Value: avgPM25,
          color: this.getAirQualityColor(level.level)
        };
      }
    }

    return { level: '严重污染', description: '严重超标', color: '#8B0000' };
  }

  // 获取空气质量颜色
  getAirQualityColor(level) {
    const colors = {
      '优': '#00E400',
      '良': '#FFFF00',
      '轻度污染': '#FF7E00',
      '中度污染': '#FF0000',
      '重度污染': '#8F3F97',
      '严重污染': '#8B0000'
    };
    return colors[level] || '#999999';
  }

  // 计算综合舒适度
  calculateComfort(analysis) {
    let scores = [];
    let factors = [];

    // 温度舒适度评分
    if (analysis.temperature && analysis.temperature.avg !== null) {
      const tempScore = this.getComfortScore('temperature', analysis.temperature.avg);
      scores.push(tempScore);
      factors.push({ type: 'temperature', score: tempScore, value: analysis.temperature.avg });
    }

    // 湿度舒适度评分
    if (analysis.humidity && analysis.humidity.avg !== null) {
      const humScore = this.getComfortScore('humidity', analysis.humidity.avg);
      scores.push(humScore);
      factors.push({ type: 'humidity', score: humScore, value: analysis.humidity.avg });
    }

    // PM2.5舒适度评分
    if (analysis.pm25 && analysis.pm25.avg !== null) {
      const pm25Score = this.getComfortScore('pm25', analysis.pm25.avg);
      scores.push(pm25Score);
      factors.push({ type: 'pm25', score: pm25Score, value: analysis.pm25.avg });
    }

    if (scores.length === 0) {
      return { level: '未知', score: 0, description: '数据不足', factors: [] };
    }

    const avgScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;

    return {
      level: this.getComfortLevel(avgScore),
      score: Number(avgScore.toFixed(1)),
      description: this.getComfortDescription(avgScore),
      factors: factors,
      color: this.getComfortColor(avgScore)
    };
  }

  // 获取单项舒适度评分
  getComfortScore(type, value) {
    const standards = this.comfortLevels[type];

    if (type === 'pm25') {
      if (value <= standards.optimal.max) return 100;
      if (value <= standards.good.max) return 80;
      if (value <= standards.fair.max) return 60;
      return Math.max(20, 100 - (value - standards.fair.max) / 2);
    } else {
      if (value >= standards.optimal.min && value <= standards.optimal.max) return 100;
      if (value >= standards.good.min && value <= standards.good.max) return 80;
      if (value >= standards.fair.min && value <= standards.fair.max) return 60;
      return 40;
    }
  }

  // 获取舒适度等级
  getComfortLevel(score) {
    if (score >= 90) return '非常舒适';
    if (score >= 80) return '舒适';
    if (score >= 70) return '较舒适';
    if (score >= 60) return '一般';
    if (score >= 40) return '不太舒适';
    return '不舒适';
  }

  // 获取舒适度描述
  getComfortDescription(score) {
    if (score >= 90) return '环境条件优异，非常适宜';
    if (score >= 80) return '环境条件良好，比较适宜';
    if (score >= 70) return '环境条件尚可，基本适宜';
    if (score >= 60) return '环境条件一般，可以接受';
    if (score >= 40) return '环境条件偏差，建议改善';
    return '环境条件较差，需要改善';
  }

  // 获取舒适度颜色
  getComfortColor(score) {
    if (score >= 90) return '#00E400';
    if (score >= 80) return '#7ED321';
    if (score >= 70) return '#FFFF00';
    if (score >= 60) return '#FF7E00';
    if (score >= 40) return '#FF0000';
    return '#8B0000';
  }

  // 获取时间范围
  getTimeRange(sensorData) {
    if (!sensorData || sensorData.length === 0) {
      return { start: null, end: null };
    }

    const times = sensorData.map(d => new Date(d.time || d.timestamp)).filter(t => !isNaN(t));

    if (times.length === 0) {
      return { start: null, end: null };
    }

    return {
      start: new Date(Math.min(...times)).toISOString(),
      end: new Date(Math.max(...times)).toISOString()
    };
  }

  // 检查是否为传感器设备
  isSensorDevice(deviceType) {
    // 支持历史数据类型的传感器设备
    return this.sensorTypes.hasOwnProperty(deviceType) || deviceType === 'history';
  }

  // 获取空的分析结果
  getEmptyAnalysisResult() {
    return {
      temperature: { avg: null, max: null, min: null, trend: 'stable', dataCount: 0 },
      humidity: { avg: null, max: null, min: null, trend: 'stable', dataCount: 0 },
      pm25: { avg: null, max: null, min: null, dataCount: 0 },
      airQuality: { level: '未知', description: '无数据', color: '#999999' },
      comfort: { level: '未知', score: 0, description: '数据不足', factors: [] }
    };
  }

  // 获取支持的传感器类型
  getSupportedSensorTypes() {
    return this.sensorTypes;
  }

  // 分析多个分组的数据（用于对比）
  async analyzeMultipleGroups(groupIds) {
    const results = [];

    for (const groupId of groupIds) {
      const result = await this.analyzeGroupSensorData(groupId);
      results.push({
        groupId: groupId,
        ...result
      });
    }

    return {
      success: true,
      message: '多分组数据分析完成',
      data: results,
      analyzedAt: new Date().toISOString()
    };
  }

  // 生成整体评估
  getOverallAssessment(analysisResult) {
    const comfort = analysisResult.comfort;
    if (!comfort || comfort.score === 0) {
      return '数据不足，无法进行综合评估';
    }

    const score = comfort.score;
    if (score >= 90) {
      return '环境状况极佳！各项指标都达到了优秀水平，适宜长时间居住和工作。';
    } else if (score >= 80) {
      return '环境状况良好，大部分指标表现不错，整体舒适度较高。';
    } else if (score >= 70) {
      return '环境状况尚可，某些指标需要关注，建议适当调整。';
    } else if (score >= 60) {
      return '环境状况一般，存在一些不适宜的因素，建议改善。';
    } else {
      return '环境状况较差，多项指标不理想，建议及时采取改善措施。';
    }
  }

  // 生成改善建议
  generateRecommendations(analysisResult) {
    const recommendations = [];

    // 温度建议
    if (analysisResult.temperature && analysisResult.temperature.avg !== null) {
      const temp = analysisResult.temperature.avg;
      if (temp < 18) {
        recommendations.push('温度偏低，建议适当调高室内温度或增加保暖措施');
      } else if (temp > 28) {
        recommendations.push('温度偏高，建议开启空调或增加通风降温');
      }
    }

    // 湿度建议
    if (analysisResult.humidity && analysisResult.humidity.avg !== null) {
      const humidity = analysisResult.humidity.avg;
      if (humidity < 30) {
        recommendations.push('湿度过低，建议使用加湿器或放置水盆增加湿度');
      } else if (humidity > 70) {
        recommendations.push('湿度过高，建议开启除湿器或增加通风');
      }
    }

    // PM2.5建议
    if (analysisResult.pm25 && analysisResult.pm25.avg !== null) {
      const pm25 = analysisResult.pm25.avg;
      if (pm25 > 115) {
        recommendations.push('空气质量较差，建议减少户外活动，开启空气净化器');
      } else if (pm25 > 75) {
        recommendations.push('空气质量一般，建议开启空气净化器改善室内空气');
      }
    }

    // 空气质量建议
    if (analysisResult.airQuality && analysisResult.airQuality.level) {
      const level = analysisResult.airQuality.level;
      if (level === '轻度污染' || level === '中度污染') {
        recommendations.push('建议关闭门窗，使用空气净化设备');
      } else if (level === '重度污染' || level === '严重污染') {
        recommendations.push('空气污染严重，建议避免户外活动，密闭室内环境并使用高效空气净化器');
      }
    }

    return recommendations.length > 0 ? recommendations : ['当前环境状况良好，请保持'];
  }

  // 导出分析结果
  exportAnalysisResult(analysisResult) {
    return {
      ...analysisResult,
      exportedAt: new Date().toISOString(),
      analyzerVersion: '1.0.0'
    };
  }
}

module.exports = SensorDataAnalyzer;

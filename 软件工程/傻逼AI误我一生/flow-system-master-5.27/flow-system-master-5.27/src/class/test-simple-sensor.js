console.log('🔍 测试传感器数据分析数据结构...');

try {
  // 模拟SensorDataAnalyzer的简化版本
  class SimpleSensorDataAnalyzer {
    constructor() {
      this.groupAPIManager = {
        sensorHistoryData: new Map(),
        getSensorHistory: (deviceId, hours) => {
          return this.groupAPIManager.sensorHistoryData.get(deviceId) || [];
        }
      };
      this.deviceStorageManager = {
        devices: new Map(),
        getDevicesByGroup: (groupId) => {
          return Array.from(this.deviceStorageManager.devices.values()).filter(d => d.groupId === groupId);
        },
        getAllDevices: () => {
          return Array.from(this.deviceStorageManager.devices.values());
        }
      };
    }

    // 模拟传感器设备
    setupMockData(groupId) {
      // 添加温湿度传感器
      const tempSensor = {
        did: 'temp_sensor_001',
        name: '小米温湿度计',
        type: 'history',
        groupId: groupId,
        status: { temperature: 23.5, humidity: 45 }
      };

      // 添加空气质量传感器
      const airSensor = {
        did: 'air_sensor_001',
        name: '小米空气质量检测仪',
        type: 'history',
        groupId: groupId,
        status: { temperature: 24.1, humidity: 50, pm25: 35 }
      };

      this.deviceStorageManager.devices.set(tempSensor.did, tempSensor);
      this.deviceStorageManager.devices.set(airSensor.did, airSensor);

      // 生成历史数据
      const now = new Date();
      const tempHistory = [];
      const airHistory = [];

      for (let i = 23; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);

        tempHistory.push({
          timestamp: timestamp.toISOString(),
          time: timestamp.toISOString(),
          temperature: 20 + Math.random() * 8, // 20-28°C
          humidity: 35 + Math.random() * 30 // 35-65%
        });

        airHistory.push({
          timestamp: timestamp.toISOString(),
          time: timestamp.toISOString(),
          temperature: 22 + Math.random() * 6, // 22-28°C
          humidity: 40 + Math.random() * 25, // 40-65%
          pm25: 20 + Math.random() * 50 // 20-70 μg/m³
        });
      }

      this.groupAPIManager.sensorHistoryData.set(tempSensor.did, tempHistory);
      this.groupAPIManager.sensorHistoryData.set(airSensor.did, airHistory);

      console.log(`✅ 模拟数据设置完成:`);
      console.log(`   温湿度传感器: ${tempHistory.length} 个数据点`);
      console.log(`   空气质量传感器: ${airHistory.length} 个数据点`);
    }

    // 分析分组传感器数据
    async analyzeGroupSensorData(groupId) {
      try {
        console.log(`\n🔍 开始分析分组 ${groupId} 的传感器数据...`);

        // 获取分组内的传感器设备
        const groupDevices = this.deviceStorageManager.getDevicesByGroup(groupId);
        const sensorDevices = groupDevices.filter(device =>
          device.type === 'mi_temp_hum_sensor' ||
          device.type === 'mi_air_sensor' ||
          device.type === 'history'
        );

        console.log(`找到 ${sensorDevices.length} 个传感器设备`);

        if (sensorDevices.length === 0) {
          return {
            success: false,
            message: '该分组中没有传感器设备',
            data: null
          };
        }

        // 收集所有传感器的历史数据
        const allSensorData = [];

        for (const device of sensorDevices) {
          const history = this.groupAPIManager.getSensorHistory(device.did, 24);
          console.log(`设备 ${device.name}: ${history.length} 个历史数据点`);
          allSensorData.push(...history);
        }

        console.log(`总计收集到 ${allSensorData.length} 个数据点`);

        if (allSensorData.length === 0) {
          return {
            success: false,
            message: '没有可分析的传感器数据',
            data: null
          };
        }

        // 分析数据
        const result = this.calculateMetrics(allSensorData);
        result.sensorCount = sensorDevices.length;
        result.deviceCount = sensorDevices.length;
        result.sampleCount = allSensorData.length;
        result.analysisTime = new Date().toISOString();

        console.log('\n📊 分析结果数据结构:');
        console.log(JSON.stringify(result, null, 2));

        return {
          success: true,
          message: '传感器数据分析完成',
          data: result
        };

      } catch (error) {
        console.error('传感器数据分析失败:', error);
        return {
          success: false,
          message: '传感器数据分析失败: ' + error.message,
          data: null
        };
      }
    }

    // 计算指标
    calculateMetrics(sensorData) {
      const temperatures = sensorData.filter(d => d.temperature !== undefined).map(d => d.temperature);
      const humidities = sensorData.filter(d => d.humidity !== undefined).map(d => d.humidity);
      const pm25s = sensorData.filter(d => d.pm25 !== undefined).map(d => d.pm25);

      const result = {};

      // 温度分析
      if (temperatures.length > 0) {
        result.temperature = {
          avg: this.calculateAverage(temperatures),
          max: Math.max(...temperatures),
          min: Math.min(...temperatures),
          trend: this.calculateTrend(temperatures)
        };
      }

      // 湿度分析
      if (humidities.length > 0) {
        result.humidity = {
          avg: this.calculateAverage(humidities),
          max: Math.max(...humidities),
          min: Math.min(...humidities),
          trend: this.calculateTrend(humidities)
        };
      }

      // PM2.5分析
      if (pm25s.length > 0) {
        result.pm25 = {
          avg: this.calculateAverage(pm25s),
          max: Math.max(...pm25s),
          min: Math.min(...pm25s),
          trend: this.calculateTrend(pm25s)
        };
      }

      // 空气质量评估
      if (result.pm25) {
        result.airQuality = this.getAirQualityAssessment(result.pm25.avg);
      }

      // 舒适度评分
      result.comfort = this.calculateComfortScore(result.temperature?.avg, result.humidity?.avg);

      // 总体评估
      result.overallAssessment = this.getOverallAssessment(result);

      // 改善建议
      result.recommendations = this.generateRecommendations(result);

      return result;
    }

    calculateAverage(values) {
      return values.reduce((sum, val) => sum + val, 0) / values.length;
    }

    calculateTrend(values) {
      if (values.length < 2) return 'stable';

      const firstHalf = values.slice(0, Math.floor(values.length / 2));
      const secondHalf = values.slice(Math.floor(values.length / 2));

      const firstAvg = this.calculateAverage(firstHalf);
      const secondAvg = this.calculateAverage(secondHalf);

      const diff = secondAvg - firstAvg;
      const threshold = 0.1;

      if (diff > threshold) return 'rising';
      if (diff < -threshold) return 'falling';
      return 'stable';
    }

    getAirQualityAssessment(pm25) {
      if (pm25 <= 35) {
        return { level: '优', description: '空气质量很好' };
      } else if (pm25 <= 75) {
        return { level: '良', description: '空气质量良好' };
      } else if (pm25 <= 115) {
        return { level: '轻度污染', description: '轻度污染，敏感人群注意' };
      } else {
        return { level: '污染', description: '空气质量较差' };
      }
    }

    calculateComfortScore(temperature, humidity) {
      let score = 100;

      // 温度评分（理想温度 20-26°C）
      if (temperature !== undefined) {
        if (temperature < 18 || temperature > 28) score -= 30;
        else if (temperature < 20 || temperature > 26) score -= 15;
      }

      // 湿度评分（理想湿度 40-60%）
      if (humidity !== undefined) {
        if (humidity < 30 || humidity > 70) score -= 20;
        else if (humidity < 40 || humidity > 60) score -= 10;
      }

      score = Math.max(0, score);

      let level = '差';
      if (score >= 80) level = '优秀';
      else if (score >= 60) level = '良好';
      else if (score >= 40) level = '一般';

      return { score, level };
    }

    getOverallAssessment(result) {
      const assessments = [];

      if (result.temperature) {
        const temp = result.temperature.avg;
        if (temp >= 20 && temp <= 26) {
          assessments.push('温度适宜');
        } else {
          assessments.push('温度偏离舒适范围');
        }
      }

      if (result.humidity) {
        const hum = result.humidity.avg;
        if (hum >= 40 && hum <= 60) {
          assessments.push('湿度适宜');
        } else {
          assessments.push('湿度需要调节');
        }
      }

      if (result.airQuality) {
        assessments.push(`空气质量${result.airQuality.level}`);
      }

      return assessments.join('，');
    }

    generateRecommendations(result) {
      const recommendations = [];

      if (result.temperature) {
        const temp = result.temperature.avg;
        if (temp < 20) {
          recommendations.push('建议适当提高室内温度');
        } else if (temp > 26) {
          recommendations.push('建议适当降低室内温度');
        }
      }

      if (result.humidity) {
        const hum = result.humidity.avg;
        if (hum < 40) {
          recommendations.push('建议使用加湿器增加室内湿度');
        } else if (hum > 60) {
          recommendations.push('建议使用除湿器降低室内湿度');
        }
      }

      if (result.pm25 && result.pm25.avg > 35) {
        recommendations.push('建议使用空气净化器改善空气质量');
      }

      if (recommendations.length === 0) {
        recommendations.push('当前环境状况良好，请保持');
      }

      return recommendations;
    }
  }

  // 创建分析器并测试
  const analyzer = new SimpleSensorDataAnalyzer();
  const groupId = 'test_group_001';

  // 设置模拟数据
  analyzer.setupMockData(groupId);

  // 执行分析
  analyzer.analyzeGroupSensorData(groupId).then(result => {
    console.log('\n✅ 分析完成！');
    console.log('🎯 检查数据结构是否符合页面期望:');

    if (result.success && result.data) {
      const data = result.data;

      console.log('\n📊 数据字段检查:');
      console.log(`temperature.avg: ${data.temperature?.avg} (页面期望: number)`);
      console.log(`humidity.avg: ${data.humidity?.avg} (页面期望: number)`);
      console.log(`pm25.avg: ${data.pm25?.avg} (页面期望: number)`);
      console.log(`comfort.score: ${data.comfort?.score} (页面期望: number)`);
      console.log(`deviceCount: ${data.deviceCount} (页面期望: number)`);
      console.log(`sampleCount: ${data.sampleCount} (页面期望: number)`);
      console.log(`recommendations: ${Array.isArray(data.recommendations)} (页面期望: array)`);

      // 验证页面期望的数据格式
      const validations = [];

      if (data.temperature?.avg !== undefined && typeof data.temperature.avg === 'number') {
        validations.push('✅ temperature.avg 格式正确');
      } else {
        validations.push('❌ temperature.avg 格式错误或缺失');
      }

      if (data.humidity?.avg !== undefined && typeof data.humidity.avg === 'number') {
        validations.push('✅ humidity.avg 格式正确');
      } else {
        validations.push('❌ humidity.avg 格式错误或缺失');
      }

      if (data.comfort?.score !== undefined && typeof data.comfort.score === 'number') {
        validations.push('✅ comfort.score 格式正确');
      } else {
        validations.push('❌ comfort.score 格式错误或缺失');
      }

      if (data.deviceCount !== undefined && typeof data.deviceCount === 'number') {
        validations.push('✅ deviceCount 格式正确');
      } else {
        validations.push('❌ deviceCount 格式错误或缺失');
      }

      if (data.sampleCount !== undefined && typeof data.sampleCount === 'number') {
        validations.push('✅ sampleCount 格式正确');
      } else {
        validations.push('❌ sampleCount 格式错误或缺失');
      }

      console.log('\n🔍 页面兼容性验证:');
      validations.forEach(validation => console.log(validation));

    } else {
      console.log('❌ 分析失败:', result.message);
    }
  });

} catch (error) {
  console.error('❌ 测试失败:', error);
}

# 设备管理系统 API 使用说明

## 概述

本文档为前端开发者提供设备管理系统的完整API使用说明，包括所有可用的IPC接口、参数说明和返回值格式。

## 前置条件

### 1. 用户登录

在使用设备相关功能前，确保用户已成功登录：

```javascript
// 检查自动登录
const autoLoginResult = await window.electronAPI.invoke('check-auto-login');

// 或者手动登录
const loginResult = await window.electronAPI.invoke('login', {
  userId: 'user123',
  password: 'password',
  rememberMe: true
});

if (loginResult.success) {
  console.log('登录成功，设备控制器已初始化');
}
```

## 设备管理 API

### 1. 获取所有设备

```javascript
const result = await window.electronAPI.invoke('get-all-devices');

// 返回格式
{
  success: true,
  data: [
    {
      did: "device123",
      name: "客厅空调",
      type: "mi_ac",
      brand: "Xiaomi",
      online: true,
      status: {
        power: "ON",
        target_temperature: 26,
        mode: "cool",
        fan_speed: "medium"
      }
    },
    // ... 更多设备
  ]
}
```

### 2. 根据品牌获取设备

```javascript
const result = await window.electronAPI.invoke('get-devices-by-brand', 'Xiaomi');

// 返回格式同上，但只包含指定品牌的设备
```

**支持的品牌**:
- `Xiaomi` - 小米
- `Midea` - 美的

### 3. 获取可控制设备

```javascript
const result = await window.electronAPI.invoke('get-controllable-devices');

// 返回所有非传感器设备（可以被控制的设备）
```

### 4. 获取传感器设备

```javascript
const result = await window.electronAPI.invoke('get-sensor-devices');

// 返回格式
{
  success: true,
  data: [
    {
      did: "sensor123",
      name: "客厅温湿度计",
      type: "mi_temp_humidity_sensor",
      brand: "Xiaomi",
      online: true,
      isSensor: true,
      supportedMetrics: ["temperature", "humidity"],
      status: {
        temperature: 25.5,
        humidity: 55,
        time: "2023-08-20T14:30:00Z"
      }
    }
  ]
}
```

### 5. 获取设备控制选项

```javascript
const result = await window.electronAPI.invoke('get-device-control-options', 'device123');

// 返回格式
{
  success: true,
  data: {
    did: "device123",
    name: "客厅空调",
    type: "mi_ac",
    brand: "Xiaomi",
    online: true,
    controls: [
      {
        property: "power",
        type: "select",
        options: ["ON", "OFF"],
        current: "ON"
      },
      {
        property: "target_temperature",
        type: "number",
        min: 16,
        max: 30,
        step: 0.1,
        current: 26
      },
      {
        property: "fan_speed",
        type: "select",
        options: ["low", "medium", "high", "auto"],
        current: "medium"
      },
      {
        property: "mode",
        type: "select",
        options: ["cool", "heat", "dry", "fan"],
        current: "cool"
      }
    ]
  }
}
```

### 6. 控制设备

```javascript
const result = await window.electronAPI.invoke('control-device', {
  did: 'device123',
  operation: 'power',
  value: 'ON'
});

// 返回格式
{
  success: true,
  message: "设备控制成功"
}

// 错误情况
{
  success: false,
  message: "设备离线，无法执行任何操作"
}
```

**常用控制示例**:

```javascript
// 开关空调
await window.electronAPI.invoke('control-device', {
  did: 'ac001',
  operation: 'power',
  value: 'ON'
});

// 设置空调温度
await window.electronAPI.invoke('control-device', {
  did: 'ac001',
  operation: 'target_temperature',
  value: 24
});

// 设置加湿器湿度
await window.electronAPI.invoke('control-device', {
  did: 'humidifier001',
  operation: 'target_humidity',
  value: 60
});
```

### 7. 刷新设备状态

```javascript
const result = await window.electronAPI.invoke('refresh-devices');

// 返回格式
{
  success: true,
  message: "设备数据加载成功",
  deviceCount: 10
}
```

## 传感器数据 API

### 1. 获取传感器历史数据

```javascript
const result = await window.electronAPI.invoke('get-sensor-history', 'sensor123', 'temperature');

// 返回格式
{
  success: true,
  data: {
    deviceId: "sensor123",
    metricType: "temperature",
    data: [
      { hour: "2023-08-19T15:00:00Z", value: 25.2 },
      { hour: "2023-08-19T16:00:00Z", value: 26.1 },
      // ... 24小时数据
    ],
    statistics: {
      average: 25.5,
      min: 22.0,
      max: 28.5,
      count: 24
    },
    trend: "rising",
    latestValue: 26.1
  }
}
```

**支持的指标类型**:
- `temperature` - 温度 (°C)
- `humidity` - 湿度 (%)
- `pm25` - PM2.5 (μg/m³)

### 2. 获取所有传感器历史数据

```javascript
const result = await window.electronAPI.invoke('get-all-sensor-history');

// 返回格式
{
  success: true,
  data: {
    "sensor123": {
      "temperature": { /* 温度历史数据 */ },
      "humidity": { /* 湿度历史数据 */ }
    },
    "sensor456": {
      "pm25": { /* PM2.5历史数据 */ },
      "temperature": { /* 温度历史数据 */ }
    }
  }
}
```

### 3. 刷新传感器历史数据

```javascript
const result = await window.electronAPI.invoke('refresh-sensor-history');

// 返回格式
{
  success: true,
  message: "刷新完成：8/10 个历史数据更新成功",
  successCount: 8,
  totalCount: 10
}
```

## 环境数据分析 API

### 1. 分析环境数据

```javascript
// 分析所有传感器数据
const result = await window.electronAPI.invoke('analyze-environment-data');

// 分析指定传感器数据
const result = await window.electronAPI.invoke('analyze-environment-data', ['sensor123', 'sensor456']);

// 返回格式
{
  success: true,
  data: {
    temperature: {
      average: 25.5,
      min: 22.0,
      max: 28.5,
      trend: "rising",
      devices: [
        {
          deviceId: "sensor123",
          average: 25.5,
          min: 22.0,
          max: 28.5,
          count: 24,
          trend: "rising"
        }
      ]
    },
    humidity: {
      average: 55.2,
      min: 45,
      max: 65,
      trend: "stable",
      devices: [/* 设备详情 */]
    },
    pm25: {
      average: 35.8,
      min: 25,
      max: 48,
      airQuality: "good",
      devices: [/* 设备详情 */]
    },
    comfort: {
      level: "very_good",
      score: 85,
      factors: [
        {
          factor: "temperature",
          status: "optimal",
          impact: 0
        },
        {
          factor: "humidity",
          status: "acceptable",
          impact: -5
        },
        {
          factor: "air_quality",
          status: "optimal",
          impact: 0
        }
      ]
    }
  }
}
```

**趋势类型**:
- `rising` - 上升
- `falling` - 下降
- `stable` - 稳定

**空气质量等级**:
- `excellent` - 优秀 (PM2.5 ≤ 35)
- `good` - 良好 (PM2.5 ≤ 75)
- `fair` - 中等 (PM2.5 ≤ 115)
- `poor` - 较差 (PM2.5 ≤ 150)
- `very_poor` - 很差 (PM2.5 > 150)

**舒适度等级**:
- `excellent` - 极佳 (≥90分)
- `very_good` - 很好 (≥80分)
- `good` - 良好 (≥70分)
- `fair` - 一般 (≥60分)
- `poor` - 较差 (≥50分)
- `very_poor` - 很差 (<50分)

## 系统管理 API

### 1. 刷新所有数据

```javascript
const result = await window.electronAPI.invoke('refresh-all-data');

// 返回格式
{
  success: true,
  message: "数据刷新完成",
  deviceResult: {
    success: true,
    message: "设备数据加载成功",
    deviceCount: 10
  },
  sensorResult: {
    success: true,
    message: "刷新完成：8/10 个历史数据更新成功",
    successCount: 8,
    totalCount: 10
  }
}
```

### 2. 获取系统状态

```javascript
const result = await window.electronAPI.invoke('get-system-status');

// 返回格式
{
  success: true,
  data: {
    isInitialized: true,
    currentUserId: "user123",
    devices: {
      total: 10,
      online: 8,
      offline: 2,
      sensors: 4,
      controllable: 6,
      byBrand: {
        "Xiaomi": 6,
        "Midea": 4
      }
    },
    data: {
      totalHistoryData: 12,
      deviceCount: 4,
      metricTypes: {
        temperature: 4,
        humidity: 4,
        pm25: 4
      },
      totalDataPoints: 288
    },
    sse: {
      isConnected: true,
      sseConnectionId: "user123",
      reconnectAttempts: 0,
      maxReconnectAttempts: 5
    },
    timestamp: "2023-08-20T14:30:00Z"
  }
}
```

### 3. 重新连接SSE

```javascript
const result = await window.electronAPI.invoke('reconnect-sse');

// 返回格式
{
  success: true,
  message: "SSE连接成功"
}
```

## 错误处理

### 通用错误格式

```javascript
{
  success: false,
  message: "具体的错误描述"
}
```

### 常见错误类型

1. **设备控制错误**:
   ```javascript
   {
     success: false,
     message: "设备离线，无法执行任何操作"
   }
   ```

2. **验证错误**:
   ```javascript
   {
     success: false,
     message: "目标温度必须在16°C到30°C之间"
   }
   ```

3. **网络错误**:
   ```javascript
   {
     success: false,
     message: "服务器无响应"
   }
   ```

4. **认证错误**:
   ```javascript
   {
     success: false,
     message: "用户未登录"
   }
   ```

## 实时数据更新

系统会通过SSE自动接收服务端推送的实时数据，包括：

1. **设备状态变化**: 当设备状态改变时，会自动更新本地缓存
2. **传感器数据更新**: 每小时会接收一次传感器历史数据更新

前端无需手动处理这些更新，数据会自动同步到相应的API调用结果中。

## 最佳实践

### 1. 错误处理

```javascript
try {
  const result = await window.electronAPI.invoke('control-device', controlData);
  if (result.success) {
    // 成功处理
    showSuccessMessage(result.message);
  } else {
    // 错误处理
    showErrorMessage(result.message);
  }
} catch (error) {
  // 异常处理
  showErrorMessage('操作失败，请重试');
  console.error('设备控制异常:', error);
}
```

### 2. 加载状态管理

```javascript
// 显示加载状态
setLoading(true);

try {
  const devices = await window.electronAPI.invoke('get-all-devices');
  updateDeviceList(devices.data);
} finally {
  setLoading(false);
}
```

### 3. 数据缓存

```javascript
// 缓存设备列表，避免频繁请求
let deviceCache = null;
let cacheTime = 0;
const CACHE_DURATION = 30000; // 30秒

async function getDevices() {
  const now = Date.now();
  if (deviceCache && (now - cacheTime) < CACHE_DURATION) {
    return deviceCache;
  }
  
  const result = await window.electronAPI.invoke('get-all-devices');
  if (result.success) {
    deviceCache = result.data;
    cacheTime = now;
  }
  
  return deviceCache;
}
```

### 4. 批量操作

```javascript
// 批量控制多个设备
async function controlMultipleDevices(controlCommands) {
  const results = await Promise.all(
    controlCommands.map(cmd => 
      window.electronAPI.invoke('control-device', cmd)
    )
  );
  
  const successCount = results.filter(r => r.success).length;
  console.log(`成功控制 ${successCount}/${results.length} 个设备`);
}
```

## 完整示例

### 设备控制页面示例

```javascript
// 设备控制组件
export default {
  data() {
    return {
      devices: [],
      loading: false,
      selectedDevice: null
    }
  },
  
  async mounted() {
    await this.loadDevices();
  },
  
  methods: {
    async loadDevices() {
      this.loading = true;
      try {
        const result = await window.electronAPI.invoke('get-controllable-devices');
        if (result.success) {
          this.devices = result.data;
        }
      } catch (error) {
        console.error('加载设备失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async controlDevice(did, operation, value) {
      try {
        const result = await window.electronAPI.invoke('control-device', {
          did,
          operation,
          value
        });
        
        if (result.success) {
          this.$message.success('控制成功');
          // 刷新设备状态
          await this.loadDevices();
        } else {
          this.$message.error(result.message);
        }
      } catch (error) {
        this.$message.error('控制失败，请重试');
      }
    }
  }
}
```

---

*如有疑问，请参考完整的系统实现文档或联系开发团队。* 
# 品牌方授权URL统一管理修改说明

## 修改背景

原本品牌方授权网站的URL在多个地方硬编码：
- `src/renderer/src/views/children/account/index.vue` 中硬编码了 `const baseUrl = 'http://192.168.58.56:3000'`
- `src/class/services/api/AccountAPIRegistry.js` 中也有 `baseURL: 'http://192.168.58.56:3000'`

这样的设计导致URL变化时需要修改多个文件，不利于维护。

## 修改目标

将品牌方授权网站的URL统一依赖于AccountAPIRegistry中的BASE_URL，实现：
- 只需要在一个地方修改URL配置
- 避免URL不一致的问题
- 便于维护和管理

## 修改内容

### 1. AccountAPIRegistry.js - 添加获取baseURL方法

**文件**: `src/class/services/api/AccountAPIRegistry.js`

```javascript
// 获取基础URL
getBaseURL() {
  return this.apiConfig.baseURL;
}
```

### 2. 主进程 - 添加IPC处理

**文件**: `src/main/index.js`

```javascript
// 获取API baseURL
ipcMain.handle('get-api-base-url', async () => {
  try {
    const { accountManager } = require('../class');
    const baseURL = accountManager.apiRegistry.getBaseURL();
    return { success: true, baseURL: baseURL };
  } catch (error) {
    console.error('Getting API base URL failed:', error);
    return { success: false, message: error.message || 'Getting API base URL failed' };
  }
});
```

### 3. 预加载脚本 - 添加API接口

**文件**: `src/preload/index.js`

```javascript
const api = {
  // ... 其他API
  getApiBaseUrl: () => ipcRenderer.invoke('get-api-base-url'),
  // ... 其他API
}
```

### 4. Vue组件 - 修改授权网站打开逻辑

**文件**: `src/renderer/src/views/children/account/index.vue`

**修改前**:
```javascript
// 打开外部授权网站
openAuthorizationWebsite(brand) {
  // 根据品牌构建授权URL
  const baseUrl = 'http://192.168.58.56:3000'; // 硬编码BASE_URL
  const authUrl = `${baseUrl}/auth/auth-page?brand=${brand}`;
  
  // ... 打开逻辑
}
```

**修改后**:
```javascript
// 打开外部授权网站
async openAuthorizationWebsite(brand) {
  try {
    // 从AccountAPIRegistry获取BASE_URL，实现统一管理
    const result = await window.api.getApiBaseUrl();
    
    if (!result.success) {
      console.error('❌ [账号中心] 获取API baseURL失败:', result.message);
      ElMessage.error('获取服务器地址失败，请重试');
      return;
    }

    const baseUrl = result.baseURL;
    const authUrl = `${baseUrl}/auth/auth-page?brand=${brand}`;
    
    console.log(`🌐 [账号中心] 打开 ${brand} 授权网站: ${authUrl}`);
    console.log(`🌐 [账号中心] 使用统一管理的BASE_URL: ${baseUrl}`);
    
    // ... 打开逻辑
  } catch (error) {
    console.error('❌ [账号中心] 打开授权网站异常:', error);
    ElMessage.error('打开授权网站失败，请重试');
  }
}
```

## 修改效果

### 1. 统一管理
- 所有URL配置都依赖于 `AccountAPIRegistry.js` 中的 `baseURL` 配置
- 修改服务器地址时只需修改一处：`src/class/services/api/AccountAPIRegistry.js` 第6行

### 2. 错误处理
- 添加了完整的错误处理机制
- 当获取baseURL失败时会给用户友好的提示

### 3. 日志记录
- 添加了详细的日志记录，便于调试
- 明确显示使用的是统一管理的BASE_URL

## 使用方式

### 修改服务器地址
只需要修改 `src/class/services/api/AccountAPIRegistry.js` 中的配置：

```javascript
this.apiConfig = {
  baseURL: 'http://新的服务器地址:端口', // 只需修改这一行
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
};
```

### 验证修改
1. 启动应用
2. 登录后进入账号中心
3. 点击品牌绑定，查看控制台日志
4. 确认显示的baseURL是统一管理的地址

## 兼容性

- 保持了原有的功能逻辑不变
- 向后兼容，不影响其他功能
- 添加了错误处理，提高了健壮性

## 总结

通过这次修改，我们成功实现了品牌方授权URL的统一管理，提高了代码的可维护性和配置的一致性。现在当服务端IP变化时，只需要修改一个地方即可，大大简化了维护工作。 
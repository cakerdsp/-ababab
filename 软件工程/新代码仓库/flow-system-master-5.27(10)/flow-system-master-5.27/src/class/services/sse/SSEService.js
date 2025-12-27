const EventSource = require('eventsource');

/**
 * SSEService 类负责管理与服务器的Server-Sent Events (SSE)连接。
 * 它处理连接的建立、断开、自动重连以及消息的接收和分发。
 */
class SSEService {
  constructor() {
    this.eventSource = null; // EventSource实例，用于SSE通信
    this.isConnected = false; // 当前连接状态
    this.connectionUrl = 'http://192.168.99.56:3000/events'; // SSE服务器端点URL
    this.sseConnectionId = null; // 用于标识SSE连接的唯一ID，通常是用户ID
    this.messageHandlers = new Map(); // 存储消息处理器，key为消息类型(如'deviceUpdate'), value为回调函数数组
    this.reconnectAttempts = 0; // 当前重连尝试次数
    this.maxReconnectAttempts = 5; // 最大重连次数
    this.reconnectDelay = 3000; // 重连延迟时间（毫秒）
    this.statusReportingIntervalId = null; // 用于存储状态报告定时器的ID
  }

  /**
   * 设置用于建立连接的SSE Connection ID。
   * @param {string} userId - 用户的唯一标识符。
   */
  setSseConnectionId(userId) {
    this.sseConnectionId = userId;
  }

  /**
   * 建立SSE连接。
   * 这是一个异步方法，返回一个Promise。
   * @returns {Promise<{success: boolean, message: string}>} 连接结果。
   */
  connect() {
    return new Promise((resolve, reject) => {
      // 如果已经连接，则直接返回成功
      if (this.isConnected) {
        console.log('[SSE_DEBUG] SSE connection already exists.');
        resolve({ success: true, message: 'SSE connection already exists' });
        return;
      }

      // 必须先设置sseConnectionId才能连接
      if (!this.sseConnectionId) {
        console.error('[SSE_ERROR] SSE Connection ID is not set before connecting.');
        reject(new Error('SSE Connection ID is not set'));
        return;
      }

      try {
        // 将sseConnectionId作为查询参数附加到URL
        const url = `${this.connectionUrl}?sseconid=${this.sseConnectionId}`;
        console.log(`[SSE_DEBUG] Connecting to SSE endpoint: ${url}`);

        this.eventSource = new EventSource(url);

        /**
         * onopen: 当SSE连接成功建立时触发。
         * 这里我们会重置重连计数器，并更新连接状态。
         */
        this.eventSource.onopen = () => {
          console.log('[SSE_SUCCESS] SSE connection established successfully.');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          // this.startStatusReporting(); // 禁用SSE连接状态定时汇报
          resolve({ success: true, message: 'SSE connection successful' });
        };

        /**
         * onmessage: 当从服务器接收到任何消息时触发。
         * 这是处理所有SSE推送的核心位置。
         *
         * [排查点] 如果您在收到第一条连接成功消息后就收不到其他消息，
         * 1. 确认服务器是否真的在推送后续消息。
         * 2. 检查此处的 console.log 是否在设备状态变化时打印了新的event.data。
         *    如果没有打印，说明客户端没有收到消息，问题可能在服务器端或网络。
         *    如果打印了，说明客户端收到了但未正确处理，问题在 handleMessage 或其调用者。
         */
        this.eventSource.onmessage = (event) => {
          console.log("[SSE_RAW_MESSAGE] Received raw SSE data:", event.data);
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('[SSE_ERROR] Failed to parse SSE message JSON. Raw data:', event.data, 'Error:', error);
          }
        };

        /**
         * onerror: 当连接发生错误时触发。
         * 这可能是网络问题、服务器关闭或URL错误等。
         *
         * [排查点] 如果连接在第一次消息后中断，这里应该会打印错误日志，并触发自动重连。
         * 观察这里的日志可以判断连接是否稳定。
         */
        this.eventSource.onerror = (error) => {
          console.error('[SSE_ERROR] SSE connection error:', error);
          this.isConnected = false;

          // 启动自动重连机制
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[SSE_RECONNECT] Attempting to reconnect SSE (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
              this.connect(); // 稍后尝试重连
            }, this.reconnectDelay);
          } else {
            console.error('[SSE_FAIL] SSE reconnection failed after maximum attempts.');
            this.disconnect(); // 达到最大次数后停止重连并清理
          }
        };

      } catch (error) {
        console.error('[SSE_FATAL] Failed to create SSE connection object:', error);
        reject(error);
      }
    });
  }

  /**
   * 主动断开SSE连接并清理资源。
   */
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close(); // 关闭连接
      this.eventSource = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = 0; // 重置重连计数
    this.stopStatusReporting(); // 连接断开时，停止报告状态
    console.log('[SSE_INFO] SSE connection disconnected.');
  }

  /**
   * 处理解析后的SSE消息，并将其分发给对应的处理器。
   * @param {object} data - 从服务器收到的JSON对象。
   *
   * [排查点] 这是消息处理的核心分发逻辑。
   * 1. 检查收到的`data`对象的结构是否符合预期。
   * 2. 确认`data.did`是否存在于设备更新消息中。如果不存在，它会被当作通用'message'处理。
   * 3. 观察`notifyHandlers`前的日志，可以确认消息被分发到了哪个类型(`'deviceUpdate'` 或 `'message'`)。
   */
  handleMessage(data) {
    try {
      console.log('[SSE_HANDLE_MESSAGE] Handling parsed SSE message:', data);

      // 优先处理传感器历史数据更新 (type: 'history')
      if (data.type === 'history' && data.did && data.metric_type && Array.isArray(data.data) && data.data.length > 0) {
        console.log(`[SSE_DISPATCH] Handling 'sensorHistoryUpdate' for DID: ${data.did}, Metric: ${data.metric_type}, Data points: ${data.data.length}`);

        // 使用第一个数据点更新设备当前状态
        const firstDataPoint = data.data[0];
        const statusUpdatePayload = {
          did: data.did,
          [data.metric_type]: firstDataPoint.value,
          lastUpdated: data.timestamp,
          timestamp: data.timestamp
        };

        console.log(`[SSE_DISPATCH] Status update payload:`, statusUpdatePayload);

        // 分发设备状态更新
        this.notifyHandlers('deviceUpdate', statusUpdatePayload);

        // 分发传感器历史数据更新（包含完整的历史数据）
        const historyUpdatePayload = {
          did: data.did,
          metric_type: data.metric_type,
          historyData: data.data, // 完整的历史数据数组
          timestamp: data.timestamp,
          type: 'history'
        };

        console.log(`[SSE_DISPATCH] History update payload:`, historyUpdatePayload);
        this.notifyHandlers('sensorHistoryUpdate', historyUpdatePayload);
      }
      // 再处理通用的设备参数修改 (有did但不是history类型)
      else if (data.did) {
        // 如果消息中有 'did' (Device ID)，我们认为这是一个设备相关的消息
        console.log(`[SSE_DISPATCH] Dispatching as 'deviceUpdate' for DID: ${data.did}`);
        this.notifyHandlers('deviceUpdate', data);
      } else if (data.message && data.message === "SSE connected") {
        // 这是连接成功后服务器发送的确认消息，可以单独处理或忽略
        console.log('[SSE_INFO] Received connection confirmation message from server.');
        this.notifyHandlers('message', data);
      } else {
        // 对于其他所有类型的消息，分发为通用的 'message' 类型
        console.log("[SSE_DISPATCH] Dispatching as generic 'message'.");
        this.notifyHandlers('message', data);
      }
    } catch (error) {
      console.error('[SSE_ERROR] Error in handleMessage:', error);
    }
  }

  /**
   * 注册一个消息处理器。
   * 外部模块（如DeviceSSEManager）可以通过此方法来监听特定类型的消息。
   * @param {string} type - 消息类型，如 'deviceUpdate', 'message'。
   * @param {Function} handler - 处理消息的回调函数。
   */
  registerHandler(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
    console.log(`[SSE_HANDLER] Registered a new handler for message type: '${type}'`);
  }

  /**
   * 注销一个已注册的消息处理器。
   * @param {string} type - 消息类型。
   * @param {Function} handler - 要注销的回调函数。
   */
  unregisterHandler(type, handler) {
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
        console.log(`[SSE_HANDLER] Unregistered a handler for message type: '${type}'`);
      }
    }
  }

  /**
   * 遍历并执行所有已注册的特定类型的处理器。
   * @param {string} type - 消息类型。
   * @param {object} data - 要传递给处理器的数据。
   *
   * [排查点] 如果消息分发日志已打印，但功能无表现，
   * 1. 确认`this.messageHandlers.has(type)`是否为`true`。如果为`false`，说明没有任何处理器被注册来处理这类消息。
   * 2. 检查`handler(data)`执行时是否报错（虽然这里有try-catch保护）。
   */
  notifyHandlers(type, data) {
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type);
      console.log(`[SSE_NOTIFY] Notifying ${handlers.length} handler(s) for message type: '${type}'`);
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`[SSE_ERROR] A message handler for type '${type}' failed:`, error);
        }
      });
    } else {
      console.warn(`[SSE_WARN] No handlers registered for message type: '${type}'. Message was received but not processed.`);
    }
  }

  // 获取连接状态
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      sseConnectionId: this.sseConnectionId,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }

  /**
   * (新增) 开始定时报告SSE连接状态。
   * @param {number} interval - 报告的间隔时间（毫秒），默认为5000ms (5秒)。
   */
  startStatusReporting(interval = 5000) {
    // 先清除已有的定时器，防止重复启动
    this.stopStatusReporting();

    console.log(`[SSE_STATUS] Starting status reporting every ${interval}ms.`);
    this.statusReportingIntervalId = setInterval(() => {
      const status = this.getConnectionStatus();
      console.log('[SSE_STATUS_REPORT]', status);
    }, interval);
  }

  /**
   * (新增) 停止SSE连接状态的定时报告。
   */
  stopStatusReporting() {
    if (this.statusReportingIntervalId) {
      clearInterval(this.statusReportingIntervalId);
      this.statusReportingIntervalId = null;
      console.log('[SSE_STATUS] Stopped status reporting.');
    }
  }

  // 通知服务端退出连接
  async notifyExit(apiRegistry) {
    if (!this.sseConnectionId || !apiRegistry) {
      return { success: false, message: '缺少必要参数' };
    }

    try {
      const response = await apiRegistry.callAPI('sseExit', {
        sseconid: this.sseConnectionId
      });

      if (response && response.code === 204) {
        return { success: true, message: 'SSE退出通知成功' };
      } else {
        return { success: false, message: response.message || 'SSE退出通知失败' };
      }
    } catch (error) {
      console.error('通知SSE退出失败:', error);
      return { success: false, message: '通知SSE退出失败：' + error.message };
    }
  }

  // 重置SSE服务
  reset() {
    this.disconnect();
    this.messageHandlers.clear();
    this.sseConnectionId = null;
    this.reconnectAttempts = 0;
  }

  // 设置重连参数
  setReconnectConfig(maxAttempts, delay) {
    this.maxReconnectAttempts = maxAttempts || 5;
    this.reconnectDelay = delay || 3000;
  }

  // 手动重连
  reconnect() {
    if (this.isConnected) {
      this.disconnect();
    }
    this.reconnectAttempts = 0;
    return this.connect();
  }
}

module.exports = SSEService;
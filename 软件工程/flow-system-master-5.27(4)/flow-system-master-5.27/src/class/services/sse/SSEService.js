const EventSource = require('eventsource');

/**
 * The SSEService class is responsible for managing the Server-Sent Events (SSE) connection with the server.
 * It handles connection establishment, disconnection, automatic reconnection, and message reception and dispatch.
 */
class SSEService {
  constructor() {
    this.eventSource = null; // EventSource instance for SSE communication
    this.isConnected = false; // Current connection status
    this.connectionUrl = 'http://192.168.58.56:3000/events'; // SSE server endpoint URL
    this.sseConnectionId = null; // Unique ID to identify the SSE connection, usually the user ID
    this.messageHandlers = new Map(); // Stores message handlers, key is message type (e.g., 'deviceUpdate'), value is an array of callback functions
    this.reconnectAttempts = 0; // Current number of reconnection attempts
    this.maxReconnectAttempts = 5; // Maximum number of reconnection attempts
    this.reconnectDelay = 3000; // Reconnection delay time (in milliseconds)
    this.statusReportingIntervalId = null; // Used to store the ID of the status reporting timer
  }

  /**
   * Sets the SSE Connection ID used to establish the connection.
   * @param {string} userId - The user's unique identifier.
   */
  setSseConnectionId(userId) {
    this.sseConnectionId = userId;
  }

  /**
   * Establishes the SSE connection.
   * This is an asynchronous method that returns a Promise.
   * @returns {Promise<{success: boolean, message: string}>} The connection result.
   */
  connect() {
    return new Promise((resolve, reject) => {
      // If already connected, return success directly
      if (this.isConnected) {
        console.log('[SSE_DEBUG] SSE connection already exists.');
        resolve({ success: true, message: 'SSE connection already exists' });
        return;
      }

      // sseConnectionId must be set before connecting
      if (!this.sseConnectionId) {
        console.error('[SSE_ERROR] SSE Connection ID is not set before connecting.');
        reject(new Error('SSE Connection ID is not set'));
        return;
      }

      try {
        // Append sseConnectionId as a query parameter to the URL
        const url = `${this.connectionUrl}?sseconid=${this.sseConnectionId}`;
        console.log(`[SSE_DEBUG] Connecting to SSE endpoint: ${url}`);

        this.eventSource = new EventSource(url);

        /**
         * onopen: Triggered when the SSE connection is successfully established.
         * Here we reset the reconnection counter and update the connection status.
         */
        this.eventSource.onopen = () => {
          console.log('[SSE_SUCCESS] SSE connection established successfully.');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startStatusReporting(); // Start periodic status reporting after successful connection
          resolve({ success: true, message: 'SSE connection successful' });
        };

        /**
         * onmessage: Triggered when any message is received from the server.
         * This is the core location for handling all SSE pushes.
         *
         * [Troubleshooting Point] If you stop receiving messages after the first "connected" message:
         * 1. Confirm if the server is actually pushing subsequent messages.
         * 2. Check if the console.log here prints new event.data when the device status changes.
         *    If it doesn't print, the client is not receiving messages, and the problem might be on the server side or in the network.
         *    If it does print, the client received it but didn't process it correctly; the problem is in handleMessage or its caller.
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
         * onerror: Triggered when a connection error occurs.
         * This could be a network issue, server shutdown, URL error, etc.
         *
         * [Troubleshooting Point] If the connection breaks after the first message, an error log should be printed here,
         * and automatic reconnection should be triggered. Observing the logs here can determine if the connection is stable.
         */
        this.eventSource.onerror = (error) => {
          console.error('[SSE_ERROR] SSE connection error:', error);
          this.isConnected = false;

          // Start the automatic reconnection mechanism
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[SSE_RECONNECT] Attempting to reconnect SSE (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            setTimeout(() => {
              this.connect(); // Try to reconnect later
            }, this.reconnectDelay);
          } else {
            console.error('[SSE_FAIL] SSE reconnection failed after maximum attempts.');
            this.disconnect(); // Stop reconnecting and clean up after reaching the maximum number of attempts
          }
        };

      } catch (error) {
        console.error('[SSE_FATAL] Failed to create SSE connection object:', error);
        reject(error);
      }
    });
  }

  /**
   * Actively disconnects the SSE connection and cleans up resources.
   */
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close(); // Close the connection
      this.eventSource = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = 0; // Reset reconnect counter
    this.stopStatusReporting(); // Stop status reporting when the connection is disconnected
    console.log('[SSE_INFO] SSE connection disconnected.');
  }

  /**
   * Handles parsed SSE messages and dispatches them to the corresponding handlers.
   * @param {object} data - The JSON object received from the server.
   *
   * [Troubleshooting Point] This is the core dispatch logic for message handling.
   * 1. Check if the structure of the received `data` object is as expected.
   * 2. Confirm if `data.did` exists in device update messages. If not, it will be treated as a generic 'message'.
   * 3. Observe the logs before `notifyHandlers` to confirm which type (`'deviceUpdate'` or `'message'`) the message was dispatched to.
   */
  handleMessage(data) {
    try {
      console.log('[SSE_HANDLE_MESSAGE] Handling parsed SSE message:', data);

      // Prioritize handling sensor history data updates (type: 'history')
      if (data.type === 'history' && data.did && data.metric_type && Array.isArray(data.data) && data.data.length > 0) {
        console.log(`[SSE_DISPATCH] Handling 'sensorUpdate' for DID: ${data.did}, Metric: ${data.metric_type}`);

        // Convert the sensor data structure to a standard device status update object
        // Example: { did: '...', temperature: 10.9, lastUpdated: '...' }
        const updatePayload = {
          did: data.did,
          [data.metric_type]: data.data[0].value, // Use metric_type as the key
          lastUpdated: data.timestamp, // Update timestamp
        };

        // Reuse the 'deviceUpdate' event channel for dispatching, as the storage layer does not distinguish between devices and sensors
        this.notifyHandlers('deviceUpdate', updatePayload);
      }
      // Then handle generic device parameter modifications (has did but not history type)
      else if (data.did) {
        // If the message contains a 'did' (Device ID), we consider it a device-related message
        console.log(`[SSE_DISPATCH] Dispatching as 'deviceUpdate' for DID: ${data.did}`);
          this.notifyHandlers('deviceUpdate', data);
      } else if (data.message && data.message === "SSE connected") {
        // This is a confirmation message sent by the server after a successful connection, which can be handled separately or ignored
        console.log('[SSE_INFO] Received connection confirmation message from server.');
        this.notifyHandlers('message', data);
      } else {
        // For all other types of messages, dispatch as a generic 'message' type
        console.log("[SSE_DISPATCH] Dispatching as generic 'message'.");
        this.notifyHandlers('message', data);
      }
    } catch (error) {
      console.error('[SSE_ERROR] Error in handleMessage:', error);
    }
  }

  /**
   * Registers a message handler.
   * External modules (like DeviceSSEManager) can use this method to listen for specific types of messages.
   * @param {string} type - The message type, e.g., 'deviceUpdate', 'message'.
   * @param {Function} handler - The callback function to handle the message.
   */
  registerHandler(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
    console.log(`[SSE_HANDLER] Registered a new handler for message type: '${type}'`);
  }

  /**
   * Unregisters a registered message handler.
   * @param {string} type - The message type.
   * @param {Function} handler - The callback function to unregister.
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
   * Iterates through and executes all registered handlers for a specific type.
   * @param {string} type - The message type.
   * @param {object} data - The data to be passed to the handlers.
   *
   * [Troubleshooting Point] If the message dispatch log has been printed, but there is no functional effect:
   * 1. Confirm if `this.messageHandlers.has(type)` is `true`. If `false`, it means no handlers are registered for this message type.
   * 2. Check if `handler(data)` execution throws an error (although it's protected by a try-catch block here).
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

  // Get connection status
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      sseConnectionId: this.sseConnectionId,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }

  /**
   * (New) Starts periodic reporting of the SSE connection status.
   * @param {number} interval - The reporting interval in milliseconds, defaults to 5000ms (5 seconds).
   */
  startStatusReporting(interval = 5000) {
    // Clear any existing timer first to prevent multiple instances
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

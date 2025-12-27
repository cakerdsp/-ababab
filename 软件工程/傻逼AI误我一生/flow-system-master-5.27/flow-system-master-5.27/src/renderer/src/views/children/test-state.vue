<template>
  <div class="test-state-page">
    <div class="page-header">
      <h1>🧪 状态保持测试页面</h1>
      <p>用于测试页面切换后状态是否保持</p>
    </div>

    <div class="test-sections">
      <!-- 表单数据测试 -->
      <div class="test-section">
        <h2>📝 表单数据测试</h2>
        <div class="form-group">
          <label>文本输入框：</label>
          <input v-model="formData.textInput" placeholder="请输入一些文字，然后切换页面再回来看是否保留">
        </div>
        <div class="form-group">
          <label>数字输入框：</label>
          <input type="number" v-model="formData.numberInput" placeholder="输入数字">
        </div>
        <div class="form-group">
          <label>下拉选择：</label>
          <select v-model="formData.selectValue">
            <option value="option1">选项1</option>
            <option value="option2">选项2</option>
            <option value="option3">选项3</option>
          </select>
        </div>
        <div class="form-group">
          <label>复选框：</label>
          <label v-for="option in checkboxOptions" :key="option.value">
            <input type="checkbox" :value="option.value" v-model="formData.checkboxValues">
            {{ option.label }}
          </label>
        </div>
        <div class="form-group">
          <label>文本域：</label>
          <textarea v-model="formData.textareaValue" placeholder="输入多行文本"></textarea>
        </div>
      </div>

      <!-- 计数器测试 -->
      <div class="test-section">
        <h2>🔢 计数器测试</h2>
        <div class="counter-section">
          <p>当前计数：<strong>{{ counter }}</strong></p>
          <button @click="increment">+1</button>
          <button @click="decrement">-1</button>
          <button @click="reset">重置</button>
        </div>
      </div>

      <!-- 时间戳测试 -->
      <div class="test-section">
        <h2>⏰ 时间戳测试</h2>
        <p>页面创建时间：{{ createdTime }}</p>
        <p>最后更新时间：{{ lastUpdateTime }}</p>
        <button @click="updateTime">更新时间</button>
      </div>

      <!-- 状态显示 -->
      <div class="test-section">
        <h2>📊 当前状态</h2>
        <pre>{{ JSON.stringify(allState, null, 2) }}</pre>
      </div>
    </div>

    <!-- 测试说明 -->
    <div class="test-instructions">
      <h2>🔍 测试说明</h2>
      <ol>
        <li>在上面的表单中填写一些数据</li>
        <li>点击计数器按钮，改变计数值</li>
        <li>点击"更新时间"按钮</li>
        <li>切换到其他页面（如分组管理、设备发现等）</li>
        <li>再切换回来，检查所有数据是否保留</li>
      </ol>

      <div class="status-indicators">
        <div class="indicator" :class="{ active: !isDestroyed }">
          <span class="dot"></span>
          组件{{ isDestroyed ? '已销毁' : '存活中' }}
        </div>
        <div class="indicator" :class="{ active: isKeepAlive }">
          <span class="dot"></span>
          Keep-alive {{ isKeepAlive ? '已启用' : '未启用' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestStatePage',
  data() {
    return {
      // 表单数据
      formData: {
        textInput: '',
        numberInput: 0,
        selectValue: 'option1',
        checkboxValues: [],
        textareaValue: ''
      },

      // 复选框选项
      checkboxOptions: [
        { value: 'check1', label: '选项A' },
        { value: 'check2', label: '选项B' },
        { value: 'check3', label: '选项C' }
      ],

      // 计数器
      counter: 0,

      // 时间戳
      createdTime: '',
      lastUpdateTime: '',

      // 状态标识
      isDestroyed: false,
      isKeepAlive: false
    }
  },

  computed: {
    allState() {
      return {
        formData: this.formData,
        counter: this.counter,
        createdTime: this.createdTime,
        lastUpdateTime: this.lastUpdateTime
      }
    }
  },

  // === 调试生命周期钩子 ===
  created() {
    this.createdTime = new Date().toLocaleString();
    this.lastUpdateTime = this.createdTime;
    console.log('🔍 [调试] TestStatePage created - 测试页面创建', {
      timestamp: new Date().toLocaleTimeString(),
      createdTime: this.createdTime
    });
  },

  mounted() {
    console.log('🔍 [调试] TestStatePage mounted - 测试页面挂载完成', {
      timestamp: new Date().toLocaleTimeString()
    });
  },

  activated() {
    this.isKeepAlive = true;
    console.log('🔍 [调试] TestStatePage activated - 测试页面被激活 (keep-alive)', {
      timestamp: new Date().toLocaleTimeString(),
      message: '✅ keep-alive正在工作！',
      currentState: this.allState
    });
  },

  deactivated() {
    console.log('🔍 [调试] TestStatePage deactivated - 测试页面被缓存 (keep-alive)', {
      timestamp: new Date().toLocaleTimeString(),
      message: '页面被缓存，状态应该保持',
      currentState: this.allState
    });
  },

  beforeUnmount() {
    this.isDestroyed = true;
    console.log('🔍 [调试] TestStatePage beforeUnmount - 测试页面即将销毁', {
      timestamp: new Date().toLocaleTimeString(),
      message: '⚠️ 组件即将被销毁，状态会丢失！',
      currentState: this.allState
    });
  },

  unmounted() {
    console.log('🔍 [调试] TestStatePage unmounted - 测试页面已销毁', {
      timestamp: new Date().toLocaleTimeString(),
      message: '❌ 组件已销毁，所有状态已丢失'
    });
  },

  watch: {
    formData: {
      handler(newVal) {
        console.log('🔍 [调试] TestStatePage formData 变化:', newVal);
      },
      deep: true
    },

    counter(newVal, oldVal) {
      console.log('🔍 [调试] TestStatePage counter 变化:', {
        from: oldVal,
        to: newVal
      });
    }
  },

  methods: {
    increment() {
      this.counter++;
      this.updateTime();
    },

    decrement() {
      this.counter--;
      this.updateTime();
    },

    reset() {
      this.counter = 0;
      this.updateTime();
    },

    updateTime() {
      this.lastUpdateTime = new Date().toLocaleString();
    }
  }
}
</script>

<style scoped>
.test-state-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.page-header p {
  color: #7f8c8d;
}

.test-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.test-section {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.test-section h2 {
  color: #34495e;
  margin-bottom: 15px;
  font-size: 18px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 5px;
  margin-left: 10px;
}

.form-group textarea {
  height: 80px;
  resize: vertical;
}

.counter-section {
  text-align: center;
}

.counter-section p {
  margin-bottom: 15px;
  font-size: 18px;
}

.counter-section button {
  margin: 0 5px;
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.counter-section button:hover {
  background: #2980b9;
}

.test-instructions {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
}

.test-instructions h2 {
  color: #495057;
  margin-bottom: 15px;
}

.test-instructions ol {
  margin-bottom: 20px;
}

.test-instructions li {
  margin-bottom: 8px;
  color: #6c757d;
}

.status-indicators {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.indicator {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  background: #ffeaa7;
  color: #d63031;
}

.indicator.active {
  background: #d1f2eb;
  color: #00b894;
}

.indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  margin-right: 8px;
}

pre {
  background: #f1f2f6;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
</style>
 
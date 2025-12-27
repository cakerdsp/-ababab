<template>
  <div class="title-bar" :style="{ width: expandState ? '' : '510px' }">
    <div
      class="title-bar-left"
      :style="{ backgroundColor: expandState ? 'rgba(255,255,255,0.9)' : '#fff' }"
    >
      <img src="~@/assets/bar/logo.svg" alt="图标" class="icon" />
      <div class="title">全屋环境检测</div>
    </div>

    <div class="title-bar-right">
      <!-- 页面缩放控制 - 暂时禁用修复页面显示问题 -->
      <div v-if="false && expandState" class="scale-control">
        <label class="scale-label">页面缩放:</label>
        <select v-model="selectedScale" @change="handleScaleChange" class="scale-select">
          <option v-for="option in scaleOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <div class="operating-button close-button" @click="closeWindow">
        <img src="~@/assets/bar/close.svg" />
      </div>
      <div class="operating-button minimum-button" @click="minimumWindow">
        <img src="~@/assets/bar/minimum.svg" />
      </div>
      <div v-if="expandState" class="operating-button expand-button" @click="expandWindow">
        <img src="~@/assets/bar/expand.svg" />
      </div>
      <div style="width: 10px"></div>
    </div>
  </div>
</template>


<script>
export default {
  name: 'TitleBar',
  data() {
    return {
      expandState: false,
      selectedScale: 1.0,
      scaleOptions: [
        { value: 0.5, label: '50%' },
        { value: 0.6, label: '60%' },
        { value: 0.7, label: '70%' },
        { value: 0.8, label: '80%' },
        { value: 0.9, label: '90%' },
        { value: 1.0, label: '100%' },
        { value: 1.1, label: '110%' },
        { value: 1.2, label: '120%' },
        { value: 1.3, label: '130%' },
        { value: 1.5, label: '150%' }
      ]
    }
  },
  mounted() {
    this.expandState = !(this.$route.path === '/' || this.$route.path === '/login')

    // 完全重置页面缩放，确保页面正常显示
    this.$nextTick(() => {
      console.log('🔍 [调试] 重置页面缩放样式')

      // 清除所有可能的缩放设置
      localStorage.removeItem('pageScale')

      // 重置app元素样式
      const appElement = document.getElementById('app')
      if (appElement) {
        appElement.style.transform = ''
        appElement.style.width = ''
        appElement.style.height = ''
        appElement.style.transformOrigin = ''
        appElement.style.overflow = ''
        console.log('🔍 [调试] app元素样式已重置')
      }

      // 重置缩放变量
      this.selectedScale = 1.0
    })
  },
  methods: {
    closeWindow() {
      window.close() // 关闭窗口
    },
    minimumWindow() {
      window.ipcRenderer.send('minimizing')
    },
    expandWindow() {
      // console.log('放大按钮被点击，发送expandWindow事件')
      window.ipcRenderer.send('expandWindow', {
        screenWidth: window.screen.width,
        screenHeight: window.screen.height
      })
    },
        handleScaleChange() {
      console.log('🔍 [调试] 页面缩放变更:', this.selectedScale)

      // 如果选择100%，直接重置所有样式
      if (this.selectedScale === 1.0) {
        this.resetScale()
      } else {
        this.applyScale(this.selectedScale)
      }

      // 保存缩放设置到localStorage
      localStorage.setItem('pageScale', this.selectedScale.toString())

      // Vue 3 兼容：移除 $emit 到 $root 的调用
      // this.$root.$emit('page-scale-changed', this.selectedScale)
      console.log('🔍 [调试] Vue 3 兼容：跳过缩放事件发射');
    },

    resetScale() {
      // 完全重置页面缩放
      console.log('🔍 [调试] 重置页面缩放')
      const appElement = document.getElementById('app')
      if (appElement) {
        appElement.style.transform = ''
        appElement.style.width = ''
        appElement.style.height = ''
        appElement.style.transformOrigin = ''
      }
    },
        applyScale(scale) {
      // 应用页面缩放 - 修复版本
      console.log('🔍 [调试] 应用缩放:', scale)

      // 等待DOM加载完成
      this.$nextTick(() => {
        const appElement = document.getElementById('app')
        console.log('🔍 [调试] 找到app元素:', !!appElement)

        if (appElement) {
          // 重置样式（防止叠加）
          appElement.style.transform = ''
          appElement.style.width = ''
          appElement.style.height = ''

          // 如果缩放比例不是100%，才应用缩放
          if (scale !== 1.0) {
            appElement.style.transform = `scale(${scale})`
            appElement.style.transformOrigin = 'top left'

            // 调整容器尺寸以适应缩放，避免内容被截断
            const scaleWidth = scale < 1 ? `${100 / scale}%` : '100%'
            const scaleHeight = scale < 1 ? `${100 / scale}%` : '100%'

            appElement.style.width = scaleWidth
            appElement.style.height = scaleHeight
          }

          console.log('🔍 [调试] 缩放应用完成:', {
            transform: appElement.style.transform,
            width: appElement.style.width,
            height: appElement.style.height
          })
        } else {
          console.error('🔍 [调试] 未找到app元素')
        }
      })
    }
  }
}
</script>

<style scoped>
@import './index.css';
</style>

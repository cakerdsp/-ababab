<template>
  <div class="flow-main" :style="{ height: screenHeight + 'px' }">
    <div class="flow-main-left">
      <sidebar />
    </div>
    <div class="flow-main-right">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
  </div>
</template>

<script>
import sidebar from '../../components/sidebar/index.vue'
export default {
  name: 'index',
  components: {
    sidebar
  },
  data() {
    return {
      screenWidth: (window.screen.width / 5) * 3 + 100,
      screenHeight: window.innerHeight - 50, // 初始高度，减去可能的标题栏或边距
      currentScale: 1.0
    }
  },
  created() {
    console.log('🔍 [调试] main/index.vue created - 主容器组件创建');
    this.updateHeight()
    window.addEventListener('resize', this.updateHeight) // 监听窗口大小变化

    // Vue 3 中移除了 $on 方法，暂时注释掉缩放监听
    // this.$root.$on('page-scale-changed', this.handleScaleChange)
    console.log('🔍 [调试] Vue 3 兼容：跳过缩放事件监听');
  },
  mounted() {
    console.log('🔍 [调试] main/index.vue mounted - 主容器组件挂载完成');

    // 强制确保页面可见
    this.$nextTick(() => {
      const mainElement = this.$el;
      console.log('🔍 [调试] main元素信息:', {
        element: !!mainElement,
        display: mainElement?.style?.display || 'default',
        visibility: mainElement?.style?.visibility || 'default',
        height: mainElement?.offsetHeight || '未知',
        width: mainElement?.offsetWidth || '未知',
        className: mainElement?.className || '无'
      });

      // 强制设置可见性
      if (mainElement) {
        mainElement.style.display = 'flex';
        mainElement.style.visibility = 'visible';
        mainElement.style.opacity = '1';
        console.log('🔍 [调试] main元素可见性已强制设置');
      }
    });
  },
  beforeUnmount() {
    console.log('🔍 [调试] main/index.vue beforeUnmount - 主容器组件即将销毁');
    window.removeEventListener('resize', this.updateHeight) // 清理事件监听器
    // Vue 3 兼容：移除 $off 方法调用
    // this.$root.$off('page-scale-changed', this.handleScaleChange) // 清理缩放监听
    console.log('🔍 [调试] Vue 3 兼容：跳过缩放事件清理');
  },
  watch: {
    '$route'(to, from) {
      console.log('🔍 [调试] main/index.vue 子路由变化:', {
        from: from?.path || '无',
        to: to?.path || '无',
        keepAlive: '已启用keep-alive包装'
      });
    }
  },
  methods: {
    updateHeight() {
      this.screenHeight = window.innerHeight - 50 // 更新为窗口高度，减去标题栏
    },
    handleScaleChange(scale) {
      console.log('🔍 [调试] main容器接收到缩放变化:', scale)
      this.currentScale = scale
      // 根据缩放调整容器高度
      this.updateHeight()
    }
  }
}
</script>

<style scoped>
.flow-main {
  width: auto;
  border-left: 1px solid #d9d9d9;
  border-bottom: 1px solid #d9d9d9;
  border-right: 1px solid #d9d9d9;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
  overflow: auto; /* 允许滚动 */
  color: #151717;
  display: flex; /* 使用flex布局 */
  min-height: 100%; /* 确保最小高度 */
}
.flow-main-left {
  width: 25%;
  min-height: 100%; /* 左侧最小高度 */
  background-color: rgba(221, 228, 234, 0.9);
  border-bottom-left-radius: 20px;
  flex-shrink: 0; /* 防止收缩 */
}
.flow-main-right {
  width: 75%;
  min-height: 100%; /* 右侧最小高度 */
  background-color: white;
  overflow-y: auto; /* 右侧内容区域允许垂直滚动 */
  flex: 1; /* 占用剩余空间 */
}
</style>

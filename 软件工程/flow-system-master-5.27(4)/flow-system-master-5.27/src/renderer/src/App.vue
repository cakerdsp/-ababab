<script>
import bar from "./components/bar/index.vue";
export default {
  components:{
    bar
  },
  created() {
    // 移除应用级自动登录检查，因为登录页面会处理
    console.log('🔍 [调试] App.vue created - 应用根组件创建');
  },
  mounted() {
    console.log('🔍 [调试] App.vue mounted - 应用根组件挂载完成');
  },
  watch: {
    '$route'(to, from) {
      console.log('🔍 [调试] App.vue 路由变化:', {
        from: from?.path || '无',
        to: to?.path || '无',
        fromName: from?.name || '无',
        toName: to?.name || '无'
      });
        }
  }
}
</script>

<template>
  <div id="app-container">
    <bar />
    <router-view />
  </div>
</template>

<style lang="less">
@import './assets/css/styles.less';

/* 页面基础样式 - 移除缩放相关样式 */
#app-container {
  min-height: 100vh;
  /* 暂时移除overflow限制，确保页面正常显示 */
}

/* 移除所有缩放过渡效果 */

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* 响应式优化 */
@media (max-width: 1200px) {
  .flow-main-left {
    width: 30% !important;
  }
  .flow-main-right {
    width: 70% !important;
  }
}

@media (max-width: 768px) {
  .flow-main-left {
    width: 35% !important;
  }
  .flow-main-right {
    width: 65% !important;
  }
}
</style>

import { createRouter, createWebHashHistory } from "vue-router";

const router = createRouter({
  mode: "hash",
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "login",
      redirect: "/login",
    },
    {
      path: "/login",
      name: "登录",
      component: () => import('@/views/login/index.vue')
    },
    {
      path: "/main",
      redirect: "/desktop",
      name: "主容器",
      component: () => import('@/views/main/index.vue'),
      children: [
        {
          path: "/desktop",
          name: "主页",
          component: () => import('@/views/children/desktop/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: "/group",
          name: "付款",
          component: () => import('@/views/children/group/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: "/device",
          name: "设置",
          component: () => import('@/views/children/device/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: "/account",
          name: "账号中心",
          component: () => import('@/views/children/account/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: "/report",
          name: "环境报告",
          component: () => import('@/views/children/report/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: '/third-party-auth',
          name: '第三方授权',
          component: () => import('@/views/children/ThirdPartyAuth/index.vue'),
          meta: { keepAlive: true }
        },
        {
          path: '/test-state',
          name: '状态测试',
          component: () => import('@/views/children/test-state.vue'),
          meta: { keepAlive: true }
        },
      ]
    }
  ]
})
export default router


import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: 'LightRAG 知识图谱问答' } },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: '管理员登录' } },
  { path: '/admin', name: 'Admin', component: () => import('../views/Admin.vue'), meta: { title: '管理后台', requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'LightRAG Web'
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router

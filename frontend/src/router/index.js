import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: 'LightRAG 知识图谱问答' } },
  { path: '/admin', name: 'Admin', component: () => import('../views/Admin.vue'), meta: { title: '管理后台', requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'LightRAG Web'
  if (to.meta.requiresAdmin) {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')
    if (!token || role !== 'admin') {
      next({ path: '/' })
      return
    }
  }
  next()
})

export default router

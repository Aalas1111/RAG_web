import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({ baseURL, timeout: 120000 })

// 公开接口
export const getGraphs = () => api.get('/graphs').then(r => r.data)
/** 知识图谱列表 + 今日已用/每日限额（用于选择弹窗展示剩余次数） */
export const getGraphsWithUsage = () => api.get('/graphs_with_usage').then(r => r.data)
export const query = (graphId, queryText, mode = 'hybrid') =>
  api.post('/query', { graph_id: graphId, query: queryText, mode }).then(r => r.data)

// 管理员接口（需带 token）
function authHeaders() {
  const token = localStorage.getItem('admin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const login = (username, password) =>
  api.post('/admin/login', { username, password }).then(r => r.data)

export const adminGetGraphs = () =>
  api.get('/admin/graphs', { headers: authHeaders() }).then(r => r.data)

export const adminCreateGraph = (formData) =>
  api.post('/admin/graphs', formData, {
    headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  }).then(r => r.data)

export const adminUpdateGraph = (graphId, files) => {
  const formData = new FormData()
  const fileList = Array.isArray(files) ? files : (files && files.length ? Array.from(files) : [])
  fileList.forEach(file => formData.append('files', file))
  return api.post(`/admin/graphs/${graphId}/update`, formData, {
    headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  }).then(r => r.data)
}

export const adminDeleteGraph = (graphId) =>
  api.delete(`/admin/graphs/${graphId}`, { headers: authHeaders() }).then(r => r.data)

export const adminPatchGraph = (graphId, data) =>
  api.patch(`/admin/graphs/${graphId}`, data, { headers: authHeaders() }).then(r => r.data)

export const adminGetStats = () =>
  api.get('/admin/stats', { headers: authHeaders() }).then(r => r.data)

export const adminSetLimit = (graphId, dailyLimit) =>
  api.patch(`/admin/graphs/${graphId}/limit`, { daily_limit: dailyLimit }, { headers: authHeaders() }).then(r => r.data)

/** 环境变量：GET 返回列表（敏感项为占位），PATCH 仅更新传入的键 */
export const adminGetEnv = () =>
  api.get('/admin/env', { headers: authHeaders() }).then(r => r.data)

export const adminPatchEnv = (env) =>
  api.patch('/admin/env', { env }, { headers: authHeaders() }).then(r => r.data)

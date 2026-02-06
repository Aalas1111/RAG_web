import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({ baseURL, timeout: 120000 })

// 统一认证头：token 存 localStorage，用户/管理员共用同一 token 字段，后端通过 JWT role 区分
function authHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 公开接口
export const getGraphs = () => api.get('/graphs').then(r => r.data)
export const getGraphsWithUsage = () => api.get('/graphs_with_usage').then(r => r.data)
export const query = (graphId, queryText, mode = 'hybrid') =>
  api.post('/query', { graph_id: graphId, query: queryText, mode }, { headers: authHeaders() }).then(r => r.data)

// 用户注册 / 登录（返回 token + username）
export const register = (username, password, passwordConfirm) =>
  api.post('/register', { username, password, password_confirm: passwordConfirm }).then(r => r.data)
export const userLogin = (username, password) =>
  api.post('/user/login', { username, password }).then(r => r.data)
export const userMe = () => api.get('/user/me', { headers: authHeaders() }).then(r => r.data)
export const getQueryHistory = (graphId) =>
  api.get('/query_history', { params: { graph_id: graphId }, headers: authHeaders() }).then(r => r.data)
export const deleteQueryHistory = (historyId) =>
  api.delete(`/query_history/${historyId}`, { headers: authHeaders() }).then(r => r.data)
export const changeMyPassword = (oldPassword, newPassword) =>
  api.patch('/user/password', { old_password: oldPassword, new_password: newPassword }, { headers: authHeaders() }).then(r => r.data)
export const deleteMyAccount = () =>
  api.delete('/user/me', { headers: authHeaders() }).then(r => r.data)

// 管理员登录（返回 token，role=admin）
export const adminLogin = (username, password) =>
  api.post('/admin/login', { username, password }).then(r => r.data)

// 管理员接口（需带 token，且后端校验 role=admin）
export const adminGetGraphs = () =>
  api.get('/admin/graphs', { headers: authHeaders() }).then(r => r.data)
export const adminCreateGraph = (formData) =>
  api.post('/admin/graphs', formData, {
    headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  }).then(r => r.data)
export const adminCreateGraphFromFolder = (formData) =>
  api.post('/admin/graphs/from_folder', formData, {
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
export const adminGetEnv = () =>
  api.get('/admin/env', { headers: authHeaders() }).then(r => r.data)
export const adminPatchEnv = (env) =>
  api.patch('/admin/env', { env }, { headers: authHeaders() }).then(r => r.data)

// 账号管理（管理员）
export const adminGetUsers = (search) =>
  api.get('/admin/users', { params: search ? { search } : {}, headers: authHeaders() }).then(r => r.data)
export const adminGetUserHistory = (userId) =>
  api.get(`/admin/users/${userId}/history`, { headers: authHeaders() }).then(r => r.data)
export const adminUpdateUserPassword = (userId, newPassword) =>
  api.patch(`/admin/users/${userId}/password`, { new_password: newPassword }, { headers: authHeaders() }).then(r => r.data)
export const adminDeleteUser = (userId) =>
  api.delete(`/admin/users/${userId}`, { headers: authHeaders() }).then(r => r.data)

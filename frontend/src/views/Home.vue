<template>
  <div class="min-h-screen bg-dark-900 text-violet-300 flex flex-col">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between px-4 py-3 border-b border-dark-700 shrink-0">
      <div class="flex items-center gap-2">
        <!-- 左侧栏展开/折叠 -->
        <button
          type="button"
          class="p-2 rounded-lg text-violet-400 hover:text-violet-200 hover:bg-dark-700 transition-colors"
          title="查询记录"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <button
          type="button"
          class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 hover:border-violet-600 transition-colors text-sm"
          @click="showGraphModal = true"
        >
          <svg class="w-4 h-4 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span>{{ selectedGraph ? selectedGraph.name : '选择知识图谱' }}</span>
        </button>
      </div>
      <div class="flex items-center gap-2">
        <template v-if="currentUsername">
          <span class="text-violet-300 text-sm mr-1">{{ currentUsername }}</span>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="px-3 py-1.5 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 text-sm"
          >
            管理界面
          </router-link>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg bg-red-900/40 border border-red-800/50 text-red-300 hover:bg-red-900/60 text-sm transition-colors"
            @click="logout"
          >
            退出
          </button>
        </template>
        <button
          v-else
          type="button"
          class="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 hover:border-violet-600 transition-colors text-sm"
          @click="showLoginModal = true"
        >
          <svg class="w-4 h-4 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span>登录</span>
        </button>
      </div>
    </header>

    <div class="flex flex-1 min-h-0">
      <!-- 左侧查询记录栏 -->
      <aside
        v-show="sidebarOpen"
        class="w-72 shrink-0 border-r border-dark-700 bg-dark-800/80 flex flex-col overflow-hidden"
      >
        <div class="p-3 border-b border-dark-700">
          <button
            type="button"
            class="w-full py-2.5 rounded-lg bg-violet-600/80 text-white text-sm font-medium hover:bg-violet-500 transition-colors"
            @click="startNewQuery"
          >
            Start a new query
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <template v-if="!currentUsername">
            <p class="text-violet-500 text-xs px-2 py-4">登录后可查看并保存查询记录</p>
          </template>
          <template v-else-if="!selectedGraph">
            <p class="text-violet-500 text-xs px-2 py-4">请先选择知识图谱</p>
          </template>
          <template v-else-if="historyLoading">
            <p class="text-violet-500 text-xs px-2 py-4">加载中...</p>
          </template>
          <template v-else-if="!queryHistory.length">
            <p class="text-violet-500 text-xs px-2 py-4">暂无查询记录</p>
          </template>
          <template v-else>
            <button
              v-for="h in queryHistory"
              :key="h.id"
              type="button"
              class="w-full text-left px-3 py-2.5 rounded-lg mb-1.5 transition-colors"
              :class="viewingRecordId === h.id ? 'bg-violet-800/40 border border-violet-600/50' : 'hover:bg-dark-700 border border-transparent'"
              @click="viewRecord(h)"
            >
              <div class="text-xs text-violet-400">{{ formatHistoryDate(h.created_at) }}</div>
              <div class="text-violet-200 text-sm mt-0.5 line-clamp-2">{{ h.query_text }}</div>
            </button>
          </template>
        </div>
      </aside>

      <!-- 主内容 -->
      <main class="flex-1 flex flex-col items-center justify-center px-6 py-8 min-w-0">
        <div class="w-full max-w-2xl flex flex-col items-center">
          <h1 class="text-5xl font-semibold text-violet-200 mb-1">RAGweb</h1>
          <p class="text-violet-400 text-sm mb-8">以 lightRAG 为基础的知识图谱问答</p>

          <!-- 查看记录时的展示 -->
          <div v-if="viewingRecord" class="w-full space-y-4">
            <div class="rounded-2xl bg-dark-800 border border-violet-800/50 p-5">
              <div class="text-xs text-violet-500 mb-2">{{ formatHistoryDate(viewingRecord.created_at) }}</div>
              <div class="text-violet-300 font-medium mb-2">问题：</div>
              <p class="text-violet-200 text-sm whitespace-pre-wrap">{{ viewingRecord.query_text }}</p>
            </div>
            <div class="rounded-2xl bg-dark-800 border border-violet-800/50 p-5">
              <div class="text-violet-300 font-medium mb-2">回复：</div>
              <div class="markdown-body max-w-none text-sm" v-html="viewingRecordAnswerHtml"></div>
            </div>
          </div>

          <!-- 新查询：对话框 -->
          <template v-else>
            <div class="w-full rounded-2xl bg-dark-800 border border-violet-800/50 shadow-xl overflow-hidden">
              <div class="px-5 pt-4 pb-2 border-b border-dark-700">
                <label class="text-violet-400 text-sm mr-2">检索模式</label>
                <select
                  v-model="queryMode"
                  class="bg-dark-700 border border-violet-800/50 rounded-lg px-3 py-2 text-violet-200 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                >
                  <option value="naive">naive（纯向量）</option>
                  <option value="local">local（局部图谱）</option>
                  <option value="global">global（全局图谱）</option>
                  <option value="hybrid">hybrid（混合，推荐）</option>
                </select>
              </div>
              <div class="p-5 relative">
                <textarea
                  v-model="queryText"
                  placeholder="在此输入您的问题..."
                  rows="4"
                  class="w-full bg-dark-700 border border-violet-800/50 rounded-xl px-4 py-3 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 resize-none"
                />
                <button
                  type="button"
                  :disabled="loadingQuery || !queryText.trim() || !selectedGraph"
                  class="absolute right-3 bottom-3 p-2 rounded-lg text-violet-400 hover:text-violet-200 hover:bg-dark-600/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="提交查询"
                  @click="doQuery"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- 回答区：加载中 -->
            <div v-if="loadingQuery" class="w-full mt-6 rounded-2xl bg-dark-800 border border-violet-800/50 p-6 animate-fade-in">
              <div class="flex items-center justify-center gap-2 text-violet-400">
                <span class="inline-block w-2 h-2 rounded-full bg-violet-400 animate-pulse-dots" style="animation-delay: 0ms"></span>
                <span class="inline-block w-2 h-2 rounded-full bg-violet-400 animate-pulse-dots" style="animation-delay: 160ms"></span>
                <span class="inline-block w-2 h-2 rounded-full bg-violet-400 animate-pulse-dots" style="animation-delay: 320ms"></span>
                <span class="ml-2 text-sm">答案生成中...</span>
              </div>
            </div>
            <!-- 回答区：结果 -->
            <div v-else-if="answer !== null" class="w-full mt-6 rounded-2xl bg-dark-800 border border-violet-800/50 p-5 animate-fade-in">
              <div class="markdown-body max-w-none" v-html="answerHtml"></div>
              <p v-if="usage" class="mt-4 text-violet-500 text-sm">今日已用 {{ usage.today_used }} / {{ usage.daily_limit }} 次</p>
            </div>
            <div v-else-if="queryError" class="w-full mt-6 rounded-xl bg-red-900/20 border border-red-800/50 px-4 py-3 text-red-300 text-sm">
              {{ queryError }}
            </div>
          </template>
        </div>
      </main>
    </div>

    <!-- 选择知识图谱弹窗 -->
    <Teleport to="body">
      <div
        v-if="showGraphModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 animate-fade-in"
        @click.self="showGraphModal = false"
      >
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col">
          <div class="px-6 py-4 border-b border-dark-700 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-violet-200">选择知识图谱</h2>
            <button type="button" class="p-2 text-violet-400 hover:text-violet-200 rounded-lg hover:bg-dark-700" @click="showGraphModal = false">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-4">
            <div v-if="loadingGraphs" class="text-center text-violet-500 py-8">加载中...</div>
            <div v-else-if="!graphsWithUsage.length" class="text-center text-violet-500 py-8">暂无知识图谱</div>
            <div v-else class="space-y-3">
              <button
                v-for="g in graphsWithUsage"
                :key="g.id"
                type="button"
                class="w-full text-left px-4 py-4 rounded-xl border transition-colors"
                :class="selectedGraph && selectedGraph.id === g.id ? 'bg-violet-800/30 border-violet-600 text-violet-200' : 'bg-dark-700 border-dark-600 text-violet-300 hover:border-violet-800/50'"
                @click="selectGraph(g); showGraphModal = false"
              >
                <div class="font-medium">{{ g.name }}</div>
                <div class="text-sm text-violet-500 mt-1">{{ g.description || '暂无简介' }}</div>
                <div class="text-xs text-violet-400 mt-2">剩余 {{ Math.max(0, g.daily_limit - g.today_used) }} / {{ g.daily_limit }} 次</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 登录/注册弹窗 -->
    <Teleport to="body">
      <div
        v-if="showLoginModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 animate-fade-in"
        @click.self="showLoginModal = false"
      >
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl w-full max-w-sm p-6 shadow-2xl">
          <div class="flex gap-2 mb-4 border-b border-dark-700 pb-2">
            <button
              type="button"
              class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="loginTab === 'user' ? 'bg-violet-600/50 text-violet-200' : 'text-violet-500 hover:text-violet-300'"
              @click="loginTab = 'user'; loginError = ''"
            >
              用户登录
            </button>
            <button
              type="button"
              class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="loginTab === 'admin' ? 'bg-violet-600/50 text-violet-200' : 'text-violet-500 hover:text-violet-300'"
              @click="loginTab = 'admin'; loginError = ''; isRegister = false"
            >
              管理员登录
            </button>
          </div>
          <form v-if="loginTab === 'admin'" @submit.prevent="submitAdminLogin" class="space-y-4">
            <div>
              <label class="block text-sm text-violet-400 mb-1">账号</label>
              <input v-model="adminUsername" type="text" required autocomplete="username" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">密码</label>
              <input v-model="adminPassword" type="password" required autocomplete="current-password" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <p v-if="loginError" class="text-red-300 text-sm">{{ loginError }}</p>
            <button type="submit" class="w-full py-2.5 rounded-lg bg-violet-600 text-white font-medium hover:bg-violet-500 disabled:opacity-50" :disabled="loginLoading">
              {{ loginLoading ? '登录中...' : '登录' }}
            </button>
          </form>
          <template v-else>
            <form v-if="!isRegister" @submit.prevent="submitUserLogin" class="space-y-4">
              <div>
                <label class="block text-sm text-violet-400 mb-1">账号</label>
                <input v-model="userUsername" type="text" required autocomplete="username" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
              </div>
              <div>
                <label class="block text-sm text-violet-400 mb-1">密码</label>
                <input v-model="userPassword" type="password" required autocomplete="current-password" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
              </div>
              <p v-if="loginError" class="text-red-300 text-sm">{{ loginError }}</p>
              <button type="submit" class="w-full py-2.5 rounded-lg bg-violet-600 text-white font-medium hover:bg-violet-500 disabled:opacity-50" :disabled="loginLoading">
                {{ loginLoading ? '登录中...' : '登录' }}
              </button>
              <button type="button" class="w-full text-center text-violet-400 hover:text-violet-300 text-sm" @click="isRegister = true; loginError = ''">
                没有账号？先注册一个账号吧！
              </button>
            </form>
            <form v-else @submit.prevent="submitRegister" class="space-y-4">
              <div>
                <label class="block text-sm text-violet-400 mb-1">账号</label>
                <input v-model="userUsername" type="text" required autocomplete="username" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
              </div>
              <div>
                <label class="block text-sm text-violet-400 mb-1">密码</label>
                <input v-model="userPassword" type="password" required autocomplete="new-password" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
              </div>
              <div>
                <label class="block text-sm text-violet-400 mb-1">确认密码</label>
                <input v-model="userPasswordConfirm" type="password" required autocomplete="new-password" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
              </div>
              <p v-if="loginError" class="text-red-300 text-sm">{{ loginError }}</p>
              <button type="submit" class="w-full py-2.5 rounded-lg bg-violet-600 text-white font-medium hover:bg-violet-500 disabled:opacity-50" :disabled="loginLoading">
                {{ loginLoading ? '注册中...' : '注册' }}
              </button>
              <button type="button" class="w-full text-center text-violet-400 hover:text-violet-300 text-sm" @click="isRegister = false; loginError = ''">
                已有账号？去登录
              </button>
            </form>
          </template>
          <button type="button" class="w-full mt-3 py-2 text-violet-500 hover:text-violet-300 text-sm" @click="showLoginModal = false">关闭</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getGraphsWithUsage, query, userLogin, register, adminLogin, getQueryHistory, userMe } from '../api'
import { marked } from 'marked'

marked.setOptions({ gfm: true, breaks: true })

const graphsWithUsage = ref([])
const loadingGraphs = ref(true)
const selectedGraph = ref(null)
const showGraphModal = ref(false)
const queryMode = ref('hybrid')
const queryText = ref('')
const loadingQuery = ref(false)
const answer = ref(null)
const queryError = ref('')
const usage = ref(null)

const sidebarOpen = ref(false)
const queryHistory = ref([])
const historyLoading = ref(false)
const viewingRecordId = ref(null)
const viewingRecord = ref(null)

const showLoginModal = ref(false)
const loginTab = ref('user')
const isRegister = ref(false)
const adminUsername = ref('')
const adminPassword = ref('')
const userUsername = ref('')
const userPassword = ref('')
const userPasswordConfirm = ref('')
const loginError = ref('')
const loginLoading = ref(false)

const currentUsername = ref('')
const isAdmin = ref(false)

const answerHtml = computed(() => {
  if (answer.value == null) return ''
  return marked.parse(answer.value, { async: false })
})

const viewingRecordAnswerHtml = computed(() => {
  if (!viewingRecord.value?.answer) return ''
  return marked.parse(viewingRecord.value.answer, { async: false })
})

function formatHistoryDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date()
  const isToday = d.toDateString() === today.toDateString()
  if (isToday) return '今天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function loadAuth() {
  const token = localStorage.getItem('token')
  const name = localStorage.getItem('username')
  const role = localStorage.getItem('role')
  currentUsername.value = name || ''
  isAdmin.value = role === 'admin'
}

async function loadHistory() {
  if (!currentUsername.value || !selectedGraph.value) {
    queryHistory.value = []
    return
  }
  historyLoading.value = true
  try {
    queryHistory.value = await getQueryHistory(selectedGraph.value.id)
  } catch {
    queryHistory.value = []
  } finally {
    historyLoading.value = false
  }
}

watch(selectedGraph, () => {
  viewingRecordId.value = null
  viewingRecord.value = null
  loadHistory()
}, { immediate: false })

watch([currentUsername, selectedGraph], () => {
  loadHistory()
})

function startNewQuery() {
  viewingRecordId.value = null
  viewingRecord.value = null
}

function viewRecord(h) {
  viewingRecordId.value = h.id
  viewingRecord.value = h
}

onMounted(async () => {
  loadAuth()
  try {
    graphsWithUsage.value = await getGraphsWithUsage()
  } catch (e) {
    queryError.value = '加载图谱列表失败：' + (e.response?.data?.detail || e.message)
  } finally {
    loadingGraphs.value = false
  }
  if (graphsWithUsage.value.length && !selectedGraph.value) {
    showGraphModal.value = true
  }
  // 首次访问弹出一次登录
  const seen = sessionStorage.getItem('login_modal_shown_once')
  if (!seen) {
    sessionStorage.setItem('login_modal_shown_once', '1')
    showLoginModal.value = true
  }
})

function selectGraph(g) {
  selectedGraph.value = g
  answer.value = null
  queryError.value = ''
  usage.value = null
  const idx = graphsWithUsage.value.findIndex(x => x.id === g.id)
  if (idx >= 0) graphsWithUsage.value[idx] = { ...g }
}

async function doQuery() {
  if (!selectedGraph.value || !queryText.value.trim()) return
  loadingQuery.value = true
  answer.value = null
  queryError.value = ''
  try {
    const res = await query(selectedGraph.value.id, queryText.value.trim(), queryMode.value)
    answer.value = res.answer
    usage.value = { today_used: res.today_used, daily_limit: res.daily_limit }
    const g = graphsWithUsage.value.find(x => x.id === selectedGraph.value.id)
    if (g) {
      g.today_used = res.today_used
      g.daily_limit = res.daily_limit
    }
    await loadHistory()
  } catch (e) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') queryError.value = detail
    else queryError.value = '查询失败：' + (e.message || '网络错误')
  } finally {
    loadingQuery.value = false
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  loadAuth()
  showLoginModal.value = false
  window.location.reload()
}

async function submitAdminLogin() {
  loginError.value = ''
  loginLoading.value = true
  try {
    const res = await adminLogin(adminUsername.value, adminPassword.value)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('username', adminUsername.value)
    localStorage.setItem('role', 'admin')
    showLoginModal.value = false
    window.location.reload()
  } catch (e) {
    loginError.value = e.response?.data?.detail || '登录失败'
  } finally {
    loginLoading.value = false
  }
}

async function submitUserLogin() {
  loginError.value = ''
  loginLoading.value = true
  try {
    const res = await userLogin(userUsername.value, userPassword.value)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('username', res.username)
    localStorage.setItem('role', 'user')
    showLoginModal.value = false
    window.location.reload()
  } catch (e) {
    loginError.value = e.response?.data?.detail || '登录失败'
  } finally {
    loginLoading.value = false
  }
}

async function submitRegister() {
  loginError.value = ''
  if (userPassword.value !== userPasswordConfirm.value) {
    loginError.value = '两次密码不一致'
    return
  }
  loginLoading.value = true
  try {
    const res = await register(userUsername.value, userPassword.value, userPasswordConfirm.value)
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('username', res.username)
    localStorage.setItem('role', 'user')
    showLoginModal.value = false
    window.location.reload()
  } catch (e) {
    loginError.value = e.response?.data?.detail || '注册失败'
  } finally {
    loginLoading.value = false
  }
}
</script>

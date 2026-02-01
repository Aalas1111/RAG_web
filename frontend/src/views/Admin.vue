<template>
  <div class="min-h-screen bg-dark-900 text-violet-300 flex flex-col">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between px-6 py-4 border-b border-dark-700 shrink-0">
      <h1 class="text-lg font-semibold text-violet-200">管理界面</h1>
      <div class="flex items-center gap-3">
        <router-link
          to="/"
          class="px-4 py-2 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 transition-colors"
        >
          返回首页
        </router-link>
        <button
          type="button"
          class="px-4 py-2 rounded-lg bg-red-900/40 border border-red-800/50 text-red-300 hover:bg-red-900/60 transition-colors"
          @click="logout"
        >
          退出登录
        </button>
      </div>
    </header>

    <!-- 主体：知识图谱列表 -->
    <main class="flex-1 px-6 py-8 max-w-4xl mx-auto w-full">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-semibold text-violet-200">知识图谱列表</h2>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-700 border border-violet-800/50 text-violet-300 hover:bg-dark-600 hover:border-violet-600 transition-colors"
            @click="openEnvModal"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            配置环境变量
          </button>
          <button
            type="button"
            class="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500 transition-colors"
            @click="showCreateModal = true"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            创建知识图谱
          </button>
        </div>
      </div>

      <div v-if="graphsLoading" class="text-violet-500 py-12 text-center">加载中...</div>
      <div v-else-if="!graphs.length" class="text-violet-500 py-12 text-center">暂无知识图谱</div>
      <div v-else class="space-y-4">
        <div
          v-for="g in graphs"
          :key="g.id"
          class="rounded-xl bg-dark-800 border border-violet-800/50 p-5"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0 flex-1">
              <div class="font-medium text-violet-200">{{ g.name }}</div>
              <div class="text-sm text-violet-500 mt-1">{{ g.description || '无简介' }}</div>
              <div class="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-violet-400">
                <span>ID: {{ g.id }}</span>
                <span>每日限额: {{ g.daily_limit }}</span>
                <span>今日已用: {{ getTodayCount(g.id) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                type="button"
                class="p-2 rounded-lg bg-dark-700 border border-violet-800/50 text-violet-400 hover:text-violet-200 hover:border-violet-600 transition-colors"
                title="配置"
                @click="openConfig(g)"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              </button>
              <label class="p-2 rounded-lg bg-dark-700 border border-violet-800/50 text-violet-400 hover:text-violet-200 hover:border-violet-600 transition-colors cursor-pointer" title="增量更新">
                <input type="file" accept=".txt" multiple class="hidden" @change="e => startIncremental(g.id, e.target.files)" />
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
              </label>
              <button
                type="button"
                class="p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 hover:bg-red-900/50 transition-colors"
                title="删除"
                @click="confirmDelete(g)"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 创建知识图谱弹窗 -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" @click.self="showCreateModal = false">
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden">
          <div class="px-6 py-4 border-b border-dark-700 flex justify-between items-center">
            <h2 class="text-lg font-semibold text-violet-200">创建知识图谱</h2>
            <button type="button" class="p-2 text-violet-400 hover:text-violet-200 rounded-lg hover:bg-dark-700" @click="showCreateModal = false">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <div>
              <label class="block text-sm text-violet-400 mb-1">名称</label>
              <input v-model="createName" type="text" placeholder="知识图谱名称" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">简介</label>
              <input v-model="createDesc" type="text" placeholder="简介（可选）" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">每日查询限额</label>
              <input v-model.number="createDailyLimit" type="number" min="0" placeholder="100" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">上传 .txt 文件（可多选或拖入）</label>
              <div
                class="border-2 border-dashed border-violet-800/50 rounded-xl p-6 text-center transition-colors"
                :class="dropActive ? 'border-violet-600 bg-violet-800/20' : 'border-violet-800/50'"
                @dragover.prevent="dropActive = true"
                @dragleave.prevent="dropActive = false"
                @drop.prevent="onCreateDrop"
              >
                <input ref="createFileRef" type="file" accept=".txt" multiple class="hidden" @change="onCreateFile" />
                <p class="text-violet-400 text-sm mb-2">将文件拖到此处，或点击选择</p>
                <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="createFileRef?.click()">选择文件</button>
                <p v-if="createFiles.length" class="text-violet-300 text-sm mt-2">已选 {{ createFiles.length }} 个文件</p>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-dark-700 flex justify-end gap-3">
            <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="showCreateModal = false">取消</button>
            <button type="button" class="px-4 py-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50" :disabled="creating || !createName.trim() || !createFiles.length" @click="createGraph">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 配置弹窗 -->
    <Teleport to="body">
      <div v-if="configGraph" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" @click.self="configGraph = null">
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl w-full max-w-md p-6">
          <h2 class="text-lg font-semibold text-violet-200 mb-4">配置 · {{ configGraph.name }}</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-violet-400 mb-1">名称</label>
              <input v-model="editName[configGraph.id]" type="text" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">简介</label>
              <input v-model="editDesc[configGraph.id]" type="text" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
            <div>
              <label class="block text-sm text-violet-400 mb-1">每日查询限额</label>
              <input v-model.number="limitEdit[configGraph.id]" type="number" min="0" class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="configGraph = null">取消</button>
            <button type="button" class="px-4 py-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500" @click="saveConfig">保存</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 增量更新弹窗（选文件后直接提交，进度在 progress 弹窗） -->
    <!-- 进度/结果弹窗（处理中不可点击遮罩关闭） -->
    <Teleport to="body">
      <div v-if="progressModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" @click.self="progressModal !== 'loading' && (progressModal = null)">
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl w-full max-w-sm p-6">
          <div v-if="progressModal === 'loading'" class="text-center">
            <div class="text-violet-200 font-medium mb-2">正在处理...</div>
            <div class="text-violet-500 text-sm">构建或增量更新中，请稍候</div>
          </div>
          <div v-else-if="progressModal === 'success'" class="text-center">
            <div class="text-violet-200 font-medium mb-2">完成</div>
            <div class="text-violet-500 text-sm mb-4">操作已成功完成</div>
            <button type="button" class="px-4 py-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500" @click="progressModal = null">关闭</button>
          </div>
          <div v-else class="text-center">
            <div class="text-red-300 font-medium mb-2">失败</div>
            <div class="text-violet-400 text-sm mb-4">{{ progressError }}</div>
            <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="progressModal = null">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <div v-if="toDelete" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" @click.self="toDelete = null">
        <div class="bg-dark-800 border border-red-800/50 rounded-2xl w-full max-w-md p-6">
          <h2 class="text-lg font-semibold text-violet-200 mb-2">确认删除</h2>
          <p class="text-violet-400 text-sm mb-6">确定要删除知识图谱「{{ toDelete.name }}」吗？此操作不可恢复，该图谱下的所有数据将被删除。</p>
          <div class="flex justify-end gap-3">
            <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="toDelete = null">取消</button>
            <button type="button" class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-500" @click="doDelete(toDelete.id)">确认删除</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 配置环境变量弹窗 -->
    <Teleport to="body">
      <div v-if="showEnvModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" @click.self="showEnvModal = false">
        <div class="bg-dark-800 border border-violet-800/50 rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden">
          <div class="px-6 py-4 border-b border-dark-700 flex justify-between items-center">
            <h2 class="text-lg font-semibold text-violet-200">配置环境变量</h2>
            <button type="button" class="p-2 text-violet-400 hover:text-violet-200 rounded-lg hover:bg-dark-700" @click="showEnvModal = false">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <p class="text-violet-500 text-sm">敏感项（API Key、密码等）不显示原值，留空表示不修改。</p>
            <div v-for="item in envList" :key="item.key" class="space-y-1">
              <label class="block text-sm text-violet-400">{{ item.key }}</label>
              <input
                v-model="envForm[item.key]"
                :type="item.masked ? 'password' : 'text'"
                :placeholder="item.masked ? '留空则不修改' : (item.value || '未设置')"
                class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
            </div>
            <div v-if="envLoadError" class="text-red-400 text-sm">{{ envLoadError }}</div>
          </div>
          <div class="px-6 py-4 border-t border-dark-700 flex justify-end gap-3">
            <button type="button" class="px-4 py-2 rounded-lg bg-dark-700 text-violet-300 hover:bg-dark-600" @click="showEnvModal = false">取消</button>
            <button type="button" class="px-4 py-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50" :disabled="envSaving" @click="saveEnv">
              {{ envSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  adminGetGraphs,
  adminCreateGraph,
  adminUpdateGraph,
  adminDeleteGraph,
  adminPatchGraph,
  adminGetStats,
  adminSetLimit,
  adminGetEnv,
  adminPatchEnv,
} from '../api'

const graphs = ref([])
const graphsLoading = ref(true)
const stats = ref([])
const showCreateModal = ref(false)
const configGraph = ref(null)
const progressModal = ref(null)
const progressError = ref('')
const createName = ref('')
const createDesc = ref('')
const createDailyLimit = ref(100)
const createFileRef = ref(null)
const createFiles = ref([])
const creating = ref(false)
const dropActive = ref(false)
const editName = reactive({})
const editDesc = reactive({})
const limitEdit = reactive({})
const toDelete = ref(null)
const showEnvModal = ref(false)
const envList = ref([])
const envForm = reactive({})
const envLoadError = ref('')
const envSaving = ref(false)

function getTodayCount(id) {
  const s = stats.value.find(x => x.id === id)
  return s ? s.today_count : 0
}

onMounted(async () => {
  await loadGraphs()
  await loadStats()
})

async function loadGraphs() {
  graphsLoading.value = true
  try {
    graphs.value = await adminGetGraphs()
    graphs.value.forEach(g => {
      editName[g.id] = g.name
      editDesc[g.id] = g.description || ''
      limitEdit[g.id] = g.daily_limit
    })
  } catch (e) {
    if (e.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login?redirect=/admin'
    }
  } finally {
    graphsLoading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await adminGetStats()
    stats.value.forEach(s => {
      if (limitEdit[s.id] === undefined) limitEdit[s.id] = s.daily_limit
    })
  } catch (e) {
    // ignore
  }
}

function onCreateFile(e) {
  createFiles.value = e.target.files ? Array.from(e.target.files) : []
}

function onCreateDrop(e) {
  dropActive.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.txt'))
  if (files.length) createFiles.value = [...createFiles.value, ...files]
}

async function createGraph() {
  if (!createName.value.trim() || !createFiles.value.length) return
  showCreateModal.value = false
  progressModal.value = 'loading'
  creating.value = true
  progressError.value = ''
  try {
    const formData = new FormData()
    formData.append('name', createName.value.trim())
    formData.append('description', createDesc.value.trim())
    formData.append('daily_limit', createDailyLimit.value >= 0 ? createDailyLimit.value : 100)
    createFiles.value.forEach(file => formData.append('files', file))
    await adminCreateGraph(formData)
    createName.value = ''
    createDesc.value = ''
    createDailyLimit.value = 100
    createFiles.value = []
    createFileRef.value && (createFileRef.value.value = '')
    await loadGraphs()
    await loadStats()
    progressModal.value = 'success'
  } catch (e) {
    progressError.value = e.response?.data?.detail || '创建失败'
    progressModal.value = 'error'
  } finally {
    creating.value = false
  }
}

function openConfig(g) {
  configGraph.value = g
}

async function saveConfig() {
  if (!configGraph.value) return
  try {
    await adminPatchGraph(configGraph.value.id, {
      name: editName[configGraph.value.id],
      description: editDesc[configGraph.value.id],
    })
    await adminSetLimit(configGraph.value.id, limitEdit[configGraph.value.id] ?? configGraph.value.daily_limit)
    configGraph.value = null
    await loadGraphs()
    await loadStats()
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

async function startIncremental(id, fileList) {
  if (!fileList || !fileList.length) return
  progressModal.value = 'loading'
  progressError.value = ''
  try {
    await adminUpdateGraph(id, fileList)
    await loadGraphs()
    await loadStats()
    progressModal.value = 'success'
  } catch (e) {
    progressError.value = e.response?.data?.detail || '更新失败'
    progressModal.value = 'error'
  }
}

function confirmDelete(g) {
  toDelete.value = g
}

async function doDelete(id) {
  try {
    await adminDeleteGraph(id)
    toDelete.value = null
    await loadGraphs()
    await loadStats()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function logout() {
  localStorage.removeItem('admin_token')
  window.location.href = '/login'
}

async function openEnvModal() {
  showEnvModal.value = true
  envLoadError.value = ''
  envList.value = []
  Object.keys(envForm).forEach(k => delete envForm[k])
  try {
    const list = await adminGetEnv()
    envList.value = list
    list.forEach(item => {
      envForm[item.key] = item.masked ? '' : (item.value || '')
    })
  } catch (e) {
    if (e.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login?redirect=/admin'
    } else {
      envLoadError.value = e.response?.data?.detail || '加载环境变量失败'
    }
  }
}

async function saveEnv() {
  const updates = {}
  envList.value.forEach(item => {
    const v = envForm[item.key]
    if (v !== undefined && String(v).trim() !== '') updates[item.key] = String(v).trim()
  })
  if (Object.keys(updates).length === 0) {
    showEnvModal.value = false
    return
  }
  envSaving.value = true
  try {
    await adminPatchEnv(updates)
    showEnvModal.value = false
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    envSaving.value = false
  }
}
</script>

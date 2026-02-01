<template>
  <div class="min-h-screen bg-dark-900 text-violet-300 flex flex-col">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between px-6 py-4 border-b border-dark-700 shrink-0">
      <button
        type="button"
        class="flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 hover:border-violet-600 transition-colors"
        @click="showGraphModal = true"
      >
        <svg class="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        <span>{{ selectedGraph ? `当前知识图谱：${selectedGraph.name}` : '选择一个知识图谱' }}</span>
      </button>
      <router-link
        to="/login"
        class="flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-800 border border-violet-800/50 text-violet-300 hover:bg-dark-700 hover:border-violet-600 transition-colors"
      >
        <svg class="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span>登录管理界面</span>
      </router-link>
    </header>

    <!-- 主内容：居中对话框 -->
    <main class="flex-1 flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-2xl flex flex-col items-center">
        <h1 class="text-5xl font-semibold text-violet-200 mb-1">RAGweb</h1>
        <p class="text-violet-400 text-sm mb-8">以 lightRAG 为基础的知识图谱问答</p>

        <!-- 对话框 -->
        <div class="w-full rounded-2xl bg-dark-800 border border-violet-800/50 shadow-xl overflow-hidden">
          <!-- 检索模式：左上 -->
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
          <!-- 输入区 -->
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
              class="absolute right-3 bottom-3 p-2 rounded-lg bg-violet-600 text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="提交查询"
              @click="doQuery"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 回答区 -->
        <div v-if="loadingQuery" class="w-full mt-6 rounded-2xl bg-dark-800 border border-violet-800/50 p-5 flex items-center justify-center">
          <div class="text-violet-400">
            <div class="flex items-center justify-center gap-2">
              <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>答案生成中...</span>
            </div>
          </div>
        </div>
        <div v-else-if="answer !== null" class="w-full mt-6 rounded-2xl bg-dark-800 border border-violet-800/50 p-5 animate-fade-in">
          <div class="markdown-body max-w-none" v-html="answerHtml"></div>
          <p v-if="usage" class="mt-4 text-violet-500 text-sm">今日已用 {{ usage.today_used }} / {{ usage.daily_limit }} 次</p>
        </div>
        <div v-else-if="queryError" class="w-full mt-6 rounded-xl bg-red-900/20 border border-red-800/50 px-4 py-3 text-red-300 text-sm">
          {{ queryError }}
        </div>
      </div>
    </main>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getGraphsWithUsage, query } from '../api'
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

const answerHtml = computed(() => {
  if (answer.value == null) return ''
  return marked.parse(answer.value, { async: false })
})

onMounted(async () => {
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
})

function selectGraph(g) {
  selectedGraph.value = g
  answer.value = null
  queryError.value = ''
  usage.value = null
  const idx = graphsWithUsage.value.findIndex(x => x.id === g.id)
  if (idx >= 0) {
    graphsWithUsage.value[idx] = { ...g }
  }
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
  } catch (e) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') queryError.value = detail
    else queryError.value = '查询失败：' + (e.message || '网络错误')
  } finally {
    loadingQuery.value = false
  }
}
</script>

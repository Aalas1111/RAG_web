<template>
  <div class="min-h-screen bg-dark-900 flex items-center justify-center px-4">
    <div class="w-full max-w-sm rounded-2xl bg-dark-800 border border-violet-800/50 p-8 shadow-xl">
      <h1 class="text-xl font-semibold text-violet-200 text-center mb-6">管理员登录</h1>
      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm text-violet-400 mb-1">用户名</label>
          <input
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
        </div>
        <div>
          <label class="block text-sm text-violet-400 mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full bg-dark-700 border border-violet-800/50 rounded-lg px-4 py-2 text-violet-200 placeholder-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
        </div>
        <p v-if="error" class="text-red-300 text-sm">{{ error }}</p>
        <button
          type="submit"
          class="w-full py-2.5 rounded-lg bg-violet-600 text-white font-medium hover:bg-violet-500 disabled:opacity-50 transition-colors"
          :disabled="loading"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <router-link to="/" class="block text-center mt-4 text-violet-400 hover:text-violet-300 text-sm transition-colors">返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '../api'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await login(username.value, password.value)
    localStorage.setItem('admin_token', res.access_token)
    const redirect = route.query.redirect || '/admin'
    router.push(redirect)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

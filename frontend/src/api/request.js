import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 凭证由后端以 httpOnly cookie 下发，前端不再存 token；
// withCredentials 让 axios 自动携带同源 cookie（跨域需后端 CORS allow_credentials）。
const request = axios.create({ baseURL: '/api/v1', timeout: 15000, withCredentials: true })

function clearAuth() {
  // 删除 cookie 只能由后端做（httpOnly），这里异步调 /auth/logout 并清本地非敏感状态
  request.post('/auth/logout').catch(() => {})
  localStorage.removeItem('user')
  // 同步 Pinia 状态，避免页面仍显示"已登录"（动态导入规避循环依赖）
  import('@/store/user').then(({ useUserStore }) => {
    const store = useUserStore()
    store.user = null
  })
}

function handleUnauthorized(err) {
  // 40100 = 未登录，40101 = token 过期/失效，提示语应区分
  const code = err.response?.data?.code
  const message = code === 40101 ? '登录已过期，请重新登录' : '请先登录'
  const current = router.currentRoute.value

  clearAuth()

  // 已在登录/注册页则不重复跳转、不重复弹提示
  if (current.path === '/login' || current.path === '/register') return

  ElMessage.error(message)
  router.push({ path: '/login', query: { redirect: current.fullPath } })
}

request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && body.code === 0) return body.data
    ElMessage.error(body?.message || '请求失败')
    return Promise.reject(new Error(body?.message || '请求失败'))
  },
  (err) => {
    const status = err.response?.status
    const body = err.response?.data
    // silent 请求（如后台刷新购物车角标）失败时保持安静，不弹窗打扰
    const silent = err.config?.silent
    const url = err.config?.url || ''

    // 登录/注册是「获取凭证」的入口，它们的 401 是业务失败（密码错误/账号锁定/账号或密码错误），
    // 不是 token 失效。必须直接提示后端返回的具体原因，而不是走"认证失效→清凭证→跳转"的逻辑，
    // 否则用户在登录页输错密码会毫无反馈，误以为"登录失效"。
    const isAuthEntry = url.includes('/auth/login') || url.includes('/auth/register')

    if (isAuthEntry) {
      ElMessage.error(body?.message || '请求失败')
    } else if (status === 401) {
      if (silent) {
        // 静默清理凭证，但不打扰用户；由下一次主动操作触发跳转
        clearAuth()
      } else {
        handleUnauthorized(err)
      }
    } else if (status === 403) {
      ElMessage.error(body?.message || '无权限')
    } else if (!silent) {
      ElMessage.error(body?.message || `请求失败 (${status})`)
    }
    return Promise.reject(err)
  }
)

export default request

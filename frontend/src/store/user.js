import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi } from '@/api'

const USER_KEY = 'user'

/**
 * 读取本地缓存的用户画像（非敏感信息，仅用于渲染昵称/角色与路由守卫）。
 *
 * 凭证本体在 httpOnly cookie 里，JS 无法读写——这是 M5 的安全目标。
 * localStorage 里的 user 只是"展示层缓存"，被篡改也不会越权：真正的鉴权在服务端。
 */
function readCachedUser() {
  try {
    const parsed = JSON.parse(localStorage.getItem(USER_KEY) || 'null')
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch (e) {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: readCachedUser()
  }),
  getters: {
    // 有用户画像即视为"已登录"；cookie 若已过期，后端 401 会由拦截器清理并跳转登录
    isLoggedIn: (s) => !!s.user,
    isAdmin: (s) => !!s.user?.is_admin
  },
  actions: {
    async login(account, password) {
      const data = await loginApi(account, password)
      this.user = data.user
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    },
    async logout() {
      this.user = null
      localStorage.removeItem(USER_KEY)
      // 凭证在 httpOnly cookie，删除只能交给后端；失败静默（本地状态已清）
      try {
        await logoutApi()
      } catch (e) {
        /* 忽略 */
      }
    }
  }
})

<template>
  <div class="auth-form">
    <p class="xw-eyebrow">ACCOUNT</p>
    <h1 class="auth-title">登录</h1>
    <p class="auth-lede">
      用邮箱或手机号登录。登录后，游客购物车里的商品会自动并进来。
    </p>

    <form class="form" novalidate @submit.prevent="doLogin">
      <div class="xw-field">
        <label for="account">邮箱 / 手机号</label>
        <input
          id="account"
          v-model.trim="account"
          class="xw-input"
          :class="{ 'is-error': errors.account }"
          type="text"
          autocomplete="username"
          placeholder="buyer@example.com"
          autofocus
          @input="errors.account = ''"
        />
        <span v-if="errors.account" class="xw-field-error">{{ errors.account }}</span>
      </div>

      <div class="xw-field">
        <label for="password">密码</label>
        <div class="xw-input-wrap">
          <input
            id="password"
            v-model="password"
            class="xw-input"
            :class="{ 'is-error': errors.password }"
            :type="showPwd ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
            @input="errors.password = ''"
          />
          <button
            class="xw-input-action"
            type="button"
            :aria-label="showPwd ? '隐藏密码' : '显示密码'"
            @click="showPwd = !showPwd"
          >
            <LineIcon :name="showPwd ? 'eye-off' : 'eye'" :size="16" />
          </button>
        </div>
        <span v-if="errors.password" class="xw-field-error">{{ errors.password }}</span>
      </div>

      <button class="xw-btn xw-btn--block xw-btn--lg submit" type="submit" :disabled="loading">
        {{ loading ? '正在登录…' : '登录' }}
      </button>
    </form>

    <p class="switch">
      还没有账号？<RouterLink to="/register">注册一个</RouterLink>
    </p>

    <RouterLink to="/" class="back">
      <LineIcon name="arrow-left" :size="13" />
      返回首页
    </RouterLink>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import LineIcon from '@/components/store/LineIcon.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const account = ref('')
const password = ref('')
const loading = ref(false)
const showPwd = ref(false)
const errors = reactive({ account: '', password: '' })

async function doLogin() {
  errors.account = account.value ? '' : '请输入邮箱或手机号'
  errors.password = password.value ? '' : '请输入密码'
  if (errors.account || errors.password) return

  loading.value = true
  try {
    await userStore.login(account.value, password.value)
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (e) {
    // 具体原因（账号锁定 / 密码错误）由请求拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-title {
  margin: 14px 0 10px;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 500;
  letter-spacing: -0.035em;
  line-height: 1.1;
}

.auth-lede {
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--xw-muted);
  max-width: 330px;
}

.form {
  display: grid;
  gap: 18px;
  margin: 34px 0 22px;
}

.submit {
  margin-top: 6px;
}

.switch {
  font-size: 12.5px;
  color: var(--xw-muted);
}

.switch a {
  color: var(--xw-ink);
  border-bottom: 1px solid var(--xw-line-ink);
  padding-bottom: 1px;
  margin-left: 4px;
}

.switch a:hover {
  color: var(--xw-accent);
  border-color: var(--xw-accent);
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 30px;
  font-size: 11.5px;
  color: var(--xw-muted);
}

.back:hover {
  color: var(--xw-ink);
}
</style>

<template>
  <div class="auth-form">
    <p class="xw-eyebrow">CREATE ACCOUNT</p>
    <h1 class="auth-title">注册</h1>
    <p class="auth-lede">
      创建账号后即可加购下单。邮箱用于登录，手机号只用于配送联系。
    </p>

    <form class="form" novalidate @submit.prevent="doRegister">
      <div class="xw-field">
        <label for="email">邮箱<span class="req">*</span></label>
        <input
          id="email"
          v-model.trim="form.email"
          class="xw-input"
          :class="{ 'is-error': errors.email }"
          type="email"
          autocomplete="email"
          placeholder="you@example.com"
          @input="errors.email = ''"
        />
        <span v-if="errors.email" class="xw-field-error">{{ errors.email }}</span>
      </div>

      <div class="xw-modal-grid">
        <div class="xw-field">
          <label for="phone">手机号<span class="hint">（选填）</span></label>
          <input
            id="phone"
            v-model.trim="form.phone"
            class="xw-input"
            :class="{ 'is-error': errors.phone }"
            type="tel"
            inputmode="numeric"
            maxlength="11"
            placeholder="13800138000"
            @input="onPhoneInput"
          />
          <span v-if="errors.phone" class="xw-field-error">{{ errors.phone }}</span>
        </div>

        <div class="xw-field">
          <label for="nickname">昵称<span class="hint">（选填）</span></label>
          <input
            id="nickname"
            v-model.trim="form.nickname"
            class="xw-input"
            type="text"
            maxlength="20"
            placeholder="默认取邮箱前缀"
          />
        </div>
      </div>

      <div class="xw-field">
        <label for="password">密码<span class="req">*</span></label>
        <div class="xw-input-wrap">
          <input
            id="password"
            v-model="form.password"
            class="xw-input"
            :class="{ 'is-error': errors.password }"
            :type="showPwd ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="8-64 位，需包含字母和数字"
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
        <span v-else class="xw-field-hint">8-64 位，至少包含一个字母和一个数字</span>
      </div>

      <button class="xw-btn xw-btn--block xw-btn--lg submit" type="submit" :disabled="loading">
        {{ loading ? '正在创建…' : '创建账号' }}
      </button>
    </form>

    <p class="switch">
      已经有账号了？<RouterLink to="/login">直接登录</RouterLink>
    </p>

    <RouterLink to="/" class="back">
      <LineIcon name="arrow-left" :size="13" />
      返回首页
    </RouterLink>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api'
import LineIcon from '@/components/store/LineIcon.vue'

const router = useRouter()
const loading = ref(false)
const showPwd = ref(false)
const form = reactive({ email: '', phone: '', nickname: '', password: '' })
const errors = reactive({ email: '', phone: '', password: '' })

function onPhoneInput() {
  // 只保留数字，避免粘贴带字母/空格的号码
  form.phone = form.phone.replace(/\D/g, '')
  errors.phone = ''
}

function validate() {
  errors.email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
    ? ''
    : '请输入有效的邮箱地址'
  errors.phone = !form.phone || /^1[3-9]\d{9}$/.test(form.phone)
    ? ''
    : '请输入 11 位手机号'
  const strong = form.password.length >= 8 && form.password.length <= 64
  const mixed = /[A-Za-z]/.test(form.password) && /\d/.test(form.password)
  errors.password = strong && mixed ? '' : '密码需 8-64 位，且包含字母和数字'
  return !errors.email && !errors.phone && !errors.password
}

async function doRegister() {
  if (!validate()) return
  loading.value = true
  try {
    await register({
      email: form.email,
      phone: form.phone || null,
      nickname: form.nickname || null,
      password: form.password
    })
    ElMessage.success('注册成功，请登录')
    router.push({ path: '/login', query: { redirect: '/' } })
  } catch (e) {
    // 邮箱/手机号重复等错误由拦截器提示
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
  gap: 16px;
  margin: 30px 0 22px;
}

.hint {
  color: var(--xw-muted);
  font-size: 10.5px;
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

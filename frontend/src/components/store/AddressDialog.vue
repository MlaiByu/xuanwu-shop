<template>
  <Teleport to="body">
    <div v-if="open" class="xw-modal-mask" @click.self="close">
      <div class="xw-modal" role="dialog" aria-modal="true" :aria-label="address ? '编辑收货地址' : '新增收货地址'">
        <header class="xw-modal-head">
          <h3>{{ address ? '编辑收货地址' : '新增收货地址' }}</h3>
          <button class="xw-icon-btn" type="button" aria-label="关闭" @click="close">
            <LineIcon name="close" :size="18" />
          </button>
        </header>

        <form id="address-form" class="xw-modal-body" novalidate @submit.prevent="save">
          <div class="xw-modal-grid">
            <div class="xw-field">
              <label for="receiver">收货人<span class="req">*</span></label>
              <input
                id="receiver"
                v-model.trim="form.receiver"
                class="xw-input"
                :class="{ 'is-error': errors.receiver }"
                maxlength="20"
                placeholder="姓名"
                @input="errors.receiver = ''"
              />
              <span v-if="errors.receiver" class="xw-field-error">{{ errors.receiver }}</span>
            </div>

            <div class="xw-field">
              <label for="phone">手机号<span class="req">*</span></label>
              <input
                id="phone"
                v-model.trim="form.phone"
                class="xw-input"
                :class="{ 'is-error': errors.phone }"
                inputmode="numeric"
                maxlength="11"
                placeholder="13800138000"
                @input="onPhoneInput"
              />
              <span v-if="errors.phone" class="xw-field-error">{{ errors.phone }}</span>
            </div>
          </div>

          <div class="xw-field">
            <label>省 / 市 / 区<span class="req">*</span></label>
            <div class="region">
              <input
                v-model.trim="form.province"
                class="xw-input"
                :class="{ 'is-error': errors.region }"
                maxlength="50"
                placeholder="省"
                aria-label="省"
                @input="errors.region = ''"
              />
              <input
                v-model.trim="form.city"
                class="xw-input"
                :class="{ 'is-error': errors.region }"
                maxlength="50"
                placeholder="市"
                aria-label="市"
                @input="errors.region = ''"
              />
              <input
                v-model.trim="form.district"
                class="xw-input"
                :class="{ 'is-error': errors.region }"
                maxlength="50"
                placeholder="区"
                aria-label="区"
                @input="errors.region = ''"
              />
            </div>
            <span v-if="errors.region" class="xw-field-error">{{ errors.region }}</span>
          </div>

          <div class="xw-field">
            <label for="detail">详细地址<span class="req">*</span></label>
            <textarea
              id="detail"
              v-model.trim="form.detail"
              class="xw-input xw-textarea"
              :class="{ 'is-error': errors.detail }"
              maxlength="200"
              placeholder="街道、门牌号、楼层与房间号，5 字以上"
              @input="errors.detail = ''"
            ></textarea>
            <span v-if="errors.detail" class="xw-field-error">{{ errors.detail }}</span>
          </div>

          <button class="default-row" type="button" @click="form.is_default = !form.is_default">
            <span class="xw-check" :class="{ 'is-checked': form.is_default }">
              <LineIcon name="check" :size="12" />
            </span>
            <span>设为默认收货地址</span>
          </button>
        </form>

        <footer class="xw-modal-foot">
          <button class="xw-btn xw-btn--ghost" type="button" @click="close">取消</button>
          <button class="xw-btn" type="submit" form="address-form" :disabled="submitting">
            {{ submitting ? '保存中…' : '保存地址' }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { createAddress, updateAddress } from '@/api'
import LineIcon from './LineIcon.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  address: { type: Object, default: null }
})
const emit = defineEmits(['update:open', 'saved'])

const submitting = ref(false)
const form = reactive({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_default: false
})
const errors = reactive({ receiver: '', phone: '', region: '', detail: '' })

function reset() {
  const source = props.address || {}
  form.receiver = source.receiver || ''
  form.phone = source.phone || ''
  form.province = source.province || ''
  form.city = source.city || ''
  form.district = source.district || ''
  form.detail = source.detail || ''
  form.is_default = !!source.is_default
  Object.keys(errors).forEach((key) => {
    errors[key] = ''
  })
}

function onPhoneInput() {
  // 只保留数字，避免粘贴带字母/空格的号码
  form.phone = form.phone.replace(/\D/g, '')
  errors.phone = ''
}

function validatePhone(value) {
  if (!value) return '请填写手机号'
  // 先判长度，再判号段，避免"11 位却提示不是 11 位"的误导
  if (!/^\d{11}$/.test(value)) return '请填写 11 位手机号'
  if (!/^1[3-9]\d{9}$/.test(value)) return '手机号格式不正确'
  return ''
}

function validate() {
  errors.receiver = form.receiver ? '' : '请填写收货人'
  errors.phone = validatePhone(form.phone)
  errors.region =
    form.province && form.city && form.district ? '' : '请填写完整的省、市、区'
  errors.detail =
    form.detail.length >= 5 && form.detail.length <= 200
      ? ''
      : '详细地址需 5-200 字'
  return !errors.receiver && !errors.phone && !errors.region && !errors.detail
}

function close() {
  emit('update:open', false)
}

async function save() {
  if (!validate()) return
  submitting.value = true
  try {
    const payload = {
      receiver: form.receiver,
      phone: form.phone,
      province: form.province,
      city: form.city,
      district: form.district,
      detail: form.detail,
      is_default: form.is_default
    }
    const saved = props.address
      ? await updateAddress(props.address.id, payload)
      : await createAddress(payload)
    ElMessage.success(props.address ? '地址已更新' : '地址已添加')
    emit('saved', saved)
    close()
  } catch (e) {
    // 校验失败 / 权限错误由拦截器提示
  } finally {
    submitting.value = false
  }
}

function onKeydown(event) {
  if (event.key === 'Escape' && props.open) close()
}

watch(
  () => props.open,
  (value) => {
    document.body.style.overflow = value ? 'hidden' : ''
    if (value) {
      reset()
      window.addEventListener('keydown', onKeydown)
    } else {
      window.removeEventListener('keydown', onKeydown)
    }
  }
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.region {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.default-row {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  border: 0;
  background: none;
  padding: 0;
  font-size: 12.5px;
  color: var(--xw-ink-soft);
  cursor: pointer;
}

.default-row .xw-check {
  pointer-events: none;
}
</style>

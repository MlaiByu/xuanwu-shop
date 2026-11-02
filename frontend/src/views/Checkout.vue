<template>
  <div class="xw-shell">
    <header class="xw-page-head">
      <div>
        <p class="xw-eyebrow">CHECKOUT</p>
        <h1>确认订单</h1>
        <p v-if="preview.items.length" class="xw-meta checkout-sub">
          共 {{ preview.total_quantity }} 件 · 48 小时内发出 · 支付后可在订单里查看物流
        </p>
      </div>
      <RouterLink class="xw-text-btn back-link" to="/cart">
        <LineIcon name="arrow-left" :size="13" /> 返回购物车
      </RouterLink>
    </header>

    <div v-if="loading" class="checkout">
      <div class="panel-stack">
        <div class="xw-panel skeleton-block"></div>
        <div class="xw-panel skeleton-block tall"></div>
      </div>
      <div class="xw-panel skeleton-block"></div>
    </div>

    <div v-else-if="!preview.items.length" class="xw-empty">
      <h3>没有待结算的商品</h3>
      <p>回到购物车勾选商品后再来结算。</p>
      <RouterLink class="xw-btn" to="/cart">返回购物车</RouterLink>
    </div>

    <div v-else class="checkout">
      <div class="panel-stack">
        <section class="xw-panel">
          <header class="xw-panel-head">
            <h2>收货地址</h2>
            <button class="xw-text-btn" type="button" @click="openAddressDialog">
              新增地址
            </button>
          </header>

          <div v-if="addresses.length" class="addr-list">
            <button
              v-for="item in addresses"
              :key="item.id"
              type="button"
              class="addr-option"
              :class="{ active: addressId === item.id }"
              :aria-pressed="addressId === item.id"
              @click="addressId = item.id"
            >
              <div class="addr-line">
                <strong>{{ item.receiver }}</strong>
                <span>{{ maskPhone(item.phone) }}</span>
                <span v-if="item.is_default" class="xw-status xw-status--ok">默认</span>
              </div>
              <p>{{ item.province }}{{ item.city }}{{ item.district }}{{ item.detail }}</p>
              <span v-if="addressId === item.id" class="addr-picked">
                <LineIcon name="check" :size="11" /> 已选择
              </span>
            </button>
          </div>

          <div v-else class="addr-empty">
            还没有收货地址，
            <button class="xw-text-btn" type="button" @click="openAddressDialog">
              先添加一个
            </button>
          </div>
        </section>

        <section class="xw-panel">
          <header class="xw-panel-head">
            <h2>商品清单</h2>
            <span class="xw-meta">{{ preview.total_quantity }} 件</span>
          </header>

          <ul class="co-items">
            <li v-for="item in preview.items" :key="item.cart_item_id">
              <div class="co-media">
                <ProductMedia
                  :src="item.main_image"
                  :name="item.product_name"
                  ratio="1 / 1"
                />
              </div>
              <div class="co-info">
                <span class="co-name">{{ item.product_name }}</span>
                <span class="co-attrs">
                  {{ Object.values(item.sku_attrs || {}).join(' / ') || '默认规格' }}
                  <em class="co-qty-inline">×{{ item.quantity }}</em>
                </span>
                <span v-if="!item.is_valid" class="xw-status xw-status--warn">
                  已失效，无法结算
                </span>
              </div>
              <span class="co-qty">×{{ item.quantity }}</span>
              <PriceText :value="item.subtotal" size="sm" />
            </li>
          </ul>

          <div class="co-remark">
            <label for="remark">订单备注<span class="xw-field-hint">（选填）</span></label>
            <input
              id="remark"
              v-model.trim="remark"
              class="xw-input"
              maxlength="200"
              placeholder="例如：工作日送达，放前台即可"
            />
            <span class="xw-field-hint">{{ remark.length }} / 200</span>
          </div>
        </section>
      </div>

      <aside class="summary">
        <h2>订单摘要</h2>

        <dl class="sum-lines">
          <div>
            <dt>商品金额</dt>
            <dd>{{ formatPrice(preview.total_amount) }}</dd>
          </div>
          <div>
            <dt>运费</dt>
            <dd>{{ Number(preview.freight) > 0 ? formatPrice(preview.freight) : '包邮' }}</dd>
          </div>
          <div>
            <dt>应付合计</dt>
            <dd class="sum-strong">
              <PriceText :value="payable " size="lg" />
            </dd>
          </div>
        </dl>

        <p v-if="hasInvalid" class="sum-warn">
          有 {{ invalidCount }} 件商品已失效，请返回购物车移除后再结算。
        </p>

        <button
          class="xw-btn xw-btn--block xw-btn--lg"
          type="button"
          :disabled="submitting || !canSubmit"
          @click="submitOrder"
        >
          {{ submitting ? '正在提交…' : '提交订单并支付' }}
        </button>

        <p class="sum-note">
          点击即表示同意《玄武商城交易条款》<br />
          支付方式：微信支付 / 支付宝（演示环境直接完成支付）
        </p>
      </aside>
    </div>

    <AddressDialog v-model:open="addressOpen" :address="null" @saved="onAddressSaved" />

    <div v-if="preview.items.length && !loading" class="mobile-submit">
      <div class="mobile-submit-total">
        <span>应付</span>
        <PriceText :value="payable" size="md" />
      </div>
      <button
        class="xw-btn"
        type="button"
        :disabled="submitting || !canSubmit"
        @click="submitOrder"
      >
        {{ submitting ? '提交中…' : `提交订单（${preview.total_quantity}）` }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createOrder, getAddresses, getCheckout, payOrder } from '@/api'
import { formatPrice } from '@/utils/format'
import { useCartStore } from '@/store/cart'
import ProductMedia from '@/components/store/ProductMedia.vue'
import PriceText from '@/components/store/PriceText.vue'
import LineIcon from '@/components/store/LineIcon.vue'
import AddressDialog from '@/components/store/AddressDialog.vue'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const loading = ref(true)
const submitting = ref(false)
const addresses = ref([])
const addressId = ref(null)
const addressOpen = ref(false)
const remark = ref('')
const preview = reactive({
  items: [],
  total_quantity: 0,
  total_amount: '0.00',
  freight: '0.00'
})

const ids = computed(() =>
  String(route.query.cart_item_ids || '')
    .split(',')
    .map(Number)
    .filter(Boolean)
)

const payable = computed(() => {
  const amount = Math.round(Number(preview.total_amount || 0) * 100)
  const freight = Math.round(Number(preview.freight || 0) * 100)
  return (amount + freight) / 100
})

const hasInvalid = computed(() => preview.items.some((item) => !item.is_valid))
const invalidCount = computed(() => preview.items.filter((item) => !item.is_valid).length)
const canSubmit = computed(() => !!addressId.value && !hasInvalid.value)

function maskPhone(phone) {
  return String(phone || '').replace(/^(\d{3})\d{4}(\d{4})$/, '$1****$2')
}

function openAddressDialog() {
  addressOpen.value = true
}

function onAddressSaved(saved) {
  getAddresses()
    .then((list) => {
      addresses.value = list
      if (saved?.id) addressId.value = saved.id
    })
    .catch(() => {})
}

async function load() {
  loading.value = true
  try {
    const data = await getCheckout(ids.value.join(','))
    Object.assign(preview, data, {
      items: data.items || [],
      total_quantity: data.total_quantity || 0,
      total_amount: data.total_amount || '0.00',
      freight: data.freight || '0.00'
    })
    addresses.value = await getAddresses()
    const preferred =
      addresses.value.find((item) => item.is_default) || addresses.value[0] || null
    addressId.value = preferred ? preferred.id : null
  } catch (e) {
    preview.items = []
  } finally {
    loading.value = false
  }
}

/**
 * 幂等键在整个结算页生命周期内保持不变，提交成功后才轮换。
 *
 * 不能在 submitOrder 里现生成：那样每次重试都是新 key，后端
 * ON CONFLICT 原子占位拿不到重复，超时重试会真的下两单、扣两次库存。
 *
 * crypto.randomUUID 只在安全上下文（HTTPS / localhost）可用，
 * 用 http://IP 打开时它是 undefined，必须降级，否则订单提交直接抛 TypeError。
 */
function newIdemKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

let idemKey = newIdemKey()

async function submitOrder() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    const order = await createOrder(
      {
        address_id: addressId.value,
        cart_item_ids: preview.items.map((item) => item.cart_item_id),
        remark: remark.value || null
      },
      idemKey
    )
    // 下单成功才换 key，失败重试沿用旧 key 由后端幂等返回首次结果
    idemKey = newIdemKey()
    await payOrder(order.id)
    await cartStore.load()
    ElMessage.success('支付成功，订单已创建')
    router.replace(`/orders/${order.id}`)
  } catch (e) {
    // 有 response 说明是后端业务错误，拦截器已经提示过；这里只兜本地异常
    if (!e?.response) ElMessage.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.checkout-sub {
  margin-top: 8px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.checkout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 36px;
  align-items: start;
}

.panel-stack {
  display: grid;
  gap: 16px;
}

/* ---------- 地址 ---------- */
.addr-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 18px;
  max-height: 268px;
  overflow-y: auto;
}

.addr-option {
  position: relative;
  padding: 14px 15px;
  border: 1px solid var(--xw-line);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.16s, background 0.16s;
}

.addr-option:hover {
  border-color: var(--xw-line-ink);
}

.addr-option.active {
  border-color: var(--xw-ink);
  background: rgba(26, 22, 17, 0.025);
}

.addr-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.addr-line strong {
  font-size: 12.5px;
  font-weight: 600;
}

.addr-line span {
  font-size: 11.5px;
  color: var(--xw-muted);
  font-variant-numeric: tabular-nums;
}

.addr-line .xw-status {
  margin-left: auto;
}

.addr-option p {
  margin-top: 8px;
  font-size: 11.5px;
  line-height: 1.65;
  color: var(--xw-ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.addr-option.active p {
  padding-right: 54px;
}

.addr-picked {
  position: absolute;
  right: 12px;
  bottom: 10px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  letter-spacing: 0.04em;
  color: var(--xw-ink);
}

.addr-empty {
  padding: 26px 20px;
  font-size: 12.5px;
  color: var(--xw-muted);
}

/* ---------- 商品 ---------- */
.co-items li {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 54px 88px;
  align-items: center;
  gap: 14px;
  padding: 15px 20px;
  border-bottom: 1px solid var(--xw-line);
}

.co-items li:last-child {
  border-bottom: 0;
}

.co-media {
  width: 64px;
}

.co-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.co-name {
  font-size: 13px;
  color: var(--xw-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.co-attrs {
  font-size: 11px;
  color: var(--xw-muted);
}

.co-qty-inline {
  display: none;
  margin-left: 6px;
  font-style: normal;
  color: var(--xw-ink-soft);
}

.co-qty {
  font-size: 12px;
  color: var(--xw-muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.co-items li :deep(.xw-price) {
  text-align: right;
}

.co-remark {
  display: grid;
  gap: 7px;
  padding: 16px 20px 20px;
  border-top: 1px solid var(--xw-line);
}

.co-remark label {
  font-size: 11.5px;
  letter-spacing: 0.04em;
  color: var(--xw-muted);
}

.co-remark .xw-field-hint {
  justify-self: end;
}

/* ---------- 摘要 ---------- */
.summary {
  position: sticky;
  top: calc(var(--xw-header-h) + 20px);
  padding: 22px;
  background: var(--xw-surface);
  border: 1px solid var(--xw-line);
}

.summary h2 {
  padding-bottom: 14px;
  border-bottom: 1px solid var(--xw-line);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
}

.sum-lines {
  display: grid;
  gap: 13px;
  padding: 18px 0;
}

.sum-lines div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
}

.sum-lines dt {
  color: var(--xw-muted);
}

.sum-lines dd {
  color: var(--xw-ink);
  font-variant-numeric: tabular-nums;
}

.sum-lines div:last-child {
  padding-top: 12px;
  border-top: 1px solid var(--xw-line);
}

.sum-strong :deep(.xw-price) {
  font-size: 24px;
}

.sum-warn {
  margin-bottom: 14px;
  padding: 9px 11px;
  border: 1px solid rgba(180, 67, 43, 0.28);
  background: rgba(180, 67, 43, 0.05);
  font-size: 11px;
  line-height: 1.65;
  color: var(--xw-accent);
}

.sum-note {
  margin-top: 14px;
  font-size: 10.5px;
  line-height: 1.75;
  color: var(--xw-muted);
}

.skeleton-block {
  min-height: 160px;
  background: linear-gradient(100deg, #eae3d4 18%, #f6f1e7 38%, #eae3d4 58%);
  background-size: 220% 100%;
  animation: xw-shimmer 1.35s linear infinite;
}

.skeleton-block.tall {
  min-height: 320px;
}

.mobile-submit {
  display: none;
}

@media (max-width: 1080px) {
  .checkout {
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 24px;
  }
}

@media (max-width: 900px) {
  .checkout {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .addr-list {
    grid-template-columns: 1fr;
    max-height: none;
    padding: 14px;
  }
  .co-items li {
    grid-template-columns: 56px minmax(0, 1fr) 72px;
    gap: 11px;
    padding: 14px;
  }
  .co-media {
    width: 56px;
  }
  .co-qty {
    display: none;
  }
  .co-remark {
    padding: 14px;
  }
  .summary {
    position: static;
    padding: 18px;
  }
  .summary .xw-btn {
    display: none;
  }
  .co-qty-inline {
    display: inline;
  }
  .checkout {
    padding-bottom: 82px;
  }
  .mobile-submit {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 55;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 10px var(--xw-gutter) calc(10px + env(safe-area-inset-bottom));
    background: rgba(255, 253, 248, 0.96);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--xw-line);
  }
  .mobile-submit-total {
    display: flex;
    align-items: baseline;
    gap: 6px;
  }
  .mobile-submit-total span {
    font-size: 10.5px;
    color: var(--xw-muted);
  }
  .mobile-submit .xw-btn {
    height: 44px;
    padding: 0 20px;
    font-size: 12.5px;
  }
}
</style>

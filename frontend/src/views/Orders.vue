<template>
  <div class="xw-shell">
    <header class="xw-page-head">
      <div>
        <p class="xw-eyebrow">ACCOUNT · ORDERS</p>
        <h1>我的订单</h1>
        <p class="xw-meta orders-sub">支付后 48 小时内发出，发货后可在这里确认收货</p>
      </div>
      <RouterLink class="xw-btn xw-btn--ghost" to="/addresses">收货地址</RouterLink>
    </header>

    <nav class="xw-tabs" aria-label="订单状态">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        :class="{ active: activeTab === tab.value }"
        @click="changeTab(tab.value)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <div v-if="loading" class="order-list">
      <div v-for="n in 3" :key="n" class="xw-panel order-skel">
        <div class="xw-skel xw-skel--text" style="width: 30%"></div>
        <div class="xw-skel xw-skel--text" style="width: 55%; height: 60px"></div>
      </div>
    </div>

    <div v-else-if="!orders.length" class="xw-empty orders-empty">
      <h3>这里还没有订单</h3>
      <p>挑点东西试试，满 ¥199 顺丰包邮。</p>
      <RouterLink class="xw-btn" to="/products">去逛逛</RouterLink>
    </div>

    <ul v-else class="order-list">
      <li v-for="order in orders" :key="order.id" class="xw-panel order">
        <header class="order-head">
          <span class="order-no">订单号 {{ order.order_no }}</span>
          <span class="order-time">{{ formatTime(order.created_at) }}</span>
          <span class="xw-status" :class="statusClass(order.status)">
            {{ statusLabel(order.status) }}
          </span>
        </header>

        <div class="order-body">
          <RouterLink :to="`/orders/${order.id}`" class="order-media">
            <ProductMedia
              :src="order.preview_image"
              :name="order.preview_name || '订单商品'"
              ratio="1 / 1"
            />
          </RouterLink>

          <div class="order-info">
            <RouterLink :to="`/orders/${order.id}`" class="order-name">
              {{ order.preview_name || '订单商品' }}
            </RouterLink>
            <span class="xw-meta">共 {{ order.total_quantity }} 件</span>
          </div>

          <div class="order-amount">
            <span class="xw-meta">实付</span>
            <PriceText :value="order.total_amount" size="md" />
          </div>

          <div class="order-actions">
            <template v-if="order.status === 'pending'">
              <button class="xw-btn order-btn" type="button" @click="pay(order)">去支付</button>
              <button class="xw-text-btn" type="button" @click="cancel(order)">取消</button>
            </template>
            <template v-else-if="order.status === 'shipped'">
              <button class="xw-btn order-btn" type="button" @click="confirm(order)">
                确认收货
              </button>
            </template>
            <RouterLink class="xw-text-btn" :to="`/orders/${order.id}`">订单详情</RouterLink>
          </div>
        </div>
      </li>
    </ul>

    <nav v-if="pages > 1" class="xw-pager" aria-label="分页">
      <button
        class="xw-pager-btn"
        type="button"
        :disabled="page <= 1"
        @click="goPage(page - 1)"
      >
        <LineIcon name="arrow-left" :size="14" /> 上一页
      </button>
      <div class="xw-pager-nums">
        <button
          v-for="p in pageList"
          :key="p"
          type="button"
          class="xw-pager-num"
          :class="{ active: p === page }"
          @click="goPage(p)"
        >
          {{ p }}
        </button>
      </div>
      <button
        class="xw-pager-btn"
        type="button"
        :disabled="page >= pages"
        @click="goPage(page + 1)"
      >
        下一页 <LineIcon name="arrow-right" :size="14" />
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelOrder, confirmOrder, getOrders, payOrder } from '@/api'
import ProductMedia from '@/components/store/ProductMedia.vue'
import PriceText from '@/components/store/PriceText.vue'
import LineIcon from '@/components/store/LineIcon.vue'

const tabs = [
  { label: '全部', value: 'all' },
  { label: '待支付', value: 'pending' },
  { label: '待发货', value: 'paid' },
  { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' }
]

const activeTab = ref('all')
const orders = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const loading = ref(true)

const pages = computed(() => Math.max(1, Math.ceil(total.value / size)))
const pageList = computed(() => {
  const start = Math.max(1, Math.min(page.value - 2, pages.value - 4))
  const list = []
  for (let i = start; i < start + 5 && i <= pages.value; i += 1) list.push(i)
  return list
})

const LABELS = {
  pending: '待支付',
  paid: '待发货',
  shipped: '待收货',
  completed: '已完成',
  cancelled: '已取消'
}

function statusLabel(status) {
  return LABELS[status] || status
}

function statusClass(status) {
  if (status === 'pending') return 'xw-status--warn'
  if (status === 'completed') return 'xw-status--ok'
  if (status === 'cancelled') return 'xw-status--muted'
  return ''
}

function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    const data = await getOrders({ status: activeTab.value, page: page.value, size })
    orders.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function changeTab(value) {
  activeTab.value = value
  page.value = 1
  load()
}

function goPage(next) {
  if (next < 1 || next > pages.value) return
  page.value = next
  load()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function pay(order) {
  try {
    await payOrder(order.id)
    ElMessage.success('支付成功')
    load()
  } catch (e) {
    /* 状态冲突等由拦截器提示 */
  }
}

async function cancel(order) {
  try {
    await ElMessageBox.confirm('取消后库存会释放，订单不可恢复。', '取消订单', {
      confirmButtonText: '取消订单',
      cancelButtonText: '保留订单',
      type: 'warning'
    })
  } catch (e) {
    return
  }
  try {
    await cancelOrder(order.id)
    ElMessage.success('订单已取消')
    load()
  } catch (e) {
    /* 同上 */
  }
}

async function confirm(order) {
  try {
    await ElMessageBox.confirm('确认已经收到商品？', '确认收货', {
      confirmButtonText: '确认收货',
      cancelButtonText: '还没收到'
    })
  } catch (e) {
    return
  }
  try {
    await confirmOrder(order.id)
    ElMessage.success('交易完成')
    load()
  } catch (e) {
    /* 同上 */
  }
}

onMounted(load)
</script>

<style scoped>
.orders-sub {
  margin-top: 8px;
}

.order-list {
  display: grid;
  gap: 14px;
  margin-top: 22px;
}

.order {
  padding: 0;
}

.order-head {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--xw-line);
  background: rgba(26, 22, 17, 0.015);
}

.order-no {
  font-size: 11.5px;
  letter-spacing: 0.02em;
  color: var(--xw-ink-soft);
  font-variant-numeric: tabular-nums;
}

.order-time {
  font-size: 11px;
  color: var(--xw-muted);
}

.order-head .xw-status {
  margin-left: auto;
}

.order-body {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr) 120px 200px;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
}

.order-media {
  width: 68px;
}

.order-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.order-name {
  font-size: 13.5px;
  color: var(--xw-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.order-name:hover {
  color: var(--xw-accent);
}

.order-amount {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
}

.order-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
}

.order-btn {
  height: 34px;
  padding: 0 16px;
  font-size: 12px;
}

.order-skel {
  display: grid;
  gap: 12px;
  padding: 18px 20px;
}

.orders-empty {
  margin-top: 22px;
}

@media (max-width: 900px) {
  .order-head {
    flex-wrap: wrap;
    gap: 8px 12px;
    padding: 12px 14px;
  }
  .order-head .xw-status {
    margin-left: 0;
  }
  .order-time {
    margin-left: auto;
  }
  .order-body {
    grid-template-columns: 58px minmax(0, 1fr) auto;
    grid-template-areas:
      "media info amount"
      "actions actions actions";
    gap: 12px;
    padding: 14px;
  }
  .order-media {
    grid-area: media;
    width: 58px;
  }
  .order-info {
    grid-area: info;
  }
  .order-amount {
    grid-area: amount;
  }
  .order-actions {
    grid-area: actions;
    justify-content: flex-end;
    padding-top: 10px;
    border-top: 1px solid var(--xw-line);
  }
  .order-list {
    margin-top: 16px;
  }
}
</style>

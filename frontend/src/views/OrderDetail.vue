<template>
  <div class="xw-shell">
    <nav class="crumb" aria-label="面包屑">
      <RouterLink to="/orders">我的订单</RouterLink>
      <span>/</span>
      <span class="current">订单详情</span>
    </nav>

    <div v-if="loading" class="xw-panel detail-skel"></div>

    <div v-else-if="!order" class="xw-empty">
      <h3>订单不存在</h3>
      <p>它可能已被删除，或者不属于当前账号。</p>
      <RouterLink class="xw-btn" to="/orders">回到我的订单</RouterLink>
    </div>

    <template v-else>
      <header class="status-hero">
        <div class="hero-copy">
          <p class="xw-eyebrow">ORDER · {{ order.order_no }}</p>
          <h1>{{ statusTitle }}</h1>
          <p class="hero-desc">{{ statusDesc }}</p>
        </div>
        <div class="hero-side">
          <PriceText :value="order.total_amount" size="xl" />
          <div class="hero-actions">
            <template v-if="order.status === 'pending'">
              <button class="xw-btn" type="button" @click="pay">去支付</button>
              <button class="xw-btn xw-btn--ghost" type="button" @click="cancel">取消订单</button>
            </template>
            <template v-else-if="order.status === 'shipped'">
              <button class="xw-btn" type="button" @click="confirm">确认收货</button>
            </template>
            <RouterLink class="xw-btn xw-btn--ghost" to="/products">继续购物</RouterLink>
          </div>
        </div>
      </header>

      <div class="detail-grid">
        <div class="col-main">
          <section class="xw-panel">
            <header class="xw-panel-head">
              <h2>商品明细</h2>
              <span class="xw-meta">{{ totalQuantity }} 件</span>
            </header>
            <ul class="item-list">
              <li v-for="item in order.items" :key="item.id">
                <div class="item-media">
                  <ProductMedia
                    :src="item.main_image"
                    :name="item.product_name"
                    ratio="1 / 1"
                  />
                </div>
                <div class="item-info">
                  <span class="item-name">{{ item.product_name }}</span>
                  <span class="item-attrs">{{
                    Object.values(item.sku_attrs || {}).join(' / ') || '默认规格'
                  }}</span>
                </div>
                <span class="item-price">
                  {{ formatPrice(item.price) }} × {{ item.quantity }}
                </span>
                <PriceText :value="item.subtotal" size="sm" />
              </li>
            </ul>
            <footer class="item-total">
              <span>商品金额</span>
              <PriceText :value="order.total_amount" size="lg" />
            </footer>
          </section>

          <section class="xw-panel">
            <header class="xw-panel-head">
              <h2>收货信息</h2>
              <span class="xw-status">下单时快照</span>
            </header>
            <div class="addr-block">
              <p class="addr-person">
                {{ order.address_snapshot.receiver }}
                <span>{{ order.address_snapshot.phone }}</span>
              </p>
              <p class="addr-detail">
                {{ order.address_snapshot.province }}{{ order.address_snapshot.city
                }}{{ order.address_snapshot.district }}{{ order.address_snapshot.detail }}
              </p>
              <p v-if="order.remark" class="addr-remark">备注：{{ order.remark }}</p>
            </div>
          </section>
        </div>

        <aside class="col-side">
          <section class="xw-panel">
            <header class="xw-panel-head"><h2>订单信息</h2></header>
            <dl class="info-lines">
              <div>
                <dt>订单号</dt>
                <dd class="mono">{{ order.order_no }}</dd>
              </div>
              <div>
                <dt>下单时间</dt>
                <dd>{{ formatTime(order.created_at) }}</dd>
              </div>
              <div>
                <dt>订单状态</dt>
                <dd>{{ statusLabel }}</dd>
              </div>
              <div>
                <dt>实付金额</dt>
                <dd>{{ formatPrice(order.total_amount) }}</dd>
              </div>
            </dl>
          </section>

          <section class="xw-panel">
            <header class="xw-panel-head"><h2>订单进度</h2></header>
            <ul class="xw-timeline progress">
              <li v-for="event in order.timeline" :key="event.label + event.time">
                {{ event.label }}
                <time>{{ formatTime(event.time) }}</time>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelOrder, confirmOrder, getOrderDetail, payOrder } from '@/api'
import { formatPrice } from '@/utils/format'
import ProductMedia from '@/components/store/ProductMedia.vue'
import PriceText from '@/components/store/PriceText.vue'

const route = useRoute()
const router = useRouter()

const order = ref(null)
const loading = ref(true)

const LABELS = {
  pending: '待支付',
  paid: '待发货',
  shipped: '待收货',
  completed: '已完成',
  cancelled: '已取消'
}

const STATUS_COPY = {
  pending: {
    title: '等待付款',
    desc: '订单已创建，完成支付后我们会立刻安排发货；超过 15 分钟未支付会自动关闭。'
  },
  paid: {
    title: '已付款，等待发货',
    desc: '商家正在打包，48 小时内由顺丰发出，发货后可在这里查看物流。'
  },
  shipped: {
    title: '已发货',
    desc: '包裹已交给快递，收到商品后记得点“确认收货”。'
  },
  completed: {
    title: '交易完成',
    desc: '感谢购买。7 天内如有问题，可联系客服处理退换。'
  },
  cancelled: {
    title: '订单已取消',
    desc: '库存已回滚到商品页，如果还想买可以重新下单。'
  }
}

const statusLabel = computed(() => LABELS[order.value?.status] || order.value?.status || '')
const statusTitle = computed(
  () => STATUS_COPY[order.value?.status]?.title || statusLabel.value
)
const statusDesc = computed(() => STATUS_COPY[order.value?.status]?.desc || '')
const totalQuantity = computed(
  () => (order.value?.items || []).reduce((sum, item) => sum + item.quantity, 0)
)

function formatTime(time) {
  if (!time) return '—'
  const date = new Date(time)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    order.value = await getOrderDetail(route.params.id)
  } catch (e) {
    order.value = null
  } finally {
    loading.value = false
  }
}

async function pay() {
  try {
    await payOrder(order.value.id)
    ElMessage.success('支付成功')
    await load()
  } catch (e) {
    /* 状态冲突由拦截器提示 */
  }
}

async function cancel() {
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
    await cancelOrder(order.value.id)
    ElMessage.success('订单已取消')
    await load()
  } catch (e) {
    /* 同上 */
  }
}

async function confirm() {
  try {
    await ElMessageBox.confirm('确认已经收到商品？', '确认收货', {
      confirmButtonText: '确认收货',
      cancelButtonText: '还没收到'
    })
  } catch (e) {
    return
  }
  try {
    await confirmOrder(order.value.id)
    ElMessage.success('交易完成')
    await load()
  } catch (e) {
    /* 同上 */
  }
}

onMounted(load)
</script>

<style scoped>
.crumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 11.5px;
  color: var(--xw-muted);
}

.crumb a:hover {
  color: var(--xw-ink);
}

.crumb .current {
  color: var(--xw-ink-soft);
}

/* ---------- 状态区 ---------- */
.status-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  padding: 30px 32px;
  background: var(--xw-paper-deep);
  border: 1px solid var(--xw-line);
  margin-bottom: 22px;
}

.status-hero h1 {
  margin: 12px 0 8px;
  font-size: clamp(24px, 2.8vw, 34px);
  font-weight: 500;
  letter-spacing: -0.035em;
  line-height: 1.15;
}

.hero-desc {
  max-width: 460px;
  font-size: 12px;
  line-height: 1.75;
  color: var(--xw-ink-soft);
}

.hero-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
  flex-shrink: 0;
}

.hero-actions {
  display: flex;
  gap: 8px;
}

.hero-actions .xw-btn {
  height: 40px;
  padding: 0 18px;
  font-size: 12.5px;
}

/* ---------- 布局 ---------- */
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.col-main,
.col-side {
  display: grid;
  gap: 16px;
}

/* ---------- 商品 ---------- */
.item-list li {
  display: grid;
  grid-template-columns: 60px minmax(0, 1fr) 130px 90px;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--xw-line);
}

.item-list li:last-child {
  border-bottom: 0;
}

.item-media {
  width: 60px;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.item-name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-attrs {
  font-size: 11px;
  color: var(--xw-muted);
}

.item-price {
  font-size: 11.5px;
  color: var(--xw-muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.item-list li :deep(.xw-price) {
  text-align: right;
}

.item-total {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 14px;
  padding: 16px 20px;
  border-top: 1px solid var(--xw-line);
  font-size: 12px;
  color: var(--xw-muted);
}

/* ---------- 地址 ---------- */
.addr-block {
  padding: 18px 20px 20px;
}

.addr-person {
  font-size: 13.5px;
  font-weight: 600;
}

.addr-person span {
  margin-left: 10px;
  font-size: 12px;
  font-weight: 400;
  color: var(--xw-muted);
  font-variant-numeric: tabular-nums;
}

.addr-detail {
  margin-top: 7px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--xw-ink-soft);
}

.addr-remark {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--xw-line);
  font-size: 11.5px;
  color: var(--xw-muted);
}

/* ---------- 订单信息 ---------- */
.info-lines {
  display: grid;
  gap: 12px;
  padding: 18px 20px 20px;
  font-size: 12px;
}

.info-lines div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.info-lines dt {
  color: var(--xw-muted);
  flex-shrink: 0;
}

.info-lines dd {
  text-align: right;
  color: var(--xw-ink-soft);
}

.info-lines dd.mono {
  font-variant-numeric: tabular-nums;
  font-size: 11.5px;
}

.progress {
  padding: 18px 20px 22px;
}

.detail-skel {
  min-height: 420px;
  background: linear-gradient(100deg, #eae3d4 18%, #f6f1e7 38%, #eae3d4 58%);
  background-size: 220% 100%;
  animation: xw-shimmer 1.35s linear infinite;
}

@media (max-width: 1080px) {
  .detail-grid {
    grid-template-columns: minmax(0, 1fr) 280px;
  }
}

@media (max-width: 900px) {
  .status-hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
    padding: 22px 20px;
  }
  .hero-side {
    align-items: flex-start;
    width: 100%;
  }
  .hero-actions {
    width: 100%;
  }
  .hero-actions .xw-btn {
    flex: 1;
    padding: 0 10px;
  }
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .item-list li {
    grid-template-columns: 52px minmax(0, 1fr) 72px;
    gap: 11px;
    padding: 14px;
  }
  .item-media {
    width: 52px;
  }
  .item-price {
    display: none;
  }
  .item-total {
    padding: 14px;
  }
  .addr-block,
  .info-lines,
  .progress {
    padding: 16px 14px;
  }
}
</style>

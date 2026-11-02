<template>
  <div class="xw-shell">
    <header class="cart-head">
      <div>
        <p class="xw-eyebrow">CART</p>
        <h1>购物车</h1>
      </div>
      <p v-if="cartStore.validItems.length" class="xw-meta">
        {{ cartStore.validItems.length }} 种商品 · 共 {{ cartStore.count }} 件
      </p>
    </header>

    <div v-if="loading" class="loading-rows">
      <div v-for="n in 2" :key="n" class="loading-row">
        <div class="xw-skel" style="width: 84px; height: 104px"></div>
        <div class="loading-lines">
          <div class="xw-skel xw-skel--text" style="width: 42%"></div>
          <div class="xw-skel xw-skel--text" style="width: 24%"></div>
          <div class="xw-skel xw-skel--text" style="width: 16%"></div>
        </div>
      </div>
    </div>

    <div v-else-if="!cartStore.items.length" class="cart-empty-wrap">
      <div class="xw-empty cart-empty">
        <svg viewBox="0 0 64 64" class="empty-art" stroke="currentColor" fill="none" stroke-width="1" aria-hidden="true">
          <path d="M14 20h36l-3 32H17z" />
          <path d="M24 20v-4a8 8 0 0 1 16 0v4" />
          <path d="M26 34h12" />
        </svg>
        <h3>购物车还是空的</h3>
        <p>挑两件放进来吧，满 ¥199 顺丰包邮。</p>
        <RouterLink class="xw-btn" to="/products">去逛逛</RouterLink>
      </div>

      <section v-if="recommend.length" class="xw-sec">
        <header class="xw-sec-head">
          <div>
            <h2>为你推荐</h2>
            <p class="xw-sec-sub">销量最高的几件，先看看有没有合用的</p>
          </div>
          <RouterLink class="xw-more" to="/products">
            全部商品 <LineIcon name="arrow-right" :size="13" />
          </RouterLink>
        </header>
        <div class="xw-grid">
          <ProductCard
            v-for="(item, index) in recommend"
            :key="item.id"
            :product="item"
            :index="index + 1"
          />
        </div>
      </section>
    </div>

    <div v-else class="cart-layout">
      <div class="cart-main">
        <div class="list-head xw-only-desktop">
          <button class="xw-check" :class="{ 'is-checked': cartStore.allChecked }" type="button" aria-label="全选" @click="toggleAll">
            <LineIcon name="check" :size="12" />
          </button>
          <span class="col-goods">商品</span>
          <span class="col-price">单价</span>
          <span class="col-qty">数量</span>
          <span class="col-sub">小计</span>
          <span class="col-op"></span>
        </div>

        <ul class="cart-rows">
          <li v-for="item in cartStore.validItems" :key="item.key" class="cart-row">
            <button
              class="xw-check"
              :class="{ 'is-checked': cartStore.checked.includes(item.key) }"
              type="button"
              :aria-label="`选择 ${item.name}`"
              @click="cartStore.toggle(item.key)"
            >
              <LineIcon name="check" :size="12" />
            </button>

            <RouterLink :to="`/products/${item.productId}`" class="row-media">
              <ProductMedia :src="item.image" :name="item.name" ratio="4 / 5" />
            </RouterLink>

            <div class="row-info">
              <RouterLink :to="`/products/${item.productId}`" class="row-name">
                {{ item.name }}
              </RouterLink>
              <p class="row-attrs">{{ attrsText(item) }}</p>
              <p class="row-stock">
                <template v-if="item.stock > 0">现货 · 48 小时内发出</template>
                <template v-else>暂时缺货</template>
              </p>
            </div>

            <div class="row-price">
              <span class="mobile-label">单价</span>
              <PriceText :value="item.priceCents / 100" size="sm" />
            </div>

            <div class="row-qty">
              <QtyStepper
                :model-value="item.qty"
                :max="item.stock || 999"
                @update:model-value="(value) => cartStore.setQty(item, value)"
              />
            </div>

            <div class="row-sub">
              <PriceText :value="(item.priceCents * item.qty) / 100" size="md" />
            </div>

            <button class="row-remove" type="button" :aria-label="`移除 ${item.name}`" @click="remove(item)">
              <LineIcon name="trash" :size="15" />
            </button>
          </li>
        </ul>

        <section v-if="cartStore.invalidItems.length" class="invalid">
          <header class="invalid-head">
            <h3>已失效（{{ cartStore.invalidItems.length }}）</h3>
            <button class="xw-text-btn" type="button" @click="clearInvalid">清空失效商品</button>
          </header>
          <ul class="invalid-rows">
            <li v-for="item in cartStore.invalidItems" :key="item.key">
              <span class="invalid-tag">失效</span>
              <ProductMedia :src="item.image" :name="item.name" ratio="1 / 1" class="invalid-media" />
              <div class="invalid-info">
                <span class="row-name">{{ item.name }}</span>
                <span class="row-attrs">{{ attrsText(item) }}</span>
              </div>
              <button class="xw-text-btn" type="button" @click="remove(item)">移除</button>
            </li>
          </ul>
        </section>

        <div class="cart-foot xw-only-desktop">
          <button
            class="xw-check"
            :class="{ 'is-checked': cartStore.allChecked }"
            type="button"
            aria-label="全选"
            @click="toggleAll"
          >
            <LineIcon name="check" :size="12" />
          </button>
          <span class="foot-all">全选</span>
          <RouterLink class="xw-text-btn foot-continue" to="/products">继续购物</RouterLink>
          <span class="foot-spacer"></span>
          <span class="foot-count">已选 {{ cartStore.checkedCount }} 件</span>
        </div>
      </div>

      <aside class="summary xw-only-desktop">
        <h2>订单摘要</h2>

        <dl class="sum-lines">
          <div>
            <dt>商品金额</dt>
            <dd>{{ formatPrice(cartStore.subtotalCents / 100) }}</dd>
          </div>
          <div>
            <dt>运费</dt>
            <dd>{{ cartStore.checkedItems.length ? '包邮' : '—' }}</dd>
          </div>
          <div>
            <dt>优惠</dt>
            <dd class="muted">结算时可用</dd>
          </div>
        </dl>

        <div class="sum-total">
          <span>应付合计</span>
          <PriceText :value="cartStore.payableCents / 100" size="lg" />
        </div>

        <button class="xw-btn xw-btn--block xw-btn--lg" type="button" :disabled="!cartStore.checkedItems.length" @click="checkout">
          去结算（{{ cartStore.checkedCount }}）
        </button>

        <p class="sum-note">
          支持 7 天无理由退换 · 满 ¥199 顺丰包邮<br />
          实际运费与优惠以结算页为准
        </p>
      </aside>
    </div>

    <div v-if="cartStore.items.length" class="mobile-bar">
      <button class="xw-check" :class="{ 'is-checked': cartStore.allChecked }" type="button" aria-label="全选" @click="toggleAll">
        <LineIcon name="check" :size="12" />
      </button>
      <span class="mobile-all">全选</span>
      <div class="mobile-sum">
        <span class="mobile-label">合计</span>
        <PriceText :value="cartStore.payableCents / 100" size="md" />
      </div>
      <button class="xw-btn" type="button" :disabled="!cartStore.checkedItems.length" @click="checkout">
        结算（{{ cartStore.checkedCount }}）
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProducts } from '@/api'
import { useCartStore } from '@/store/cart'
import { useUserStore } from '@/store/user'
import { formatPrice } from '@/utils/format'
import ProductMedia from '@/components/store/ProductMedia.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import PriceText from '@/components/store/PriceText.vue'
import QtyStepper from '@/components/store/QtyStepper.vue'
import LineIcon from '@/components/store/LineIcon.vue'

const router = useRouter()
const cartStore = useCartStore()
const userStore = useUserStore()
const loading = ref(true)
const recommend = ref([])

function attrsText(item) {
  return Object.values(item.attrs || {}).join(' / ') || '默认规格'
}

function toggleAll() {
  cartStore.toggleAll(!cartStore.allChecked)
}

async function remove(item) {
  try {
    await ElMessageBox.confirm('从购物车移除这件商品？', '移除商品', {
      confirmButtonText: '移除',
      cancelButtonText: '再想想',
      type: 'warning'
    })
  } catch (e) {
    return
  }
  await cartStore.remove(item)
  ElMessage.success('已移除')
}

async function clearInvalid() {
  const items = [...cartStore.invalidItems]
  for (const item of items) {
    await cartStore.remove(item)
  }
  ElMessage.success('已清空失效商品')
}

function checkout() {
  if (!cartStore.checkedItems.length) return
  if (!userStore.isLoggedIn) {
    ElMessage.info('请先登录后结算')
    router.push({ path: '/login', query: { redirect: '/cart' } })
    return
  }
  if (cartStore.items.some((item) => !item.server)) {
    ElMessage.info('购物车正在同步，请稍候再试')
    cartStore.load()
    return
  }
  const ids = cartStore.checkedItems.map((item) => item.id).join(',')
  router.push({ path: '/checkout', query: { cart_item_ids: ids } })
}

onMounted(async () => {
  await cartStore.load()
  loading.value = false
  if (!cartStore.items.length) {
    try {
      const data = await getProducts({ sort: 'sales_desc', size: 4 })
      recommend.value = data.items || []
    } catch (e) {
      recommend.value = []
    }
  }
})
</script>

<style scoped>
.cart-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--xw-line);
  margin-bottom: 28px;
}

.cart-head h1 {
  margin-top: 10px;
  font-size: clamp(24px, 2.6vw, 32px);
  font-weight: 500;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.cart-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 56px;
  align-items: start;
}

/* ---------- 列表 ---------- */
.list-head {
  display: grid;
  grid-template-columns: 22px 92px minmax(0, 1fr) 92px 118px 96px 34px;
  align-items: center;
  gap: 18px;
  padding: 0 0 12px;
  border-bottom: 1px solid var(--xw-line);
  font-size: 10.5px;
  letter-spacing: 0.12em;
  color: var(--xw-muted);
  text-transform: uppercase;
}

.list-head .col-goods {
  grid-column: 2 / 4;
}

.cart-rows {
  display: grid;
}

.cart-row {
  display: grid;
  grid-template-columns: 22px 92px minmax(0, 1fr) 92px 118px 96px 34px;
  align-items: center;
  gap: 18px;
  padding: 22px 0;
  border-bottom: 1px solid var(--xw-line);
}

.row-media {
  display: block;
  width: 92px;
}

.row-info {
  min-width: 0;
}

.row-name {
  display: block;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--xw-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-name:hover {
  color: var(--xw-accent);
}

.row-attrs {
  margin-top: 6px;
  font-size: 11.5px;
  color: var(--xw-muted);
}

.row-stock {
  margin-top: 8px;
  font-size: 11px;
  color: var(--xw-olive);
}

.row-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 0;
  background: none;
  color: var(--xw-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.row-remove:hover {
  color: var(--xw-accent);
}

.mobile-label {
  display: none;
  font-size: 10.5px;
  color: var(--xw-muted);
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.cart-foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 0;
  border-bottom: 1px solid var(--xw-line);
}

.foot-all {
  font-size: 12.5px;
  color: var(--xw-ink-soft);
}

.foot-continue {
  margin-left: 14px;
}

.foot-spacer {
  flex: 1;
}

.foot-count {
  font-size: 12px;
  color: var(--xw-muted);
}

/* ---------- 失效 ---------- */
.invalid {
  margin-top: 26px;
  background: rgba(255, 253, 248, 0.55);
  border: 1px solid var(--xw-line);
  padding: 16px 18px;
}

.invalid-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.invalid-head h3 {
  font-size: 12px;
  font-weight: 500;
  color: var(--xw-muted);
  letter-spacing: 0.02em;
}

.invalid-rows {
  display: grid;
  gap: 10px;
}

.invalid-rows li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--xw-line);
}

.invalid-tag {
  padding: 2px 6px;
  background: var(--xw-ink);
  color: #f6f0e4;
  font-size: 9.5px;
  letter-spacing: 0.08em;
}

.invalid-media {
  width: 48px;
  flex-shrink: 0;
  opacity: 0.6;
}

.invalid-media :deep(.xw-plate-label),
.invalid-media :deep(.xw-plate-index) {
  display: none;
}

.invalid-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.invalid-info .row-name {
  font-size: 12.5px;
  color: var(--xw-muted);
}

.invalid-info .row-attrs {
  margin-top: 0;
}

/* ---------- 摘要 ---------- */
.summary {
  position: sticky;
  top: calc(var(--xw-header-h) + 20px);
  padding: 24px;
  background: var(--xw-surface);
  border: 1px solid var(--xw-line);
}

.summary h2 {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.01em;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--xw-line);
}

.sum-lines {
  display: grid;
  gap: 12px;
  padding: 18px 0;
  font-size: 12.5px;
}

.sum-lines div {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.sum-lines dt {
  color: var(--xw-muted);
}

.sum-lines dd {
  font-variant-numeric: tabular-nums;
}

.sum-lines dd.muted {
  color: var(--xw-muted);
  font-size: 11.5px;
}

.sum-total {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 16px 0 20px;
  border-top: 1px solid var(--xw-line);
  font-size: 12.5px;
}

.sum-note {
  margin-top: 14px;
  font-size: 10.5px;
  line-height: 1.7;
  color: var(--xw-muted);
}

/* ---------- 骨架 ---------- */
.loading-rows {
  display: grid;
  gap: 22px;
}

.loading-row {
  display: flex;
  gap: 18px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--xw-line);
}

.loading-lines {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 8px;
  flex: 1;
}

.cart-empty {
  padding: 88px 24px;
}

.empty-art {
  width: 56px;
  height: 56px;
  margin: 0 auto 18px;
  color: var(--xw-line-ink);
}

/* ---------- 移动端 ---------- */
.mobile-bar {
  display: none;
}

@media (max-width: 1080px) {
  .cart-layout {
    grid-template-columns: minmax(0, 1fr) 288px;
    gap: 32px;
  }
}

@media (max-width: 900px) {
  .cart-head {
    padding-bottom: 16px;
    margin-bottom: 8px;
  }
  .cart-layout {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .cart-row {
    grid-template-columns: 20px 78px minmax(0, 1fr);
    grid-template-areas:
      "check media info"
      ". price qty";
    row-gap: 12px;
    column-gap: 12px;
    padding: 18px 0;
  }

  .cart-row > .xw-check {
    grid-area: check;
    align-self: flex-start;
    margin-top: 4px;
  }
  .row-media {
    grid-area: media;
    width: 78px;
  }
  .row-info {
    grid-area: info;
    padding-right: 26px;
  }
  .row-price {
    grid-area: price;
    display: flex;
    align-items: center;
    gap: 6px;
    padding-left: 2px;
  }
  .row-qty {
    grid-area: qty;
    justify-self: start;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .row-sub {
    display: none;
  }
  .row-remove {
    position: absolute;
    right: 0;
    top: 18px;
  }
  .cart-row {
    position: relative;
  }
  .mobile-label {
    display: inline;
  }

  .cart-foot {
    display: none;
  }

  .invalid {
    padding: 14px;
  }

  .mobile-bar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 55;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px var(--xw-gutter) calc(10px + env(safe-area-inset-bottom));
    background: rgba(255, 253, 248, 0.96);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--xw-line);
  }

  .mobile-all {
    font-size: 11.5px;
    color: var(--xw-ink-soft);
  }

  .mobile-sum {
    margin-left: auto;
    display: flex;
    align-items: baseline;
    gap: 6px;
  }

  .mobile-bar .xw-btn {
    height: 42px;
    padding: 0 20px;
  }

  .cart-layout {
    padding-bottom: 84px;
  }
}
</style>

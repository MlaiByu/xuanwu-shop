<template>
  <div class="xw-shell detail-shell">
    <nav class="crumb" aria-label="面包屑">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <RouterLink :to="{ path: '/products', query: { category_id: product?.category_id } }">
        {{ categoryName || '全部商品' }}
      </RouterLink>
      <template v-if="product">
        <span>/</span>
        <span class="current">{{ product.name }}</span>
      </template>
    </nav>

    <div v-if="loading" class="detail">
      <div class="xw-skel gallery-skel"></div>
      <div class="info-skel">
        <div class="xw-skel xw-skel--text" style="width: 26%; height: 12px"></div>
        <div class="xw-skel xw-skel--text" style="width: 74%; height: 30px"></div>
        <div class="xw-skel xw-skel--text" style="width: 40%"></div>
        <div class="xw-skel xw-skel--text" style="width: 100%; height: 76px"></div>
        <div class="xw-skel xw-skel--text" style="width: 100%; height: 44px"></div>
        <div class="xw-skel xw-skel--text" style="width: 100%; height: 54px"></div>
      </div>
    </div>

    <div v-else-if="!product" class="xw-empty">
      <h3>商品不存在或已下架</h3>
      <p>它可能被商家下架了，去看看其他同类商品。</p>
      <RouterLink class="xw-btn xw-btn--ghost" to="/products">回到全部商品</RouterLink>
    </div>

    <template v-else>
      <div class="detail">
        <div class="gallery">
          <div class="gallery-main">
            <ProductMedia
              :src="activeImage"
              :name="product.name"
              :category="categoryName"
              ratio="4 / 5"
              index="01"
              eager
              class="detail-media"
            />
            <span class="gallery-badge">商品示意</span>
          </div>

          <div v-if="thumbs.length > 1" class="gallery-thumbs">
            <button
              v-for="(img, index) in thumbs"
              :key="img"
              type="button"
              class="thumb"
              :class="{ active: activeImage === img }"
              :aria-label="`查看第 ${index + 1} 张图`"
              @click="activeImage = img"
            >
              <ProductMedia :src="img" :name="product.name" :category="categoryName" ratio="1 / 1" />
            </button>
          </div>

          <p class="gallery-note">
            图片为商品示意<template v-if="thumbs.length > 1"> · 共 {{ thumbs.length }} 张</template>
            · 支持 7 天无理由退换
          </p>
        </div>

        <div class="info">
          <div class="info-head">
            <p class="xw-eyebrow">{{ categoryName }} / {{ firstSku?.sku_code }}</p>
            <h1>{{ product.name }}</h1>
            <p class="info-sub">
              已售 {{ product.sales_count }} 件
              <span class="dot">·</span>
              48 小时内发出
            </p>
          </div>

          <div class="price-block">
            <div>
              <PriceText :value="displayPrice" size="xl" />
              <p class="price-note">含税价 · 满 ¥199 顺丰包邮 · 运费在购物车单独列出</p>
            </div>
            <span class="stock-pill" :class="{ low: stock > 0 && stock <= 5, out: stock === 0 }">
              {{ stockLabel }}
            </span>
          </div>

          <div v-for="key in product.spec_keys" :key="key" class="option">
            <span class="option-label">{{ key }}</span>
            <div class="option-values">
              <button
                v-for="value in specValues(key)"
                :key="value"
                type="button"
                class="spec"
                :class="{
                  active: selected[key] === value,
                  disabled: isValueDisabled(key, value)
                }"
                :disabled="isValueDisabled(key, value)"
                :aria-pressed="selected[key] === value"
                @click="selectSpec(key, value)"
              >
                {{ value }}
              </button>
            </div>
          </div>

          <div class="option qty-option">
            <span class="option-label">数量</span>
            <QtyStepper v-model="qty" :max="Math.max(remaining, 1)" :disabled="!canAdd" />
            <span class="qty-hint">{{ currentSku ? stockHint : `请选择 ${missingSpecs}` }}</span>
          </div>

          <div class="actions">
            <button class="xw-btn xw-btn--lg" type="button" :disabled="!canAdd" @click="addToCart">
              加入购物车
            </button>
            <button
              class="xw-btn xw-btn--lg xw-btn--ghost"
              type="button"
              :disabled="!canAdd"
              @click="buyNow"
            >
              去购物车结算
            </button>
          </div>

          <ul class="assurance">
            <li>
              <LineIcon name="truck" :size="17" />
              <div><strong>48 小时内发出</strong><span>上海仓 · 顺丰包邮</span></div>
            </li>
            <li>
              <LineIcon name="returns" :size="17" />
              <div><strong>7 天无理由</strong><span>不影响二次销售可退</span></div>
            </li>
            <li>
              <LineIcon name="shield" :size="17" />
              <div><strong>一年质保</strong><span>全国联保 · 凭单保修</span></div>
            </li>
          </ul>

          <p class="delivery">
            <LineIcon name="truck" :size="14" />
            配送至 上海 · 预计 {{ eta }} 送达
          </p>

          <div class="accordion">
            <section class="panel">
              <button type="button" class="panel-head" @click="toggle('desc')">
                商品描述
                <LineIcon :name="openPanel === 'desc' ? 'minus' : 'plus'" :size="14" />
              </button>
              <div v-show="openPanel === 'desc'" class="panel-body">
                <p>{{ product.description || '商家暂未填写商品描述。' }}</p>
              </div>
            </section>

            <section class="panel">
              <button type="button" class="panel-head" @click="toggle('spec')">
                规格参数
                <LineIcon :name="openPanel === 'spec' ? 'minus' : 'plus'" :size="14" />
              </button>
              <div v-show="openPanel === 'spec'" class="panel-body">
                <table class="spec-table">
                  <thead>
                    <tr>
                      <th>规格编码</th>
                      <th>规格</th>
                      <th>价格</th>
                      <th>库存</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="sku in product.skus" :key="sku.id">
                      <td>{{ sku.sku_code }}</td>
                      <td>{{ Object.values(sku.attrs || {}).join(' / ') }}</td>
                      <td>{{ formatPrice(sku.price) }}</td>
                      <td>{{ sku.stock }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section class="panel">
              <button type="button" class="panel-head" @click="toggle('service')">
                售后与配送
                <LineIcon :name="openPanel === 'service' ? 'minus' : 'plus'" :size="14" />
              </button>
              <div v-show="openPanel === 'service'" class="panel-body">
                <p>
                  签收后 7 天内，商品不影响二次销售可申请无理由退货；质量问题由商家承担往返运费。
                  发货时间为付款后 48 小时内，遇节假日顺延。发票随货开具，可在订单详情中补开。
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>

      <section v-if="related.length" class="xw-sec">
        <header class="xw-sec-head">
          <div>
            <h2>同类推荐</h2>
            <p class="xw-sec-sub">同一个类目里，另外几件值得看的</p>
          </div>
          <RouterLink
            class="xw-more"
            :to="{ path: '/products', query: { category_id: product.category_id } }"
          >
            查看该类目 <LineIcon name="arrow-right" :size="13" />
          </RouterLink>
        </header>
        <div class="xw-grid">
          <ProductCard
            v-for="(item, index) in related"
            :key="item.id"
            :product="item"
            :category-name="categoryName"
            :index="index + 1"
          />
        </div>
      </section>
    </template>

    <div v-if="product && !loading" class="mobile-buy" :class="{ 'is-visible': showBar }">
      <div class="mobile-buy-price">
        <PriceText :value="displayPrice" size="lg" />
        <span>{{ currentSku ? stockHint : '请选择规格' }}</span>
      </div>
      <button class="xw-btn" type="button" :disabled="!canAdd" @click="addToCart">
        加入购物车
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCategories, getProductDetail, getProducts } from '@/api'
import { formatPrice } from '@/utils/format'
import { useCartStore } from '@/store/cart'
import ProductMedia from '@/components/store/ProductMedia.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import PriceText from '@/components/store/PriceText.vue'
import QtyStepper from '@/components/store/QtyStepper.vue'
import LineIcon from '@/components/store/LineIcon.vue'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const product = ref(null)
const related = ref([])
const categories = ref([])
const loading = ref(true)
const selected = reactive({})
const qty = ref(1)
const activeImage = ref('')
const openPanel = ref('desc')
const showBar = ref(false)

function onScroll() {
  showBar.value = window.scrollY > 260
}

const isDemoImage = (src) => !src || /picsum\.photos|placehold|via\.placeholder/i.test(src)

const thumbs = computed(() => {
  if (!product.value) return []
  const all = [product.value.main_image, ...(product.value.images || [])]
  const real = all.filter((src) => !isDemoImage(src))
  return real.length ? real : [product.value.main_image || '']
})

const categoryName = computed(() => {
  const map = {}
  const walk = (list) =>
    list.forEach((cat) => {
      map[cat.id] = cat.name
      if (cat.children?.length) walk(cat.children)
    })
  walk(categories.value)
  return map[product.value?.category_id] || '玄武选物'
})

const firstSku = computed(() => product.value?.skus?.[0])

const currentSku = computed(() => {
  if (!product.value) return null
  return (
    product.value.skus.find((sku) =>
      Object.entries(sku.attrs || {}).every(([key, value]) => selected[key] === value)
    ) || null
  )
})

const stock = computed(() => currentSku.value?.stock ?? 0)

// 购物车里该 SKU 已加的数量（未下单前不扣真实库存，但会占用可加购额度）
const cartQty = computed(() => {
  if (!currentSku.value) return 0
  const item = cartStore.items.find((i) => i.skuId === currentSku.value.id)
  return item ? item.qty : 0
})

// 剩余可加购数量 = 库存 - 购物车已占，避免"显示 90 件却再加就库存不足"的误导
const remaining = computed(() => Math.max(0, stock.value - cartQty.value))

const stockLabel = computed(() => {
  if (!currentSku.value) return '请选择规格'
  if (currentSku.value.stock === 0) return '暂时缺货'
  if (currentSku.value.stock <= 5) return `仅剩 ${currentSku.value.stock} 件`
  return '现货充足'
})

const stockHint = computed(() => {
  if (!currentSku.value) return ''
  if (stock.value === 0) return '暂时缺货'
  if (remaining.value === 0) return `购物车已加 ${cartQty.value} 件，已到库存上限`
  if (cartQty.value > 0) return `还可加购 ${remaining.value} 件（购物车已加 ${cartQty.value} 件）`
  return `库存 ${stock.value} 件`
})

const canAdd = computed(
  () => !!currentSku.value && remaining.value > 0 && currentSku.value.is_active !== false
)

const missingSpecs = computed(() => {
  if (!product.value) return ''
  return product.value.spec_keys.filter((key) => !selected[key]).join(' / ')
})

const displayPrice = computed(() => {
  if (currentSku.value) return currentSku.value.price
  if (!product.value) return 0
  return product.value.price_range?.min || 0
})

const eta = computed(() => {
  const date = new Date()
  date.setDate(date.getDate() + 2)
  return `${date.getMonth() + 1} 月 ${date.getDate()} 日`
})

function specValues(key) {
  if (!product.value) return []
  const set = new Set()
  product.value.skus.forEach((sku) => {
    if (sku.attrs?.[key]) set.add(sku.attrs[key])
  })
  return Array.from(set)
}

function isValueDisabled(key, value) {
  if (!product.value) return false
  return !product.value.skus.some(
    (sku) => sku.attrs?.[key] === value && sku.stock > 0 && sku.is_active !== false
  )
}

function selectSpec(key, value) {
  selected[key] = selected[key] === value ? '' : value
}

function toggle(key) {
  openPanel.value = openPanel.value === key ? '' : key
}

async function addToCart() {
  if (!canAdd.value) return
  try {
    await cartStore.add(product.value, currentSku.value, qty.value)
    ElMessage.success(`已加入购物车 · ${selectedText.value}`)
    // 加购后按新的剩余库存收敛数量，避免下次再加时超出上限
    qty.value = Math.max(1, Math.min(qty.value, remaining.value))
  } catch (e) {
    // 请求封装已弹出具体错误（库存不足 / 已下架）
  }
}

async function buyNow() {
  if (!canAdd.value) return
  try {
    await cartStore.add(product.value, currentSku.value, qty.value)
    router.push('/cart')
  } catch (e) {
    /* 同上 */
  }
}

const selectedText = computed(() =>
  product.value ? product.value.spec_keys.map((key) => selected[key]).filter(Boolean).join(' / ') : ''
)

async function load() {
  loading.value = true
  product.value = null
  related.value = []
  Object.keys(selected).forEach((key) => delete selected[key])
  try {
    const data = await getProductDetail(route.params.id)
    product.value = data
    // 预选第一个有货的规格，减少无效点击；缺货组合仍可手动切换查看
    const firstAvailable =
      data.skus.find((sku) => sku.stock > 0 && sku.is_active !== false) || data.skus[0]
    if (firstAvailable) Object.assign(selected, firstAvailable.attrs)
    activeImage.value = thumbs.value[0] || ''
    qty.value = 1
    loadRelated()
  } catch (e) {
    product.value = null
  } finally {
    loading.value = false
  }
}

async function loadRelated() {
  if (!product.value) return
  try {
    const data = await getProducts({
      category_id: product.value.category_id,
      sort: 'sales_desc',
      size: 5
    })
    related.value = (data.items || []).filter((item) => item.id !== product.value.id).slice(0, 4)
  } catch (e) {
    related.value = []
  }
}

watch(() => route.params.id, (id) => {
  if (id) load()
})

onMounted(async () => {
  load()
  window.addEventListener('scroll', onScroll, { passive: true })
  try {
    categories.value = await getCategories()
  } catch (e) {
    categories.value = []
  }
  // 详情页需要购物车里该 SKU 的已加数量来计算"剩余可加购"，确保购物车数据已加载
  if (!cartStore.loaded) await cartStore.load()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.detail-shell {
  padding-bottom: 20px;
}

.crumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 11.5px;
  color: var(--xw-muted);
  margin-bottom: 26px;
}

.crumb a:hover {
  color: var(--xw-ink);
}

.crumb .current {
  color: var(--xw-ink-soft);
}

.detail {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 64px;
  align-items: start;
}

/* ---------- 图廊 ---------- */
@media (min-width: 901px) {
  .gallery {
    position: sticky;
    top: calc(var(--xw-header-h) + 22px);
  }
}

.gallery-main {
  position: relative;
  background: var(--xw-surface);
  padding: 10px;
}

.gallery-badge {
  position: absolute;
  right: 20px;
  bottom: 20px;
  padding: 4px 9px;
  background: rgba(255, 253, 248, 0.86);
  border: 1px solid var(--xw-line);
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--xw-ink-soft);
}

.gallery-thumbs {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.thumb {
  width: 76px;
  padding: 3px;
  border: 1px solid var(--xw-line);
  background: var(--xw-surface);
  cursor: pointer;
  transition: border-color 0.16s;
}

.thumb.active,
.thumb:hover {
  border-color: var(--xw-ink);
}

.gallery-note {
  margin-top: 14px;
  font-size: 11px;
  color: var(--xw-muted);
  letter-spacing: 0.02em;
}

/* ---------- 信息 ---------- */
.info {
  position: sticky;
  top: calc(var(--xw-header-h) + 22px);
}

.info-head h1 {
  margin: 12px 0 10px;
  font-size: clamp(24px, 2.6vw, 34px);
  font-weight: 500;
  letter-spacing: -0.035em;
  line-height: 1.2;
}

.info-sub {
  font-size: 12px;
  color: var(--xw-muted);
}

.dot {
  margin: 0 6px;
}

.price-block {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 24px 0 22px;
  padding: 18px 0;
  border-top: 1px solid var(--xw-line);
  border-bottom: 1px solid var(--xw-line);
}

.price-note {
  margin-top: 8px;
  font-size: 11px;
  color: var(--xw-muted);
}

.stock-pill {
  flex-shrink: 0;
  margin-top: 4px;
  padding: 4px 9px;
  border: 1px solid var(--xw-line);
  font-size: 11px;
  color: var(--xw-ink-soft);
  letter-spacing: 0.02em;
}

.stock-pill.low {
  color: var(--xw-accent);
  border-color: rgba(180, 67, 43, 0.35);
  background: rgba(180, 67, 43, 0.05);
}

.stock-pill.out {
  color: var(--xw-muted);
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 18px;
}

.option-label {
  width: 46px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--xw-muted);
  line-height: 40px;
}

.option-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec {
  min-width: 64px;
  height: 40px;
  padding: 0 15px;
  border: 1px solid var(--xw-line);
  background: transparent;
  font-size: 12.5px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  transition: border-color 0.16s, color 0.16s, background 0.16s;
}

.spec:hover:not(.disabled) {
  border-color: var(--xw-line-ink);
  color: var(--xw-ink);
}

.spec.active {
  border-color: var(--xw-ink);
  background: var(--xw-ink);
  color: #f7f2e8;
}

.spec.disabled {
  color: #bdb2a0;
  border-color: var(--xw-line);
  background: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 4px,
    rgba(26, 22, 17, 0.03) 4px,
    rgba(26, 22, 17, 0.03) 8px
  );
  cursor: not-allowed;
  text-decoration: line-through;
}

.qty-option {
  align-items: center;
  margin-top: 4px;
}

.qty-hint {
  font-size: 11.5px;
  color: var(--xw-muted);
  align-self: center;
}

.actions {
  display: flex;
  gap: 10px;
  margin: 24px 0 26px;
}

.actions .xw-btn {
  flex: 1;
}

.assurance {
  display: grid;
  gap: 12px;
  padding: 20px 0;
  border-top: 1px solid var(--xw-line);
}

.assurance li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: var(--xw-ink-soft);
}

.assurance strong {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--xw-ink);
}

.assurance span {
  display: block;
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--xw-muted);
}

.delivery {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 12px 0 0;
  border-top: 1px solid var(--xw-line);
  font-size: 11.5px;
  color: var(--xw-muted);
}

/* ---------- 折叠面板 ---------- */
.accordion {
  margin-top: 20px;
  border-top: 1px solid var(--xw-line);
}

.panel {
  border-bottom: 1px solid var(--xw-line);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 15px 0;
  border: 0;
  background: none;
  font-size: 12.5px;
  letter-spacing: 0.02em;
  color: var(--xw-ink);
  cursor: pointer;
}

.panel-body {
  padding: 0 0 18px;
  font-size: 12.5px;
  line-height: 1.85;
  color: var(--xw-ink-soft);
}

.spec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.spec-table th {
  text-align: left;
  font-weight: 400;
  color: var(--xw-muted);
  padding: 7px 10px 7px 0;
  border-bottom: 1px solid var(--xw-line);
  white-space: nowrap;
}

.spec-table td {
  padding: 7px 10px 7px 0;
  border-bottom: 1px solid var(--xw-line);
  color: var(--xw-ink-soft);
}

.spec-table tr:last-child td {
  border-bottom: 0;
}

/* ---------- 骨架 ---------- */
.gallery-skel {
  aspect-ratio: 4 / 5;
  width: 100%;
}

.info-skel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 10px;
}

/* ---------- 移动端吸底 ---------- */
.mobile-buy {
  display: none;
}

@media (max-width: 1080px) {
  .detail {
    gap: 36px;
  }
}

@media (max-width: 900px) {
  .crumb {
    margin-bottom: 14px;
  }
  .detail {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  .gallery-main {
    padding: 0;
  }
  .detail-media {
    aspect-ratio: 1 / 1;
  }
  .gallery-badge {
    right: 12px;
    bottom: 12px;
  }
  .gallery-thumbs {
    padding: 0 2px;
  }
  .thumb {
    width: 60px;
  }
  .info {
    position: static;
  }
  .price-block {
    margin: 18px 0;
    padding: 14px 0;
  }
  .option {
    gap: 12px;
  }
  .option-label {
    width: 38px;
  }
  .spec {
    min-width: 58px;
    height: 38px;
    padding: 0 12px;
  }
  .actions {
    margin: 20px 0 22px;
  }
  .actions .xw-btn {
    height: 46px;
    padding: 0 10px;
    font-size: 12.5px;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }
  .detail-shell {
    padding-bottom: 92px;
  }
  .mobile-buy {
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
    background: rgba(255, 253, 248, 0.97);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--xw-line);
    transform: translateY(112%);
    transition: transform 0.26s var(--xw-ease);
    pointer-events: none;
  }

  .mobile-buy.is-visible {
    transform: translateY(0);
    pointer-events: auto;
  }
  .mobile-buy-price {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .mobile-buy-price span {
    font-size: 10.5px;
    color: var(--xw-muted);
  }
  .mobile-buy .xw-btn {
    padding: 0 26px;
  }
}
</style>

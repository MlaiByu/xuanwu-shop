<template>
  <div class="xw-shell">
    <nav class="crumb" aria-label="面包屑">
      <RouterLink to="/">首页</RouterLink>
      <span>/</span>
      <RouterLink to="/products">全部商品</RouterLink>
      <template v-if="filters.categoryId && categoryName">
        <span>/</span>
        <span class="current">{{ categoryName }}</span>
      </template>
    </nav>

    <header class="plist-head">
      <div>
        <p class="xw-eyebrow">{{ eyebrow }}</p>
        <h1>{{ heading }}</h1>
      </div>
      <p class="xw-meta">
        共 {{ total }} 件 · 48 小时内发出 · 满 199 顺丰包邮
      </p>
    </header>

    <div class="plist">
      <aside class="aside xw-only-desktop" aria-label="筛选">
        <div class="aside-block">
          <h3>类目</h3>
          <ul class="cat-tree">
            <li>
              <button
                type="button"
                class="cat-link"
                :class="{ active: !filters.categoryId }"
                @click="apply({ category_id: undefined })"
              >
                全部商品
              </button>
            </li>
            <li v-for="cat in topCategories" :key="cat.id">
              <button
                type="button"
                class="cat-link"
                :class="{ active: filters.categoryId === cat.id }"
                @click="apply({ category_id: cat.id })"
              >
                {{ cat.name }}
              </button>
              <ul v-if="relatedChildren(cat).length" class="cat-children">
                <li v-for="child in relatedChildren(cat)" :key="child.id">
                  <button
                    type="button"
                    class="cat-link sub"
                    :class="{ active: filters.categoryId === child.id }"
                    @click="apply({ category_id: child.id })"
                  >
                    {{ child.name }}
                  </button>
                </li>
              </ul>
            </li>
          </ul>
        </div>

        <div class="aside-block">
          <h3>价格区间</h3>
          <div class="price-row">
            <input
              v-model="priceMin"
              class="xw-input"
              type="number"
              min="0"
              placeholder="最低"
              aria-label="最低价"
            />
            <span class="dash">—</span>
            <input
              v-model="priceMax"
              class="xw-input"
              type="number"
              min="0"
              placeholder="最高"
              aria-label="最高价"
            />
          </div>
          <button class="apply-price" type="button" @click="applyPrice">应用价格</button>
          <div class="quick-price">
            <button
              v-for="range in quickRanges"
              :key="range.label"
              type="button"
              :class="{ active: isRangeActive(range) }"
              @click="apply(range.query)"
            >
              {{ range.label }}
            </button>
          </div>
        </div>

        <button class="xw-text-btn reset" type="button" @click="resetAll">清空全部筛选</button>
      </aside>

      <div class="plist-main">
        <div class="toolbar">
          <div class="sorts" role="tablist" aria-label="排序方式">
            <button
              v-for="option in sortOptions"
              :key="option.value"
              type="button"
              role="tab"
              :aria-selected="filters.sort === option.value"
              :class="{ active: filters.sort === option.value }"
              @click="apply({ sort: option.value })"
            >
              {{ option.label }}
            </button>
          </div>

          <div class="toolbar-right">
            <span class="xw-meta">{{ total }} 件</span>
            <button class="filter-btn" type="button" @click="filterOpen = true">
              <LineIcon name="filter" :size="15" /> 筛选
            </button>
          </div>
        </div>

        <div v-if="activeChips.length" class="active-chips">
          <button
            v-for="chip in activeChips"
            :key="chip.key"
            type="button"
            class="active-chip"
            @click="removeChip(chip)"
          >
            {{ chip.label }}
            <LineIcon name="close" :size="11" />
          </button>
        </div>

        <div v-if="loading" class="xw-grid xw-grid--3">
          <div v-for="n in 6" :key="n" class="card-skel">
            <div class="xw-skel card-skel-media"></div>
            <div class="xw-skel xw-skel--text" style="width: 36%"></div>
            <div class="xw-skel xw-skel--text" style="width: 86%"></div>
            <div class="xw-skel xw-skel--text" style="width: 30%"></div>
          </div>
        </div>

        <div v-else-if="items.length" class="xw-grid xw-grid--3">
          <ProductCard
            v-for="(item, index) in items"
            :key="item.id"
            :product="item"
            :category-name="categoryNameById(item.category_id)"
            :index="(filters.page - 1) * pageSize + index + 1"
          />
        </div>

        <div v-else class="xw-empty">
          <h3>没有匹配的商品</h3>
          <p>换个更短的关键词，或直接从左侧类目里挑。</p>
          <button class="xw-btn xw-btn--ghost" type="button" @click="resetAll">
            清空筛选条件
          </button>
        </div>

        <nav v-if="pages > 1" class="pager" aria-label="分页">
          <button
            type="button"
            class="pager-btn"
            :disabled="filters.page <= 1"
            @click="goPage(filters.page - 1)"
          >
            <LineIcon name="arrow-left" :size="14" /> 上一页
          </button>
          <div class="pager-nums">
            <button
              v-for="p in pageList"
              :key="p"
              type="button"
              class="pager-num"
              :class="{ active: p === filters.page }"
              @click="goPage(p)"
            >
              {{ p }}
            </button>
          </div>
          <button
            type="button"
            class="pager-btn"
            :disabled="filters.page >= pages"
            @click="goPage(filters.page + 1)"
          >
            下一页 <LineIcon name="arrow-right" :size="14" />
          </button>
        </nav>
      </div>
    </div>

    <Teleport to="body">
      <div class="xw-mask" :class="{ 'is-open': filterOpen }" @click="filterOpen = false"></div>
      <section class="xw-sheet" :class="{ 'is-open': filterOpen }" aria-label="筛选条件">
        <div class="xw-sheet-head">
          <strong>筛选</strong>
          <button class="xw-icon-btn" type="button" aria-label="关闭" @click="filterOpen = false">
            <LineIcon name="close" :size="18" />
          </button>
        </div>

        <div class="sheet-block">
          <h4>类目</h4>
          <div class="xw-chip-row">
            <button
              type="button"
              class="xw-chip"
              :class="{ 'is-active': !filters.categoryId }"
              @click="apply({ category_id: undefined }); filterOpen = false"
            >
              全部
            </button>
            <button
              v-for="cat in flatCategories"
              :key="cat.id"
              type="button"
              class="xw-chip"
              :class="{ 'is-active': filters.categoryId === cat.id }"
              @click="apply({ category_id: cat.id }); filterOpen = false"
            >
              {{ cat.name }}
            </button>
          </div>
        </div>

        <div class="sheet-block">
          <h4>价格区间</h4>
          <div class="price-row">
            <input v-model="priceMin" class="xw-input" type="number" placeholder="最低" />
            <span class="dash">—</span>
            <input v-model="priceMax" class="xw-input" type="number" placeholder="最高" />
          </div>
          <div class="quick-price">
            <button
              v-for="range in quickRanges"
              :key="range.label"
              type="button"
              :class="{ active: isRangeActive(range) }"
              @click="apply(range.query); filterOpen = false"
            >
              {{ range.label }}
            </button>
          </div>
        </div>

        <div class="sheet-actions">
          <button class="xw-btn xw-btn--ghost" type="button" @click="resetAll(); filterOpen = false">
            重置
          </button>
          <button
            class="xw-btn"
            type="button"
            @click="applyPrice(); filterOpen = false"
          >
            查看 {{ total }} 件商品
          </button>
        </div>
      </section>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCategories, getProducts } from '@/api'
import ProductCard from '@/components/store/ProductCard.vue'
import LineIcon from '@/components/store/LineIcon.vue'

const route = useRoute()
const router = useRouter()

const pageSize = 12
const categories = ref([])
const items = ref([])
const total = ref(0)
const loading = ref(true)
const filterOpen = ref(false)
const priceMin = ref('')
const priceMax = ref('')

const sortOptions = [
  { label: '综合', value: 'default' },
  { label: '销量', value: 'sales_desc' },
  { label: '价格 ↑', value: 'price_asc' },
  { label: '价格 ↓', value: 'price_desc' }
]

const quickRanges = [
  { label: '¥0 - 99', query: { min_price: 0, max_price: 99 } },
  { label: '¥100 - 499', query: { min_price: 100, max_price: 499 } },
  { label: '¥500 - 1999', query: { min_price: 500, max_price: 1999 } },
  { label: '¥2000 以上', query: { min_price: 2000, max_price: undefined } }
]

const filters = computed(() => ({
  categoryId: Number(route.query.category_id) || null,
  keyword: route.query.keyword || '',
  sort: route.query.sort || 'default',
  minPrice: route.query.min_price || '',
  maxPrice: route.query.max_price || '',
  page: Number(route.query.page) || 1
}))

const nameMap = computed(() => {
  const map = {}
  const walk = (list) =>
    list.forEach((cat) => {
      map[cat.id] = cat.name
      if (cat.children?.length) walk(cat.children)
    })
  walk(categories.value)
  return map
})

const topCategories = computed(() => categories.value)
const flatCategories = computed(() => {
  const list = []
  categories.value.forEach((cat) => {
    list.push(cat)
    ;(cat.children || []).forEach((child) => list.push(child))
  })
  return list
})

const categoryName = computed(() =>
  filters.value.categoryId ? nameMap.value[filters.value.categoryId] : ''
)

function categoryNameById(id) {
  return nameMap.value[id] || '玄武选物'
}

function relatedChildren(cat) {
  if (!filters.value.categoryId) return []
  if (cat.id === filters.value.categoryId) return cat.children || []
  return (cat.children || []).some((c) => c.id === filters.value.categoryId)
    ? cat.children
    : []
}

const heading = computed(() => {
  if (filters.value.keyword) return `“${filters.value.keyword}” 的搜索结果`
  return categoryName.value || '全部商品'
})

const eyebrow = computed(() => {
  if (filters.value.keyword) return 'SEARCH'
  return categoryName.value ? 'CATEGORY' : 'ALL PRODUCTS'
})

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const pageList = computed(() => {
  const current = filters.value.page
  const list = []
  const start = Math.max(1, Math.min(current - 2, pages.value - 4))
  for (let i = start; i < start + 5 && i <= pages.value; i += 1) list.push(i)
  return list
})

const activeChips = computed(() => {
  const chips = []
  if (filters.value.categoryId && categoryName.value) {
    chips.push({ key: 'category_id', label: categoryName.value })
  }
  if (filters.value.keyword) {
    chips.push({ key: 'keyword', label: `关键词：${filters.value.keyword}` })
  }
  if (filters.value.minPrice || filters.value.maxPrice) {
    chips.push({
      key: 'price',
      label: `¥${filters.value.minPrice || 0} - ${filters.value.maxPrice || '不限'}`
    })
  }
  return chips
})

function buildQuery(patch) {
  const next = {
    category_id: filters.value.categoryId || undefined,
    keyword: filters.value.keyword || undefined,
    sort: filters.value.sort === 'default' ? undefined : filters.value.sort,
    min_price: filters.value.minPrice || undefined,
    max_price: filters.value.maxPrice || undefined,
    ...patch
  }
  Object.keys(next).forEach((key) => {
    if (next[key] === undefined || next[key] === null || next[key] === '') delete next[key]
  })
  return next
}

function apply(patch) {
  router.push({ path: '/products', query: buildQuery(patch) })
}

function goPage(page) {
  if (page < 1 || page > pages.value) return
  const query = { ...route.query }
  if (page === 1) delete query.page
  else query.page = page
  router.push({ path: '/products', query })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function applyPrice() {
  apply({
    min_price: priceMin.value === '' ? undefined : priceMin.value,
    max_price: priceMax.value === '' ? undefined : priceMax.value
  })
}

function isRangeActive(range) {
  return (
    String(filters.value.minPrice) === String(range.query.min_price ?? '') &&
    String(filters.value.maxPrice) === String(range.query.max_price ?? '')
  )
}

function removeChip(chip) {
  if (chip.key === 'category_id') apply({ category_id: undefined })
  else if (chip.key === 'keyword') apply({ keyword: undefined })
  else apply({ min_price: undefined, max_price: undefined })
}

function resetAll() {
  priceMin.value = ''
  priceMax.value = ''
  router.push({ path: '/products' })
}

async function load() {
  loading.value = true
  priceMin.value = filters.value.minPrice
  priceMax.value = filters.value.maxPrice
  try {
    const data = await getProducts({
      category_id: filters.value.categoryId || undefined,
      keyword: filters.value.keyword || undefined,
      min_price: filters.value.minPrice || undefined,
      max_price: filters.value.maxPrice || undefined,
      sort: filters.value.sort,
      page: filters.value.page,
      size: pageSize
    })
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query,
  () => {
    if (route.path === '/products') load()
  },
  { immediate: true, deep: true }
)

onMounted(async () => {
  try {
    categories.value = await getCategories()
  } catch (e) {
    categories.value = []
  }
})
</script>

<style scoped>
.crumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  color: var(--xw-muted);
  letter-spacing: 0.02em;
}

.crumb a:hover {
  color: var(--xw-ink);
}

.crumb .current {
  color: var(--xw-ink-soft);
}

.plist-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 0 26px;
  border-bottom: 1px solid var(--xw-line);
  margin-bottom: 34px;
}

.plist-head h1 {
  margin-top: 10px;
  font-size: clamp(24px, 2.6vw, 32px);
  font-weight: 500;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.plist {
  display: grid;
  grid-template-columns: 208px minmax(0, 1fr);
  gap: 48px;
  align-items: start;
}

.aside {
  position: sticky;
  top: calc(var(--xw-header-h) + 18px);
}

.aside-block {
  padding-bottom: 26px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--xw-line);
}

.aside-block h3 {
  font-size: 10.5px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--xw-muted);
  font-weight: 400;
  margin-bottom: 14px;
}

.cat-tree {
  display: grid;
  gap: 2px;
}

.cat-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 6px 0;
  border: 0;
  background: none;
  text-align: left;
  font-size: 13px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  transition: color 0.15s;
}

.cat-link:hover {
  color: var(--xw-accent);
}

.cat-link.active {
  color: var(--xw-ink);
  font-weight: 600;
}

.cat-count {
  font-size: 10.5px;
  color: var(--xw-muted);
  font-variant-numeric: tabular-nums;
}

.cat-children {
  padding-left: 12px;
  border-left: 1px solid var(--xw-line);
  margin: 2px 0 8px;
}

.cat-link.sub {
  font-size: 12.5px;
  color: var(--xw-muted);
  padding: 4px 0;
}

.cat-link.sub:hover,
.cat-link.sub.active {
  color: var(--xw-ink);
}

.price-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-row .xw-input {
  height: 38px;
  padding: 0 10px;
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
}

.dash {
  color: var(--xw-muted);
}

.apply-price {
  width: 100%;
  height: 34px;
  margin-top: 10px;
  border: 1px solid var(--xw-line-ink);
  background: transparent;
  font-size: 12px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.apply-price:hover {
  background: var(--xw-ink);
  border-color: var(--xw-ink);
  color: #f7f2e8;
}

.quick-price {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.quick-price button {
  padding: 4px 9px;
  border: 1px solid var(--xw-line);
  background: transparent;
  font-size: 11px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  font-variant-numeric: tabular-nums;
  transition: all 0.15s;
}

.quick-price button:hover {
  border-color: var(--xw-line-ink);
}

.quick-price button.active {
  background: var(--xw-ink);
  border-color: var(--xw-ink);
  color: #f7f2e8;
}

.reset {
  margin-top: 2px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--xw-line);
  margin-bottom: 22px;
}

.sorts {
  display: flex;
  align-items: center;
  gap: 22px;
}

.sorts button {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 0;
  background: none;
  padding: 3px 0;
  font-size: 13px;
  color: var(--xw-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.sorts button:hover {
  color: var(--xw-ink);
}

.sorts button.active {
  color: var(--xw-ink);
}

.sorts button.active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -15px;
  height: 1px;
  background: var(--xw-ink);
}

.sort-caret {
  transition: transform 0.2s var(--xw-ease);
}

.sort-caret.flip {
  transform: rotate(180deg);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.filter-btn {
  display: none;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--xw-line-ink);
  background: transparent;
  font-size: 12px;
  cursor: pointer;
}

.active-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.active-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--xw-line);
  background: var(--xw-surface);
  font-size: 11.5px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.active-chip:hover {
  border-color: var(--xw-accent);
  color: var(--xw-accent);
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 54px;
  padding-top: 20px;
  border-top: 1px solid var(--xw-line);
}

.pager-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: none;
  font-size: 12px;
  color: var(--xw-ink-soft);
  cursor: pointer;
  padding: 6px 0;
}

.pager-btn:disabled {
  color: #c3b9a7;
  cursor: not-allowed;
}

.pager-nums {
  display: flex;
  gap: 4px;
}

.pager-num {
  min-width: 30px;
  height: 30px;
  border: 1px solid transparent;
  background: none;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--xw-ink-soft);
  cursor: pointer;
  transition: all 0.15s;
}

.pager-num:hover {
  border-color: var(--xw-line);
}

.pager-num.active {
  background: var(--xw-ink);
  border-color: var(--xw-ink);
  color: #f7f2e8;
}

.card-skel {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.card-skel-media {
  aspect-ratio: 4 / 5;
  margin-bottom: 4px;
}

.sheet-block {
  padding-bottom: 22px;
}

.sheet-block h4 {
  font-size: 10.5px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--xw-muted);
  font-weight: 400;
  margin-bottom: 12px;
}

.sheet-block .quick-price {
  margin-top: 14px;
}

.sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  gap: 10px;
  padding-top: 8px;
}

@media (max-width: 1080px) {
  .plist {
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 32px;
  }
}

@media (max-width: 900px) {
  .plist {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .plist-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 16px 0 18px;
    margin-bottom: 20px;
  }
  .filter-btn {
    display: inline-flex;
  }
  .toolbar {
    position: sticky;
    top: var(--xw-header-h);
    z-index: 20;
    background: var(--xw-paper);
    padding: 10px 0;
    margin-bottom: 16px;
  }
  .sorts {
    gap: 16px;
    overflow-x: auto;
    scrollbar-width: none;
  }
  .sorts::-webkit-scrollbar {
    display: none;
  }
  .sorts button {
    white-space: nowrap;
    font-size: 12.5px;
  }
  .sorts button.active::after {
    bottom: -11px;
  }
  .toolbar-right .xw-meta {
    display: none;
  }
  .pager {
    margin-top: 34px;
  }
  .pager-btn {
    font-size: 11.5px;
  }
  .pager-num {
    min-width: 26px;
    height: 26px;
  }
}
</style>

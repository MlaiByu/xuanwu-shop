<template>
  <div class="xw-shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="xw-eyebrow">2026 秋冬 · 选物第 04 辑</p>
        <h1 class="xw-h1">值得买的东西，<br />其实不多。</h1>
        <p class="xw-lede">
          24 个类目、{{ total || 34 }} 件在售。每一件都写清楚参数、库存和出货时间——不靠
          "限时秒杀"制造紧迫感，也不把价格藏在角落里。
        </p>
        <div class="hero-actions">
          <RouterLink class="xw-btn xw-btn--lg" to="/products">
            逛全部商品
            <LineIcon name="arrow-right" :size="16" />
          </RouterLink>
          <RouterLink
            class="xw-btn xw-btn--lg xw-btn--ghost"
            :to="{ path: '/products', query: { sort: 'sales_desc' } }"
          >
            看销量榜
          </RouterLink>
        </div>
        <dl class="hero-stats">
          <div>
            <dt>在售商品</dt>
            <dd>{{ total || '—' }}<small>件</small></dd>
          </div>
          <div>
            <dt>覆盖类目</dt>
            <dd>{{ categoryCount || '—' }}<small>个</small></dd>
          </div>
          <div>
            <dt>发出时效</dt>
            <dd>48<small>小时内</small></dd>
          </div>
        </dl>
      </div>

      <div class="hero-art">
        <figure class="hero-figure">
          <ProductMedia
            :src="hero.main_image"
            :name="hero.name"
            :category="heroCat"
            ratio="4 / 5"
            index="01"
            eager
            class="hero-media"
          />
          <figcaption class="hero-cap">
            <div>
              <span class="xw-eyebrow">{{ heroCat }}</span>
              <RouterLink v-if="hero.id" :to="`/products/${hero.id}`" class="hero-name">
                {{ hero.name }}
              </RouterLink>
              <span v-else class="hero-name">玄武选物</span>
            </div>
            <PriceText v-if="hero.id" :value="hero.price" size="md" />
          </figcaption>
        </figure>

        <figure v-if="subHero" class="hero-sub">
          <ProductMedia
            :src="subHero.main_image"
            :name="subHero.name"
            :category="subCat"
            ratio="1 / 1"
            index="02"
          />
          <figcaption>
            <RouterLink :to="`/products/${subHero.id}`" class="hero-sub-name">
              {{ subHero.name }}
            </RouterLink>
            <PriceText :value="subHero.price" size="sm" />
          </figcaption>
        </figure>

        <span class="hero-ver">01 / 04</span>
      </div>
    </section>

    <nav class="cat-strip" aria-label="按类目浏览">
      <span class="cat-strip-label">类目</span>
      <RouterLink
        v-for="cat in topCategories"
        :key="cat.id"
        :to="{ path: '/products', query: { category_id: cat.id } }"
      >
        {{ cat.name }}
      </RouterLink>
      <RouterLink class="cat-strip-all" to="/products">
        全部 <LineIcon name="arrow-right" :size="13" />
      </RouterLink>
    </nav>

    <section class="xw-sec">
      <header class="xw-sec-head">
        <div>
          <h2>本季精选</h2>
          <p class="xw-sec-sub">按销量与复购排序，挑出这 8 件</p>
        </div>
        <RouterLink class="xw-more" to="/products">
          查看全部 <LineIcon name="arrow-right" :size="13" />
        </RouterLink>
      </header>

      <div v-if="loading" class="xw-grid">
        <div v-for="n in 8" :key="n" class="card-skel">
          <div class="xw-skel card-skel-media"></div>
          <div class="xw-skel xw-skel--text" style="width: 40%"></div>
          <div class="xw-skel xw-skel--text" style="width: 82%"></div>
          <div class="xw-skel xw-skel--text" style="width: 28%"></div>
        </div>
      </div>

      <div v-else-if="featured.length" class="xw-grid">
        <ProductCard
          v-for="(item, index) in featured"
          :key="item.id"
          :product="item"
          :category-name="categoryName(item.category_id)"
          :index="index + 1"
        />
      </div>

      <div v-else class="xw-empty">
        <h3>货架正在补货</h3>
        <p>商品接口暂时没有返回数据，稍后再试。</p>
        <button class="xw-btn xw-btn--ghost" type="button" @click="load">重新加载</button>
      </div>
    </section>

    <section class="xw-sec">
      <header class="xw-sec-head">
        <div>
          <h2>两个企划</h2>
          <p class="xw-sec-sub">不按促销节点，按生活场景来挑东西</p>
        </div>
      </header>

      <div class="features">
        <RouterLink
          v-for="item in features"
          :key="item.title"
          class="feature"
          :style="{ background: item.tint }"
          :to="{ path: '/products', query: { category_id: item.categoryId } }"
        >
          <div class="feature-copy">
            <span class="xw-eyebrow">{{ item.eyebrow }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
            <span class="feature-link">
              逛这个企划 <LineIcon name="arrow-right" :size="14" />
            </span>
          </div>
          <svg
            class="feature-art"
            viewBox="0 0 64 64"
            stroke="currentColor"
            fill="none"
            stroke-width="1"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
            v-html="item.art"
          />
        </RouterLink>
      </div>
    </section>

    <section class="promise">
      <div v-for="item in promises" :key="item.title" class="promise-item">
        <LineIcon :name="item.icon" :size="19" />
        <div>
          <h4>{{ item.title }}</h4>
          <p>{{ item.desc }}</p>
        </div>
      </div>
    </section>

    <section class="xw-sec note">
      <div class="note-copy">
        <p class="xw-eyebrow">关于这家店</p>
        <h2>把"买得明白"当成一种服务</h2>
      </div>
      <p class="xw-lede">
        商品页上，你能看到每个规格的真实库存、价格和预计发货时间；购物车里会提早在
        金额旁算好运费；缺货的商品不会用灰色按钮糊弄你。没有满屏的倒计时和划线价，
        剩下的判断权交回给你。
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getCategories, getProducts } from '@/api'
import ProductCard from '@/components/store/ProductCard.vue'
import ProductMedia from '@/components/store/ProductMedia.vue'
import PriceText from '@/components/store/PriceText.vue'
import LineIcon from '@/components/store/LineIcon.vue'
import { artFor } from '@/components/store/product-art'

const products = ref([])
const categories = ref([])
const total = ref(0)
const loading = ref(true)

const catMap = computed(() => {
  const map = {}
  const walk = (list) => {
    list.forEach((cat) => {
      map[cat.id] = cat.name
      if (cat.children?.length) walk(cat.children)
    })
  }
  walk(categories.value)
  return map
})

const categoryCount = computed(() => Object.keys(catMap.value).length)
const topCategories = computed(() => categories.value.slice(0, 6))
const featured = computed(() => products.value.slice(0, 8))
const hero = computed(() => products.value[0] || {})
const subHero = computed(() => products.value[1] || null)
const heroCat = computed(() => categoryName(hero.value.category_id))
const subCat = computed(() => categoryName(subHero.value?.category_id))

function categoryName(id) {
  return catMap.value[id] || '玄武选物'
}

const features = computed(() => [
  {
    eyebrow: '企划 01 · 桌面',
    title: '桌面重启计划',
    desc: '一把顺手的键盘、一只不飘的鼠标，和一块能升降的桌板。',
    tint: 'var(--xw-accent-wash)',
    art: artFor('外设配件'),
    categoryId: findCategoryId('外设配件')
  },
  {
    eyebrow: '企划 02 · 户外',
    title: '秋日户外',
    desc: '帐篷、营地灯、折叠椅：周末两天，够用就好。',
    tint: '#dfe2d6',
    art: artFor('露营装备'),
    categoryId: findCategoryId('露营装备')
  }
])

function findCategoryId(name) {
  const hit = Object.entries(catMap.value).find(([, value]) => value === name)
  return hit ? Number(hit[0]) : undefined
}

const promises = [
  { icon: 'shield', title: '正品与溯源', desc: '每件商品标注供应商与保修方式' },
  { icon: 'truck', title: '48 小时内发出', desc: '满 199 元顺丰包邮，偏远地区补差价' },
  { icon: 'returns', title: '7 天无理由', desc: '不影响二次销售即可原路退回' },
  { icon: 'spark', title: '价格说清楚', desc: '到手价 = 标价，运费单独列出' }
]

async function load() {
  loading.value = true
  const [productRes, categoryRes] = await Promise.allSettled([
    getProducts({ sort: 'sales_desc', size: 8 }),
    getCategories()
  ])
  if (productRes.status === 'fulfilled') {
    products.value = productRes.value.items || []
    total.value = productRes.value.total || 0
  }
  if (categoryRes.status === 'fulfilled') {
    categories.value = categoryRes.value || []
  }
  loading.value = false
}

onMounted(load)
</script>

<style scoped>
/* ---------- Hero ---------- */
.hero {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 64px;
  align-items: center;
  padding: 28px 0 0;
}

.hero-copy {
  max-width: 500px;
}

.hero-copy h1 {
  margin: 20px 0 22px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.hero-stats {
  display: flex;
  gap: 44px;
  margin-top: 54px;
  padding-top: 20px;
  border-top: 1px solid var(--xw-line);
}

.hero-stats dt {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: var(--xw-muted);
  text-transform: uppercase;
}

.hero-stats dd {
  margin-top: 6px;
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.hero-stats dd small {
  margin-left: 5px;
  font-size: 11px;
  color: var(--xw-muted);
  letter-spacing: 0;
}

.hero-art {
  position: relative;
  padding: 0 0 64px 64px;
}

.hero-figure {
  position: relative;
  z-index: 1;
  background: var(--xw-surface);
  padding: 12px 12px 0;
  box-shadow: 0 40px 70px -54px rgba(26, 22, 17, 0.7);
}

.hero-cap {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 4px 16px;
}

.hero-cap .xw-eyebrow {
  display: block;
  margin-bottom: 5px;
}

.hero-name {
  display: block;
  font-size: 14px;
  letter-spacing: -0.01em;
}

.hero-name:hover {
  color: var(--xw-accent);
}

.hero-sub {
  position: absolute;
  left: 0;
  bottom: 0;
  z-index: 2;
  width: 45%;
  padding: 9px 9px 10px;
  background: var(--xw-surface);
  box-shadow: 0 24px 44px -34px rgba(26, 22, 17, 0.65);
}

.hero-sub figcaption {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 9px 2px 2px;
}

.hero-sub-name {
  font-size: 11.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.hero-sub-name:hover {
  color: var(--xw-accent);
}

.hero-ver {
  position: absolute;
  right: 0;
  bottom: 14px;
  font-family: var(--xw-font-serif);
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--xw-muted);
}

/* ---------- 类目条 ---------- */
.cat-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 20px;
  margin-top: 56px;
  padding: 16px 0;
  border-top: 1px solid var(--xw-line);
  border-bottom: 1px solid var(--xw-line);
}

.cat-strip-label {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--xw-muted);
  text-transform: uppercase;
  margin-right: 6px;
}

.cat-strip a {
  font-size: 13px;
  color: var(--xw-ink-soft);
  transition: color 0.16s;
}

.cat-strip a:hover {
  color: var(--xw-accent);
}

.cat-strip-all {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px !important;
  color: var(--xw-muted) !important;
}

/* ---------- 骨架 ---------- */
.card-skel {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.card-skel-media {
  aspect-ratio: 4 / 5;
  margin-bottom: 4px;
}

/* ---------- 企划 ---------- */
.features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.feature {
  position: relative;
  display: block;
  min-height: 260px;
  padding: 32px;
  overflow: hidden;
  color: var(--xw-ink);
}

.feature-copy {
  position: relative;
  z-index: 1;
  max-width: 62%;
}

.feature h3 {
  margin: 14px 0 10px;
  font-size: 24px;
  font-weight: 500;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.feature p {
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--xw-ink-soft);
}

.feature-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 26px;
  font-size: 12px;
  letter-spacing: 0.06em;
  padding-bottom: 3px;
  border-bottom: 1px solid rgba(26, 22, 17, 0.35);
  transition: gap 0.2s var(--xw-ease);
}

.feature:hover .feature-link {
  gap: 10px;
}

.feature-art {
  position: absolute;
  right: -12px;
  bottom: -18px;
  width: 46%;
  max-width: 220px;
  height: auto;
  opacity: 0.36;
  color: var(--xw-ink);
}

/* ---------- 服务承诺 ---------- */
.promise {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin-top: 72px;
  border-top: 1px solid var(--xw-line);
  border-bottom: 1px solid var(--xw-line);
}

.promise-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 24px 22px;
  border-left: 1px solid var(--xw-line);
  color: var(--xw-ink-soft);
}

.promise-item:first-child {
  border-left: 0;
  padding-left: 0;
}

.promise-item h4 {
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--xw-ink);
}

.promise-item p {
  margin-top: 4px;
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--xw-muted);
}

/* ---------- 店招 ---------- */
.note {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 48px;
  align-items: start;
  padding: 44px 0 8px;
  border-top: 1px solid var(--xw-line);
}

.note h2 {
  margin-top: 14px;
  font-size: clamp(20px, 2vw, 26px);
  font-weight: 500;
  letter-spacing: -0.025em;
}

.note .xw-lede {
  font-size: 14px;
}

@media (max-width: 1080px) {
  .hero {
    gap: 36px;
  }
  .hero-art {
    padding-left: 36px;
  }
  .promise {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .promise-item:nth-child(3) {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--xw-line);
  }
  .promise-item:nth-child(4) {
    border-top: 1px solid var(--xw-line);
  }
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    gap: 32px;
    padding-top: 12px;
  }
  .hero-copy {
    max-width: none;
    order: 2;
  }
  .hero-art {
    order: 1;
    padding: 0;
  }
  .hero-sub {
    display: none;
  }
  .hero-figure {
    padding: 8px 8px 0;
  }
  .hero-media {
    aspect-ratio: 1 / 1;
  }
  .hero-cap {
    padding: 10px 2px 12px;
  }
  .hero-stats {
    gap: 28px;
    margin-top: 34px;
  }
  .hero-stats dd {
    font-size: 18px;
  }
  .cat-strip {
    margin-top: 34px;
    gap: 10px 16px;
  }
  .cat-strip-all {
    margin-left: 0;
  }
  .features {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .feature {
    min-height: 210px;
    padding: 24px 22px;
  }
  .feature-copy {
    max-width: 72%;
  }
  .feature h3 {
    font-size: 20px;
  }
  .promise {
    grid-template-columns: 1fr;
    margin-top: 48px;
  }
  .promise-item {
    border-left: 0;
    border-top: 1px solid var(--xw-line);
    padding: 18px 0;
  }
  .promise-item:first-child {
    border-top: 0;
  }
  .note {
    grid-template-columns: 1fr;
    gap: 18px;
    padding-top: 32px;
  }
}
</style>

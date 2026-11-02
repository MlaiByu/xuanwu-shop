<template>
  <div class="xw-announce">
    <div class="xw-shell">
      <span>新客首单立减 30 元 · 全场满 199 顺丰包邮</span>
      <span class="xw-announce-right">
        <span>7 天无理由退换</span>
        <span>客服 400-020-1799</span>
      </span>
    </div>
  </div>

  <header class="xw-header" :class="{ 'is-stuck': stuck }">
    <div class="xw-shell xw-header-inner">
      <button
        class="xw-icon-btn xw-only-mobile"
        type="button"
        aria-label="打开菜单"
        @click="menuOpen = true"
      >
        <LineIcon name="menu" :size="21" />
      </button>

      <RouterLink to="/" class="xw-brand" aria-label="玄武商城首页">
        <span class="xw-brand-cn">玄武</span>
        <span class="xw-brand-en">XUANWU</span>
      </RouterLink>

      <nav class="xw-nav xw-only-desktop" aria-label="商品分类">
        <RouterLink to="/products" :class="{ 'is-active': isNavActive(null) }">
          全部商品
        </RouterLink>
        <RouterLink
          v-for="cat in navCats"
          :key="cat.id"
          :to="{ path: '/products', query: { category_id: cat.id } }"
          :class="{ 'is-active': isNavActive(cat.id) }"
        >
          {{ cat.name }}
        </RouterLink>
      </nav>

      <div class="xw-header-right">
        <button
          class="xw-search-trigger xw-only-desktop"
          type="button"
          @click="searchOpen = true"
        >
          <LineIcon name="search" :size="15" />
          <span>搜索商品</span>
          <kbd>/</kbd>
        </button>

        <button
          class="xw-icon-btn xw-only-mobile"
          type="button"
          aria-label="搜索"
          @click="searchOpen = true"
        >
          <LineIcon name="search" :size="20" />
        </button>

        <div v-if="userStore.isLoggedIn" ref="accountRef" class="xw-account xw-only-desktop">
          <button
            class="xw-account-btn"
            type="button"
            :aria-expanded="accountOpen"
            @click="accountOpen = !accountOpen"
          >
            <LineIcon name="user" :size="17" />
            <span class="xw-account-name">{{ userStore.user?.nickname || '我的账户' }}</span>
            <LineIcon name="chevron-down" :size="13" />
          </button>
          <div v-if="accountOpen" class="xw-account-menu">
            <button type="button" @click="go('/orders')">我的订单</button>
            <button type="button" @click="go('/addresses')">收货地址</button>
            <button
              v-if="userStore.user?.role === 'merchant'"
              type="button"
              @click="go('/merchant')"
            >
              商家中心
            </button>
            <button v-if="userStore.isAdmin" type="button" @click="go('/admin')">
              管理后台
            </button>
            <div class="sep"></div>
            <button type="button" @click="logout">退出登录</button>
          </div>
        </div>

        <RouterLink
          v-else
          to="/login"
          class="xw-account-btn xw-only-desktop"
          style="text-decoration: none"
        >
          <LineIcon name="user" :size="17" />
          <span>登录 / 注册</span>
        </RouterLink>

        <RouterLink to="/cart" class="xw-icon-btn" aria-label="购物车">
          <LineIcon name="bag" :size="21" />
          <span v-if="cartStore.count > 0" class="xw-count">{{
            cartStore.count > 99 ? '99+' : cartStore.count
          }}</span>
        </RouterLink>
      </div>
    </div>
  </header>

  <StoreSearch v-model:open="searchOpen" :hot="hotKeywords" />

  <Teleport to="body">
    <div class="xw-mask" :class="{ 'is-open': menuOpen }" @click="menuOpen = false"></div>
    <aside class="xw-drawer" :class="{ 'is-open': menuOpen }" aria-label="站点菜单">
      <div class="xw-drawer-head">
        <span class="xw-brand">
          <span class="xw-brand-cn">玄武</span>
          <span class="xw-brand-en">XUANWU</span>
        </span>
        <button class="xw-icon-btn" type="button" aria-label="关闭菜单" @click="menuOpen = false">
          <LineIcon name="close" :size="19" />
        </button>
      </div>

      <RouterLink to="/products" class="xw-drawer-link" @click="menuOpen = false">
        全部商品 <LineIcon name="arrow-right" :size="15" />
      </RouterLink>
      <RouterLink
        v-for="cat in navCats"
        :key="cat.id"
        :to="{ path: '/products', query: { category_id: cat.id } }"
        class="xw-drawer-link"
        @click="menuOpen = false"
      >
        {{ cat.name }} <LineIcon name="chevron-right" :size="14" />
      </RouterLink>

      <div class="xw-drawer-block">
        <h4>我的账户</h4>
        <template v-if="userStore.isLoggedIn">
          <RouterLink to="/orders" class="xw-drawer-link" @click="menuOpen = false">
            我的订单
          </RouterLink>
          <RouterLink to="/addresses" class="xw-drawer-link" @click="menuOpen = false">
            收货地址
          </RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/login" class="xw-drawer-link" @click="menuOpen = false">
            登录 / 注册
          </RouterLink>
        </template>
      </div>

      <div class="xw-drawer-block">
        <h4>服务</h4>
        <p class="xw-meta">客服 400-020-1799（每日 9:00 - 22:00）</p>
        <p class="xw-meta">满 199 顺丰包邮 · 7 天无理由退换</p>
      </div>
    </aside>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCategories } from '@/api'
import { useUserStore } from '@/store/user'
import { useCartStore } from '@/store/cart'
import LineIcon from './LineIcon.vue'
import StoreSearch from './StoreSearch.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const cartStore = useCartStore()

const categories = ref([])
const searchOpen = ref(false)
const menuOpen = ref(false)
const accountOpen = ref(false)
const stuck = ref(false)
const accountRef = ref(null)

const navCats = computed(() => categories.value.slice(0, 4))
const hotKeywords = computed(() => {
  const list = []
  categories.value.forEach((cat) => {
    ;(cat.children || []).slice(0, 3).forEach((child) => list.push(child))
  })
  return !list.length ? categories.value.slice(0, 6) : list.slice(0, 8)
})

/**
 * 导航高亮必须同时看 path 和 query。
 * vue-router 的 router-link-active 只比 path，/products?category_id=1 与
 * ?category_id=10 会被同时判为 active，导致所有分类项都带下划线。
 */
function isNavActive(categoryId) {
  if (route.path !== '/products') return false
  const current = route.query.category_id ? String(route.query.category_id) : null
  if (categoryId === null) return !current && !route.query.keyword
  return current === String(categoryId)
}

function go(path) {
  accountOpen.value = false
  router.push(path)
}

function logout() {
  accountOpen.value = false
  userStore.logout()
  cartStore.$reset()
  ElMessage.success('已退出登录')
  router.push('/')
}

function onScroll() {
  stuck.value = window.scrollY > 6
}

function onKeydown(event) {
  const tag = document.activeElement?.tagName
  const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'
  if (event.key === '/' && !typing) {
    event.preventDefault()
    searchOpen.value = true
  }
  if (event.key === 'Escape') {
    searchOpen.value = false
    menuOpen.value = false
    accountOpen.value = false
  }
}

function onDocumentClick(event) {
  if (accountRef.value && !accountRef.value.contains(event.target)) {
    accountOpen.value = false
  }
}

function lockScroll(locked) {
  document.body.style.overflow = locked ? 'hidden' : ''
}

watch([searchOpen, menuOpen], ([search, menu]) => lockScroll(search || menu))

onMounted(async () => {
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onDocumentClick)
  cartStore.load()
  try {
    categories.value = await getCategories()
  } catch (e) {
    categories.value = []
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onDocumentClick)
  lockScroll(false)
})
</script>

<style scoped>
.xw-account-name {
  max-width: 84px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.xw-drawer-block {
  padding-top: 22px;
}

.xw-drawer-block h4 {
  font-size: 10.5px;
  letter-spacing: 0.16em;
  color: var(--xw-muted);
  font-weight: 400;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.xw-drawer-block .xw-meta {
  margin-top: 6px;
}
</style>

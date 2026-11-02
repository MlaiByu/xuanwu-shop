import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/UserLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/Home.vue') },
      { path: 'products', name: 'products', component: () => import('@/views/ProductList.vue') },
      { path: 'products/:id', name: 'product-detail', component: () => import('@/views/ProductDetail.vue') },
      { path: 'cart', name: 'cart', component: () => import('@/views/Cart.vue') },
      { path: 'checkout', name: 'checkout', component: () => import('@/views/Checkout.vue'), meta: { requiresAuth: true } },
      { path: 'orders', name: 'orders', component: () => import('@/views/Orders.vue'), meta: { requiresAuth: true } },
      { path: 'orders/:id', name: 'order-detail', component: () => import('@/views/OrderDetail.vue'), meta: { requiresAuth: true } },
      { path: 'addresses', name: 'addresses', component: () => import('@/views/Address.vue'), meta: { requiresAuth: true } }
    ]
  },
  {
    path: '/login',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [{ path: '', name: 'login', component: () => import('@/views/Login.vue') }]
  },
  {
    path: '/register',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [{ path: '', name: 'register', component: () => import('@/views/Register.vue') }]
  },
  { path: '/merchant/apply', name: 'merchant-apply', component: () => import('@/views/merchant/Apply.vue'), meta: { requiresAuth: true } },
  {
    path: '/merchant',
    component: () => import('@/layouts/MerchantLayout.vue'),
    meta: { requiresAuth: true, requiresMerchant: true },
    children: [
      { path: '', redirect: '/merchant/products' },
      { path: 'products', name: 'merchant-products', component: () => import('@/views/merchant/Products.vue') },
      { path: 'orders', name: 'merchant-orders', component: () => import('@/views/merchant/Orders.vue') },
      { path: 'profile', name: 'merchant-profile', component: () => import('@/views/merchant/Profile.vue') }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/products' },
      { path: 'products', name: 'admin-products', component: () => import('@/views/admin/Products.vue') },
      { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/Categories.vue') },
      { path: 'orders', name: 'admin-orders', component: () => import('@/views/admin/Orders.vue') },
      { path: 'merchants', name: 'admin-merchants', component: () => import('@/views/admin/Merchants.vue'), meta: { requiresSuperAdmin: true } },
      { path: 'admins', name: 'admin-admins', component: () => import('@/views/admin/Admins.vue'), meta: { requiresSuperAdmin: true } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  // 用 Pinia store 作为唯一运行时事实源，localStorage 仅作展示层持久化（动态导入规避循环依赖）
  const { useUserStore } = await import('@/store/user')
  const userStore = useUserStore()
  const user = userStore.user

  if (to.meta.requiresAuth && !user) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !user?.is_admin) {
    return { path: '/' }
  }
  if (to.meta.requiresSuperAdmin && user?.role !== 'super_admin') {
    return { path: '/admin/products' }
  }
  if (to.meta.requiresMerchant && user?.role !== 'merchant') {
    return { path: '/merchant/apply' }
  }
})

export default router

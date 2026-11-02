<template>
  <el-container class="admin">
    <el-aside width="210px" class="aside">
      <div class="brand">
        <el-icon :size="20"><Shop /></el-icon>
        <span>玄武商城 · 后台</span>
      </div>
      <el-menu :default-active="$route.path" router class="menu">
        <el-menu-item index="/admin/products"><el-icon><Goods /></el-icon>商品管理</el-menu-item>
        <el-menu-item index="/admin/categories"><el-icon><Menu /></el-icon>分类管理</el-menu-item>
        <el-menu-item index="/admin/orders"><el-icon><List /></el-icon>订单管理</el-menu-item>
        <template v-if="userStore.user?.role === 'super_admin'">
          <el-menu-item index="/admin/merchants"><el-icon><Shop /></el-icon>商家审核</el-menu-item>
          <el-menu-item index="/admin/admins"><el-icon><UserFilled /></el-icon>管理员管理</el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top">
        <span class="welcome">你好，{{ userStore.user?.nickname }}</span>
        <el-button @click="backHome">返回商城</el-button>
        <el-button type="danger" plain @click="logout">退出</el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
const router = useRouter()
const userStore = useUserStore()
function backHome() { router.push('/') }
function logout() { userStore.logout(); router.push('/login') }
</script>

<style scoped>
.admin { min-height: 100vh; background: var(--bg); }
.aside { background: #ffffff; border-right: 1px solid var(--border); }
.brand { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 20px 12px; font-weight: 700; font-size: 16px; color: var(--brand); border-bottom: 1px solid var(--border); }
.menu { border-right: none; }
.menu .el-menu-item.is-active { background: var(--brand-lighter); color: var(--brand); font-weight: 500; border-right: 3px solid var(--brand); }
.top { background: #fff; display: flex; align-items: center; justify-content: flex-end; gap: 12px; border-bottom: 1px solid var(--border); }
.welcome { margin-right: auto; color: var(--text-2); }
.main { padding: var(--sp-5); }
</style>


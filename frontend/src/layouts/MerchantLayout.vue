<template>
  <el-container class="merchant">
    <el-aside width="210px" class="aside">
      <div class="brand">
        <el-icon :size="20"><Shop /></el-icon>
        <span>商家中心</span>
      </div>
      <el-menu :default-active="$route.path" router class="menu">
        <el-menu-item index="/merchant/products"><el-icon><Goods /></el-icon>商品管理</el-menu-item>
        <el-menu-item index="/merchant/orders"><el-icon><List /></el-icon>订单管理</el-menu-item>
        <el-menu-item index="/merchant/profile"><el-icon><User /></el-icon>店铺信息</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top">
        <span class="welcome">{{ shopName }}</span>
        <el-button @click="$router.push('/')">返回商城</el-button>
        <el-button type="danger" plain @click="logout">退出</el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { getMerchantProfile } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const shopName = ref('')

async function loadProfile() {
  try { shopName.value = (await getMerchantProfile()).shop_name } catch (e) {}
}
function logout() { userStore.logout(); router.push('/login') }
onMounted(loadProfile)
</script>

<style scoped>
.merchant { min-height: 100vh; background: var(--bg); }
.aside { background: #fff; border-right: 1px solid var(--border); }
.brand { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 20px 12px; font-weight: 700; font-size: 16px; color: #534AB7; border-bottom: 1px solid var(--border); }
.menu { border-right: none; }
.menu .el-menu-item.is-active { background: #EEEDFE; color: #534AB7; font-weight: 500; border-right: 3px solid #534AB7; }
.top { background: #fff; display: flex; align-items: center; justify-content: flex-end; gap: 12px; border-bottom: 1px solid var(--border); }
.welcome { margin-right: auto; color: var(--text-2); }
.main { padding: var(--sp-5); }
</style>

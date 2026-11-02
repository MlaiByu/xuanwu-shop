<template>
  <div class="apply">
    <el-card class="box">
      <template #header><span class="title">申请入驻商家</span></template>
      <el-form label-width="80px" @submit.prevent>
        <el-form-item label="店铺名称">
          <el-input v-model="shopName" placeholder="2-50 个字符" maxlength="50" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="remark" type="textarea" :rows="3" placeholder="选填，介绍你的店铺" disabled />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="submit">提交申请</el-button>
      </el-form>
      <div class="tip">提交后由平台超级管理员审核，通过后即可登录商家中心管理商品。</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { applyMerchant } from '@/api'

const router = useRouter()
const shopName = ref('')
const remark = ref('')
const loading = ref(false)

async function submit() {
  if (shopName.value.trim().length < 2) { ElMessage.warning('店铺名称至少 2 个字符'); return }
  loading.value = true
  try {
    await applyMerchant({ shop_name: shopName.value.trim() })
    ElMessage.success('申请已提交，请等待审核')
    router.push('/')
  } catch (e) {} finally { loading.value = false }
}
</script>

<style scoped>
.apply { display: flex; justify-content: center; padding: 60px 20px; min-height: 100vh; background: var(--bg); }
.box { width: 480px; }
.title { font-weight: 600; }
.tip { margin-top: 16px; color: var(--text-3); font-size: 13px; }
</style>

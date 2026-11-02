<template>
  <el-card v-if="profile" class="box">
    <template #header><span class="title">店铺信息</span></template>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="店铺名称">{{ profile.shop_name }}</el-descriptions-item>
      <el-descriptions-item label="账号邮箱">{{ profile.user_email }}</el-descriptions-item>
      <el-descriptions-item label="入驻状态">
        <el-tag :type="statusType">{{ statusLabel }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item v-if="profile.audit_remark" label="审核备注">{{ profile.audit_remark }}</el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMerchantProfile } from '@/api'

const profile = ref(null)
const statusLabel = computed(() => ({ pending: '待审核', approved: '已通过', rejected: '已驳回' }[profile.value?.status] || profile.value?.status))
const statusType = computed(() => ({ pending: 'warning', approved: 'success', rejected: 'danger' }[profile.value?.status] || 'info'))

onMounted(async () => { profile.value = await getMerchantProfile() })
</script>

<style scoped>
.box { max-width: 600px; }
.title { font-weight: 600; }
</style>

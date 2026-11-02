<template>
  <div>
    <div class="head">
      <el-radio-group v-model="status" @change="load">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已驳回</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="items" v-loading="loading">
      <el-table-column prop="shop_name" label="店铺名称" min-width="160" />
      <el-table-column prop="user_email" label="账号" min-width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><el-tag :type="typeMap[row.status]">{{ labelMap[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="audit_remark" label="审核备注" min-width="140" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" type="success" size="small" @click="approve(row)">通过</el-button>
          <el-button v-if="row.status === 'pending'" type="danger" size="small" @click="reject(row)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMerchants, approveMerchant, rejectMerchant } from '@/api'

const items = ref([])
const status = ref('all')
const loading = ref(false)
const labelMap = { pending: '待审核', approved: '已通过', rejected: '已驳回' }
const typeMap = { pending: 'warning', approved: 'success', rejected: 'danger' }

async function load() {
  loading.value = true
  try { items.value = await getMerchants({ status: status.value }) } catch (e) {} finally { loading.value = false }
}
async function approve(row) {
  await approveMerchant(row.id)
  ElMessage.success('已通过')
  await load()
}
async function reject(row) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回入驻', { inputType: 'textarea' })
  await rejectMerchant(row.id, value)
  ElMessage.success('已驳回')
  await load()
}
onMounted(load)
</script>

<style scoped>
.head { margin-bottom: 16px; }
</style>

<template>
  <div>
    <div class="head">
      <el-input v-model="query.order_no" placeholder="订单号" clearable style="width:220px" @keyup.enter="load" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width:130px" @change="load">
        <el-option v-for="(v, k) in statusMap" :key="k" :label="v" :value="k" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="items" v-loading="loading">
      <el-table-column prop="order_no" label="订单号" width="200" />
      <el-table-column label="金额" width="120"><template #default="{ row }">{{ formatPrice(row.total_amount) }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="typeMap[row.status]">{{ statusMap[row.status] }}</el-tag></template></el-table-column>
      <el-table-column label="下单时间" width="180"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.status === 'paid'" type="primary" size="small" @click="ship(row)">发货</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager" v-if="total > 0">
      <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="query.size" :current-page="query.page" @current-change="onPage" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminGetOrders, adminShipOrder } from '@/api'
import { formatPrice } from '@/utils/format'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ order_no: '', status: '', page: 1, size: 10 })
const statusMap = { pending: '待支付', paid: '待发货', shipped: '待收货', completed: '已完成', cancelled: '已取消' }
const typeMap = { pending: 'warning', paid: 'primary', shipped: 'info', completed: 'success', cancelled: 'info' }
const formatTime = (t) => new Date(t).toLocaleString('zh-CN')

async function load() {
  loading.value = true
  try {
    const data = await adminGetOrders({ order_no: query.order_no || undefined, status: query.status || undefined, page: query.page, size: query.size })
    items.value = data.items
    total.value = data.total
  } catch (e) {} finally { loading.value = false }
}
function onPage(p) { query.page = p; load() }
async function ship(row) { await adminShipOrder(row.id); ElMessage.success('已发货'); await load() }
onMounted(load)
</script>

<style scoped>
.head { display: flex; gap: 10px; margin-bottom: 16px; }
.pager { margin-top: 20px; display: flex; justify-content: center; }
</style>

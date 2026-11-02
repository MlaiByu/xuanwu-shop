<template>
  <div>
    <el-tabs v-model="activeTab" @tab-change="load">
      <el-tab-pane v-for="t in tabs" :key="t.value" :label="t.label" :name="t.value" />
    </el-tabs>

    <el-table :data="orders" v-loading="loading">
      <el-table-column prop="order_no" label="订单号" width="220" />
      <el-table-column label="商品" min-width="220">
        <template #default="{ row }">
          <div class="goods">
            <img v-if="row.preview_image" :src="row.preview_image" class="img" alt="" />
            <span>{{ row.preview_name }} 等 {{ row.total_quantity }} 件</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">{{ formatPrice(row.total_amount) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><el-tag :type="typeMap[row.status]">{{ statusMap[row.status] }}</el-tag></template>
      </el-table-column>
      <el-table-column label="下单时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loading && orders.length === 0" description="暂无订单" />

    <div class="pager" v-if="total > 0">
      <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="size" :current-page="page" @current-change="onPage" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMerchantOrders } from '@/api'
import { formatPrice } from '@/utils/format'

const tabs = [
  { label: '全部', value: 'all' }, { label: '待支付', value: 'pending' },
  { label: '待发货', value: 'paid' }, { label: '待收货', value: 'shipped' },
  { label: '已完成', value: 'completed' }, { label: '已取消', value: 'cancelled' }
]
const activeTab = ref('all')
const orders = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const loading = ref(false)
const statusMap = { pending: '待支付', paid: '待发货', shipped: '待收货', completed: '已完成', cancelled: '已取消' }
const typeMap = { pending: 'warning', paid: 'primary', shipped: 'info', completed: 'success', cancelled: 'info' }
const formatTime = (t) => new Date(t).toLocaleString('zh-CN')

async function load() {
  loading.value = true
  try {
    const data = await getMerchantOrders({ status: activeTab.value, page: page.value, size })
    orders.value = data.items
    total.value = data.total
  } catch (e) {} finally { loading.value = false }
}
function onPage(p) { page.value = p; load() }
onMounted(load)
</script>

<style scoped>
.goods { display: flex; align-items: center; gap: 8px; }
.img { width: 40px; height: 40px; object-fit: cover; border-radius: 4px; }
.pager { margin-top: 20px; display: flex; justify-content: center; }
</style>

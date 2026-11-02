<template>
  <div class="xw-shell">
    <header class="xw-page-head">
      <div>
        <p class="xw-eyebrow">ACCOUNT · ADDRESSES</p>
        <h1>收货地址</h1>
        <p class="xw-meta addr-sub">共 {{ addresses.length }} 个地址，默认地址会排在结算页第一位</p>
      </div>
      <div class="head-actions">
        <RouterLink class="xw-btn xw-btn--ghost" to="/orders">我的订单</RouterLink>
        <button class="xw-btn" type="button" @click="openCreate">新增地址</button>
      </div>
    </header>

    <div v-if="loading" class="addr-grid">
      <div v-for="n in 3" :key="n" class="xw-panel addr-skel">
        <div class="xw-skel xw-skel--text" style="width: 38%; height: 14px"></div>
        <div class="xw-skel xw-skel--text" style="width: 62%"></div>
        <div class="xw-skel xw-skel--text" style="width: 88%"></div>
      </div>
    </div>

    <div v-else-if="!addresses.length" class="xw-empty">
      <h3>还没有收货地址</h3>
      <p>添加一个地址，结算时就不用重复填写了。</p>
      <button class="xw-btn" type="button" @click="openCreate">新增地址</button>
    </div>

    <div v-else class="addr-grid">
      <article
        v-for="item in addresses"
        :key="item.id"
        class="xw-panel addr-card"
        :class="{ 'is-default': item.is_default }"
      >
        <header class="addr-top">
          <div>
            <strong>{{ item.receiver }}</strong>
            <span class="addr-phone">{{ maskPhone(item.phone) }}</span>
          </div>
          <span v-if="item.is_default" class="xw-status xw-status--ok">默认</span>
        </header>

        <p class="addr-text">
          {{ item.province }}{{ item.city }}{{ item.district }}<br />
          {{ item.detail }}
        </p>

        <footer class="addr-ops">
          <button
            v-if="!item.is_default"
            class="xw-text-btn"
            type="button"
            @click="setDefault(item)"
          >
            设为默认
          </button>
          <button class="xw-text-btn" type="button" @click="openEdit(item)">编辑</button>
          <button class="xw-text-btn danger" type="button" @click="remove(item)">删除</button>
        </footer>
      </article>
    </div>

    <AddressDialog
      v-model:open="dialogOpen"
      :address="editing"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAddresses,
  removeAddress,
  setDefaultAddress
} from '@/api'
import AddressDialog from '@/components/store/AddressDialog.vue'

const addresses = ref([])
const loading = ref(true)
const dialogOpen = ref(false)
const editing = ref(null)

function maskPhone(phone) {
  return String(phone || '').replace(/^(\d{3})\d{4}(\d{4})$/, '$1****$2')
}

async function load() {
  loading.value = true
  try {
    addresses.value = await getAddresses()
  } catch (e) {
    addresses.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  dialogOpen.value = true
}

function openEdit(item) {
  editing.value = { ...item }
  dialogOpen.value = true
}

async function onSaved() {
  await load()
}

async function setDefault(item) {
  try {
    await setDefaultAddress(item.id)
    ElMessage.success('已设为默认地址')
    await load()
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function remove(item) {
  try {
    await ElMessageBox.confirm('删除后不可恢复，确定删除该地址吗？', '删除地址', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch (e) {
    return
  }
  try {
    await removeAddress(item.id)
    ElMessage.success('地址已删除')
    await load()
  } catch (e) {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<style scoped>
.addr-sub {
  margin-top: 8px;
}

.addr-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.addr-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
  transition: border-color 0.18s;
}

.addr-card:hover {
  border-color: var(--xw-line-ink);
}

.addr-card.is-default {
  border-color: var(--xw-ink);
}

.addr-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.addr-top strong {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.addr-phone {
  margin-left: 10px;
  font-size: 12px;
  color: var(--xw-muted);
  font-variant-numeric: tabular-nums;
}

.addr-text {
  flex: 1;
  margin: 14px 0 18px;
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--xw-ink-soft);
}

.addr-ops {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--xw-line);
}

.addr-ops .danger:hover {
  color: var(--xw-accent);
}

.addr-skel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  min-height: 150px;
}

@media (max-width: 1080px) {
  .addr-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .addr-grid {
    grid-template-columns: 1fr;
  }
  .xw-page-head .head-actions {
    width: 100%;
  }
  .xw-page-head .head-actions .xw-btn {
    flex: 1;
    height: 42px;
    padding: 0 12px;
    font-size: 12.5px;
  }
}
</style>

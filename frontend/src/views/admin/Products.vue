<template>
  <div>
    <div class="head">
      <el-input v-model="query.keyword" placeholder="商品名搜索" clearable style="width:200px" @keyup.enter="load" />
      <el-select v-model="query.is_active" placeholder="状态" clearable style="width:120px" @change="load">
        <el-option label="上架" :value="true" /><el-option label="下架" :value="false" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button type="success" @click="openDialog()">新增商品</el-button>
    </div>

    <el-table :data="items" v-loading="loading">
      <el-table-column label="主图" width="80">
        <template #default="{ row }"><img :src="row.main_image" class="img" alt="" /></template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column label="价格" width="160">
        <template #default="{ row }">{{ formatPrice(row.price) }} ~ {{ formatPrice(row.max_price) }}</template>
      </el-table-column>
      <el-table-column prop="sku_count" label="SKU数" width="80" />
      <el-table-column prop="sales_count" label="销量" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '上架' : '下架' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggle(row)">{{ row.is_active ? '下架' : '上架' }}</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager" v-if="total > 0">
      <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="query.size" :current-page="query.page" @current-change="onPage" />
    </div>

    <el-drawer v-model="drawerVisible" :title="editing ? '编辑商品' : '新增商品'" size="560px">
      <el-form label-width="90px">
        <el-form-item label="商品名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="分类">
          <el-cascader v-model="categoryVal" :options="categoryOptions" :props="{ value: 'id', label: 'name', checkStrictly: true }" placeholder="选择分类" clearable style="width:100%" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
        <el-form-item label="主图">
          <el-input v-model="form.main_image" placeholder="图片 URL" />
          <el-upload :show-file-list="false" :http-request="doUpload" accept="image/*">
            <el-button size="small">上传</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="上架"><el-switch v-model="form.is_active" /></el-form-item>
        <el-divider>SKU 列表（规格属性填 JSON，如 {"颜色":"红","容量":"128G"}）</el-divider>
        <SkuFormRow
          v-for="(sku, idx) in form.skus"
          :key="sku.uid"
          :model-value="sku"
          @remove="form.skus.splice(idx, 1)"
        />
        <el-button @click="addSku">添加 SKU</el-button>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminGetProducts, adminCreateProduct, adminUpdateProduct, adminDeleteProduct, adminSetProductStatus, getCategories, uploadImage } from '@/api'
import { formatPrice } from '@/utils/format'
import SkuFormRow from '@/components/SkuFormRow.vue'

const items = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const drawerVisible = ref(false)
const editing = ref(null)
const categoryOptions = ref([])
const categoryVal = ref([])
const query = reactive({ keyword: '', is_active: null, page: 1, size: 10 })
const form = reactive({ name: '', category_id: null, description: '', main_image: '', images: [], is_active: true, skus: [] })

// SKU 表单行的稳定 key：表单行无业务 id，用递增 uid 做 :key，
// 避免用数组下标（增删中间行会复用错行、输入框错位）。
let _uid = 0
function nextUid() { return 'sku-' + (++_uid) }

async function load() {
  loading.value = true
  try {
    const data = await adminGetProducts({ keyword: query.keyword || undefined, is_active: query.is_active, page: query.page, size: query.size })
    items.value = data.items
    total.value = data.total
  } catch (e) {} finally { loading.value = false }
}
function onPage(p) { query.page = p; load() }
function addSku() { form.skus.push({ uid: nextUid(), sku_code: '', attrsText: '{}', price: 0, stock: 0 }) }
function openDialog(row) {
  editing.value = row || null
  if (row) {
    Object.assign(form, { name: row.name, description: row.description, main_image: row.main_image, images: [], is_active: row.is_active, category_id: row.category_id })
    form.skus = row.skus.map(s => ({ uid: nextUid(), sku_code: s.sku_code, attrsText: JSON.stringify(s.attrs), price: Number(s.price), stock: s.stock }))
    categoryVal.value = [row.category_id]
  } else {
    Object.assign(form, { name: '', description: '', main_image: '', images: [], is_active: true, category_id: null })
    form.skus = [{ uid: nextUid(), sku_code: '', attrsText: '{}', price: 0, stock: 0 }]
    categoryVal.value = []
  }
  drawerVisible.value = true
}
function buildPayload() {
  const category_id = categoryVal.value && categoryVal.value.length ? categoryVal.value[categoryVal.value.length - 1] : form.category_id
  const skus = form.skus.map(s => ({ sku_code: s.sku_code, attrs: JSON.parse(s.attrsText), price: String(s.price), stock: s.stock }))
  return { name: form.name, category_id, description: form.description, main_image: form.main_image, images: [], is_active: form.is_active, skus }
}
async function save() {
  saving.value = true
  try {
    const payload = buildPayload()
    if (editing.value) await adminUpdateProduct(editing.value.id, payload)
    else await adminCreateProduct(payload)
    ElMessage.success('保存成功')
    drawerVisible.value = false
    await load()
  } catch (e) {} finally { saving.value = false }
}
async function toggle(row) {
  await adminSetProductStatus(row.id, !row.is_active)
  ElMessage.success('已更新')
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm('确定删除该商品？', '提示', { type: 'warning' })
  await adminDeleteProduct(row.id)
  ElMessage.success('已删除')
  await load()
}
async function doUpload(option) {
  const data = await uploadImage(option.file)
  form.main_image = data.url
  ElMessage.success('上传成功')
}
onMounted(async () => { categoryOptions.value = await getCategories(); await load() })
</script>

<style scoped>
.head { display: flex; gap: 10px; margin-bottom: 16px; }
.img { width: 50px; height: 50px; object-fit: cover; border-radius: 4px; }
.pager { margin-top: 20px; display: flex; justify-content: center; }
</style>

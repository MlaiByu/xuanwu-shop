<template>
  <div>
    <div class="head">
      <el-button type="success" @click="openDialog">新增管理员</el-button>
    </div>

    <el-table :data="items" v-loading="loading">
      <el-table-column prop="email" label="邮箱" min-width="200" />
      <el-table-column prop="nickname" label="昵称" width="140" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'super_admin' ? 'danger' : 'primary'">{{ row.role === 'super_admin' ? '超级管理员' : '管理员' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.role !== 'super_admin'">
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggle(row)">{{ row.is_active ? '禁用' : '启用' }}</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增管理员" width="420px">
      <el-form label-width="70px">
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="form.nickname" placeholder="选填" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password placeholder="8-64位，含字母数字" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdmins, createAdmin, deleteAdmin, setAdminStatus } from '@/api'

const items = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = reactive({ email: '', nickname: '', password: '' })

async function load() {
  loading.value = true
  try { items.value = await getAdmins() } catch (e) {} finally { loading.value = false }
}
function openDialog() { Object.assign(form, { email: '', nickname: '', password: '' }); dialogVisible.value = true }
async function save() {
  await createAdmin({ email: form.email, nickname: form.nickname || null, password: form.password })
  ElMessage.success('已创建')
  dialogVisible.value = false
  await load()
}
async function toggle(row) {
  await setAdminStatus(row.id, !row.is_active)
  ElMessage.success('已更新')
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm('确定删除该管理员？', '提示', { type: 'warning' })
  await deleteAdmin(row.id)
  ElMessage.success('已删除')
  await load()
}
onMounted(load)
</script>

<style scoped>
.head { margin-bottom: 16px; }
</style>

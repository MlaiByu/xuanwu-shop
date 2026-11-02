<template>
  <div>
    <div class="head">
      <el-button type="success" @click="openDialog()">新增一级分类</el-button>
    </div>
    <el-table :data="tree" v-loading="loading" row-key="id" :tree-props="{ children: 'children' }">
      <el-table-column prop="name" label="分类名称" min-width="200" />
      <el-table-column prop="level" label="层级" width="80" />
      <el-table-column prop="sort" label="排序" width="80" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button v-if="row.level < 3" size="small" @click="openDialog(null, row)">添加子分类</el-button>
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="420px">
      <el-form label-width="70px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="form.parent_id" placeholder="不选则为一级" clearable style="width:100%">
            <el-option v-for="c in flatOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCategories, adminCreateCategory, adminUpdateCategory, adminDeleteCategory } from '@/api'

const tree = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ name: '', parent_id: null, sort: 0 })

const flatOptions = computed(() => {
  const out = []
  const walk = (list) => list.forEach(c => { out.push(c); if (c.children) walk(c.children) })
  walk(tree.value)
  return out
})

async function load() { loading.value = true; try { tree.value = await getCategories() } catch (e) {} finally { loading.value = false } }
function openDialog(row, parent) {
  editing.value = row || null
  Object.assign(form, row ? { name: row.name, parent_id: row.parent_id, sort: row.sort } : { name: '', parent_id: parent ? parent.id : null, sort: 0 })
  dialogVisible.value = true
}
async function save() {
  if (editing.value) await adminUpdateCategory(editing.value.id, { name: form.name, parent_id: form.parent_id, sort: form.sort })
  else await adminCreateCategory({ name: form.name, parent_id: form.parent_id, sort: form.sort })
  ElMessage.success('保存成功')
  dialogVisible.value = false
  await load()
}
async function remove(row) {
  await ElMessageBox.confirm('确定删除该分类？', '提示', { type: 'warning' })
  await adminDeleteCategory(row.id)
  ElMessage.success('已删除')
  await load()
}
onMounted(load)
</script>

<style scoped>
.head { margin-bottom: 16px; }
</style>

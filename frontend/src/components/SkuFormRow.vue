<template>
  <div class="sku-row">
    <el-input
      :model-value="modelValue.sku_code"
      @update:model-value="modelValue.sku_code = $event"
      placeholder="SKU编码"
      style="width: 120px"
    />
    <el-input
      :model-value="modelValue.attrsText"
      @update:model-value="modelValue.attrsText = $event"
      placeholder='{"颜色":"红"}'
      style="width: 180px"
    />
    <el-input-number
      :model-value="modelValue.price"
      @update:model-value="modelValue.price = $event"
      :min="0"
      :precision="2"
      placeholder="价格"
      style="width: 120px"
    />
    <el-input-number
      :model-value="modelValue.stock"
      @update:model-value="modelValue.stock = $event"
      :min="0"
      placeholder="库存"
      style="width: 100px"
    />
    <el-button type="danger" text @click="$emit('remove')">删除</el-button>
  </div>
</template>

<script setup>
// 商品表单里的 SKU 编辑行，admin 与商家端共用。
// modelValue 是父级 reactive 数组里的行对象，这里只改它的字段、不重绑引用，
// 因此父级 form.skus 的响应式不会断。
defineProps({
  modelValue: { type: Object, required: true }
})
defineEmits(['remove'])
</script>

<style scoped>
.sku-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>

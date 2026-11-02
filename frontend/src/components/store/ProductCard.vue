<template>
  <RouterLink :to="`/products/${product.id}`" class="xw-card">
    <div class="xw-card-media">
      <span v-if="!product.has_stock" class="xw-card-flag soldout">暂时缺货</span>
      <ProductMedia
        :src="product.main_image"
        :name="product.name"
        :category="categoryName"
        :index="indexLabel"
        ratio="4 / 5"
      />
    </div>
    <div class="xw-card-body">
      <h3 class="xw-card-name">{{ product.name }}</h3>
      <div class="xw-card-foot">
        <PriceText :value="product.price" size="md" />
        <span class="xw-card-sales">已售 {{ product.sales_count }}</span>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import ProductMedia from './ProductMedia.vue'
import PriceText from './PriceText.vue'

const props = defineProps({
  product: { type: Object, required: true },
  categoryName: { type: String, default: '' },
  index: { type: Number, default: 0 }
})

const indexLabel = computed(() =>
  props.index ? String(props.index).padStart(2, '0') : ''
)
</script>

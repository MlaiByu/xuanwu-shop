<template>
  <div class="xw-media" :style="{ '--xw-media-ratio': ratio }">
    <img
      v-if="showImage"
      :src="src"
      :alt="alt || name"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      @error="failed = true"
    />
    <div
      v-else
      class="xw-plate"
      :style="{ background: tint }"
      role="img"
      :aria-label="`${name} 商品图占位`"
    >
      <span class="xw-plate-label">{{ label }}</span>
      <span v-if="index" class="xw-plate-index">{{ index }}</span>
      <svg
        viewBox="0 0 64 64"
        stroke-width="1.2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
        v-html="art"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { artFor, tintFor } from './product-art'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
  name: { type: String, default: '' },
  category: { type: String, default: '' },
  ratio: { type: String, default: '4 / 5' },
  index: { type: [String, Number], default: '' },
  eager: { type: Boolean, default: false }
})

const failed = ref(false)

// 随机占位图（picsum）与商品语义无关，直接走铜版兜底
const isDemoPlaceholder = computed(() =>
  /picsum\.photos|placehold\.co|via\.placeholder|loremflickr/i.test(props.src || '')
)

const showImage = computed(() => !!props.src && !failed.value && !isDemoPlaceholder.value)

const art = computed(() => artFor(props.category, props.name))
const tint = computed(() => tintFor(props.name || props.category))
const label = computed(() => props.category || 'XUANWU')
</script>

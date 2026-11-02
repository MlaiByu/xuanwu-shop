<template>
  <span class="xw-price" :class="`xw-price--${size}`">
    <span class="unit">¥</span><span class="int">{{ parts.int }}</span><span
      v-if="showCents"
      class="cents"
      >.{{ parts.cents }}</span
    >
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [String, Number], default: 0 },
  size: { type: String, default: 'md' },
  showCents: { type: Boolean, default: true }
})

const parts = computed(() => {
  const num = Number(props.value || 0)
  const [int, cents] = num.toFixed(2).split('.')
  return { int: Number(int).toLocaleString('zh-CN'), cents }
})
</script>

<style scoped>
.xw-price {
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  color: var(--xw-ink);
  line-height: 1;
  white-space: nowrap;
}

.xw-price .unit {
  font-size: 0.62em;
  margin-right: 1px;
}

.xw-price .cents {
  font-size: 0.7em;
}

.xw-price--sm {
  font-size: 13px;
}

.xw-price--md {
  font-size: 15px;
}

.xw-price--lg {
  font-size: 24px;
}

.xw-price--xl {
  font-size: 34px;
  letter-spacing: -0.03em;
}
</style>

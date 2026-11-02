<template>
  <div class="xw-stepper" :class="{ 'is-disabled': disabled }">
    <button
      type="button"
      aria-label="减少数量"
      :disabled="disabled || modelValue <= min"
      @click="step(-1)"
    >
      <LineIcon name="minus" :size="13" />
    </button>
    <input
      :value="modelValue"
      type="number"
      inputmode="numeric"
      :min="min"
      :max="max"
      :disabled="disabled"
      aria-label="购买数量"
      @change="onInput"
      @blur="onInput"
    />
    <button
      type="button"
      aria-label="增加数量"
      :disabled="disabled || modelValue >= max"
      @click="step(1)"
    >
      <LineIcon name="plus" :size="13" />
    </button>
  </div>
</template>

<script setup>
import LineIcon from './LineIcon.vue'

const props = defineProps({
  modelValue: { type: Number, default: 1 },
  min: { type: Number, default: 1 },
  max: { type: Number, default: 999 },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

function clamp(value) {
  const n = Math.round(Number(value))
  if (Number.isNaN(n)) return props.min
  return Math.min(props.max, Math.max(props.min, n))
}

function step(delta) {
  if (props.disabled) return
  emit('update:modelValue', clamp(props.modelValue + delta))
}

function onInput(event) {
  const next = clamp(event.target.value)
  event.target.value = next
  emit('update:modelValue', next)
}
</script>

<style scoped>
.is-disabled {
  opacity: 0.5;
}
</style>

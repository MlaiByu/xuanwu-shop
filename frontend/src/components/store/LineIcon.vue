<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke-width="strokeWidth"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    v-html="path"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 1.5 }
})

// 安全约束：模板里的 v-html="path" 只能渲染下面 ICONS 这个封闭静态映射里的内容。
// 严禁把用户输入、接口字段或任何动态字符串喂进 v-html，否则即 XSS 入口。
const ICONS = {
  search: '<circle cx="11" cy="11" r="6.4"/><path d="M16 16l4.6 4.6"/>',
  bag: '<path d="M5.6 8h12.8l1 12.2H4.6z"/><path d="M9 8V6.2a3 3 0 0 1 6 0V8"/>',
  user: '<circle cx="12" cy="8.2" r="3.4"/><path d="M5 20c1.3-3.8 3.9-5.7 7-5.7s5.7 1.9 7 5.7"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h10"/>',
  close: '<path d="M5.5 5.5l13 13M18.5 5.5l-13 13"/>',
  'arrow-right': '<path d="M4 12h15"/><path d="M13.5 6.5L19 12l-5.5 5.5"/>',
  'arrow-left': '<path d="M20 12H5"/><path d="M10.5 6.5L5 12l5.5 5.5"/>',
  check: '<path d="M5 12.8l4.2 4.2L19 6.6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  'chevron-down': '<path d="M6 9.2l6 6 6-6"/>',
  'chevron-right': '<path d="M9.2 6l6 6-6 6"/>',
  filter: '<path d="M4 6.5h16M7 12h10M10 17.5h4"/>',
  truck:
    '<rect x="2.8" y="7" width="11" height="8.6" rx="1"/><path d="M13.8 10h3.6l3 3v2.6h-6.6"/><circle cx="7" cy="18" r="1.7"/><circle cx="17" cy="18" r="1.7"/>',
  shield: '<path d="M12 3.2l7 2.8v5.8c0 4.2-3 7.2-7 9-4-1.8-7-4.8-7-9V6z"/><path d="M9 12l2.2 2.2L15.4 10"/>',
  returns: '<path d="M4 11a8 8 0 1 1 2.4 6"/><path d="M4 5.5V11h5.5"/>',
  trash: '<path d="M4 7h16M9.5 7V4.8h5V7"/><path d="M6.4 7l1 13h9.2l1-13"/>',
  spark: '<path d="M12 3.5l1.9 5.2 5.2 1.9-5.2 1.9L12 17.7l-1.9-5.2L4.9 10.6l5.2-1.9z"/>',
  chat: '<path d="M20.6 12.3c0 3.8-3.8 6.9-8.5 6.9-1 0-2-.1-2.9-.4L4.2 20.8l1.3-3.5c-1.3-1.2-2.1-3-2.1-5 0-3.8 3.8-6.9 8.7-6.9s8.5 3.1 8.5 6.9z"/><path d="M8.9 12.3h.01M12.1 12.3h.01M15.3 12.3h.01"/>',
  eye: '<path d="M2.6 12S6.2 5.8 12 5.8 21.4 12 21.4 12 17.8 18.2 12 18.2 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="2.9"/>',
  'eye-off':
    '<path d="M3.8 3.8l16.4 16.4"/><path d="M9.8 5.4A8.6 8.6 0 0 1 12 5.3c5.8 0 9.4 6.7 9.4 6.7a17 17 0 0 1-2.8 3.6M6.6 6.9A17.4 17.4 0 0 0 2.6 12s3.6 6.7 9.4 6.7a8.4 8.4 0 0 0 3.7-.9"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>'
}

const path = computed(() => ICONS[props.name] || '')
</script>

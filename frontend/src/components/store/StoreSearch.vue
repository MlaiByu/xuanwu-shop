<template>
  <Teleport to="body">
    <div v-if="open" class="xw-search-layer" @click.self="close">
      <div class="xw-search-panel">
        <div class="xw-search-bar">
          <LineIcon name="search" :size="20" />
          <input
            ref="inputRef"
            v-model="keyword"
            type="search"
            placeholder="搜索商品，例如「小米 14」"
            @keyup.enter="submit(keyword)"
          />
          <button class="xw-text-btn" type="button" @click="close">ESC 关闭</button>
        </div>

        <div v-if="recent.length" class="xw-search-group">
          <h4>最近搜索</h4>
          <div class="xw-chip-row">
            <button
              v-for="item in recent"
              :key="item"
              class="xw-chip"
              type="button"
              @click="submit(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="xw-search-group">
          <h4>热门类目</h4>
          <div class="xw-chip-row">
            <button
              v-for="item in hot"
              :key="item.id"
              class="xw-chip"
              type="button"
              @click="goCategory(item.id)"
            >
              {{ item.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LineIcon from './LineIcon.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  hot: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:open'])

const RECENT_KEY = 'xw_recent_search'
const router = useRouter()
const keyword = ref('')
const recent = ref([])
const inputRef = ref(null)

function readRecent() {
  try {
    recent.value = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]').slice(0, 6)
  } catch (e) {
    recent.value = []
  }
}

function close() {
  emit('update:open', false)
}

function submit(value) {
  const word = String(value || '').trim()
  if (!word) return
  const next = [word, ...recent.value.filter((i) => i !== word)].slice(0, 6)
  localStorage.setItem(RECENT_KEY, JSON.stringify(next))
  recent.value = next
  close()
  router.push({ path: '/products', query: { keyword: word } })
}

function goCategory(id) {
  close()
  router.push({ path: '/products', query: { category_id: id } })
}

watch(
  () => props.open,
  async (value) => {
    if (value) {
      readRecent()
      await nextTick()
      inputRef.value?.focus()
    } else {
      keyword.value = ''
    }
  }
)
</script>

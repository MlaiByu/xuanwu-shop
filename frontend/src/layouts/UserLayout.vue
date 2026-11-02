<template>
  <div class="xw-store">
    <StoreHeader />
    <main class="xw-main">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </main>
    <StoreFooter />
    <StoreSupport />
  </div>
</template>

<script setup>
import StoreHeader from '@/components/store/StoreHeader.vue'
import StoreFooter from '@/components/store/StoreFooter.vue'
import StoreSupport from '@/components/store/StoreSupport.vue'
</script>

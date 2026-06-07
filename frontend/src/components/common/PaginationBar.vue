<script setup lang="ts">
defineProps<{
  page: number
  pageCount: number
  pageSize: number
  total: number
}>()

defineEmits<{
  changePage: [page: number]
  changePageSize: [size: number]
}>()
</script>

<template>
  <footer class="pagination">
    <span>共 {{ total }} 条</span>
    <div class="pagination-controls">
      <select :value="pageSize" aria-label="每页数量" @change="$emit('changePageSize', Number(($event.target as HTMLSelectElement).value))">
        <option :value="10">10 条/页</option>
        <option :value="20">20 条/页</option>
        <option :value="50">50 条/页</option>
      </select>
      <button type="button" :disabled="page <= 1" @click="$emit('changePage', page - 1)">上一页</button>
      <span>{{ page }} / {{ pageCount }}</span>
      <button type="button" :disabled="page >= pageCount" @click="$emit('changePage', page + 1)">下一页</button>
    </div>
  </footer>
</template>

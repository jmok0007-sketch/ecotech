<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
})
</script>

<template>
  <div class="stat-card card">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="hint" class="stat-hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.stat-card { display: flex; flex-direction: column; gap: 0.25rem; }
.stat-label { color: var(--color-muted); font-size: 0.85rem; }
.stat-value { font-size: 1.6rem; font-weight: 700; color: var(--color-primary); }
.stat-hint { color: var(--color-muted); font-size: 0.8rem; }
</style>

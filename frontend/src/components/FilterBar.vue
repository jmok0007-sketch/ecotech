<script setup>
defineProps({
  filters: { type: Array, default: () => [] }, // [{ key, label, options:[{value,label}], value }]
})
const emit = defineEmits(['update'])

function onChange(key, event) {
  emit('update', { key, value: event.target.value })
}
</script>

<template>
  <div class="filter-bar card">
    <div v-for="f in filters" :key="f.key" class="filter">
      <label>{{ f.label }}</label>
      <select :value="f.value" @change="(e) => onChange(f.key, e)">
        <option v-for="opt in f.options" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.filter {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.filter label {
  font-size: 0.8rem;
  color: var(--color-muted);
}
.filter select {
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
}
</style>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, default: '' },
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
})

const chartEl = ref(null)
let chart = null

function render() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  chart.setOption(props.option, true)
}

onMounted(() => {
  render()
  window.addEventListener('resize', () => chart && chart.resize())
})

onBeforeUnmount(() => {
  if (chart) chart.dispose()
})

watch(() => props.option, render, { deep: true })
</script>

<template>
  <div class="chart-card card">
    <h3 v-if="title">{{ title }}</h3>
    <div ref="chartEl" :style="{ height }"></div>
  </div>
</template>

<style scoped>
.chart-card { margin-bottom: 1rem; }
.chart-card h3 { font-size: 1rem; margin-bottom: 0.75rem; }
</style>

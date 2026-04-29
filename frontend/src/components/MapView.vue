<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  locations: { type: Array, default: () => [] },
  center: { type: Array, default: () => [-25.27, 133.77] }, // Australia
  zoom: { type: Number, default: 4 },
  height: { type: String, default: '500px' },
})

const mapEl = ref(null)
let map = null
let markerLayer = null

function renderMarkers() {
  if (!map) return
  if (markerLayer) markerLayer.remove()
  markerLayer = L.layerGroup().addTo(map)
  for (const loc of props.locations) {
    if (loc.latitude == null || loc.longitude == null) continue
    L.marker([loc.latitude, loc.longitude])
      .bindPopup(
        `<strong>${loc.facility_name || 'Facility'}</strong><br>${loc.address || ''}<br>${loc.suburb || ''} ${loc.state || ''} ${loc.postcode || ''}`
      )
      .addTo(markerLayer)
  }
}

onMounted(() => {
  map = L.map(mapEl.value).setView(props.center, props.zoom)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
  }).addTo(map)
  renderMarkers()
})

onBeforeUnmount(() => {
  if (map) map.remove()
})

watch(() => props.locations, renderMarkers, { deep: true })
</script>

<template>
  <div ref="mapEl" :style="{ height }" class="map-view"></div>
</template>

<style scoped>
.map-view {
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
</style>

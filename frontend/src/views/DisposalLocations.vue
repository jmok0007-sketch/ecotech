<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

import { api } from '@/api'
import {
  buildCategorySummary,
  buildFacilityMarkers,
  getCategoryLabel,
  getCategoryOptions,
  getFacilityBounds,
} from '../lib/ewasteMapModel'

const mapboxAccessToken = String(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '').trim()
const mapContainerRef = ref(null)
const isLoading = ref(false)
const loadError = ref('')
const searchTerm = ref('')
const selectedCategory = ref('')
const facilityRows = ref([])
const facilityMarkers = ref([])
const selectedMarkerId = ref('')
const activePipeline = ref('api')

let map = null
let mapReady = false
let activePopup = null
let activeRequestController = null
let requestTimer = null
let renderedMarkers = []

const categoryOptions = computed(() => {
  return getCategoryOptions().filter(
    (c) => c.value !== 'transfer_station' && c.value !== 'repair_reuse',
  )
})

const hasToken = computed(() => Boolean(mapboxAccessToken))

const visibleMarkers = computed(() => {
  const needle = searchTerm.value.trim().toLowerCase()

  return facilityMarkers.value.filter((marker) => {
    if (marker.category === 'transfer_station' || marker.category === 'repair_reuse') {
      return false
    }

    if (selectedCategory.value && marker.category !== selectedCategory.value) {
      return false
    }

    if (!needle) {
      return true
    }

    const haystack = [
      marker.facilityName,
      marker.address,
      marker.suburb,
      marker.postcode,
      marker.state,
      marker.categoryLabel,
      marker.source,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(needle)
  })
})

const selectedMarker = computed(
  () => visibleMarkers.value.find((marker) => marker.id === selectedMarkerId.value) || null,
)

const categorySummary = computed(() => buildCategorySummary(visibleMarkers.value))

const tokenHelpText = computed(() =>
  hasToken.value
    ? ''
    : 'Set VITE_MAPBOX_ACCESS_TOKEN in .env.local, then restart the Vite dev server.',
)

const visibleCount = computed(() => visibleMarkers.value.length)

const pipelineLabel = computed(() => {
  if (activePipeline.value === 'azure') return 'Azure API'
  return activePipeline.value || 'Unknown'
})

function buildRequestPayload() {
  return {
    resourceType: 'disposal',
    state: '',
    category: '',
    searchText: '',
    limit: 1000,
  }
}

function removeRenderedMarkers() {
  renderedMarkers.forEach((entry) => entry.remove())
  renderedMarkers = []
}

function closePopup() {
  if (activePopup) {
    activePopup.remove()
    activePopup = null
  }
}

function popupHtml(marker) {
  const rows = [
    ['Address', marker.address || 'Not provided'],
    ['Suburb', marker.suburb || 'Not provided'],
    ['Postcode', marker.postcode || 'Not provided'],
    ['State', marker.state || 'Not provided'],
    ['Category', marker.categoryLabel || getCategoryLabel(marker.category)],
  ]

  return `
    <article class="map-popup">
      <p class="map-popup__eyebrow">Disposal Site</p>
      <h3>${escapeHtml(marker.facilityName)}</h3>
      ${rows
        .map(
          ([label, value]) => `
            <div class="map-popup__row">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join('')}
    </article>
  `
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function selectMarker(marker, options = {}) {
  selectedMarkerId.value = marker.id

  if (!map) return

  closePopup()

  const popup = new mapboxgl.Popup({
    offset: 18,
    maxWidth: '320px',
    closeButton: true,
  })
    .setLngLat([marker.longitude, marker.latitude])
    .setHTML(popupHtml(marker))
    .addTo(map)

  popup.on('close', () => {
    if (activePopup === popup) {
      activePopup = null
    }
  })

  activePopup = popup

  if (!options.skipFlyTo) {
    map.flyTo({
      center: [marker.longitude, marker.latitude],
      zoom: Math.max(map.getZoom(), 8.2),
      speed: 0.9,
      essential: true,
    })
  }
}

function fitMapToMarkers(markers) {
  if (!map || !markers.length) return

  const bounds = getFacilityBounds(markers)
  if (!bounds) return

  if (bounds.minLongitude === bounds.maxLongitude && bounds.minLatitude === bounds.maxLatitude) {
    map.easeTo({
      center: [bounds.minLongitude, bounds.minLatitude],
      zoom: 8.5,
      duration: 700,
    })
    return
  }

  map.fitBounds(
    [
      [bounds.minLongitude, bounds.minLatitude],
      [bounds.maxLongitude, bounds.maxLatitude],
    ],
    {
      padding: 56,
      maxZoom: 9.5,
      duration: 700,
    },
  )
}

function renderMarkers() {
  if (!map || !mapReady) return

  removeRenderedMarkers()
  closePopup()

  renderedMarkers = visibleMarkers.value.map((marker) => {
    const element = document.createElement('button')
    element.type = 'button'
    element.className = 'facility-marker'
    element.style.backgroundColor = marker.categoryColor
    element.setAttribute('aria-label', marker.facilityName)
    element.addEventListener('click', () => {
      selectMarker(marker)
    })

    return new mapboxgl.Marker({
      element,
      anchor: 'center',
    })
      .setLngLat([marker.longitude, marker.latitude])
      .addTo(map)
  })

  if (selectedMarker.value) {
    selectMarker(selectedMarker.value, { skipFlyTo: true })
    return
  }

  fitMapToMarkers(visibleMarkers.value)
}

async function loadFacilities() {
  if (!hasToken.value) {
    loadError.value = ''
    facilityRows.value = []
    facilityMarkers.value = []
    return
  }

  if (activeRequestController) {
    activeRequestController.abort()
  }

  const controller = new AbortController()
  activeRequestController = controller
  isLoading.value = true
  loadError.value = ''

  try {
    const response = await api.searchDisposalLocations({
      signal: controller.signal,
    })
    const rows = Array.isArray(response?.items) ? response.items : []

    facilityRows.value = rows
    facilityMarkers.value = buildFacilityMarkers(rows)
    activePipeline.value = response?.meta?.pipeline || 'api'

    if (
      selectedMarkerId.value &&
      !facilityMarkers.value.some((marker) => marker.id === selectedMarkerId.value)
    ) {
      selectedMarkerId.value = ''
    }

    await nextTick()
    renderMarkers()
  } catch (error) {
    if (error?.name === 'AbortError') return

    console.error('[DisposalLocations] failed to load disposal facilities:', error)
    loadError.value = error instanceof Error ? error.message : 'Failed to load disposal facilities'
    facilityRows.value = []
    facilityMarkers.value = []
    selectedMarkerId.value = ''
    activePipeline.value = 'api'
    removeRenderedMarkers()
    closePopup()
  } finally {
    if (activeRequestController === controller) {
      activeRequestController = null
      isLoading.value = false
    }
  }
}

function queueMarkerRefresh() {
  if (requestTimer) {
    window.clearTimeout(requestTimer)
  }

  requestTimer = window.setTimeout(() => {
    requestTimer = null
    renderMarkers()
  }, 80)
}

function initialiseMap() {
  if (!hasToken.value || map || !mapContainerRef.value) return

  mapboxgl.accessToken = mapboxAccessToken
  map = new mapboxgl.Map({
    container: mapContainerRef.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [144.9631, -37.8136],
    zoom: 5.4,
  })

  map.addControl(new mapboxgl.NavigationControl(), 'top-right')

  map.on('load', () => {
    mapReady = true
    renderMarkers()
  })
}

function resetFilters() {
  selectedCategory.value = ''
  searchTerm.value = ''
}

function openDirections() {
  if (!selectedMarker.value) return

  const { longitude, latitude } = selectedMarker.value
  const url = `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

watch(visibleMarkers, () => {
  queueMarkerRefresh()
})

onMounted(async () => {
  initialiseMap()
  await loadFacilities()
})

onBeforeUnmount(() => {
  if (requestTimer) {
    window.clearTimeout(requestTimer)
  }

  if (activeRequestController) {
    activeRequestController.abort()
  }

  removeRenderedMarkers()
  closePopup()

  if (map) {
    map.remove()
    map = null
  }

  mapReady = false
})
</script>

<template>
  <section class="disposal-page">
    <header class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">Disposal Locations</p>
        <h1>Find a safe place to dispose of e-waste</h1>
        <p class="hero-text">
          Search by suburb, postcode, address, or facility name to find disposal locations near you.
        </p>
      </div>

      <div class="hero-stats">
        <article>
          <span>Visible locations</span>
          <strong>{{ visibleCount }}</strong>
          <small>Source: {{ pipelineLabel }}</small>
        </article>
      </div>
    </header>

    <div class="content-grid">
      <section class="map-panel">
        <div class="toolbar-card">
          <label>
            <span>Search</span>
            <input
              v-model.trim="searchTerm"
              type="search"
              placeholder="Facility, suburb, address, postcode"
            />
          </label>

          <label>
            <span>Category</span>
            <select v-model="selectedCategory">
              <option value="">All categories</option>
              <option
                v-for="category in categoryOptions"
                :key="category.value"
                :value="category.value"
              >
                {{ category.label }}
              </option>
            </select>
          </label>

          <div class="toolbar-actions">
            <button type="button" class="ghost" @click="resetFilters">Clear filters</button>
          </div>
        </div>

        <div class="map-frame">
          <div v-if="!hasToken" class="map-overlay map-overlay--warning">
            <h2>Mapbox token required</h2>
            <p>{{ tokenHelpText }}</p>
            <code>VITE_MAPBOX_ACCESS_TOKEN=your_token_here</code>
          </div>

          <div v-else-if="isLoading" class="map-overlay">
            <p>Loading disposal locations...</p>
          </div>

          <div v-else-if="loadError" class="map-overlay map-overlay--error">
            <h2>Unable to load disposal data</h2>
            <p>{{ loadError }}</p>
          </div>

          <div ref="mapContainerRef" class="map-container" />
        </div>
      </section>

      <aside class="side-panel">
        <section class="panel-card">
          <p class="section-label">Selected location</p>

          <template v-if="selectedMarker">
            <h2>{{ selectedMarker.facilityName }}</h2>
            <p class="support-copy selected-copy">
              Review the details below, then open directions to navigate there.
            </p>

            <div class="detail-list">
              <div class="detail-row">
                <span>Address</span>
                <strong>{{ selectedMarker.address || 'Not provided' }}</strong>
              </div>
              <div class="detail-row">
                <span>Suburb</span>
                <strong>{{ selectedMarker.suburb || 'Not provided' }}</strong>
              </div>
              <div class="detail-row">
                <span>Postcode</span>
                <strong>{{ selectedMarker.postcode || 'Not provided' }}</strong>
              </div>
              <div class="detail-row">
                <span>State</span>
                <strong>{{ selectedMarker.state || 'Not provided' }}</strong>
              </div>
              <div class="detail-row">
                <span>Category</span>
                <strong>{{ selectedMarker.categoryLabel }}</strong>
              </div>
            </div>

            <div class="panel-actions">
              <button type="button" class="primary-action" @click="openDirections">
                Navigate
              </button>
            </div>
          </template>

          <template v-else>
            <h2>Select a location</h2>
            <p class="support-copy">
              Click any point on the map to see details and navigate.
            </p>
          </template>
        </section>

        <section class="panel-card">
          <p class="section-label">Visible categories</p>
          <h2>What is currently shown</h2>
          <div class="category-list">
            <div v-for="entry in categorySummary" :key="entry.key" class="category-row">
              <span class="category-label">
                <span class="category-dot" :style="{ backgroundColor: entry.color }" />
                {{ entry.label }}
              </span>
              <strong>{{ entry.count }}</strong>
            </div>
            <p v-if="!categorySummary.length" class="support-copy">
              No disposal locations match the current filters.
            </p>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.disposal-page {
  min-height: 100vh;
  padding: 32px;
  background: linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #1f3b2d;
}

.hero-card {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 1.25rem;
  padding: 36px 40px;
  margin-bottom: 28px;
  background: linear-gradient(135deg, #f4fbf4 0%, #edf7ee 100%);
  border: 1px solid #dcebdc;
  border-radius: 28px;
  box-shadow: 0 10px 30px rgba(27, 67, 50, 0.06);
}

.hero-card::before {
  content: '';
  position: absolute;
  top: -40px;
  right: -60px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(129, 199, 132, 0.28) 0%, rgba(129, 199, 132, 0) 70%);
  pointer-events: none;
}

.hero-card::after {
  content: '';
  position: absolute;
  bottom: -60px;
  right: 180px;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(165, 214, 167, 0.18) 0%, rgba(165, 214, 167, 0) 72%);
  pointer-events: none;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #2e7d32;
  background: #e8f5e9;
  border: 1px solid #cfe8d1;
  border-radius: 999px;
  letter-spacing: 0.3px;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  position: relative;
  z-index: 1;
  margin: 0 0 12px;
  font-size: 48px;
  line-height: 1.12;
  font-weight: 800;
  color: #163828;
  letter-spacing: -0.8px;
  max-width: 900px;
}

h2 {
  margin: 0 0 12px;
  font-size: 21px;
  font-weight: 700;
  color: #173a29;
  letter-spacing: -0.2px;
}

.hero-text,
.support-copy {
  margin: 0;
  font-size: 16px;
  line-height: 1.75;
  color: #557260;
}

.selected-copy {
  margin-bottom: 16px;
}

.hero-stats {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  width: 100%;
}

.hero-stats article {
  width: 320px;
  padding: 24px 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  border: 1px solid #deebdf;
  box-shadow: 0 8px 20px rgba(27, 67, 50, 0.05);
}

.hero-stats span {
  display: block;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #3f8f46;
}

.hero-stats strong {
  display: block;
  font-size: 24px;
  font-weight: 800;
  color: #173a29;
  letter-spacing: -0.3px;
}

.hero-stats small {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: #6b8a74;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.85fr);
  gap: 20px;
  align-items: start;
}

.map-panel,
.side-panel {
  display: grid;
  gap: 20px;
}

.toolbar-card,
.panel-card {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdfb 100%);
  border: 1px solid #e2eee3;
  border-radius: 24px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(27, 67, 50, 0.05);
}

.toolbar-card {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(180px, 0.7fr) auto;
  gap: 18px;
  align-items: end;
}

label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #3f8f46;
}

label span {
  display: block;
  margin-bottom: 10px;
  font-weight: 700;
  font-size: 14px;
  color: #173a29;
}

input,
select {
  width: 100%;
  min-height: 52px;
  border: 1px solid #deebdf;
  border-radius: 16px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.9);
  color: #173a29;
  font-size: 16px;
  font-weight: 500;
  outline: none;
  box-shadow: 0 8px 20px rgba(27, 67, 50, 0.03);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

input::placeholder {
  color: #8aa091;
  font-weight: 400;
}

input:focus,
select:focus {
  border-color: #bdd8c0;
  box-shadow: 0 0 0 4px rgba(129, 199, 132, 0.12);
  background: #ffffff;
}

.toolbar-actions {
  display: flex;
  align-items: end;
}

button {
  min-height: 48px;
  border: none;
  border-radius: 999px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #cfe8d1;
}

.ghost:hover {
  background: #dff0e1;
}

.primary-action {
  background: #2e7d32;
  color: #ffffff;
  border: 1px solid #2e7d32;
}

.primary-action:hover {
  background: #276b2a;
}

.panel-actions {
  margin-top: 18px;
}

.map-frame {
  position: relative;
  min-height: 640px;
  border: 1px solid #dcebdc;
  border-radius: 24px;
  overflow: hidden;
  background: #edf5ee;
  box-shadow: 0 8px 24px rgba(27, 67, 50, 0.05);
}

.map-container {
  width: 100%;
  height: 640px;
}

.map-overlay {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 2;
  max-width: 340px;
  padding: 18px 20px;
  background: rgba(248, 251, 248, 0.94);
  backdrop-filter: blur(10px);
  border: 1px solid #dcebdc;
  border-radius: 20px;
  box-shadow: 0 8px 20px rgba(27, 67, 50, 0.06);
  color: #173a29;
}

.map-overlay h2 {
  margin: 0 0 10px;
  font-size: 18px;
}

.map-overlay p {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #557260;
}

.map-overlay code {
  display: block;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f1f7f2;
  border: 1px solid #e3efe5;
  font-size: 13px;
  color: #173a29;
  word-break: break-all;
}

.map-overlay--warning {
  background: rgba(255, 248, 236, 0.95);
  border-color: #f0dec4;
}

.map-overlay--error {
  background: rgba(255, 241, 241, 0.95);
  border-color: #efcaca;
}

.detail-list,
.category-list {
  display: grid;
  gap: 12px;
}

.detail-row,
.category-row {
  display: flex;
  gap: 14px;
  justify-content: space-between;
  align-items: flex-start;
}

.detail-row span,
.category-row span {
  font-size: 14px;
  line-height: 1.5;
  color: #6b8a74;
}

.detail-row strong,
.category-row strong {
  font-size: 14px;
  line-height: 1.5;
  font-weight: 700;
  text-align: right;
  color: #173a29;
}

.category-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.category-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  flex: 0 0 auto;
}

:deep(.facility-marker) {
  width: 18px;
  height: 18px;
  border: 3px solid #ffffff;
  border-radius: 999px;
  box-shadow: 0 6px 16px rgba(27, 67, 50, 0.16);
  cursor: pointer;
  padding: 0;
}

:deep(.mapboxgl-popup-content) {
  padding: 0;
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdfb 100%);
  box-shadow: 0 14px 30px rgba(27, 67, 50, 0.12);
}

:deep(.mapboxgl-popup-close-button) {
  padding: 8px 10px;
  font-size: 18px;
  color: #6b8a74;
}

:deep(.map-popup) {
  padding: 18px 18px 16px;
  min-width: 240px;
  color: #173a29;
}

:deep(.map-popup__eyebrow) {
  display: inline-block;
  margin: 0 0 10px;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 700;
  color: #2e7d32;
  background: #e8f5e9;
  border: 1px solid #cfe8d1;
  border-radius: 999px;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

:deep(.map-popup h3) {
  margin: 0 0 12px;
  font-size: 17px;
  line-height: 1.35;
  font-weight: 700;
  color: #173a29;
}

:deep(.map-popup__row) {
  display: flex;
  gap: 10px;
  justify-content: space-between;
  align-items: flex-start;
  padding: 4px 0;
}

:deep(.map-popup__row span) {
  color: #6b8a74;
  font-size: 13px;
}

:deep(.map-popup__row strong) {
  max-width: 160px;
  text-align: right;
  font-size: 13px;
  color: #173a29;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .toolbar-card {
    grid-template-columns: 1fr;
  }

  .hero-card {
    grid-template-columns: 1fr;
    padding: 28px 24px;
  }

  h1 {
    font-size: 34px;
  }

  .disposal-page {
    padding: 20px;
  }
}

@media (max-width: 760px) {
  .hero-stats {
    grid-template-columns: 1fr;
  }

  .map-frame,
  .map-container {
    min-height: 520px;
    height: 520px;
  }
}

@media (max-width: 640px) {
  .detail-row,
  .category-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-row strong,
  .category-row strong {
    text-align: left;
  }
}

.section-label {
  margin-bottom: 12px;
  padding-bottom: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #3f8f46;
  border-bottom: 1px solid #e2eee3;
}
</style>

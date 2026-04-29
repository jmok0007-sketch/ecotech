<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { actAnnotation, australiaStatesGeoJson } from '../lib/australiaStatesGeoJson.js'
import vicLgaGda2020Raw from '../lib/vic_lga_gda2020.geojson?raw'
import {
  buildCategorySummary,
  buildFacilityMarkers,
  buildStateSummary,
  filterFacilities,
  getCategoryLabel,
  getCategoryOptions,
} from '../lib/ewasteMapModel'
import {
  buildGeoFeaturePaths,
  mapViewport,
  projectCoordinates,
  projectMelbourneRegionCoordinates,
} from '../lib/uvMapModel'
import { api } from '@/api'

const svgRef = ref(null)
const hoveredFacilityId = ref('')
const hoveredStateCode = ref('')
const selectedFacilityId = ref('')
const selectedState = ref('VIC')
const selectedCategory = ref('')
const searchTerm = ref('')
const resourceType = ref('disposal')
const suburb = ref('')
const brand = ref('')
const zoom = ref(1)
const pan = ref({ x: 0, y: 0 })
const dragState = ref(null)
const facilityRows = ref([])
const facilityMarkers = ref([])
const isLoading = ref(false)
const loadError = ref('')
let requestTimer = null
let activeRequestController = null

const stateOptions = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
const categoryOptions = getCategoryOptions()
const australiaGeoFeatures = buildGeoFeaturePaths(australiaStatesGeoJson)
const vicLgaGda2020GeoJson = JSON.parse(vicLgaGda2020Raw)
const victoriaGeoFeatures = buildGeoFeaturePaths(vicLgaGda2020GeoJson, {
  projector: projectMelbourneRegionCoordinates,
  getName: (properties) => properties?.LGA_NAME || properties?.ABB_NAME || properties?.name || '',
  getCode: (properties, _, index) => properties?.LGA_PID || properties?.LG_PLY_PID || `VIC-LGA-${index}`,
})
const projectedAct = {
  centroid: projectCoordinates(149.15, -35.45),
  lineEnd: projectCoordinates(actAnnotation.lineEnd[0], actAnnotation.lineEnd[1]),
}
const isVictoriaDisposalMode = computed(() => resourceType.value === 'disposal')
const geoFeatures = computed(() => (isVictoriaDisposalMode.value ? victoriaGeoFeatures : australiaGeoFeatures))

const visibleMarkers = computed(() =>
  filterFacilities(facilityMarkers.value, {
    selectedState: selectedState.value,
    selectedCategory: selectedCategory.value,
    searchTerm: searchTerm.value,
  }),
)

const visibleCategorySummary = computed(() => buildCategorySummary(visibleMarkers.value))
const visibleStateSummary = computed(() => buildStateSummary(visibleMarkers.value))
const importantSuburbLabels = computed(() => {
  if (!isVictoriaDisposalMode.value) return []

  const grouped = new Map()

  for (const marker of visibleMarkers.value) {
    const suburbName = String(marker?.suburb || '').trim()
    if (!suburbName) continue

    const key = suburbName.toUpperCase()
    const point = markerPoint(marker)
    const existing = grouped.get(key)

    if (existing) {
      existing.count += 1
      existing.sumX += point.x
      existing.sumY += point.y
      continue
    }

    grouped.set(key, {
      key,
      label: titleCase(suburbName),
      count: 1,
      sumX: point.x,
      sumY: point.y,
    })
  }

  const ranked = Array.from(grouped.values())
    .map((entry) => ({
      ...entry,
      x: entry.sumX / entry.count,
      y: entry.sumY / entry.count,
    }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))

  const selected = []
  const minDistance = 44
  const maxLabels = 10

  for (const entry of ranked) {
    const overlaps = selected.some((item) => {
      const dx = item.x - entry.x
      const dy = item.y - entry.y
      return Math.hypot(dx, dy) < minDistance
    })

    if (overlaps) continue

    selected.push(entry)
    if (selected.length >= maxLabels) break
  }

  return selected
})

const stateFillSummary = computed(() => {
  const counts = new Map(visibleStateSummary.value.map((entry) => [entry.key, entry.count]))
  const max = Math.max(0, ...counts.values())

  return new Map(
    stateOptions.map((stateCode) => {
      const count = counts.get(stateCode) || 0
      const intensity = max ? count / max : 0
      const fill = count ? `rgba(204, 107, 73, ${0.34 + intensity * 0.5})` : 'rgba(231, 221, 199, 0.92)'
      return [stateCode, { count, fill }]
    }),
  )
})

const hoveredMarker = computed(() => visibleMarkers.value.find((marker) => marker.id === hoveredFacilityId.value) || null)
const selectedMarker = computed(
  () =>
    visibleMarkers.value.find((marker) => marker.id === selectedFacilityId.value) ||
    facilityMarkers.value.find((marker) => marker.id === selectedFacilityId.value) ||
    null,
)
const hoveredState = computed(() => geoFeatures.value.find((feature) => feature.code === hoveredStateCode.value) || null)
const hoveredStateSummary = computed(() => (hoveredState.value ? stateFillSummary.value.get(hoveredState.value.code) || null : null))
const selectedRegionLabel = computed(() => {
  if (isVictoriaDisposalMode.value) return 'Victoria'
  return selectedState.value || 'Australia'
})
const selectedCategoryLabel = computed(() => {
  if (resourceType.value === 'repair') return 'Repair and reuse'
  return selectedCategory.value ? getCategoryLabel(selectedCategory.value) : 'All categories'
})
const selectedCategoryVisibleCount = computed(() => (selectedCategory.value ? visibleMarkers.value.filter((marker) => marker.category === selectedCategory.value).length : visibleMarkers.value.length))
const mapTransform = computed(() => `translate(${pan.value.x} ${pan.value.y}) scale(${zoom.value})`)
const pageEyebrow = computed(() => (resourceType.value === 'repair' ? 'National Repair Map' : 'Victoria Disposal Map'))
const pageTitle = computed(() => (resourceType.value === 'repair' ? 'Australia repair agencies for electronic devices' : 'Victoria e-waste drop-off and recycling facilities'))
const pageDescription = computed(() =>
  resourceType.value === 'repair'
    ? 'Search for repair agencies by suburb and optional brand, then inspect the returned locations on the same custom SVG basemap.'
    : 'Explore cleaned facility records from the API, with disposal sites filtered on the frontend. The disposal map is zoomed to the main serviced region so remote areas do not dominate the view.',
)
const activeMapTitle = computed(() => (resourceType.value === 'repair' ? 'Repair agency overview' : 'Victoria facility overview'))
const activeLegendTitle = computed(() => (resourceType.value === 'repair' ? 'Repair legend' : 'Facility legend'))
const activeSearchPlaceholder = computed(() => (resourceType.value === 'repair' ? 'Repair business, suburb, or address' : 'Facility name or suburb'))
const visibleLegendOptions = computed(() => (resourceType.value === 'repair' ? categoryOptions.filter((option) => option.value === 'repair_reuse') : categoryOptions))
const statsSearchLabel = computed(() => (resourceType.value === 'repair' ? 'Additional search' : 'Search term'))

function buildRequestPayload() {
  return {
    resourceType: resourceType.value,
    state: resourceType.value === 'disposal' ? 'VIC' : selectedState.value,
    category: resourceType.value === 'repair' ? '' : selectedCategory.value,
    searchText: searchTerm.value,
    suburb: resourceType.value === 'repair' ? suburb.value : '',
    brand: resourceType.value === 'repair' ? brand.value : '',
    limit: resourceType.value === 'repair' ? 25 : 300,
  }
}

async function loadFacilities() {
  if (activeRequestController) {
    activeRequestController.abort()
  }

  const controller = new AbortController()
  activeRequestController = controller
  isLoading.value = true
  loadError.value = ''

  try {
    const response = await api.searchDisposalLocations({ signal: controller.signal })
    const rows = Array.isArray(response?.items) ? response.items : []

    facilityRows.value = rows
    facilityMarkers.value = buildFacilityMarkers(rows)

    if (selectedFacilityId.value && !facilityMarkers.value.some((marker) => marker.id === selectedFacilityId.value)) {
      selectedFacilityId.value = ''
    }
  } catch (error) {
    if (error?.name === 'AbortError') return

    console.error('[EwasteAustraliaMap] failed to load facilities:', error)
    loadError.value = error instanceof Error ? error.message : 'Failed to load facilities'
    facilityRows.value = []
    facilityMarkers.value = []
    selectedFacilityId.value = ''
  } finally {
    if (activeRequestController === controller) {
      activeRequestController = null
      isLoading.value = false
    }
  }
}

function queueFacilityLoad() {
  if (requestTimer) {
    clearTimeout(requestTimer)
  }

  requestTimer = window.setTimeout(() => {
    requestTimer = null
    loadFacilities()
  }, 220)
}

function markerScreenPoint(marker) {
  const point = isVictoriaDisposalMode.value
    ? projectMelbourneRegionCoordinates(marker.longitude, marker.latitude)
    : marker.point

  return { x: point.x * zoom.value + pan.value.x, y: point.y * zoom.value + pan.value.y }
}

function stateScreenPoint(stateFeature) {
  if (!stateFeature?.labelPoint) return { x: 24, y: 24 }
  return { x: stateFeature.labelPoint.x * zoom.value + pan.value.x, y: stateFeature.labelPoint.y * zoom.value + pan.value.y }
}

function setZoom(nextZoom) {
  zoom.value = Math.min(3.2, Math.max(1, Number(nextZoom.toFixed(2))))
}

function zoomIn() {
  setZoom(zoom.value + 0.25)
}

function zoomOut() {
  setZoom(zoom.value - 0.25)
}

function resetView() {
  zoom.value = 1
  pan.value = { x: 0, y: 0 }
}

function beginDrag(event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  const rect = svgRef.value?.getBoundingClientRect()
  if (!rect) return

  dragState.value = {
    startClientX: event.clientX,
    startClientY: event.clientY,
    startPanX: pan.value.x,
    startPanY: pan.value.y,
    scaleX: mapViewport.width / rect.width,
    scaleY: mapViewport.height / rect.height,
  }

  svgRef.value.setPointerCapture(event.pointerId)
}

function updateDrag(event) {
  if (!dragState.value) return

  const deltaX = (event.clientX - dragState.value.startClientX) * dragState.value.scaleX
  const deltaY = (event.clientY - dragState.value.startClientY) * dragState.value.scaleY
  pan.value = { x: dragState.value.startPanX + deltaX, y: dragState.value.startPanY + deltaY }
}

function endDrag(event) {
  if (dragState.value && svgRef.value?.hasPointerCapture(event.pointerId)) {
    svgRef.value.releasePointerCapture(event.pointerId)
  }
  dragState.value = null
}

function onWheel(event) {
  event.preventDefault()
  setZoom(zoom.value + (event.deltaY < 0 ? 0.2 : -0.2))
}

function selectMarker(marker) {
  selectedFacilityId.value = marker.id
}

function toggleState(stateCode) {
  if (isVictoriaDisposalMode.value) return

  selectedState.value = selectedState.value === stateCode ? '' : stateCode

  if (selectedFacilityId.value && !filterFacilities(facilityMarkers.value, {
    selectedState: selectedState.value,
    selectedCategory: selectedCategory.value,
    searchTerm: searchTerm.value,
  }).some((marker) => marker.id === selectedFacilityId.value)) {
    selectedFacilityId.value = ''
  }
}

function clearFilters() {
  selectedState.value = resourceType.value === 'disposal' ? 'VIC' : ''
  searchTerm.value = ''
  suburb.value = ''
  brand.value = ''
  if (resourceType.value === 'disposal') {
    selectedCategory.value = ''
  }
  selectedFacilityId.value = ''
}

function stateFill(stateCode) {
  if (isVictoriaDisposalMode.value) {
    return 'rgba(204, 107, 73, 0.28)'
  }
  return stateFillSummary.value.get(stateCode)?.fill || 'rgba(231, 221, 199, 0.92)'
}

function stateOpacity(stateCode) {
  if (isVictoriaDisposalMode.value) return 0.88
  if (selectedState.value && selectedState.value !== stateCode) return 0.5
  return hoveredStateCode.value === stateCode || selectedState.value === stateCode ? 0.92 : 0.76
}

function stateStrokeWidth(stateCode) {
  if (isVictoriaDisposalMode.value) return hoveredStateCode.value === stateCode ? 2.8 : 1.5
  return hoveredStateCode.value === stateCode || selectedState.value === stateCode ? 4 : 2.6
}

function markerRadius(marker) {
  if (selectedFacilityId.value === marker.id) return 13
  if (hoveredFacilityId.value === marker.id) return 11
  return 8.5
}

function titleCase(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function markerTooltipAddress(marker) {
  if (!marker) return 'Address not provided'
  if (resourceType.value === 'disposal') {
    return [marker.address, marker.suburb, marker.postcode].filter(Boolean).join(', ') || 'Address not provided'
  }
  return `${marker.suburb || marker.state || ''} ${marker.postcode || ''}`.trim()
}

function detailsRows(marker) {
  if (!marker) return []
  const row = marker.row || {}

  return [
    { label: resourceType.value === 'repair' ? 'Agency' : 'Facility', value: row.facility_name || marker.facilityName || 'Unknown facility' },
    { label: 'Address', value: row.address || marker.address || 'Not provided' },
    { label: 'Suburb', value: row.suburb || marker.suburb || 'Not provided' },
    { label: 'Postcode', value: row.postcode || marker.postcode || 'Not provided' },
    { label: 'State', value: row.state || marker.state || 'Not provided' },
    { label: 'Category', value: getCategoryLabel(row.ewaste_category || marker.category) },
    { label: 'Source', value: row.source || marker.source || '' },
    { label: 'Score', value: marker.score == null ? '' : marker.score },
    { label: 'Coord source', value: row.coord_source || marker.coordSource || '' },
    { label: 'Source file', value: row.source_file || marker.sourceFile || '' },
  ].filter((entry) => entry.value)
}

function markerPoint(marker) {
  return isVictoriaDisposalMode.value
    ? projectMelbourneRegionCoordinates(marker.longitude, marker.latitude)
    : marker.point
}

watch(resourceType, (nextType) => {
  selectedFacilityId.value = ''
  selectedCategory.value = ''
  searchTerm.value = ''
  loadError.value = ''

  if (nextType === 'repair') {
    selectedState.value = ''
    suburb.value = suburb.value || 'Sydney'
  } else {
    selectedState.value = 'VIC'
    brand.value = ''
    suburb.value = ''
  }
})

watch([resourceType, selectedState, selectedCategory, searchTerm, suburb, brand], () => {
  queueFacilityLoad()
})

onMounted(() => {
  loadFacilities()
})

onBeforeUnmount(() => {
  if (requestTimer) {
    clearTimeout(requestTimer)
  }
  if (activeRequestController) {
    activeRequestController.abort()
  }
  dragState.value = null
})
</script>

<template>
  <section class="ewaste-page">
    <div class="hero-card">
      <p class="eyebrow">{{ pageEyebrow }}</p>
      <div class="hero-copy">
        <div>
          <h1>{{ pageTitle }}</h1>
          <p class="hero-text">{{ pageDescription }}</p>
        </div>
        <div class="summary-card">
          <p class="summary-label">Selection summary</p>
          <div class="summary-grid">
            <article><span>Mode</span><strong>{{ resourceType === 'repair' ? 'Repair' : 'Disposal' }}</strong></article>
            <article><span>Region</span><strong>{{ selectedRegionLabel }}</strong></article>
            <article><span>Visible facilities</span><strong>{{ visibleMarkers.length }}</strong></article>
            <article><span>Visible categories</span><strong>{{ visibleCategorySummary.length }}</strong></article>
            <article><span>Category</span><strong>{{ selectedCategoryLabel }}</strong></article>
          </div>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <section class="map-shell">
        <div class="filters-card">
          <div class="filter-row">
            <label>
              <span>Resource type</span>
              <select v-model="resourceType">
                <option value="disposal">Disposal</option>
                <option value="repair">Repair</option>
              </select>
            </label>
            <label>
              <span>State</span>
              <select v-model="selectedState" :disabled="resourceType === 'disposal'">
                <option value="">All states</option>
                <option v-for="state in stateOptions" :key="state" :value="state">{{ state }}</option>
              </select>
            </label>
            <label v-if="resourceType === 'disposal'">
              <span>Category</span>
              <select v-model="selectedCategory">
                <option value="">All categories</option>
                <option v-for="category in categoryOptions" :key="category.value" :value="category.value">{{ category.label }}</option>
              </select>
            </label>
            <label v-if="resourceType === 'repair'">
              <span>Suburb</span>
              <input v-model.trim="suburb" type="search" placeholder="Sydney" />
            </label>
            <label v-if="resourceType === 'repair'">
              <span>Brand</span>
              <input v-model.trim="brand" type="search" placeholder="Apple, Samsung, Google..." />
            </label>
            <label class="search-field">
              <span>{{ resourceType === 'repair' ? 'Additional search' : 'Search' }}</span>
              <input v-model.trim="searchTerm" type="search" :placeholder="activeSearchPlaceholder" />
            </label>
          </div>

          <div class="toolbar-row">
            <div class="toolbar-copy">
              <p class="eyebrow">Request Driven Map</p>
              <h2>{{ activeMapTitle }}</h2>
            </div>
            <div class="zoom-controls">
              <button type="button" @click="zoomOut">-</button>
              <span>{{ zoom.toFixed(2) }}x</span>
              <button type="button" @click="zoomIn">+</button>
              <button type="button" class="ghost" @click="resetView">Reset</button>
              <button type="button" class="ghost" @click="clearFilters">Clear filters</button>
            </div>
          </div>
        </div>

        <div class="map-board">
          <div v-if="isLoading || loadError" class="map-status">
            <p v-if="isLoading">Loading {{ resourceType === 'repair' ? 'repair agencies' : 'disposal facilities' }}...</p>
            <p v-else>{{ loadError }}</p>
          </div>
          <svg
            ref="svgRef"
            class="map-svg"
            :viewBox="`0 0 ${mapViewport.width} ${mapViewport.height}`"
            role="img"
            :aria-label="resourceType === 'repair' ? 'Australia repair facility map' : 'Victoria e-waste facility map'"
            @pointerdown="beginDrag"
            @pointermove="updateDrag"
            @pointerup="endDrag"
            @pointercancel="endDrag"
            @pointerleave="endDrag"
            @wheel="onWheel"
          >
            <defs>
              <linearGradient id="ewaste-ocean" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f8efe4" />
                <stop offset="100%" stop-color="#eadbc3" />
              </linearGradient>
            </defs>

            <rect width="100%" height="100%" fill="url(#ewaste-ocean)" rx="34" />

            <g :transform="mapTransform">
              <g class="states-layer">
                <path
                  v-for="state in geoFeatures"
                  :key="state.code"
                  :d="state.path"
                  class="state-shape"
                  :style="{ fill: stateFill(state.code), opacity: stateOpacity(state.code), strokeWidth: stateStrokeWidth(state.code) }"
                  @mouseenter="hoveredStateCode = state.code"
                  @mouseleave="hoveredStateCode = ''"
                  @click.stop="toggleState(state.code)"
                />

                <text
                  v-for="state in geoFeatures.filter((feature) => !isVictoriaDisposalMode && feature.code !== 'ACT' && feature.labelPoint)"
                  :key="`${state.code}-label`"
                  :x="state.labelPoint.x"
                  :y="state.labelPoint.y"
                  text-anchor="middle"
                  class="state-code"
                >
                  {{ state.code }}
                </text>

                <line v-if="!isVictoriaDisposalMode" :x1="projectedAct.centroid.x" :y1="projectedAct.centroid.y" :x2="projectedAct.lineEnd.x" :y2="projectedAct.lineEnd.y" class="act-line" />
                <text v-if="!isVictoriaDisposalMode" :x="projectedAct.lineEnd.x + 10" :y="projectedAct.lineEnd.y - 6" text-anchor="start" class="state-code act-code" @click.stop="toggleState('ACT')">ACT</text>
              </g>

              <g v-for="marker in visibleMarkers" :key="marker.id">
                <circle :cx="markerPoint(marker).x" :cy="markerPoint(marker).y" :r="markerRadius(marker) + 8" :fill="`${marker.categoryColor}22`" />
                <circle
                  :cx="markerPoint(marker).x"
                  :cy="markerPoint(marker).y"
                  :r="markerRadius(marker)"
                  :fill="marker.categoryColor"
                  :stroke="selectedFacilityId === marker.id ? '#102a43' : 'white'"
                  :stroke-width="selectedFacilityId === marker.id ? 4.5 : 3"
                  class="marker"
                  @mouseenter="hoveredFacilityId = marker.id"
                  @mouseleave="hoveredFacilityId = ''"
                  @click.stop="selectMarker(marker)"
                />
              </g>

              <g v-if="importantSuburbLabels.length" class="suburb-label-layer">
                <g v-for="label in importantSuburbLabels" :key="label.key" class="suburb-label-group">
                  <text :x="label.x + 12" :y="label.y - 14" class="suburb-label-shadow">{{ label.label }}</text>
                  <text :x="label.x + 12" :y="label.y - 14" class="suburb-label">{{ label.label }}</text>
                </g>
              </g>
            </g>

            <g v-if="hoveredMarker && hoveredMarker.id !== selectedFacilityId">
              <template v-for="screenPoint in [markerScreenPoint(hoveredMarker)]" :key="hoveredMarker.id">
                <rect :x="Math.min(screenPoint.x + 16, mapViewport.width - 270)" :y="Math.max(screenPoint.y - 72, 18)" width="250" height="68" rx="16" fill="rgba(16, 42, 67, 0.9)" />
                <text :x="Math.min(screenPoint.x + 30, mapViewport.width - 256)" :y="Math.max(screenPoint.y - 44, 42)" class="tooltip-title">{{ hoveredMarker.facilityName }}</text>
                <text :x="Math.min(screenPoint.x + 30, mapViewport.width - 256)" :y="Math.max(screenPoint.y - 22, 64)" class="tooltip-copy">{{ markerTooltipAddress(hoveredMarker) }}</text>
                <text :x="Math.min(screenPoint.x + 30, mapViewport.width - 256)" :y="Math.max(screenPoint.y, 86)" class="tooltip-copy">{{ hoveredMarker.categoryLabel }}</text>
              </template>
            </g>

            <g v-if="!isVictoriaDisposalMode && hoveredState && hoveredStateSummary">
              <template v-for="screenPoint in [stateScreenPoint(hoveredState)]" :key="hoveredState.code">
                <rect :x="Math.min(screenPoint.x + 16, mapViewport.width - 260)" :y="Math.max(screenPoint.y - 62, 18)" width="240" height="56" rx="16" fill="rgba(16, 42, 67, 0.88)" />
                <text :x="Math.min(screenPoint.x + 30, mapViewport.width - 246)" :y="Math.max(screenPoint.y - 36, 44)" class="tooltip-title">{{ hoveredState.code }} facilities</text>
                <text :x="Math.min(screenPoint.x + 30, mapViewport.width - 246)" :y="Math.max(screenPoint.y - 14, 66)" class="tooltip-copy">{{ hoveredStateSummary.count }} visible locations</text>
              </template>
            </g>
          </svg>

          <div class="map-notes">
            <p>{{ resourceType === 'repair' ? 'Drag to pan. Use mouse wheel or controls to zoom. Click a state to filter and click a marker to load details.' : 'Drag to pan. Use mouse wheel or controls to zoom. Disposal mode uses API data and focuses on the main serviced region rather than remote areas.' }}</p>
          </div>
        </div>

        <div class="legend-card">
          <h3>{{ activeLegendTitle }}</h3>
          <div class="legend-list">
            <button
              v-for="category in visibleLegendOptions"
              :key="category.value"
              type="button"
              class="legend-item"
              :class="{ active: selectedCategory === category.value }"
              :disabled="resourceType === 'repair'"
              @click="selectedCategory = selectedCategory === category.value ? '' : category.value"
            >
              <span class="legend-dot" :style="{ backgroundColor: category.color }" />
              <span>{{ category.label }}</span>
            </button>
          </div>
        </div>
      </section>

      <aside class="info-column">
        <section class="panel-card focus-card">
          <template v-if="selectedMarker">
            <p class="eyebrow">Selected Facility</p>
            <h3>{{ selectedMarker.facilityName }}</h3>
            <div class="detail-list">
              <div v-for="entry in detailsRows(selectedMarker)" :key="entry.label" class="detail-row">
                <span>{{ entry.label }}</span>
                <strong>{{ entry.value }}</strong>
              </div>
            </div>
          </template>

          <template v-else>
            <p class="eyebrow">Visible Distribution</p>
            <h3>Facility breakdown</h3>
            <p class="supporting-copy">
              Use the filters or click a state on the map to narrow the facility list. Category and state counts below update from the current visible results.
            </p>
            <div class="summary-stack">
              <section>
                <h4>By category</h4>
                <div class="mini-list">
                  <div v-for="entry in visibleCategorySummary" :key="entry.key" class="mini-row">
                    <span class="mini-label"><span class="legend-dot" :style="{ backgroundColor: entry.color }" />{{ entry.label }}</span>
                    <strong>{{ entry.count }}</strong>
                  </div>
                  <p v-if="!visibleCategorySummary.length" class="empty-copy">No facilities match the current filters.</p>
                </div>
              </section>
              <section>
                <h4>By state</h4>
                <div class="mini-list">
                  <div v-for="entry in visibleStateSummary" :key="entry.key" class="mini-row">
                    <span>{{ entry.label }}</span>
                    <strong>{{ entry.count }}</strong>
                  </div>
                  <p v-if="!visibleStateSummary.length" class="empty-copy">No state counts available.</p>
                </div>
              </section>
            </div>
          </template>
        </section>

        <section class="panel-card stats-card">
          <p class="eyebrow">Snapshot</p>
          <h3>Current map status</h3>
          <div class="detail-list compact">
            <div class="detail-row"><span>Resource type</span><strong>{{ resourceType }}</strong></div>
            <div class="detail-row"><span>Selected region</span><strong>{{ selectedRegionLabel }}</strong></div>
            <div class="detail-row"><span>Selected category</span><strong>{{ selectedCategoryLabel }}</strong></div>
            <div class="detail-row"><span>Category result count</span><strong>{{ selectedCategoryVisibleCount }}</strong></div>
            <div class="detail-row"><span>{{ statsSearchLabel }}</span><strong>{{ searchTerm || 'None' }}</strong></div>
            <div v-if="resourceType === 'repair'" class="detail-row"><span>Suburb</span><strong>{{ suburb || 'Not set' }}</strong></div>
            <div v-if="resourceType === 'repair'" class="detail-row"><span>Brand</span><strong>{{ brand || 'Any brand' }}</strong></div>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.ewaste-page{min-height:100vh;padding:2rem;background:radial-gradient(circle at top left,rgba(255,244,228,.9),transparent 28%),linear-gradient(180deg,#fdf8f1 0%,#f6efe4 100%);color:#102a43}
.hero-card,.filters-card,.legend-card,.panel-card{border:1px solid rgba(16,42,67,.12);border-radius:30px;background:rgba(255,251,246,.9);box-shadow:0 24px 60px rgba(16,42,67,.08)}
.hero-card{padding:1.5rem;margin-bottom:1.5rem}
.hero-copy{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(300px,.95fr);gap:1.25rem;align-items:stretch}
.eyebrow{margin:0 0 .35rem;color:#a44a17;font-size:.76rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
h1,h2,h3,h4,p{margin-top:0}
h1{margin-bottom:.75rem;font-size:clamp(2rem,3vw,3.4rem);line-height:1.05}
.hero-text,.supporting-copy,.map-notes p,.empty-copy{margin-bottom:0;color:#486581;line-height:1.6}
.summary-card{padding:1.2rem;border-radius:24px;background:linear-gradient(145deg,rgba(16,42,67,.96),rgba(40,68,95,.92));color:#fff}
.summary-label{margin-bottom:.9rem;font-size:.82rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.72)}
.summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem}
.summary-grid article{padding:.9rem 1rem;border-radius:18px;background:rgba(255,255,255,.08)}
.summary-grid span{display:block;margin-bottom:.35rem;font-size:.82rem;color:rgba(255,255,255,.68)}
.summary-grid strong{font-size:1.1rem}
.content-grid{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(310px,.85fr);gap:1.5rem;align-items:start}
.map-shell{display:grid;gap:1rem}
.filters-card,.legend-card,.panel-card{padding:1.2rem}
.filter-row,.toolbar-row{display:flex;gap:1rem;align-items:end;justify-content:space-between;flex-wrap:wrap}
.filter-row{margin-bottom:1.15rem}
label{display:grid;gap:.4rem;min-width:150px;color:#334e68;font-size:.92rem;font-weight:700}
.search-field{flex:1 1 240px}
select,input{min-height:46px;border:1px solid rgba(16,42,67,.14);border-radius:16px;padding:.85rem 1rem;background:#fffdfa;color:#102a43;font:inherit}
.toolbar-copy h2{margin-bottom:0;font-size:clamp(1.4rem,2vw,2rem)}
.zoom-controls{display:flex;gap:.55rem;align-items:center;flex-wrap:wrap}
button,.zoom-controls span{min-height:42px;border-radius:999px}
button{border:0;padding:.72rem 1rem;background:#102a43;color:#fff;font-weight:700;cursor:pointer}
.ghost{background:rgba(16,42,67,.12);color:#102a43}
.zoom-controls span{display:inline-flex;align-items:center;padding:0 .9rem;background:rgba(16,42,67,.08);color:#102a43;font-weight:700}
.map-board{position:relative;border:1px solid rgba(16,42,67,.14);border-radius:30px;background:rgba(255,250,244,.86);box-shadow:0 24px 60px rgba(16,42,67,.12);overflow:hidden}
.map-status{position:absolute;top:16px;right:16px;z-index:3;max-width:320px;padding:.8rem 1rem;border-radius:18px;background:rgba(16,42,67,.88);color:#fff}
.map-status p{margin:0;font-size:.92rem;line-height:1.5}
.map-svg{display:block;width:100%;height:auto;touch-action:none;cursor:grab}
.map-svg:active{cursor:grabbing}
.state-shape{stroke:#7b6540;stroke-linejoin:round;cursor:pointer;transition:opacity .2s ease,stroke-width .2s ease}
.state-code{fill:rgba(16,42,67,.74);font-size:22px;font-weight:800;letter-spacing:.06em}
.act-code{font-size:18px}
.act-line{stroke:rgba(16,42,67,.74);stroke-width:3;pointer-events:none}
.marker{cursor:pointer;transition:r .18s ease,stroke-width .18s ease}
.suburb-label-layer{pointer-events:none}
.suburb-label{fill:#224b5f;font-size:18px;font-weight:800;letter-spacing:.01em}
.suburb-label-shadow{fill:rgba(255,251,246,.95);font-size:18px;font-weight:800;stroke:rgba(255,251,246,.95);stroke-width:5;stroke-linejoin:round}
.tooltip-title{fill:#fff;font-size:18px;font-weight:700}
.tooltip-copy{fill:rgba(255,255,255,.82);font-size:15px}
.map-notes{padding:.9rem 1.2rem 1.2rem}
.legend-card h3,.panel-card h3,.panel-card h4{margin-bottom:.85rem}
.legend-list{display:flex;gap:.75rem;flex-wrap:wrap}
.legend-item{display:inline-flex;align-items:center;gap:.55rem;background:rgba(16,42,67,.08);color:#102a43}
.legend-item:disabled{opacity:.65;cursor:default}
.legend-item.active{background:rgba(16,42,67,.18)}
.legend-dot{width:12px;height:12px;border-radius:999px;display:inline-block;flex:0 0 auto}
.info-column,.detail-list,.summary-stack,.mini-list{display:grid;gap:.75rem}
.detail-row,.mini-row{display:flex;gap:1rem;align-items:start;justify-content:space-between}
.detail-row span,.mini-row span{color:#486581}
.detail-row strong,.mini-row strong{text-align:right}
.mini-label{display:inline-flex;align-items:center;gap:.55rem}
.compact .detail-row{padding:.1rem 0}
@media (max-width:1080px){.hero-copy,.content-grid{grid-template-columns:1fr}}
@media (max-width:760px){.ewaste-page{padding:1rem}.summary-grid{grid-template-columns:1fr}.toolbar-row{align-items:stretch}}
</style>

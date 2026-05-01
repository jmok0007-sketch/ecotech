<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { api } from '@/api'
import * as echarts from 'echarts'

const loading = ref(true)
const error = ref('')
const healthData = ref([])
const stateData = ref([])
const facilityData = ref([])
const showAllCancers = ref(false)

const pathwayChains = ref([
  {
    tag: 'CHAIN 1',
    title: 'E-waste to environment',
    steps: [
      'E-waste generation',
      'Hazardous disposal and recycling pressure',
      'Air, land, and water emissions',
    ],
    evidence:
      'The environmental analysis links e-waste pressure with pollutant release patterns, especially heavy metal and total emission indicators.',
  },
  {
    tag: 'CHAIN 2',
    title: 'Environment to health',
    steps: ['Pollution indicators', 'State-year health comparison', 'Mortality and burden signals'],
    evidence:
      'The health analysis compares emission indicators with outcomes such as deaths, premature deaths, avoidable deaths, and years of life lost.',
  },
])

const HEAVY_METAL_LINKED = [
  { name: 'Lung cancer', icon: '🫁', metal: 'Pb · Cd' },
  { name: 'Kidney cancer', icon: '🩺', metal: 'Pb · Cd' },
  { name: 'Bladder cancer', icon: '🩺', metal: 'Cd' },
  { name: 'Prostate cancer', icon: '👨', metal: 'Cd' },
  { name: 'Brain cancer', icon: '🧠', metal: 'Pb' },
  { name: 'Acute myeloid leukaemia', icon: '🩸', metal: 'Pb' },
  { name: 'Acute lymphoblastic leukaemia', icon: '🩸', metal: 'Pb' },
  { name: 'Stomach cancer', icon: '🫀', metal: 'Pb' },
  { name: 'Liver cancer', icon: '🫀', metal: 'Cd · Hg' },
  { name: 'Pancreatic cancer', icon: '🫀', metal: 'Cd' },
]

function parseFY(reportYear) {
  if (reportYear === null || reportYear === undefined) return null
  const s = String(reportYear)
  if (s.includes('/')) return parseInt(s.split('/')[0], 10)
  const n = parseInt(s, 10)
  return Number.isFinite(n) ? n : null
}

function shortMetal(m) {
  return String(m || '').replace(' & compounds', '')
}

function formatNumber(v) {
  return Math.round(Number(v || 0)).toLocaleString()
}

function formatTonnes(kg) {
  const t = Number(kg || 0) / 1000
  if (t >= 1000) return `${(t / 1000).toFixed(1)}k tonnes`
  if (t >= 1) return `${t.toFixed(1)} tonnes`
  return `${Math.round(Number(kg || 0))} kg`
}

function pct(n) {
  if (!Number.isFinite(n)) return '—'
  const sign = n >= 0 ? '+' : '−'
  return `${sign}${Math.abs(Math.round(n))}%`
}

const emissionsByYear = computed(() => {
  const map = {}
  for (const r of stateData.value) {
    const y = parseFY(r.report_year)
    if (!y) continue
    map[y] = (map[y] || 0) + Number(r.total_air_emission_kg || 0)
  }
  return map
})

const earliestYear = computed(() => {
  const ys = Object.keys(emissionsByYear.value).map(Number)
  return ys.length ? Math.min(...ys) : null
})

const latestYear = computed(() => {
  const ys = Object.keys(emissionsByYear.value).map(Number)
  return ys.length ? Math.max(...ys) : null
})

const latestEmissionsKg = computed(() => emissionsByYear.value[latestYear.value] || 0)
const earliestEmissionsKg = computed(() => emissionsByYear.value[earliestYear.value] || 0)

const emissionsChange = computed(() => {
  const a = earliestEmissionsKg.value
  const b = latestEmissionsKg.value
  if (!a) return null
  return ((b - a) / a) * 100
})

const linkedCancerByYear = computed(() => {
  const linkedSet = new Set(HEAVY_METAL_LINKED.map((c) => c.name))
  const map = {}
  for (const r of healthData.value) {
    if (r.sex !== 'persons') continue
    if (!linkedSet.has(r.cancer_type)) continue
    map[r.year] = (map[r.year] || 0) + Number(r.cancer_cases || 0)
  }
  return map
})

const earliestHealthYear = computed(() => {
  const ys = Object.keys(linkedCancerByYear.value).map(Number)
  return ys.length ? Math.min(...ys) : null
})

const latestHealthYear = computed(() => {
  const ys = Object.keys(linkedCancerByYear.value).map(Number)
  return ys.length ? Math.max(...ys) : null
})

const latestLinkedCases = computed(() => linkedCancerByYear.value[latestHealthYear.value] || 0)
const earliestLinkedCases = computed(() => linkedCancerByYear.value[earliestHealthYear.value] || 0)

const cancerChange = computed(() => {
  const a = earliestLinkedCases.value
  const b = latestLinkedCases.value
  if (!a) return null
  return ((b - a) / a) * 100
})

const perCancerGrowth = computed(() => {
  const result = []

  for (const c of HEAVY_METAL_LINKED) {
    const points = healthData.value.filter((r) => r.sex === 'persons' && r.cancer_type === c.name)

    if (!points.length) {
      result.push({ ...c, change: null, latest: 0 })
      continue
    }

    const sorted = [...points].sort((a, b) => a.year - b.year)
    const first = Number(sorted[0].cancer_cases || 0)
    const last = Number(sorted[sorted.length - 1].cancer_cases || 0)
    const change = first > 0 ? ((last - first) / first) * 100 : null

    result.push({ ...c, change, latest: last })
  }

  return result
    .sort((a, b) => b.change - a.change)
})

const displayedCancers = computed(() => {
  return showAllCancers.value ? perCancerGrowth.value : perCancerGrowth.value.slice(0, 6)
})

const topPollutingStates = computed(() => {
  const map = {}
  for (const r of stateData.value) {
    if (!r.state) continue
    map[r.state] = (map[r.state] || 0) + Number(r.total_air_emission_kg || 0)
  }
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([state, kg]) => ({ state, kg }))
})

const allStatesEmissions = computed(() => {
  return stateData.value.reduce((s, r) => s + Number(r.total_air_emission_kg || 0), 0)
})

const top3Share = computed(() => {
  const top = topPollutingStates.value.reduce((s, r) => s + r.kg, 0)
  return allStatesEmissions.value > 0 ? (top / allStatesEmissions.value) * 100 : 0
})

const metalMix = computed(() => {
  const map = { Lead: 0, Mercury: 0, Cadmium: 0 }
  for (const r of stateData.value) {
    const m = shortMetal(r.metal)
    if (m in map) map[m] += Number(r.total_air_emission_kg || 0)
  }
  const total = map.Lead + map.Mercury + map.Cadmium
  return Object.entries(map).map(([metal, kg]) => ({
    metal,
    kg,
    pct: total > 0 ? (kg / total) * 100 : 0,
  }))
})

const trendChartRef = ref(null)
let trendChart = null

const trendChartOption = computed(() => {
  const eYears = Object.keys(emissionsByYear.value)
    .map(Number)
    .sort((a, b) => a - b)

  const cYears = Object.keys(linkedCancerByYear.value)
    .map(Number)
    .sort((a, b) => a - b)

  if (!eYears.length || !cYears.length) return {}

  const ePoints = eYears.map((y) => ({ year: y, val: emissionsByYear.value[y] }))
  const cPoints = cYears.map((y) => ({ year: y, val: linkedCancerByYear.value[y] }))

  const eBase = ePoints[0].val || 1
  const cBase = cPoints[0].val || 1

  const eIndexed = ePoints.map((p) => [p.year, Math.round((p.val / eBase) * 100)])
  const cIndexed = cPoints.map((p) => [p.year, Math.round((p.val / cBase) * 100)])

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const year = params[0].axisValue
        let html = `<strong>${year}</strong><br>`
        for (const p of params) {
          html += `${p.marker} ${p.seriesName}: <b>${p.data[1]}</b> (${p.data[1] - 100 >= 0 ? '+' : ''}${p.data[1] - 100}% vs first year)<br>`
        }
        return html
      },
    },
    legend: { bottom: 0, icon: 'roundRect', itemHeight: 10 },
    grid: { left: 70, right: 30, top: 30, bottom: 60 },
    xAxis: {
      type: 'value',
      min: Math.min(eYears[0], cYears[0]),
      max: Math.max(eYears[eYears.length - 1], cYears[cYears.length - 1]),
      axisLabel: { color: '#4b5563', formatter: (v) => Math.round(v) },
      splitLine: { show: false },
      axisLine: { lineStyle: { color: '#d1d5db' } },
    },
    yAxis: {
      type: 'value',
      name: 'Indexed (first year = 100)',
      nameTextStyle: { color: '#6b7280', fontSize: 11 },
      axisLabel: { color: '#4b5563' },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    series: [
      {
        name: '⚠️  Heavy-metal pollution',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3 },
        itemStyle: { color: '#dc2626' },
        data: eIndexed,
      },
      {
        name: '🩺  Linked cancer cases',
        type: 'line',
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 3 },
        itemStyle: { color: '#7c3aed' },
        data: cIndexed,
      },
    ],
  }
})

const stateChartRef = ref(null)
let stateChart = null

const stateChartOption = computed(() => {
  const map = {}
  for (const r of stateData.value) {
    if (!r.state) continue
    map[r.state] = (map[r.state] || 0) + Number(r.total_air_emission_kg || 0)
  }

  const sorted = Object.entries(map).sort((a, b) => a[1] - b[1])

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (v) => formatTonnes(v),
    },
    grid: { left: 60, right: 60, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#4b5563',
        formatter: (v) =>
          v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M kg` : `${(v / 1000).toFixed(0)}k`,
      },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(([s]) => s),
      axisLabel: { color: '#374151', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 22,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (p) => {
            const total = sorted.length
            return p.dataIndex >= total - 3 ? '#dc2626' : '#22c55e'
          },
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p) => formatTonnes(p.value),
          color: '#4b5563',
          fontSize: 12,
        },
        data: sorted.map(([, v]) => Math.round(v)),
      },
    ],
  }
})

function renderCharts() {
  if (trendChartRef.value) {
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption(trendChartOption.value, true)
  }

  if (stateChartRef.value) {
    if (!stateChart) stateChart = echarts.init(stateChartRef.value)
    stateChart.setOption(stateChartOption.value, true)
  }
}

function handleResize() {
  trendChart?.resize()
  stateChart?.resize()
}

function extractItems(response) {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.items)) return response.items
  return []
}

async function loadData() {
  try {
    loading.value = true
    error.value = ''

    const [healthResponse, stateResponse, facilityResponse] = await Promise.all([
      api.getHealthAll(),
      api.getHeavyMetalState(),
      api.getHeavyMetalFacility(),
    ])

    healthData.value = extractItems(healthResponse)
    stateData.value = extractItems(stateResponse)
    facilityData.value = extractItems(facilityResponse)

    if (!healthData.value.length || !stateData.value.length) {
      throw new Error('API responded, but dashboard received empty data arrays.')
    }
  } catch (e) {
    console.error('Dashboard load error:', e)
    error.value = e?.message || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
    await nextTick()
    renderCharts()
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  stateChart?.dispose()
})
</script>

<template>
  <div class="dashboard">
    <section class="hero">
      <p class="eyebrow">Health insights</p>
      <h1>Old electronics quietly poison the air we breathe.</h1>
      <p class="lede">
        When phones, laptops, and TVs end up in landfill instead of recycling, the
        <strong>lead, mercury and cadmium</strong> inside them leak into the air, water, and soil.
        These metals are linked to cancer of the lung, kidney, bladder, prostate, and more. Here is
        what Australia's data is showing us.
      </p>
    </section>

    <section v-if="loading" class="state">Loading…</section>

    <section v-else-if="error" class="state error">
      <strong>Couldn't load data.</strong>
      <p>{{ error }}</p>
    </section>

    <template v-else>
      <section class="pathway-grid">
        <article v-for="chain in pathwayChains" :key="chain.title" class="pathway-card">
          <span class="section-tag">{{ chain.tag }}</span>
          <h2>{{ chain.title }}</h2>
          <p class="pathway-evidence">{{ chain.evidence }}</p>

          <div class="pathway-steps-vertical">
            <template v-for="(step, index) in chain.steps" :key="step">
              <div class="step-box">{{ step }}</div>
              <div v-if="index < chain.steps.length - 1" class="arrow-down">↓</div>
            </template>
          </div>
        </article>
      </section>

      <section class="takeaway">
        <p class="eyebrow centered">The big picture</p>
        <h2>Pollution and cancer are rising together.</h2>
        <p class="takeaway-lede">
          Both heavy metal pollution from industry <em>and</em> cancers linked to those metals have
          grown sharply in Australia over the last few decades. One chart, two lines, same
          direction.
        </p>

        <div class="big-stats">
          <div class="big-stat danger">
            <span class="big-icon">⚠️</span>
            <p class="big-label">Heavy-metal air pollution</p>
            <p class="big-value">{{ pct(emissionsChange) }}</p>
            <p class="big-hint">Compared to {{ earliestYear }} (latest year: {{ latestYear }})</p>
          </div>

          <div class="big-stat warning">
            <span class="big-icon">🩺</span>
            <p class="big-label">Cancers linked to heavy metals</p>
            <p class="big-value">{{ pct(cancerChange) }}</p>
            <p class="big-hint">
              {{ earliestHealthYear }} → {{ latestHealthYear }} (combined cases per year)
            </p>
          </div>
        </div>

        <div class="trend-chart-wrap">
          <p class="chart-help">
            Both series are indexed to <strong>100</strong> at their first year so you can compare
            growth side by side.
          </p>
          <div ref="trendChartRef" class="trend-chart" />
        </div>
      </section>

      <section class="card-section">
        <h2>
          {{ showAllCancers ? '10 cancers tied to heavy-metal exposure' : 'Top 6 cancers tied to heavy-metal exposure' }}
        </h2>
        <p class="section-lede">
          These cancers all have published links to lead, mercury, or cadmium exposure. Here's how each one has grown in Australia from 1982 to 2010.
        </p>

        <div class="cancer-grid">
          <article
            v-for="(c, index) in displayedCancers"
            :key="c.name"
            class="cancer-card"
            :class="{
              'cancer-up': (c.change || 0) > 0,
              'cancer-flat': Math.abs(c.change || 0) < 5,
            }"
          >
            <div class="cancer-top">
              <span class="cancer-icon">{{ c.icon }}</span>
              <span v-if="index === 0" class="top-badge">Highest increase</span>
              <span v-else class="cancer-metal">Linked to {{ c.metal }}</span>
            </div>
            <h3>{{ c.name }}</h3>
            <p class="cancer-change">{{ pct(c.change) }}</p>
            <p class="cancer-detail">{{ formatNumber(c.latest) }} cases in 2010</p>
          </article>
        </div>

        <div class="expand-btn-wrap">
          <button type="button" class="expand-btn" @click="showAllCancers = !showAllCancers">
            {{ showAllCancers ? 'Show less ↑' : 'Show all cancers ↓' }}
          </button>
        </div>
      </section>

      <section class="card-section">
        <h2>What's in the air? Three metals, three risks.</h2>
        <p class="section-lede">
          Australia's industrial pollution data tracks three heavy metals known to come from
          electronics, batteries, and old screens.
        </p>

        <div class="metal-grid">
          <div v-for="m in metalMix" :key="m.metal" class="metal-card">
            <div class="metal-header">
              <span class="metal-symbol" :class="`metal-${m.metal.toLowerCase()}`">
                {{ m.metal === 'Lead' ? 'Pb' : m.metal === 'Mercury' ? 'Hg' : 'Cd' }}
              </span>
              <h3>{{ m.metal }}</h3>
            </div>

            <p class="metal-percent">{{ m.pct.toFixed(1) }}%</p>
            <p class="metal-share">of all heavy-metal air emissions</p>

            <div class="metal-divider"></div>

            <p class="metal-source">
              <span v-if="m.metal === 'Lead'">Old electronics, batteries, paint, soldering</span>
              <span v-else-if="m.metal === 'Mercury'">LCD screens, fluorescent bulbs, switches</span>
              <span v-else>Rechargeable batteries, plating, plastics</span>
            </p>
          </div>
        </div>
      </section>

      <section class="card-section">
        <h2>Where pollution concentrates</h2>
        <p class="section-lede">
          Just <strong>three states</strong> account for
          <strong>{{ Math.round(top3Share) }}%</strong>
          of Australia's reported heavy-metal air pollution. Local action — including responsible
          e-waste recycling — has the biggest impact in these areas.
        </p>

        <ol class="podium">
          <li v-for="(s, i) in topPollutingStates" :key="s.state" class="podium-item">
            <span class="podium-rank">{{ i + 1 }}</span>
            <div>
              <p class="podium-state">{{ s.state }}</p>
              <p class="podium-amount">{{ formatTonnes(s.kg) }} air emissions, all-time</p>
            </div>
          </li>
        </ol>

        <div ref="stateChartRef" class="state-chart" />
      </section>

      <section class="meaning-card">
        <p class="eyebrow">What this means for you</p>
        <h2>One phone may be small. Millions of phones aren't.</h2>
        <div class="meaning-grid">
          <div>
            <p class="meaning-num">8 g</p>
            <p>Average heavy-metal content in a single smartphone</p>
          </div>
          <div>
            <p class="meaning-num">~25 yrs</p>
            <p>How long lead can persist in soil after landfilling</p>
          </div>
          <div>
            <p class="meaning-num">100%</p>
            <p>Of these metals can be safely contained by recycling</p>
          </div>
        </div>
        <p class="meaning-foot">
          When you drop an old device at a verified e-waste centre, those grams stay out of the air,
          water, and food chain — for generations.
        </p>
      </section>

      <section class="method">
        <p class="eyebrow yellow">How we built this</p>
        <h3>Two parallel trends — not direct proof of causation.</h3>
        <ul>
          <li>
            <strong>What we can show:</strong> pollution and metal-linked cancers have both risen
            over the same decades.
          </li>
          <li>
            <strong>What this suggests:</strong> exposure to heavy metals from sources like e-waste may contribute to long-term health risks.
          </li>
          <li>
            <strong>Sources:</strong> AIHW Cancer Data (1982 - 2010) · National Pollutant Inventory
            (1998 - 2024) · IARC monographs.
          </li>
        </ul>
      </section>

      <section class="cta">
        <div>
          <h2>Be part of the solution.</h2>
          <p>Find a verified e-waste drop-off near you in seconds.</p>
        </div>
        <router-link to="/disposal-locations" class="cta-btn"> Find a disposal site → </router-link>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 32px 36px 64px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 32px;
  color: #173a29;
  background:
    radial-gradient(circle at 95% 0%, rgba(129, 199, 132, 0.1), transparent 22%),
    radial-gradient(circle at 0% 100%, rgba(67, 160, 71, 0.06), transparent 28%),
    linear-gradient(180deg, #f8fbf8 0%, #ffffff 100%);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 11px;
  font-weight: 700;
  color: #16a34a;
  margin: 0 0 8px;
}

.eyebrow.centered {
  text-align: center;
}

.eyebrow.yellow {
  color: #b45309;
}

.hero {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
  border: 1px solid #d1fae5;
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 12px 30px rgba(22, 163, 74, 0.05);
}

.hero h1 {
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
  font-weight: 800;
  color: #0f3a25;
  margin: 0 0 18px;
  max-width: 800px;
}

.hero .lede {
  font-size: 17px;
  line-height: 1.65;
  color: #355845;
  max-width: 760px;
  margin: 0;
}

.state {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  color: #4b5563;
}

.state.error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.pathway-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.pathway-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(251, 253, 251, 0.92));
  border: 1px solid rgba(210, 232, 214, 0.98);
  border-radius: 28px;
  padding: 32px;
  box-shadow: 0 18px 34px rgba(27, 67, 50, 0.05);
}

.pathway-evidence {
  margin: 8px 0 24px;
  color: #587465;
  line-height: 1.65;
  font-size: 15px;
}

.pathway-steps-vertical {
  display: flex;
  flex-direction: column;
  align-items: center;  
}

.step-box {
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.9);
  border: 1px solid rgba(210, 232, 214, 0.98);
  color: #163728;
  font-weight: 500;
}

.arrow-down {
  font-size: 20px;
  color: #2e7d32;
  margin: 6px 0;
}

.section-tag {
  display: inline-flex;
  margin: 0 0 20px;
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.9);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.pathway-card h2 {
  margin: 0 0 24px;
  color: #143324;
  font-size: 1.8rem;
  font-weight: 500;
}

.pathway-card p {
  color: #587465;
  line-height: 1.75;
  font-size: 15px;
}

.pathway-steps {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.pathway-steps strong {
  display: inline-flex;
  align-items: center;
  min-height: 48px;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(241, 248, 242, 0.9);
  border: 1px solid rgba(210, 232, 214, 0.98);
  color: #163728;
  font-weight: 500;
}

.pathway-steps .arrow {
  color: #2e7d32;
  font-size: 1.35rem;
  font-weight: 900;
}

.takeaway {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(15, 58, 37, 0.04);
}

.takeaway h2,
.card-section h2,
.meaning-card h2 {
  font-weight: 800;
  color: #0f3a25;
}

.takeaway h2 {
  font-size: clamp(24px, 3vw, 32px);
  margin: 0 0 12px;
}

.takeaway-lede {
  font-size: 16px;
  color: #4b5563;
  max-width: 720px;
  margin: 0 auto 28px;
  line-height: 1.6;
}

.big-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.big-stat {
  border-radius: 18px;
  padding: 24px;
  text-align: center;
}

.big-stat.danger {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
}

.big-stat.warning {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border: 1px solid #e9d5ff;
}

.big-icon {
  font-size: 36px;
  display: block;
  margin-bottom: 8px;
}

.big-label {
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  margin: 0 0 4px;
}

.big-value {
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  margin: 4px 0 8px;
}

.big-stat.danger .big-value {
  color: #dc2626;
}

.big-stat.warning .big-value {
  color: #7c3aed;
}

.big-hint {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.trend-chart-wrap {
  background: #fafafa;
  border-radius: 16px;
  padding: 20px;
  margin-top: 8px;
}

.chart-help {
  font-size: 13px;
  color: #6b7280;
  text-align: center;
  margin: 0 0 8px;
}

.trend-chart {
  width: 100%;
  height: 320px;
}

.card-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  padding: 36px;
  box-shadow: 0 4px 12px rgba(15, 58, 37, 0.04);
}

.card-section h2 {
  font-size: clamp(22px, 2.5vw, 28px);
  margin: 0 0 8px;
}

.section-lede {
  font-size: 15px;
  color: #4b5563;
  line-height: 1.6;
  max-width: 760px;
  margin: 0 0 24px;
}

.cancer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

.cancer-card {
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.cancer-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(15, 58, 37, 0.08);
}

.cancer-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.cancer-icon {
  font-size: 22px;
}

.cancer-metal,
.top-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
}

.cancer-metal {
  color: #6b7280;
  background: #f3f4f6;
}

.top-badge {
  color: #b45309;
  background: #fef3c7;
}

.cancer-card h3 {
  font-size: 15px;
  margin: 4px 0 8px;
  color: #1f2937;
  font-weight: 600;
  line-height: 1.3;
  min-height: 38px;
}

.cancer-change {
  font-size: 26px;
  font-weight: 800;
  margin: 0 0 4px;
  color: #6b7280;
}

.cancer-up .cancer-change {
  color: #dc2626;
}

.cancer-flat .cancer-change {
  color: #6b7280;
}

.cancer-detail {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.expand-btn-wrap {
  margin-top: 22px;
  text-align: center;
}

.expand-btn {
  border: none;
  background: #ecfdf5;
  color: #16a34a;
  font-size: 14px;
  font-weight: 700;
  padding: 11px 20px;
  border-radius: 999px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    transform 0.2s ease;
}

.expand-btn:hover {
  background: #d1fae5;
  transform: translateY(-1px);
}

.metal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.metal-card {
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 6px 16px rgba(15, 58, 37, 0.04);
}

.metal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.metal-symbol {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 16px;
}

.metal-lead {
  background: #dc2626;
}

.metal-mercury {
  background: #7c3aed;
}

.metal-cadmium {
  background: #0284c7;
}

.metal-card h3 {
  margin: 0;
  font-size: 20px;
  color: #1f2937;
}

.metal-percent {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
  margin: 0 0 8px;
  color: #dc2626;
}

.metal-card:nth-child(2) .metal-percent {
  color: #7c3aed;
}

.metal-card:nth-child(3) .metal-percent {
  color: #0284c7;
}

.metal-share {
  font-size: 14px;
  color: #4b5563;
  margin: 0;
  font-weight: 600;
}

.metal-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 20px 0;
}

.metal-source {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
  margin: 0;
}

@media (max-width: 900px) {
  .metal-grid {
    grid-template-columns: 1fr;
  }
}

.podium {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.podium-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
}

.podium-rank {
  font-size: 32px;
  font-weight: 800;
  color: #dc2626;
  width: 36px;
  text-align: center;
}

.podium-state {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.podium-amount {
  font-size: 12px;
  color: #6b7280;
  margin: 2px 0 0;
}

.state-chart {
  width: 100%;
  height: 360px;
}

.meaning-card {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border: 1px solid #6ee7b7;
  border-radius: 24px;
  padding: 40px;
}

.meaning-card h2 {
  font-size: clamp(22px, 2.5vw, 28px);
  margin: 0 0 24px;
}

.meaning-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 16px;
}

.meaning-grid > div {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  text-align: center;
  border: 1px solid #d1fae5;
}

.meaning-num {
  font-size: 36px;
  font-weight: 800;
  color: #15803d;
  margin: 0 0 6px;
  line-height: 1;
}

.meaning-grid p {
  font-size: 13px;
  color: #4b5563;
  margin: 0;
  line-height: 1.4;
}

.meaning-foot {
  margin: 0;
  font-size: 14px;
  color: #355845;
  text-align: center;
  padding-top: 8px;
  font-style: italic;
}

.method {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 16px;
  padding: 24px 28px;
}

.method h3 {
  font-size: 17px;
  color: #78350f;
  margin: 0 0 12px;
  font-weight: 700;
}

.method ul {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  color: #57534e;
  line-height: 1.7;
}

.cta {
  background: linear-gradient(135deg, #15803d 0%, #16a34a 100%);
  border-radius: 24px;
  padding: 36px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  box-shadow: 0 12px 30px rgba(22, 163, 74, 0.25);
}

.cta h2 {
  font-size: 26px;
  margin: 0 0 6px;
}

.cta p {
  font-size: 15px;
  margin: 0;
  opacity: 0.95;
}

.cta-btn {
  background: #fff;
  color: #15803d;
  padding: 14px 24px;
  border-radius: 999px;
  font-weight: 700;
  text-decoration: none;
  font-size: 15px;
  white-space: nowrap;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.cta-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.18);
}

@media (max-width: 900px) {
  .pathway-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .dashboard {
    padding: 24px 18px 56px;
  }

  .hero,
  .takeaway,
  .card-section,
  .meaning-card,
  .pathway-card {
    padding: 24px;
    border-radius: 18px;
  }

  .big-value {
    font-size: 42px;
  }

  .metal-card {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .cancer-card h3 {
    min-height: 0;
  }

  .trend-chart,
  .state-chart {
    height: 280px;
  }

  .cta {
    padding: 24px;
  }

  .cta h2 {
    font-size: 22px;
  }
}
</style>
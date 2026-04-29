<template>
  <section class="device-optimizer-page">
    <div class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">EcoTech AI</p>
        <h1>AI Device Optimizer</h1>
        <p class="lede">
          Choose your device type, write the issue in your own words, and get simple optimisation
          tips plus a plain-language explanation of what may be affecting performance.
        </p>
      </div>

      <div class="hero-meta">
        <div class="meta-chip">
          <span class="chip-label">Supported devices</span>
          <strong>Laptop and phone</strong>
        </div>
        <div class="meta-chip">
          <span class="chip-label">Input</span>
          <strong>Free-text issue description</strong>
        </div>
        <div class="meta-chip">
          <span class="chip-label">Output</span>
          <strong>Easy tips and explanation</strong>
        </div>
      </div>
    </div>

    <div class="workspace">
      <aside class="sidebar">
        <div class="panel">
          <div class="panel-heading">
            <h2>1. Device type</h2>
            <p>Choose the device you want help with.</p>
          </div>

          <div class="choice-list">
            <button
              v-for="device in deviceTypes"
              :key="device.value"
              class="choice-button"
              :class="{ active: selectedDeviceType === device.value }"
              type="button"
              @click="selectedDeviceType = device.value"
            >
              <span>{{ device.label }}</span>
              <small>{{ device.hint }}</small>
            </button>
          </div>
        </div>

        <div class="panel">
          <div class="panel-heading">
            <h2>2. Write the issue</h2>
            <p>Describe what you are seeing in your own words.</p>
          </div>

          <label class="issue-field">
            <span>Your issue</span>
            <textarea
              v-model="issueText"
              rows="7"
              placeholder="Describe the issue in your own words."
            />
          </label>
        </div>

        <div class="panel compact">
          <button class="primary-button" type="button" :disabled="isSending" @click="getTips">
            Get Optimisation Tips
          </button>
          <button class="secondary-button" type="button" @click="resetForm">
            Reset form
          </button>
          <p class="panel-note">
            The form checks that you select a device and write an issue before generating results.
          </p>
        </div>
      </aside>

      <main class="results-panel">
        <div class="results-header">
          <div>
            <p class="eyebrow">Results</p>
            <h2>{{ resultTitle }}</h2>
          </div>

          <div class="status-chip" :class="{ ready: canOptimize, loading: isSending }">
            <span v-if="isSending">Generating</span>
            <span v-else-if="canOptimize">Ready to run</span>
            <span v-else>Waiting for input</span>
          </div>
        </div>

        <article v-if="result" class="result-card">
          <div class="result-summary">
            <div class="summary-block">
              <span>Device</span>
              <strong>{{ result.device_label }}</strong>
            </div>
            <div class="summary-block">
              <span>Issue category</span>
              <strong>{{ result.issue_label }}</strong>
            </div>
            <div class="summary-block">
              <span>Why it matters</span>
              <strong>{{ result.device_summary }}</strong>
            </div>
          </div>

          <div class="result-section">
            <h3>What may be affecting your device</h3>
            <p>{{ result.issue_explanation }}</p>
          </div>

          <div class="result-section">
            <h3>Optimisation tips</h3>
            <ul class="tips-list">
              <li v-for="tip in result.suggestions" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </article>

        <article v-else class="placeholder-card">
          <p class="placeholder-title">Your optimisation tips will appear here.</p>
          <p>
            Select a device type, write your issue, then click <strong>Get Optimisation Tips</strong>.
          </p>
        </article>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </main>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { api } from '@/api'

const STORAGE_KEY = 'ecotech-device-optimizer-v2'

const deviceTypes = [
  {
    value: 'laptop',
    label: 'Laptop',
    hint: 'Good for study, work, and longer sessions',
  },
  {
    value: 'phone',
    label: 'Phone',
    hint: 'Good for everyday use and mobility',
  },
]

const selectedDeviceType = ref('')
const issueText = ref('')
const result = ref(null)
const errorMessage = ref('')
const isSending = ref(false)

const resultTitle = computed(() => {
  if (result.value) {
    return `${result.value.device_label} - ${result.value.issue_label}`
  }

  if (selectedDeviceType.value && issueText.value.trim()) {
    const device = getDeviceLabel(selectedDeviceType.value)
    return `${device} - Ready for analysis`
  }

  return 'No results yet'
})

const canOptimize = computed(() => Boolean(selectedDeviceType.value && issueText.value.trim()))

function getDeviceLabel(value) {
  const item = deviceTypes.find((entry) => entry.value === value)
  return item ? item.label : 'Device'
}

function loadState() {
  if (typeof window === 'undefined') return

  const raw = window.sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return

  try {
    const parsed = JSON.parse(raw)
    selectedDeviceType.value = parsed.selectedDeviceType || ''
    issueText.value = parsed.issueText || ''
    result.value = parsed.result || null
  } catch {
    selectedDeviceType.value = ''
    issueText.value = ''
    result.value = null
  }
}

function persistState() {
  if (typeof window === 'undefined') return

  window.sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      selectedDeviceType: selectedDeviceType.value,
      issueText: issueText.value,
      result: result.value,
    }),
  )
}

function resetForm() {
  selectedDeviceType.value = ''
  issueText.value = ''
  result.value = null
  errorMessage.value = ''
  persistState()
}

async function getTips() {
  if (!selectedDeviceType.value || !issueText.value.trim()) {
    errorMessage.value = 'Please select a device type and describe the issue before getting optimisation tips.'
    result.value = null
    persistState()
    return
  }

  if (isSending.value) return

  isSending.value = true
  errorMessage.value = ''

  try {
    const response = await api.getDeviceOptimizationTips({
      device_type: selectedDeviceType.value,
      issue_text: issueText.value.trim(),
    })

    result.value = response
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Something went wrong.'
    result.value = null
  } finally {
    isSending.value = false
    persistState()
  }
}

watch([selectedDeviceType, issueText, result], persistState, { deep: true })

onMounted(() => {
  loadState()
  persistState()
})
</script>

<style scoped>
.device-optimizer-page {
  min-height: 100vh;
  padding: 32px 24px 48px;
  background:
    radial-gradient(circle at top left, rgba(35, 123, 87, 0.2), transparent 28%),
    radial-gradient(circle at 88% 12%, rgba(219, 169, 79, 0.14), transparent 24%),
    linear-gradient(180deg, #f7fbf8 0%, #edf4ee 100%);
  color: #173023;
}

.hero-card,
.panel,
.results-panel {
  border: 1px solid rgba(23, 48, 35, 0.1);
  box-shadow: 0 18px 50px rgba(23, 48, 35, 0.08);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.hero-copy {
  max-width: 760px;
}

.eyebrow,
.chip-label {
  margin: 0 0 8px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #2b7a59;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(2.1rem, 4vw, 3.8rem);
  line-height: 1.02;
}

.lede {
  margin: 14px 0 0;
  max-width: 66ch;
  font-size: 1.02rem;
  line-height: 1.7;
  color: #51655c;
}

.hero-meta {
  display: grid;
  gap: 12px;
  min-width: 250px;
}

.meta-chip {
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f7fff9 0%, #e8f4ec 100%);
  border: 1px solid rgba(47, 125, 87, 0.16);
}

.meta-chip strong {
  display: block;
  font-size: 1rem;
  color: #173626;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  gap: 20px;
  margin-top: 20px;
}

.sidebar {
  display: grid;
  gap: 16px;
}

.panel,
.results-panel {
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
}

.panel-heading h2,
.results-header h2 {
  margin: 0;
}

.panel-heading p {
  margin: 6px 0 0;
  color: #5f7167;
  line-height: 1.5;
}

.choice-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.choice-button,
.primary-button,
.secondary-button {
  border: 0;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
}

.choice-button {
  text-align: left;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f4f8f5;
  color: #214132;
}

.choice-button span {
  display: block;
  font-weight: 700;
}

.choice-button small {
  display: block;
  margin-top: 4px;
  color: #60746a;
  line-height: 1.35;
}

.choice-button.active {
  background: linear-gradient(135deg, #c9efcf 0%, #9fe0ae 100%);
  box-shadow: 0 10px 20px rgba(63, 148, 82, 0.16);
}

.choice-button:hover,
.primary-button:hover,
.secondary-button:hover {
  transform: translateY(-1px);
}

.issue-field {
  display: grid;
  gap: 8px;
  margin-top: 16px;
  color: #294337;
}

.issue-field span {
  font-weight: 700;
}

.issue-field textarea,
.choice-button {
  width: 100%;
}

.issue-field textarea {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(22, 48, 35, 0.14);
  background: #fff;
  color: #173023;
  resize: vertical;
  outline: none;
  line-height: 1.6;
}

.issue-field textarea:focus {
  border-color: rgba(31, 122, 81, 0.45);
  box-shadow: 0 0 0 4px rgba(31, 122, 81, 0.08);
}

.panel.compact {
  display: grid;
  gap: 10px;
}

.primary-button,
.secondary-button {
  border-radius: 14px;
  padding: 12px 16px;
  font-weight: 700;
}

.primary-button {
  background: #1f7a51;
  color: #fff;
}

.primary-button:disabled {
  cursor: not-allowed;
  background: #93b8a1;
}

.secondary-button {
  background: #edf4ef;
  color: #234032;
}

.panel-note {
  margin: 0;
  color: #62776d;
  line-height: 1.55;
}

.results-panel {
  display: grid;
  gap: 16px;
  min-height: 72vh;
}

.results-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.status-chip {
  padding: 10px 14px;
  border-radius: 999px;
  background: #eef3ef;
  color: #5f7167;
  font-size: 0.92rem;
  font-weight: 700;
}

.status-chip.ready {
  background: #d4eed9;
  color: #1f6a48;
}

.status-chip.loading {
  background: #fff0d1;
  color: #91670f;
}

.result-card,
.placeholder-card {
  padding: 20px;
  border-radius: 22px;
  background: #f7fbf8;
  border: 1px solid rgba(23, 48, 35, 0.08);
}

.placeholder-card {
  display: grid;
  align-content: start;
  min-height: 300px;
}

.placeholder-title {
  margin-top: 0;
  font-size: 1.12rem;
  font-weight: 700;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-block {
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #eef6f0 100%);
  border: 1px solid rgba(47, 125, 87, 0.12);
}

.summary-block span {
  display: block;
  margin-bottom: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #5d7267;
}

.summary-block strong {
  display: block;
  color: #173626;
  line-height: 1.45;
}

.result-section + .result-section {
  margin-top: 16px;
}

.result-section h3 {
  margin: 0 0 8px;
}

.result-section p {
  margin: 0;
  line-height: 1.7;
  color: #244134;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 10px;
  color: #244134;
}

.error-message {
  margin: 0;
  color: #ad3b3b;
  font-weight: 600;
}

@media (max-width: 1080px) {
  .hero-card {
    flex-direction: column;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .results-panel {
    min-height: auto;
  }
}

@media (max-width: 760px) {
  .device-optimizer-page {
    padding: 18px 14px 28px;
  }

  .hero-card,
  .panel,
  .results-panel {
    border-radius: 20px;
  }

  .results-header {
    flex-direction: column;
  }

  .result-summary {
    grid-template-columns: 1fr;
  }
}
</style>

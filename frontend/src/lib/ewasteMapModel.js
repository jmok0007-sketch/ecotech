import { projectCoordinates } from './uvMapModel'

const STATE_ALIASES = {
  NSW: 'NSW',
  'NEW SOUTH WALES': 'NSW',
  VIC: 'VIC',
  VICTORIA: 'VIC',
  QLD: 'QLD',
  QUEENSLAND: 'QLD',
  SA: 'SA',
  'SOUTH AUSTRALIA': 'SA',
  WA: 'WA',
  'WESTERN AUSTRALIA': 'WA',
  TAS: 'TAS',
  TASMANIA: 'TAS',
  NT: 'NT',
  'NORTHERN TERRITORY': 'NT',
  ACT: 'ACT',
  'AUSTRALIAN CAPITAL TERRITORY': 'ACT',
}

const CATEGORY_CONFIG = {
  e_waste_recycling: { color: '#cc6b49', label: 'E-waste recycling' },
  battery_recycling: { color: '#d8a400', label: 'Battery recycling' },
  drop_off: { color: '#2a9d8f', label: 'Drop-off point' },
  transfer_station: { color: '#5f6caf', label: 'Transfer station' },
  repair_reuse: { color: '#7b9e45', label: 'Repair and reuse' },
  other: { color: '#8f5c7a', label: 'Other' },
}

const CATEGORY_ORDER = [
  'e_waste_recycling',
  'battery_recycling',
  'drop_off',
  'transfer_station',
  'repair_reuse',
  'other',
]

function titleCase(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function normalizeCategoryKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

function deriveCategory(row) {
  const explicit = normalizeCategoryKey(row?.category || row?.ewaste_category)
  if (CATEGORY_CONFIG[explicit]) {
    return explicit
  }

  if (row?.resourceType === 'repair') {
    return 'repair_reuse'
  }

  const haystack = [
    row?.ewaste_category,
    row?.ewaste_match_text,
    row?.ewaste_match_column,
    row?.facility_name,
    row?.source_file,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  if (haystack.includes('battery')) return 'battery_recycling'
  if (haystack.includes('repair') || haystack.includes('reuse') || haystack.includes('tip shop')) return 'repair_reuse'
  if (haystack.includes('transfer station') || haystack.includes('waste management') || haystack.includes('refuse')) return 'transfer_station'
  if (haystack.includes('recycling') || haystack.includes('resource recovery') || haystack.includes('recycle')) return 'e_waste_recycling'
  if (haystack.includes('drop off') || haystack.includes('drop-off') || haystack.includes('officeworks') || haystack.includes('harvey norman') || haystack.includes('domayne')) return 'drop_off'

  return 'other'
}

export function normalizeStateCode(value) {
  if (!value) return ''
  return STATE_ALIASES[String(value).trim().toUpperCase()] || ''
}

export function getCategoryColor(category) {
  return CATEGORY_CONFIG[category]?.color || CATEGORY_CONFIG.other.color
}

export function getCategoryLabel(category) {
  return CATEGORY_CONFIG[category]?.label || CATEGORY_CONFIG.other.label
}

export function getCategoryOptions() {
  return CATEGORY_ORDER.map((key) => ({
    value: key,
    label: getCategoryLabel(key),
    color: getCategoryColor(key),
  }))
}

export function buildFacilityMarkers(rows = []) {
  return rows
    .map((row, index) => {
      const latitude = Number(row?.latitude)
      const longitude = Number(row?.longitude)
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null

      const state = normalizeStateCode(row?.state)
      if (!state) return null

      const category = deriveCategory(row)
      const point = projectCoordinates(longitude, latitude)
      const facilityName = row?.facility_name || row?.name || `Facility ${index + 1}`
      const suburb = row?.suburb || ''
      const postcode = row?.postcode == null ? '' : String(row.postcode)

      return {
        id: row?.dedupe_key || `${facilityName}-${postcode}-${index}`,
        point,
        latitude,
        longitude,
        state,
        category,
        categoryColor: getCategoryColor(category),
        categoryLabel: getCategoryLabel(category),
        labelText: suburb ? `${titleCase(suburb)}${postcode ? ` ${postcode}` : ''}` : titleCase(facilityName),
        facilityName,
        suburb,
        postcode,
        address: row?.address || '',
        source: row?.source || '',
        score: row?.score == null ? null : Number(row.score),
        resourceType: row?.resourceType || '',
        coordSource: row?.coord_source || '',
        sourceFile: row?.source_file || '',
        row: {
          ...row,
          state,
          latitude,
          longitude,
          ewaste_category: category,
        },
      }
    })
    .filter(Boolean)
}

export function filterFacilities(rows = [], filters = {}) {
  const selectedState = normalizeStateCode(filters.selectedState)
  const selectedCategory = filters.selectedCategory || ''
  const searchTerm = String(filters.searchTerm || '').trim().toLowerCase()

  return rows.filter((row) => {
    if (selectedState && normalizeStateCode(row?.state) !== selectedState) return false

    const category = row?.category || deriveCategory(row)
    if (selectedCategory && category !== selectedCategory) return false

    if (!searchTerm) return true

    const haystack = [row?.facilityName, row?.facility_name, row?.suburb, row?.address, row?.postcode, row?.state, row?.source]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    return haystack.includes(searchTerm)
  })
}

export function buildCategorySummary(rows = []) {
  const counts = new Map()

  for (const row of rows) {
    const category = row?.category || deriveCategory(row)
    counts.set(category, (counts.get(category) || 0) + 1)
  }

  return CATEGORY_ORDER.map((category) => ({
    key: category,
    label: getCategoryLabel(category),
    color: getCategoryColor(category),
    count: counts.get(category) || 0,
  })).filter((item) => item.count > 0)
}

export function buildStateSummary(rows = []) {
  const counts = new Map()

  for (const row of rows) {
    const state = normalizeStateCode(row?.state)
    if (!state) continue
    counts.set(state, (counts.get(state) || 0) + 1)
  }

  return Array.from(counts.entries())
    .map(([state, count]) => ({ key: state, label: state, count }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
}

export function getFacilityBounds(rows = []) {
  const coordinates = rows
    .map((row) => {
      const latitude = Number(row?.latitude)
      const longitude = Number(row?.longitude)

      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        return null
      }

      return [longitude, latitude]
    })
    .filter(Boolean)

  if (!coordinates.length) return null

  const [firstLongitude, firstLatitude] = coordinates[0]
  const bounds = {
    minLongitude: firstLongitude,
    maxLongitude: firstLongitude,
    minLatitude: firstLatitude,
    maxLatitude: firstLatitude,
  }

  for (const [longitude, latitude] of coordinates.slice(1)) {
    bounds.minLongitude = Math.min(bounds.minLongitude, longitude)
    bounds.maxLongitude = Math.max(bounds.maxLongitude, longitude)
    bounds.minLatitude = Math.min(bounds.minLatitude, latitude)
    bounds.maxLatitude = Math.max(bounds.maxLatitude, latitude)
  }

  return bounds
}

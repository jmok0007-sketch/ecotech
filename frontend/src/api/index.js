const API_SITE = (import.meta.env.VITE_API_SITE || 'http://localhost:8000/api').replace(/\/$/, '')

const AI_API_SITE = API_SITE

console.log('API_SITE:', API_SITE)

async function request(baseUrl, path, options = {}) {
  const requestOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  }

  const response = await fetch(`${baseUrl}${path}`, requestOptions)

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json()
}

// API
export const api = {
  // Emissions
  getHeavyMetalState() {
    return request(API_SITE, '/emissions/state')
  },

  getHeavyMetalFacility() {
    return request(API_SITE, '/emissions/facility')
  },
  getHealthAll() {
    return request(API_SITE, '/health/all')
  },
  // Disposal locations
  searchDisposalLocations(options = {}) {
    return request(API_SITE, '/map/disposal-locations', options)
  },

  getDeviceOptimizationTips(payload) {
    return request(AI_API_SITE, '/ai/device-optimizer', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }
}

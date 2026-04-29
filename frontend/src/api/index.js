const API_SITE = (
  import.meta.env.VITE_API_SITE ||
  'http://ecotech-backend-prod.eba-muzmzyza.ap-southeast-2.elasticbeanstalk.com/api'
).replace(/\/$/, '')

async function request(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API request failed: ${response.status} - ${text}`)
  }

  return response.json()
}

export const api = {
  getHeavyMetalState() {
    return request(API_SITE, '/emissions/state')
  },

  getHeavyMetalFacility() {
    return request(API_SITE, '/emissions/facility')
  },

  getHealthAll() {
    return request(API_SITE, '/health/all')
  },

  searchDisposalLocations(options = {}) {
    return request(API_SITE, '/map/disposal-locations', options)
  },

  getDeviceOptimizationTips(payload) {
    return request(API_SITE, '/ai/device-optimizer', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
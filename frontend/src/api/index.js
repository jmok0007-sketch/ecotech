const API_SITE =
  import.meta.env.VITE_API_SITE ||
  "https://9f68uovov3.execute-api.ap-southeast-2.amazonaws.com/prod/api";

async function request(path, options = {}) {
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_SITE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  return response.json();
}

export const api = {
  getHealthAll() {
    return request("/health/all");
  },

  getHeavyMetalState() {
    return request("/emissions/state");
  },

  getHeavyMetalFacility() {
    return request("/emissions/facility");
  },

  searchDisposalLocations(options = {}) {
    return request("/map/disposal-locations", options);
  },

  getDeviceOptimizationTips(payload) {
    return request("/ai/device-optimizer", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
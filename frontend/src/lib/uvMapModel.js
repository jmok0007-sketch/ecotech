const AUSTRALIA_BOUNDS = {
  minLongitude: 112,
  maxLongitude: 154.5,
  minLatitude: -44.8,
  maxLatitude: -10,
}

export const VIC_BOUNDS = {
  minLongitude: 140.8,
  maxLongitude: 150.1,
  minLatitude: -39.3,
  maxLatitude: -33.9,
}

export const MELBOURNE_REGION_BOUNDS = {
  minLongitude: 143.6,
  maxLongitude: 146.3,
  minLatitude: -39.2,
  maxLatitude: -37.0,
}

export const mapViewport = {
  width: 980,
  height: 760,
  padding: 48,
}

const STATE_NAME_TO_CODE = {
  'NEW SOUTH WALES': 'NSW',
  VICTORIA: 'VIC',
  QUEENSLAND: 'QLD',
  'SOUTH AUSTRALIA': 'SA',
  'WESTERN AUSTRALIA': 'WA',
  TASMANIA: 'TAS',
  'NORTHERN TERRITORY': 'NT',
  'AUSTRALIAN CAPITAL TERRITORY': 'ACT',
  NSW: 'NSW',
  VIC: 'VIC',
  QLD: 'QLD',
  SA: 'SA',
  WA: 'WA',
  TAS: 'TAS',
  NT: 'NT',
  ACT: 'ACT',
}

export function stateCodeFromName(name) {
  if (!name) {
    return ''
  }

  return STATE_NAME_TO_CODE[String(name).trim().toUpperCase()] || ''
}

export function createProjector(bounds = AUSTRALIA_BOUNDS) {
  const xSpan = bounds.maxLongitude - bounds.minLongitude
  const ySpan = bounds.maxLatitude - bounds.minLatitude
  const drawableWidth = mapViewport.width - mapViewport.padding * 2
  const drawableHeight = mapViewport.height - mapViewport.padding * 2

  return (longitude, latitude) => {
    const x = ((Number(longitude) - bounds.minLongitude) / xSpan) * drawableWidth + mapViewport.padding
    const y = (1 - (Number(latitude) - bounds.minLatitude) / ySpan) * drawableHeight + mapViewport.padding

    return { x, y }
  }
}

export const projectCoordinates = createProjector()
export const projectVictoriaCoordinates = createProjector(VIC_BOUNDS)
export const projectMelbourneRegionCoordinates = createProjector(MELBOURNE_REGION_BOUNDS)

function collectRingPoints(coordinates = []) {
  const points = []

  for (const ring of coordinates) {
    for (const coordinate of ring || []) {
      if (Array.isArray(coordinate) && coordinate.length >= 2) {
        points.push(coordinate)
      }
    }
  }

  return points
}

function polygonPath(coordinates = [], projector = projectCoordinates) {
  return coordinates
    .map((ring) =>
      (ring || [])
        .map((coordinate, index) => {
          const point = projector(coordinate[0], coordinate[1])
          return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
        })
        .concat('Z')
        .join(' '),
    )
    .join(' ')
}

function centroidFromPoints(points, projector = projectCoordinates) {
  if (!points.length) {
    return null
  }

  let minX = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY

  for (const [longitude, latitude] of points) {
    minX = Math.min(minX, longitude)
    maxX = Math.max(maxX, longitude)
    minY = Math.min(minY, latitude)
    maxY = Math.max(maxY, latitude)
  }

  return projector((minX + maxX) / 2, (minY + maxY) / 2)
}

export function buildGeoFeaturePaths(geoJson, options = {}) {
  const features = Array.isArray(geoJson?.features) ? geoJson.features : []
  const projector = options.projector || projectCoordinates
  const getName = options.getName || ((properties) => properties.STATE_NAME || properties.name || '')
  const getCode = options.getCode || ((properties) => stateCodeFromName(properties.STATE_NAME || properties.name || properties.code || ''))

  return features.map((feature, index) => {
    const geometry = feature?.geometry || {}
    const properties = feature?.properties || {}
    const polygons = geometry.type === 'MultiPolygon' ? geometry.coordinates || [] : [geometry.coordinates || []]
    const points = polygons.flatMap((polygon) => collectRingPoints(polygon))

    return {
      name: getName(properties, feature, index),
      code: getCode(properties, feature, index),
      path: polygons.map((polygon) => polygonPath(polygon, projector)).join(' '),
      labelPoint: centroidFromPoints(points, projector),
      geometry,
      properties,
    }
  })
}

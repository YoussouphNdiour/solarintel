import { LocalPolygon } from '../types'

const EARTH_RADIUS = 6371000 // meters

/**
 * Convert a WGS84 polygon ring to local XY coordinates (meters)
 * with the centroid as the origin.
 * Returns points, centroid (lon/lat), and bounding box info.
 */
export function polygonToLocal(rings: [number, number][]): LocalPolygon {
  if (rings.length === 0) {
    return {
      points: [],
      centroid: [0, 0],
      bbox: { w: 10, h: 8, angle: 0, cx: 0, cy: 0 },
    }
  }

  // Compute geographic centroid
  const centLon = rings.reduce((s, p) => s + p[0], 0) / rings.length
  const centLat = rings.reduce((s, p) => s + p[1], 0) / rings.length
  const lat0 = (centLat * Math.PI) / 180

  // Project to local XY (meters)
  const points: [number, number][] = rings.map(([lon, lat]) => [
    ((lon - centLon) * Math.cos(lat0) * EARTH_RADIUS * Math.PI) / 180,
    ((lat - centLat) * EARTH_RADIUS * Math.PI) / 180,
  ])

  // Principal axis via PCA to find the dominant orientation
  const n = points.length
  let mx = 0
  let my = 0
  for (const [x, y] of points) {
    mx += x
    my += y
  }
  mx /= n
  my /= n

  let cxx = 0
  let cxy = 0
  let cyy = 0
  for (const [x, y] of points) {
    const dx = x - mx
    const dy = y - my
    cxx += dx * dx
    cxy += dx * dy
    cyy += dy * dy
  }
  cxx /= n
  cxy /= n
  cyy /= n

  // Angle of principal axis (eigenvector of covariance matrix)
  const angle = 0.5 * Math.atan2(2 * cxy, cxx - cyy)

  // Rotate points and compute axis-aligned bounding box
  const cos = Math.cos(-angle)
  const sin = Math.sin(-angle)

  let minU = Infinity
  let maxU = -Infinity
  let minV = Infinity
  let maxV = -Infinity

  for (const [x, y] of points) {
    const u = x * cos - y * sin
    const v = x * sin + y * cos
    if (u < minU) minU = u
    if (u > maxU) maxU = u
    if (v < minV) minV = v
    if (v > maxV) maxV = v
  }

  const w = maxU - minU
  const h = maxV - minV
  const cx = ((minU + maxU) / 2) * Math.cos(angle) - ((minV + maxV) / 2) * Math.sin(angle)
  const cy = ((minU + maxU) / 2) * Math.sin(angle) + ((minV + maxV) / 2) * Math.cos(angle)

  return {
    points,
    centroid: [centLon, centLat],
    bbox: { w, h, angle, cx, cy },
  }
}

/**
 * Default polygon: 10x8m rectangle centered at origin
 */
export function defaultPolygon(): LocalPolygon {
  const hw = 5
  const hh = 4
  return {
    points: [
      [-hw, -hh],
      [hw, -hh],
      [hw, hh],
      [-hw, hh],
    ],
    centroid: [0, 0],
    bbox: { w: 10, h: 8, angle: 0, cx: 0, cy: 0 },
  }
}

/**
 * Compute polygon area using Shoelace formula
 */
export function polygonArea(pts: [number, number][]): number {
  let area = 0
  const n = pts.length
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    area += pts[i][0] * pts[j][1]
    area -= pts[j][0] * pts[i][1]
  }
  return Math.abs(area) / 2
}

/**
 * Check if a point (px, py) is inside a polygon
 * Uses ray casting algorithm
 */
export function pointInPolygon(px: number, py: number, poly: [number, number][]): boolean {
  let inside = false
  const n = poly.length
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const xi = poly[i][0]
    const yi = poly[i][1]
    const xj = poly[j][0]
    const yj = poly[j][1]
    const intersect =
      yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

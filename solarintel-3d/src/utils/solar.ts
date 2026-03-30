import { SunPosition } from '../types'

/**
 * Solar Position Algorithm (simplified SPA)
 * Returns azimuth (0=N, 90=E, 180=S, 270=W) and elevation in degrees.
 * Based on NOAA Solar Calculator formulas.
 */
export function getSunPosition(
  lat: number,
  lon: number,
  date: Date,
  hour: number // fractional hour in local solar time approximation
): SunPosition {
  const latRad = (lat * Math.PI) / 180

  // Build a Date object for the given hour (UTC offset approximated from lon)
  const utcOffset = lon / 15
  const d = new Date(date)
  d.setUTCHours(0, 0, 0, 0)
  const utcHour = hour - utcOffset
  d.setTime(d.getTime() + utcHour * 3600 * 1000)

  // Julian Day Number
  const JD =
    d.getTime() / 86400000 + 2440587.5

  // Julian centuries from J2000.0
  const T = (JD - 2451545.0) / 36525.0

  // Geometric mean longitude of the Sun (degrees)
  const L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360

  // Geometric mean anomaly of the Sun (degrees)
  const M = (357.52911 + T * (35999.05029 - T * 0.0001537)) % 360
  const Mrad = (M * Math.PI) / 180

  // Equation of center
  const C =
    (1.914602 - T * (0.004817 + 0.000014 * T)) * Math.sin(Mrad) +
    (0.019993 - 0.000101 * T) * Math.sin(2 * Mrad) +
    0.000289 * Math.sin(3 * Mrad)

  // Sun's true longitude (degrees)
  const sunLon = L0 + C

  // Apparent longitude (correcting for nutation & aberration)
  const omega = 125.04 - 1934.136 * T
  const apparentLon = sunLon - 0.00569 - 0.00478 * Math.sin((omega * Math.PI) / 180)
  const apparentLonRad = (apparentLon * Math.PI) / 180

  // Mean obliquity of the ecliptic (degrees)
  const eps0 = 23.439291111 - T * (0.013004167 + T * (0.0000001639 - T * 0.0000005036))
  const epsCorr = eps0 + 0.00256 * Math.cos((omega * Math.PI) / 180)
  const epsRad = (epsCorr * Math.PI) / 180

  // Sun's declination
  const sinDec = Math.sin(epsRad) * Math.sin(apparentLonRad)
  const dec = Math.asin(sinDec)

  // Right ascension
  const RA =
    (Math.atan2(Math.cos(epsRad) * Math.sin(apparentLonRad), Math.cos(apparentLonRad)) *
      180) /
    Math.PI

  // Greenwich Mean Sidereal Time (degrees)
  const JD0 = Math.floor(JD - 0.5) + 0.5
  const T0 = (JD0 - 2451545.0) / 36525.0
  const UT = ((JD - JD0) * 24) % 24
  const GMST =
    (6.697375 + 0.065709824279 * (JD - 2451545.0) + UT) % 24

  // Local Hour Angle (degrees)
  const LMST = ((GMST + lon / 15) % 24 + 24) % 24
  const HA = ((LMST - RA / 15) * 15 + 360) % 360
  const HArad = (HA * Math.PI) / 180

  // Solar elevation
  const sinAlt =
    Math.sin(latRad) * sinDec + Math.cos(latRad) * Math.cos(dec) * Math.cos(HArad)
  const elevation = (Math.asin(Math.max(-1, Math.min(1, sinAlt))) * 180) / Math.PI

  // Solar azimuth
  const cosAz =
    (sinDec - Math.sin(latRad) * sinAlt) /
    (Math.cos(latRad) * Math.cos((elevation * Math.PI) / 180) + 1e-10)
  let azimuth = (Math.acos(Math.max(-1, Math.min(1, cosAz))) * 180) / Math.PI
  if (Math.sin(HArad) > 0) azimuth = 360 - azimuth

  return { azimuth, elevation }
}

/**
 * Returns fractional hours of sunrise and sunset for a given lat/lon/date.
 * Returns null if sun never rises (polar night) or never sets (midnight sun).
 */
export function getSunriseSunset(
  lat: number,
  lon: number,
  date: Date
): { sunrise: number; sunset: number } | null {
  // Approximate by scanning every 15 min
  let prevElev = getSunPosition(lat, lon, date, 0).elevation
  let sunrise: number | null = null
  let sunset: number | null = null

  for (let h = 0.25; h <= 24; h += 0.25) {
    const elev = getSunPosition(lat, lon, date, h).elevation
    if (prevElev < 0 && elev >= 0 && sunrise === null) sunrise = h - 0.125
    if (prevElev >= 0 && elev < 0 && sunset === null) sunset = h - 0.125
    prevElev = elev
  }

  if (sunrise === null || sunset === null) return null
  return { sunrise, sunset }
}

/**
 * Sample sun path arc (elevation > 0) as array of {h, azimuth, elevation}
 * Resolution: every 15 min
 */
export function getSunPathArc(
  lat: number,
  lon: number,
  date: Date
): Array<{ h: number; azimuth: number; elevation: number }> {
  const result = []
  for (let h = 0; h < 24; h += 0.25) {
    const pos = getSunPosition(lat, lon, date, h)
    if (pos.elevation > 0) {
      result.push({ h, ...pos })
    }
  }
  return result
}

/**
 * Convert sun azimuth + elevation to a 3D direction vector
 * Three.js convention: Y up, -Z = north, X = east
 */
export function sunToDirection(
  azimuth: number,
  elevation: number,
  distance = 100
): [number, number, number] {
  const azRad = (azimuth * Math.PI) / 180
  const elRad = (elevation * Math.PI) / 180
  const x = distance * Math.cos(elRad) * Math.sin(azRad)   // east
  const y = distance * Math.sin(elRad)                       // up
  const z = -distance * Math.cos(elRad) * Math.cos(azRad)   // -north
  return [x, y, z]
}

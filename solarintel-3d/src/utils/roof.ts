import * as THREE from 'three'
import { RoofType } from '../types'
import { pointInPolygon } from './geo'

export interface RoofFace {
  geometry: THREE.BufferGeometry
  normal: THREE.Vector3        // world-space normal of the face
  tiltDeg: number              // tilt angle in degrees from horizontal
  azimuthDeg: number           // azimuth of the down-slope direction
  /** XZ boundary polygon of this face (used for panel containment checks) */
  polygonXZ?: [number, number][]
  /**
   * Returns the LOCAL height (above the eave / above wallHeight) at world XZ position (x, z).
   * Panel world Y = wallHeight + getLocalY(x, z).
   * Only set for polygon-clipped faces from buildRoofFromPolygon.
   */
  getLocalY?: (x: number, z: number) => number
}

export interface RoofConfig {
  type: RoofType
  pitch: number       // degrees
  azimuth: number     // degrees (orientation of ridge/slope, 0=N, 180=S)
  wallHeight: number  // meters
  bboxW: number       // bounding box width (along principal axis)
  bboxH: number       // bounding box height (perpendicular)
  bboxAngle: number   // rotation angle of bbox (radians)
}

/**
 * Build roof geometry for a given config.
 * The geometry is in local XZ space (Y=up) centered at origin.
 * The caller is responsible for positioning at Y=wallHeight.
 *
 * Returns an array of RoofFace (one for flat, two for shed/gable, four for hip).
 */
export function buildRoofGeometry(cfg: RoofConfig): RoofFace[] {
  const { type, pitch, wallHeight, bboxW, bboxH } = cfg
  const pitchRad = (pitch * Math.PI) / 180
  const rise = Math.tan(pitchRad)

  switch (type) {
    case 'flat':
      return buildFlatRoof(bboxW, bboxH, cfg.bboxAngle)
    case 'shed':
      return buildShedRoof(bboxW, bboxH, cfg.bboxAngle, rise, pitch, cfg.azimuth)
    case 'gable':
      return buildGableRoof(bboxW, bboxH, cfg.bboxAngle, rise, pitch, cfg.azimuth)
    case 'hip':
      return buildHipRoof(bboxW, bboxH, cfg.bboxAngle, rise, pitch, cfg.azimuth)
    default:
      return buildFlatRoof(bboxW, bboxH, cfg.bboxAngle)
  }
}

function makeBufferGeo(positions: number[], normals: number[], uvs: number[]): THREE.BufferGeometry {
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3))
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
  geo.computeBoundingBox()
  return geo
}

function rotateXZ(x: number, z: number, angle: number): [number, number] {
  const c = Math.cos(angle)
  const s = Math.sin(angle)
  return [x * c - z * s, x * s + z * c]
}

function buildFlatRoof(w: number, h: number, angle: number): RoofFace[] {
  // Flat quad in XZ plane at Y=0 (parent positions at wallHeight)
  const hw = w / 2
  const hh = h / 2
  const corners: [number, number][] = [
    [-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh],
  ]
  const rot = corners.map(([x, z]) => rotateXZ(x, z, angle))

  const positions = [
    rot[0][0], 0, rot[0][1],
    rot[1][0], 0, rot[1][1],
    rot[2][0], 0, rot[2][1],
    rot[0][0], 0, rot[0][1],
    rot[2][0], 0, rot[2][1],
    rot[3][0], 0, rot[3][1],
  ]
  const normals = Array(6).fill([0, 1, 0]).flat()
  const uvs = [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]

  return [{
    geometry: makeBufferGeo(positions, normals, uvs),
    normal: new THREE.Vector3(0, 1, 0),
    tiltDeg: 0,
    azimuthDeg: 180,
  }]
}

function buildShedRoof(w: number, h: number, angle: number, rise: number, pitchDeg: number, roofAzimuth: number): RoofFace[] {
  // Shed: one slope. Front (z = -h/2) is low, back (z = +h/2) is high.
  const hw = w / 2
  const hh = h / 2
  const ridgeHeight = rise * h

  const corners: [number, number, number][] = [
    [-hw, 0,          -hh],
    [ hw, 0,          -hh],
    [ hw, ridgeHeight, hh],
    [-hw, ridgeHeight, hh],
  ]
  // Rotate around Y axis
  const rot = corners.map(([x, y, z]) => {
    const [rx, rz] = rotateXZ(x, z, angle)
    return [rx, y, rz] as [number, number, number]
  })

  const positions = [
    ...rot[0], ...rot[1], ...rot[2],
    ...rot[0], ...rot[2], ...rot[3],
  ]

  // Normal of shed face — rotate using same convention as rotateXZ (not applyAxisAngle)
  const cosP = Math.cos(pitchDeg * Math.PI / 180)
  const sinP = Math.sin(pitchDeg * Math.PI / 180)
  const [snx, snz] = rotateXZ(0, -sinP, angle)
  const slopeNorm = new THREE.Vector3(snx, cosP, snz)

  const n = [slopeNorm.x, slopeNorm.y, slopeNorm.z]
  const normals = Array(6).fill(n).flat()
  const uvs = [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]

  return [{
    geometry: makeBufferGeo(positions, normals, uvs),
    normal: slopeNorm,
    tiltDeg: pitchDeg,
    azimuthDeg: roofAzimuth,
  }]
}

function buildGableRoof(w: number, h: number, angle: number, rise: number, pitchDeg: number, roofAzimuth: number): RoofFace[] {
  const hw = w / 2
  const hh = h / 2
  const ridgeH = rise * hh  // rise from eave to ridge (half width)

  // Front face (z < 0 side, slopes up to ridge at z=0)
  const frontCorners: [number, number, number][] = [
    [-hw, 0,    -hh],
    [ hw, 0,    -hh],
    [ hw, ridgeH, 0],
    [-hw, ridgeH, 0],
  ]
  // Back face (z > 0 side)
  const backCorners: [number, number, number][] = [
    [ hw, 0,    hh],
    [-hw, 0,    hh],
    [-hw, ridgeH, 0],
    [ hw, ridgeH, 0],
  ]

  function buildFace(corners: [number, number, number][], nSign: number): RoofFace {
    const rot = corners.map(([x, y, z]) => {
      const [rx, rz] = rotateXZ(x, z, angle)
      return [rx, y, rz] as [number, number, number]
    })
    const positions = [
      ...rot[0], ...rot[1], ...rot[2],
      ...rot[0], ...rot[2], ...rot[3],
    ]
    const cosP2 = Math.cos(pitchDeg * Math.PI / 180)
    const sinP2 = Math.sin(pitchDeg * Math.PI / 180)
    const [gnx, gnz] = rotateXZ(0, nSign * sinP2, angle)
    const slopeNorm = new THREE.Vector3(gnx, cosP2, gnz)
    const n = [slopeNorm.x, slopeNorm.y, slopeNorm.z]
    const normals = Array(6).fill(n).flat()
    const uvs = [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1]
    return {
      geometry: makeBufferGeo(positions, normals, uvs),
      normal: slopeNorm,
      tiltDeg: pitchDeg,
      azimuthDeg: nSign > 0 ? roofAzimuth : (roofAzimuth + 180) % 360,
    }
  }

  return [buildFace(frontCorners, -1), buildFace(backCorners, 1)]
}

function buildHipRoof(w: number, h: number, angle: number, rise: number, pitchDeg: number, roofAzimuth: number): RoofFace[] {
  const hw = w / 2
  const hh = h / 2
  // Ridge offset from end: ridgeEndOffset = hh / rise (capped by hw)
  const ridgeH = rise * hh
  const ridgeEndOffset = Math.min(hw, hh)
  const rw = hw - ridgeEndOffset  // half-ridge length

  // Ridge line: from [-rw, ridgeH, 0] to [rw, ridgeH, 0]
  // 4 faces: front, back, left, right

  function buildHipFace(verts: [number, number, number][], faceNormal: THREE.Vector3, tilt: number, az: number): RoofFace {
    const rot = verts.map(([x, y, z]) => {
      const [rx, rz] = rotateXZ(x, z, angle)
      return [rx, y, rz] as [number, number, number]
    })
    // triangulate as fan from first vertex or as quads
    const positions: number[] = []
    const uvs: number[] = []
    if (rot.length === 4) {
      positions.push(...rot[0], ...rot[1], ...rot[2])
      positions.push(...rot[0], ...rot[2], ...rot[3])
      uvs.push(0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1)
    } else {
      // triangle
      positions.push(...rot[0], ...rot[1], ...rot[2])
      uvs.push(0, 0, 1, 0, 0.5, 1)
    }
    const nn = [faceNormal.x, faceNormal.y, faceNormal.z]
    const normals = Array(positions.length / 3).fill(nn).flat()
    return {
      geometry: makeBufferGeo(positions, normals, uvs),
      normal: faceNormal.clone(),
      tiltDeg: tilt,
      azimuthDeg: az,
    }
  }

  const hcosP = Math.cos(pitchDeg * Math.PI / 180)
  const hsinP = Math.sin(pitchDeg * Math.PI / 180)

  // Front face — normal rotated via rotateXZ (same convention as vertices)
  const [fnx, fnz] = rotateXZ(0, -hsinP, angle)
  const frontNorm = new THREE.Vector3(fnx, hcosP, fnz)

  // Back face
  const [bnx, bnz] = rotateXZ(0, hsinP, angle)
  const backNorm = new THREE.Vector3(bnx, hcosP, bnz)

  // Left triangle
  const [lnx, lnz] = rotateXZ(-hsinP, 0, angle)
  const leftNorm = new THREE.Vector3(lnx, hcosP, lnz)

  // Right triangle
  const [rnx, rnz] = rotateXZ(hsinP, 0, angle)
  const rightNorm = new THREE.Vector3(rnx, hcosP, rnz)

  return [
    buildHipFace([[-hw,0,-hh], [hw,0,-hh], [rw,ridgeH,0], [-rw,ridgeH,0]], frontNorm, pitchDeg, roofAzimuth),
    buildHipFace([[hw,0,hh], [-hw,0,hh], [-rw,ridgeH,0], [rw,ridgeH,0]], backNorm, pitchDeg, (roofAzimuth + 180) % 360),
    buildHipFace([[-hw,0,-hh], [-hw,0,hh], [-rw,ridgeH,0]], leftNorm, pitchDeg, (roofAzimuth + 270) % 360),
    buildHipFace([[hw,0,hh], [hw,0,-hh], [rw,ridgeH,0]], rightNorm, pitchDeg, (roofAzimuth + 90) % 360),
  ]
}

// ─── Sutherland-Hodgman polygon clip ─────────────────────────────────────────
// Keeps the half-plane where a*x + b*z + c >= 0 (polygon coords are [x, z]).
function clipPoly(poly: [number, number][], a: number, b: number, c: number): [number, number][] {
  const out: [number, number][] = []
  const n = poly.length
  for (let i = 0; i < n; i++) {
    const [cx, cz] = poly[i]
    const [nx, nz] = poly[(i + 1) % n]
    const dc = a * cx + b * cz + c
    const dn = a * nx + b * nz + c
    if (dc >= 0) out.push([cx, cz])
    if ((dc >= 0) !== (dn >= 0)) {
      const t = dc / (dc - dn)
      out.push([cx + t * (nx - cx), cz + t * (nz - cz)])
    }
  }
  return out
}

// Build a ShapeGeometry (flat XZ) from local polygon points [x, z].
function makeShapeGeo(pts: [number, number][]): THREE.BufferGeometry | null {
  if (pts.length < 3) return null
  const shape = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, -z)))
  const geo = new THREE.ShapeGeometry(shape)
  geo.rotateX(-Math.PI / 2)
  return geo
}

// Apply Y displacement to each vertex of a flat XZ geometry.
// toBbox maps world (x, z) → bbox-aligned (u, v) for slope computation.
function applyY(
  geo: THREE.BufferGeometry,
  getY: (u: number, v: number) => number,
  toBbox: (x: number, z: number) => [number, number]
): void {
  const arr = geo.attributes.position.array as Float32Array
  for (let i = 0; i < arr.length; i += 3) {
    const [u, v] = toBbox(arr[i], arr[i + 2])
    arr[i + 1] = getY(u, v)
  }
  ;(geo.attributes.position as THREE.BufferAttribute).needsUpdate = true
  geo.computeVertexNormals()
  geo.computeBoundingBox()
}

/**
 * Build polygon-clipped roof geometry from actual building footprint.
 * Returns faces whose geometry is clipped to the exact polygon shape —
 * no bbox-rectangle overflow.
 *
 * @param points   Local XZ polygon points (from polygonToLocal)
 * @param type     Roof type
 * @param pitch    Pitch angle (degrees)
 * @param azimuth  Roof azimuth (degrees)
 * @param bboxAngle Bbox principal-axis angle (radians)
 * @param bboxW    Bbox width  (meters)
 * @param bboxH    Bbox height (meters)
 */
export function buildRoofFromPolygon(
  points: [number, number][],
  type: RoofType,
  pitch: number,
  azimuth: number,
  bboxAngle: number,
  bboxW: number,
  bboxH: number,
): RoofFace[] {
  if (points.length < 3) return []

  const pitchRad = (pitch * Math.PI) / 180
  const rise = Math.tan(pitchRad)
  const hw = bboxW / 2
  const hh = bboxH / 2
  const cosP = Math.cos(pitchRad)
  const sinP = Math.sin(pitchRad)

  // Transform world (x, z) → bbox-aligned (u, v)
  const ca = Math.cos(-bboxAngle), sa = Math.sin(-bboxAngle)
  function toBbox(x: number, z: number): [number, number] {
    return [x * ca - z * sa, x * sa + z * ca]
  }
  // Transform bbox (u, v) → world (x, z)
  const cb = Math.cos(bboxAngle), sb = Math.sin(bboxAngle)
  function toWorld(u: number, v: number): [number, number] {
    return [u * cb - v * sb, u * sb + v * cb]
  }

  // ── FLAT ──────────────────────────────────────────────────────────────────
  if (type === 'flat') {
    const geo = makeShapeGeo(points)
    if (!geo) return []
    geo.computeBoundingBox()
    return [{
      geometry: geo,
      normal: new THREE.Vector3(0, 1, 0),
      tiltDeg: 0,
      azimuthDeg: 180,
      polygonXZ: points,
      getLocalY: () => 0,
    }]
  }

  // ── SHED ──────────────────────────────────────────────────────────────────
  if (type === 'shed') {
    const shedGetY = (_u: number, v: number) => Math.max(0, rise * (v + hh))
    const geo = makeShapeGeo(points)
    if (!geo) return []
    applyY(geo, shedGetY, toBbox)
    const [snx, snz] = rotateXZ(0, -sinP, bboxAngle)
    return [{
      geometry: geo,
      normal: new THREE.Vector3(snx, cosP, snz),
      tiltDeg: pitch,
      azimuthDeg: azimuth,
      polygonXZ: points,
      getLocalY: (x, z) => { const [, v] = toBbox(x, z); return shedGetY(0, v) },
    }]
  }

  // ── GABLE ─────────────────────────────────────────────────────────────────
  if (type === 'gable') {
    const bboxPts = points.map(([x, z]) => toBbox(x, z) as [number, number])
    const gableGetY = (_u: number, v: number) => Math.max(0, rise * (hh - Math.abs(v)))

    const faceDefs: { keep: [number, number, number][], nSign: number }[] = [
      { keep: [[0, -1, 0]],  nSign: -1 },
      { keep: [[0,  1, 0]],  nSign:  1 },
    ]

    return faceDefs.flatMap(({ keep, nSign }) => {
      let clipped = bboxPts
      for (const [a, b, c] of keep) clipped = clipPoly(clipped, a, b, c)
      if (clipped.length < 3) return []
      const worldPts = clipped.map(([u, v]) => toWorld(u, v) as [number, number])
      const geo = makeShapeGeo(worldPts)
      if (!geo) return []
      applyY(geo, gableGetY, toBbox)
      const [gnx, gnz] = rotateXZ(0, nSign * sinP, bboxAngle)
      return [{
        geometry: geo,
        normal: new THREE.Vector3(gnx, cosP, gnz),
        tiltDeg: pitch,
        azimuthDeg: nSign < 0 ? azimuth : (azimuth + 180) % 360,
        polygonXZ: worldPts,
        getLocalY: (x, z) => { const [u, v] = toBbox(x, z); return gableGetY(u, v) },
      }] satisfies RoofFace[]
    })
  }

  // ── HIP ───────────────────────────────────────────────────────────────────
  if (type === 'hip') {
    const bboxPts = points.map(([x, z]) => toBbox(x, z) as [number, number])
    const ridgeH = rise * hh
    const hipGetY = (u: number, v: number) =>
      Math.max(0, Math.min(rise * (hh - Math.abs(v)), rise * (hw - Math.abs(u)), ridgeH))

    const faceDefs: { clips: [number, number, number][], norm: THREE.Vector3, az: number }[] = [
      {
        clips: [[0,-1,0], [-hh,-hw,0], [hh,-hw,0]],
        norm: new THREE.Vector3(...rotateXZ(0, -sinP, bboxAngle) as [number, number], 0)
          .set(rotateXZ(0, -sinP, bboxAngle)[0], cosP, rotateXZ(0, -sinP, bboxAngle)[1]),
        az: azimuth,
      },
      {
        clips: [[0,1,0], [-hh,hw,0], [hh,hw,0]],
        norm: new THREE.Vector3(rotateXZ(0, sinP, bboxAngle)[0], cosP, rotateXZ(0, sinP, bboxAngle)[1]),
        az: (azimuth + 180) % 360,
      },
      {
        clips: [[-1,0,0], [-hw,-hh,0], [-hw,hh,0]],
        norm: new THREE.Vector3(rotateXZ(-sinP, 0, bboxAngle)[0], cosP, rotateXZ(-sinP, 0, bboxAngle)[1]),
        az: (azimuth + 270) % 360,
      },
      {
        clips: [[1,0,0], [hw,-hh,0], [hw,hh,0]],
        norm: new THREE.Vector3(rotateXZ(sinP, 0, bboxAngle)[0], cosP, rotateXZ(sinP, 0, bboxAngle)[1]),
        az: (azimuth + 90) % 360,
      },
    ]

    return faceDefs.flatMap(({ clips, norm, az }) => {
      let clipped = bboxPts
      for (const [a, b, c] of clips) clipped = clipPoly(clipped, a, b, c)
      if (clipped.length < 3) return []
      const worldPts = clipped.map(([u, v]) => toWorld(u, v) as [number, number])
      const geo = makeShapeGeo(worldPts)
      if (!geo) return []
      applyY(geo, hipGetY, toBbox)
      return [{
        geometry: geo, normal: norm, tiltDeg: pitch, azimuthDeg: az,
        polygonXZ: worldPts,
        getLocalY: (x, z) => { const [u, v] = toBbox(x, z); return hipGetY(u, v) },
      }] satisfies RoofFace[]
    })
  }

  return []
}

/**
 * Generate panel grid positions on a roof face.
 * Returns array of { x, y, z, tilt, azimuth } in local 3D coords.
 */
export function generatePanelPositions(
  face: RoofFace,
  polygonPts: [number, number][],
  wallHeight: number,
  panelW = 1.72,
  panelH = 1.04,
  spacing = 0.1,
  maxPanels = 200
): Array<{ x: number; y: number; z: number; tilt: number; azimuth: number }> {
  const geo = face.geometry
  if (!geo.boundingBox) geo.computeBoundingBox()
  const bb = geo.boundingBox!

  const stepX = panelW + spacing
  const stepZ = panelH + spacing

  const results: Array<{ x: number; y: number; z: number; tilt: number; azimuth: number }> = []

  // Sample grid over bounding box XZ
  for (let x = bb.min.x + panelW / 2; x <= bb.max.x - panelW / 2 && results.length < maxPanels; x += stepX) {
    for (let z = bb.min.z + panelH / 2; z <= bb.max.z - panelH / 2 && results.length < maxPanels; z += stepZ) {
      // Check containment in polygon (XZ → geo XY)
      if (polygonPts.length > 0 && !pointInPolygon(x, z, polygonPts)) continue

      // Compute Y from face normal equation: face passes through origin at Y=wallHeight
      // The face plane: normal . (P - P0) = 0
      // We need y at position (x, z) on the face
      const y = getYOnFace(face, x, z, wallHeight)

      results.push({ x, y, z, tilt: face.tiltDeg, azimuth: face.azimuthDeg })
    }
  }

  return results
}

function getYOnFace(face: RoofFace, x: number, z: number, wallHeight: number): number {
  // Plane equation: n.x*(x-px) + n.y*(y-py) + n.z*(z-pz) = 0
  // A point on the plane: (0, wallHeight, 0) (eave center)
  const n = face.normal
  if (Math.abs(n.y) < 1e-6) return wallHeight
  // n.x*(x-0) + n.y*(y-wallHeight) + n.z*(z-0) = 0
  // y = wallHeight - (n.x*x + n.z*z) / n.y
  return wallHeight - (n.x * x + n.z * z) / n.y
}

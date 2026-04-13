import { useMemo, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { LocalPolygon, RoofType, Obstacle } from '../types'
import { buildRoofGeometry, buildRoofFromPolygon, RoofFace } from '../utils/roof'
import { useStore } from '../store/useStore'
import { getSunPosition, sunToDirection } from '../utils/solar'
import { OBSTACLE_CFG } from './Obstacles'

const PANEL_THICKNESS = 0.04

const COLOR_NORMAL   = new THREE.Color('#0EA5E9')
const COLOR_SELECTED = new THREE.Color('#F59E0B')
const COLOR_ADD_PREVIEW = new THREE.Color('#22C55E')

// Irradiance color ramp: 0 (shadow/night) → 1 (full sun)
function irradianceToColor(t: number): THREE.Color {
  if (t <= 0) return new THREE.Color('#1E293B')
  if (t < 0.25) return new THREE.Color().lerpColors(new THREE.Color('#1E3A5F'), new THREE.Color('#1D4ED8'), t / 0.25)
  if (t < 0.55) return new THREE.Color().lerpColors(new THREE.Color('#1D4ED8'), new THREE.Color('#0EA5E9'), (t - 0.25) / 0.30)
  if (t < 0.80) return new THREE.Color().lerpColors(new THREE.Color('#0EA5E9'), new THREE.Color('#22C55E'), (t - 0.55) / 0.25)
  return new THREE.Color().lerpColors(new THREE.Color('#22C55E'), new THREE.Color('#FBBF24'), (t - 0.80) / 0.20)
}

function computeIrradiance(
  px: number, py: number, pz: number,
  normal: THREE.Vector3,
  obstacles: Obstacle[],
  sunAz: number, sunEl: number
): number {
  if (sunEl <= 0) return 0

  const elRad = (sunEl * Math.PI) / 180
  const azRad = (sunAz * Math.PI) / 180
  const sunDir = new THREE.Vector3(
    Math.cos(elRad) * Math.sin(azRad),
    Math.sin(elRad),
    -Math.cos(elRad) * Math.cos(azRad)
  ).normalize()

  const incidence = Math.max(0, normal.dot(sunDir))
  if (incidence < 0.01) return 0

  const panelPos = new THREE.Vector3(px, py, pz)
  const shadowDir = sunDir.clone().negate()

  for (const obs of obstacles) {
    const cfg = OBSTACLE_CFG[obs.type]
    const obsTop = new THREE.Vector3(obs.x, obs.y + cfg.h, obs.z)
    const obsToPanel = panelPos.clone().sub(obsTop)
    const projLen = obsToPanel.dot(shadowDir)
    if (projLen > 0) {
      const projected = shadowDir.clone().multiplyScalar(projLen)
      const perpDist = obsToPanel.clone().sub(projected).length()
      const obsRadius = Math.max(cfg.w, cfg.d) * 0.6
      if (perpDist < obsRadius) {
        return incidence * 0.15
      }
    }
  }

  return Math.min(1, incidence * (0.5 + 0.5 * Math.sin(elRad)))
}

interface PanelPos {
  x: number; y: number; z: number
  tilt: number
  az: number
  normal: THREE.Vector3
  faceRight?: THREE.Vector3   // for proper panel quaternion
  faceDown?:  THREE.Vector3
}

interface Props {
  localPoly: LocalPolygon
  roofType: RoofType
  pitch: number
  azimuth: number
  wallHeight: number
  // Props optionnelles pour multi-zone (surchargent le store)
  overridePanelCount?: number
  overridePanelPositions?: [number, number][] | null
  overrideHolePolygons?: [number, number][][] | null
}

const EARTH_RADIUS = 6371000

export default function SolarPanels({ localPoly, roofType, pitch, azimuth, wallHeight, overridePanelCount, overridePanelPositions, overrideHolePolygons }: Props) {
  const {
    panelCount: storePanelCount, selectedPanel, setSelectedPanel,
    removedPanels, sceneMode, addPanel,
    irradianceMode, lat, lon, simDate, simHour, obstacles,
    panelWidthMm, panelHeightMm, orientation,
    spacingHCm, spacingVCm,
    panelPositions: storePanelPositions,
    holePolygons: storeHolePolygons,
    selectedRoofFaces,
  } = useStore()

  const panelCount = overridePanelCount ?? storePanelCount
  const panelPositions = overridePanelPositions !== undefined ? overridePanelPositions : storePanelPositions
  const holePolygons = overrideHolePolygons !== undefined ? overrideHolePolygons : storeHolePolygons
  const meshRef = useRef<THREE.InstancedMesh>(null)

  const pvTexture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 512
    const ctx = canvas.getContext('2d')!
    // Background: dark navy
    ctx.fillStyle = '#071220'
    ctx.fillRect(0, 0, 256, 512)
    // PV cells: 6 columns × 12 rows
    const cols = 6, rows = 12
    const cw = 256 / cols, ch = 512 / rows
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        // Cell background (slight blue tint)
        ctx.fillStyle = 'rgba(10, 40, 80, 0.9)'
        ctx.fillRect(c * cw + 1.5, r * ch + 1.5, cw - 3, ch - 3)
        // Subtle diagonal reflection line in each cell
        ctx.strokeStyle = 'rgba(14, 165, 233, 0.12)'
        ctx.lineWidth = 0.8
        ctx.beginPath()
        ctx.moveTo(c * cw + 4, r * ch + 4)
        ctx.lineTo(c * cw + cw - 4, r * ch + ch - 4)
        ctx.stroke()
      }
    }
    // Grid lines (busbar effect)
    ctx.strokeStyle = 'rgba(30, 100, 160, 0.6)'
    ctx.lineWidth = 1.5
    for (let r = 0; r <= rows; r++) {
      ctx.beginPath(); ctx.moveTo(0, r * ch); ctx.lineTo(256, r * ch); ctx.stroke()
    }
    for (let c = 0; c <= cols; c++) {
      ctx.beginPath(); ctx.moveTo(c * cw, 0); ctx.lineTo(c * cw, 512); ctx.stroke()
    }
    const tex = new THREE.CanvasTexture(canvas)
    tex.needsUpdate = true
    return tex
  }, [])

  const panels = useMemo<PanelPos[]>(() => {
    const { bbox, points } = localPoly
    const isMultiFace = roofType === 'gable' || roofType === 'hip'
    // Use polygon-clipped geometry so panels stay within actual footprint
    const allFaces = points.length >= 3
      ? buildRoofFromPolygon(points, roofType, pitch, azimuth, bbox.angle, Math.max(bbox.w, 1), Math.max(bbox.h, 1))
      : buildRoofGeometry({ type: roofType, pitch, azimuth, wallHeight, bboxW: Math.max(bbox.w, 1), bboxH: Math.max(bbox.h, 1), bboxAngle: bbox.angle })
    // For multi-face roofs filter to only the user-selected faces
    const faces = isMultiFace
      ? allFaces.filter((_, i) => selectedRoofFaces.has(i))
      : allFaces

    const wM = panelWidthMm / 1000
    const hM = panelHeightMm / 1000
    const pW = orientation === 'portrait' ? wM : hM
    const pH = orientation === 'portrait' ? hM : wM

    // World Y of panel center on face.
    // Prefer getLocalY (exact slope formula) over plane-equation approximation.
    function getFaceY(face: RoofFace, x: number, z: number): number {
      if (face.getLocalY) return wallHeight + face.getLocalY(x, z)
      if (Math.abs(face.normal.y) < 1e-6) return wallHeight
      const arr = face.geometry.attributes.position.array as Float32Array
      const D = face.normal.x * arr[0] + face.normal.y * (arr[1] + wallHeight) + face.normal.z * arr[2]
      return (D - face.normal.x * x - face.normal.z * z) / face.normal.y
    }

    // Precompute face bounding boxes (fast early rejection)
    const faceBBs = faces.map((face) => {
      if (!face.geometry.boundingBox) face.geometry.computeBoundingBox()
      return face.geometry.boundingBox!
    })

    // Precompute face XZ polygons for precise containment.
    // For polygon-clipped faces (buildRoofFromPolygon) use the stored polygonXZ boundary.
    // For legacy bbox faces, extract unique vertices from the buffer geometry.
    const facePolysXZ = faces.map((face): [number, number][] => {
      if (face.polygonXZ && face.polygonXZ.length >= 3) return face.polygonXZ
      // Legacy: quad stored as 2 triangles → 6 verts, unique at slots 0,1,2,5
      const arr = face.geometry.attributes.position.array as Float32Array
      if (arr.length === 9) {
        return [[arr[0], arr[2]], [arr[3], arr[5]], [arr[6], arr[8]]]
      }
      return [[arr[0], arr[2]], [arr[3], arr[5]], [arr[6], arr[8]], [arr[15], arr[17]]]
    })

    // Point-in-polygon check in XZ space (ray casting)
    function inFaceXZ(px: number, pz: number, poly: [number, number][]): boolean {
      let inside = false
      const n = poly.length
      for (let i = 0, j = n - 1; i < n; j = i++) {
        const xi = poly[i][0], zi = poly[i][1]
        const xj = poly[j][0], zj = poly[j][1]
        if ((zi > pz) !== (zj > pz) && px < ((xj - xi) * (pz - zi) / (zj - zi) + xi))
          inside = !inside
      }
      return inside
    }

    // Helper: find best roof face for a given XZ position.
    // Pass 1 — strict: center must be inside the face polygon (prevents gable/hip misassignment).
    // Pass 2 — loose: bbox fallback with small tolerance for panels at roof edges.
    function pickFace(x: number, z: number): { face: RoofFace; y: number } | null {
      let bestFace: RoofFace | null = null
      let bestY = -Infinity
      // Pass 1: strict polygon containment
      for (let fi = 0; fi < faces.length; fi++) {
        const face = faces[fi]
        if (Math.abs(face.normal.y) < 0.01) continue
        const bb = faceBBs[fi]
        const tol = 0.05
        if (x < bb.min.x - tol || x > bb.max.x + tol) continue
        if (z < bb.min.z - tol || z > bb.max.z + tol) continue
        if (!inFaceXZ(x, z, facePolysXZ[fi])) continue
        const y = getFaceY(face, x, z)
        if (y >= wallHeight - 0.1 && y > bestY) { bestY = y; bestFace = face }
      }
      if (bestFace) return { face: bestFace, y: bestY }
      // Pass 2: fallback for edge panels (bbox with 0.3 m tolerance, no polygon check)
      for (let fi = 0; fi < faces.length; fi++) {
        const face = faces[fi]
        if (Math.abs(face.normal.y) < 0.01) continue
        const bb = faceBBs[fi]
        const tol = 0.3
        if (x < bb.min.x - tol || x > bb.max.x + tol) continue
        if (z < bb.min.z - tol || z > bb.max.z + tol) continue
        const y = getFaceY(face, x, z)
        if (y >= wallHeight - 0.1 && y > bestY) { bestY = y; bestFace = face }
      }
      if (!bestFace) return null
      return { face: bestFace, y: bestY }
    }

    // ── Hole polygons: convert WGS84 rings → local XZ for Branch B exclusion ─
    const [centLon, centLat] = localPoly.centroid
    const lat0Rad = centLat * Math.PI / 180

    const holePolysXZ: [number, number][][] = (holePolygons || []).map(ring => {
      const open = ring.length > 1 &&
        ring[0][0] === ring[ring.length - 1][0] &&
        ring[0][1] === ring[ring.length - 1][1]
          ? ring.slice(0, -1) : ring
      return (open as [number, number][]).map(([hLon, hLat]): [number, number] => [
        (hLon - centLon) * Math.cos(lat0Rad) * EARTH_RADIUS * Math.PI / 180,
        (hLat - centLat) * EARTH_RADIUS * Math.PI / 180,
      ])
    })

    function isInAnyHole(cx: number, cz: number): boolean {
      for (const hPoly of holePolysXZ) {
        if (hPoly.length < 3) continue
        let inside = false
        const nh = hPoly.length
        for (let i = 0, j = nh - 1; i < nh; j = i++) {
          const xi = hPoly[i][0], zi = hPoly[i][1]
          const xj = hPoly[j][0], zj = hPoly[j][1]
          if ((zi > cz) !== (zj > cz) && cx < ((xj - xi) * (cz - zi) / (zj - zi) + xi))
            inside = !inside
        }
        if (inside) return true
      }
      return false
    }

    // ── Branch A: use exact 2D panel positions (lon/lat) ─────────────────────
    if (panelPositions && panelPositions.length > 0) {
      console.log('[3D SolarPanels] Branch A — using', panelPositions.length, '2D positions')
      const result: PanelPos[] = []

      for (const [lon2d, lat2d] of panelPositions) {
        const x = (lon2d - centLon) * Math.cos(lat0Rad) * EARTH_RADIUS * Math.PI / 180
        const z = (lat2d - centLat) * EARTH_RADIUS * Math.PI / 180

        const hit = pickFace(x, z)
        if (!hit) {
          // Fallback: use first face (flat roof / no face found)
          const face = faces[0]
          if (!face) continue
          const y = getFaceY(face, x, z)
          result.push({
            x: x + face.normal.x * PANEL_THICKNESS / 2,
            y: y  + face.normal.y * PANEL_THICKNESS / 2,
            z: z  + face.normal.z * PANEL_THICKNESS / 2,
            tilt: face.tiltDeg, az: face.azimuthDeg, normal: face.normal,
          })
          continue
        }
        result.push({
          x: x + hit.face.normal.x * PANEL_THICKNESS / 2,
          y: hit.y + hit.face.normal.y * PANEL_THICKNESS / 2,
          z: z + hit.face.normal.z * PANEL_THICKNESS / 2,
          tilt: hit.face.tiltDeg, az: hit.face.azimuthDeg, normal: hit.face.normal,
          faceRight: hit.face.faceRight,
          faceDown:  hit.face.faceDown,
        })
      }
      return result
    }

    // ── Branch B: face-local grid (no 2D positions available) ────────────────
    // Grid each face independently in face-local surface coordinates.
    // faceRight (along ridge) and faceDown (down slope) define the panel rows/cols.
    // This ensures panels are always axis-aligned with the roof slope regardless of
    // bbox rotation, and containment is checked in the face's own 2D space.

    const spacingRight = spacingHCm / 100   // gap along ridge
    const spacingDown  = spacingVCm / 100   // gap along slope
    const stepRight = pW + spacingRight
    const stepDown  = pH + spacingDown
    const maxPool = Math.max(panelCount * 3, panelCount + 80)
    const result: PanelPos[] = []

    // Point-in-polygon in 2D (reusable)
    function inPoly2D(px: number, py: number, poly: [number, number][]): boolean {
      let inside = false
      const n = poly.length
      for (let i = 0, j = n - 1; i < n; j = i++) {
        const xi = poly[i][0], yi = poly[i][1]
        const xj = poly[j][0], yj = poly[j][1]
        if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi) / (yj - yi) + xi))
          inside = !inside
      }
      return inside
    }

    for (const face of faces) {
      if (result.length >= maxPool) break
      const polyXZ = face.polygonXZ
      if (!polyXZ || polyXZ.length < 3) continue
      const fR = face.faceRight
      const fD = face.faceDown
      if (!fR || !fD) continue

      // fD is a 3D slope vector; its XZ projection has magnitude cosP, not 1.
      // Normalise the XZ component so projection and recovery are consistent.
      const fDxzLen = Math.hypot(fD.x, fD.z) || 1
      const fDxzX = fD.x / fDxzLen
      const fDxzZ = fD.z / fDxzLen

      // Project polygon to face-local 2D: (u = fR·XZ, v = fDxz·XZ)
      const polyLocal = polyXZ.map(([x, z]): [number, number] => [
        fR.x * x + fR.z * z,
        fDxzX * x + fDxzZ * z,
      ])
      const uCoords = polyLocal.map(p => p[0])
      const vCoords = polyLocal.map(p => p[1])
      const uMin = Math.min(...uCoords)
      const uMax = Math.max(...uCoords)
      const vMin = Math.min(...vCoords)
      const vMax = Math.max(...vCoords)

      const halfR = pW / 2
      const halfD = pH / 2

      for (let u = uMin + halfR; u <= uMax - halfR + 1e-6; u += stepRight) {
        if (result.length >= maxPool) break
        for (let v = vMin + halfD; v <= vMax - halfD + 1e-6; v += stepDown) {
          if (result.length >= maxPool) break

          // All 4 panel corners must be inside the face polygon (in local 2D)
          if (!inPoly2D(u - halfR, v - halfD, polyLocal)) continue
          if (!inPoly2D(u + halfR, v - halfD, polyLocal)) continue
          if (!inPoly2D(u + halfR, v + halfD, polyLocal)) continue
          if (!inPoly2D(u - halfR, v + halfD, polyLocal)) continue

          // World XZ position — use normalised XZ basis vectors to invert
          const wx = fR.x * u + fDxzX * v
          const wz = fR.z * u + fDxzZ * v

          if (isInAnyHole(wx, wz)) continue

          const wy = getFaceY(face, wx, wz)
          result.push({
            x: wx + face.normal.x * PANEL_THICKNESS / 2,
            y: wy + face.normal.y * PANEL_THICKNESS / 2,
            z: wz + face.normal.z * PANEL_THICKNESS / 2,
            tilt: face.tiltDeg, az: face.azimuthDeg,
            normal: face.normal,
            faceRight: fR,
            faceDown: fD,
          })
        }
      }
    }

    return result
  }, [localPoly, roofType, pitch, azimuth, wallHeight, panelCount, panelWidthMm, panelHeightMm, orientation, spacingHCm, spacingVCm, panelPositions, holePolygons, selectedRoofFaces])

  const COLOR_REMOVED = new THREE.Color('#0F172A')
  const COLOR_GHOST = new THREE.Color('#22C55E')

  // ── Pop-in animation when panels change ──────────────────────────────────
  const animRafRef = useRef<number | null>(null)
  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh || panels.length === 0) return
    if (animRafRef.current) cancelAnimationFrame(animRafRef.current)

    const start = performance.now()
    const STAGGER = 18     // ms between each panel start
    const DUR     = 280    // ms per panel animation

    function animFrame() {
      const m = meshRef.current
      if (!m) return
      const elapsed = performance.now() - start
      const total   = DUR + panels.length * STAGGER
      const dummy2  = new THREE.Object3D()

      for (let i = 0; i < panels.length; i++) {
        const delay = i * STAGGER
        let scale: number
        if (elapsed < delay) {
          scale = 0.001
        } else {
          const t = Math.min(1, (elapsed - delay) / DUR)
          // ease-out with slight overshoot
          scale = t < 0.75 ? (t / 0.75) * 1.07 : 1.07 - ((t - 0.75) / 0.25) * 0.07
        }
        m.getMatrixAt(i, dummy2.matrix)
        dummy2.matrix.decompose(dummy2.position, dummy2.quaternion, dummy2.scale)
        dummy2.scale.setScalar(scale)
        dummy2.updateMatrix()
        m.setMatrixAt(i, dummy2.matrix)
      }
      m.instanceMatrix.needsUpdate = true

      if (elapsed < total) {
        animRafRef.current = requestAnimationFrame(animFrame)
      }
    }

    animRafRef.current = requestAnimationFrame(animFrame)
    return () => { if (animRafRef.current) cancelAnimationFrame(animRafRef.current) }
  }, [panels])

  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh) return
    const dummy = new THREE.Object3D()
    const up = new THREE.Vector3(0, 1, 0)

    // Compute sun position for irradiance mode
    const sunPos = irradianceMode ? getSunPosition(lat, lon, simDate, simHour) : null

    for (let i = 0; i < panels.length; i++) {
      const p = panels[i]
      const isRemoved = removedPanels.has(i)
      const isActive = i < panelCount && !isRemoved
      const isGhost = i === panelCount && sceneMode === 'add-panel'

      if (isRemoved || (!isActive && !isGhost)) {
        dummy.position.set(0, -1000, 0)
        dummy.scale.setScalar(0)
        dummy.updateMatrix()
        mesh.setMatrixAt(i, dummy.matrix)
        mesh.setColorAt(i, COLOR_REMOVED)
        continue
      }

      dummy.position.set(p.x, p.y, p.z)
      dummy.scale.setScalar(isGhost ? 1.05 : 1)
      dummy.rotation.set(0, 0, 0)
      if (p.faceRight && p.faceDown) {
        // Build a right-handed (det=+1) rotation matrix.
        // makeBasis(faceRight, normal, faceDown) is left-handed for several face
        // orientations (det=-1), which makes setFromRotationMatrix produce a
        // degenerate quaternion (effectively identity) — panels appear un-tilted.
        // Fix: use faceRight × normal as the guaranteed right-handed Z column.
        const n = p.normal.clone().normalize()
        const faceZ = new THREE.Vector3().crossVectors(p.faceRight, n)
        const mat = new THREE.Matrix4().makeBasis(p.faceRight, n, faceZ)
        dummy.setRotationFromMatrix(mat)
      } else if (p.tilt > 0.5) {
        const q = new THREE.Quaternion().setFromUnitVectors(up, p.normal.clone().normalize())
        dummy.quaternion.copy(q)
      }
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)

      let color: THREE.Color
      if (isGhost) {
        color = COLOR_GHOST
      } else if (i === selectedPanel) {
        color = COLOR_SELECTED
      } else if (irradianceMode && sunPos) {
        const irr = computeIrradiance(p.x, p.y, p.z, p.normal, obstacles, sunPos.azimuth, sunPos.elevation)
        color = irradianceToColor(irr)
      } else {
        color = COLOR_NORMAL
      }
      mesh.setColorAt(i, color)
    }

    mesh.instanceMatrix.needsUpdate = true
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
  }, [panels, selectedPanel, removedPanels, irradianceMode, simHour, obstacles, sceneMode, panelCount, lat, lon, simDate])

  // Compute and report shadow factor to parent whenever obstacles or panels change
  useEffect(() => {
    if (obstacles.length === 0) {
      useStore.setState({ shadingPct: 0 })
      window.parent.postMessage({ type: 'SHADOW_FACTOR', shadingPct: 0, obstacleCount: 0 }, '*')
      return
    }

    // Use equinox noon for representative shading
    const equinoxDate = new Date(new Date().getFullYear(), 2, 21)
    const sunPos = getSunPosition(lat, lon, equinoxDate, 12)
    if (!sunPos || sunPos.elevation <= 0) {
      window.parent.postMessage({ type: 'SHADOW_FACTOR', shadingPct: 0, obstacleCount: obstacles.length }, '*')
      return
    }

    const activePanels = panels.slice(0, panelCount).filter((_, i) => !removedPanels.has(i))
    if (activePanels.length === 0) return

    let shadedCount = 0
    for (const p of activePanels) {
      const irr = computeIrradiance(p.x, p.y, p.z, p.normal, obstacles, sunPos.azimuth, sunPos.elevation)
      const elRad = (sunPos.elevation * Math.PI) / 180
      const azRad = (sunPos.azimuth * Math.PI) / 180
      const sunDir = new THREE.Vector3(
        Math.cos(elRad) * Math.sin(azRad),
        Math.sin(elRad),
        -Math.cos(elRad) * Math.cos(azRad)
      ).normalize()
      const incidence = Math.max(0, p.normal.dot(sunDir))
      const unshaded = Math.min(1, incidence * (0.5 + 0.5 * Math.sin(elRad)))
      if (unshaded > 0.01 && irr < unshaded * 0.5) shadedCount++
    }

    const shadingPct = activePanels.length > 0 ? (shadedCount / activePanels.length) * 100 : 0
    const rounded = Math.round(shadingPct * 10) / 10
    useStore.setState({ shadingPct: rounded })
    window.parent.postMessage({ type: 'SHADOW_FACTOR', shadingPct: rounded, obstacleCount: obstacles.length }, '*')
  }, [panels, obstacles, panelCount, removedPanels, lat, lon])

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()

    // Add-panel mode: clicking the ghost panel confirms it
    if (sceneMode === 'add-panel') {
      addPanel()
      return
    }

    if (sceneMode !== 'view') return
    const idx = e.instanceId
    if (idx === undefined || !panels[idx] || idx >= panelCount) return
    if (removedPanels.has(idx)) return

    const p = panels[idx]
    const isDeselect = selectedPanel === idx
    setSelectedPanel(isDeselect ? null : idx)

    if (!isDeselect) {
      const tiltFactor = 0.4 + 0.8 * Math.sin((p.tilt * Math.PI) / 180)
      const production = +(0.545 * 1700 * Math.max(0.3, tiltFactor)).toFixed(0)
      useStore.setState({
        _popupX: e.nativeEvent.clientX,
        _popupY: e.nativeEvent.clientY,
        _popupData: {
          index: idx + 1,
          tilt: p.tilt,
          azimuth: p.az,
          estimatedProduction: production,
        },
      } as any)
    } else {
      useStore.setState({ _popupData: null } as any)
    }
  }

  if (panels.length === 0) return null

  // Suppress unused import warning
  void COLOR_ADD_PREVIEW

  return (
    <instancedMesh
      key={panels.length}
      ref={meshRef}
      args={[undefined, undefined, Math.max(panels.length, 1)]}
      castShadow
      receiveShadow
      onClick={handleClick}
    >
      <boxGeometry args={[
        orientation === 'portrait' ? panelWidthMm / 1000 : panelHeightMm / 1000,
        PANEL_THICKNESS,
        orientation === 'portrait' ? panelHeightMm / 1000 : panelWidthMm / 1000,
      ]} />
      <meshStandardMaterial
        color="#ffffff"
        map={pvTexture}
        roughness={0.20}
        metalness={0.55}
        transparent
        opacity={0.95}
      />
    </instancedMesh>
  )
}

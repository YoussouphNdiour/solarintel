import { useMemo, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { LocalPolygon, RoofType, Obstacle } from '../types'
import { buildRoofGeometry } from '../utils/roof'
import { useStore } from '../store/useStore'
import { getSunPosition, sunToDirection } from '../utils/solar'
import { OBSTACLE_CFG } from './Obstacles'

const PANEL_W = 1.72
const PANEL_H = 1.04
const PANEL_THICKNESS = 0.04
const SPACING = 0.08

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
}

interface Props {
  localPoly: LocalPolygon
  roofType: RoofType
  pitch: number
  azimuth: number
  wallHeight: number
}

export default function SolarPanels({ localPoly, roofType, pitch, azimuth, wallHeight }: Props) {
  const {
    panelCount, selectedPanel, setSelectedPanel,
    removedPanels, sceneMode, addPanel,
    irradianceMode, lat, lon, simDate, simHour, obstacles,
  } = useStore()
  const meshRef = useRef<THREE.InstancedMesh>(null)

  const panels = useMemo<PanelPos[]>(() => {
    const { bbox, points } = localPoly
    const faces = buildRoofGeometry({
      type: roofType, pitch, azimuth, wallHeight,
      bboxW: Math.max(bbox.w, 1),
      bboxH: Math.max(bbox.h, 1),
      bboxAngle: bbox.angle,
    })

    const polyXZ: [number, number][] = points.map(([x, y]) => [x, y])

    function inPoly(px: number, pz: number): boolean {
      if (polyXZ.length < 3) return true
      let inside = false
      const n = polyXZ.length
      for (let i = 0, j = n - 1; i < n; j = i++) {
        const xi = polyXZ[i][0], yi = polyXZ[i][1]
        const xj = polyXZ[j][0], yj = polyXZ[j][1]
        if ((yi > pz) !== (yj > pz) && px < ((xj - xi) * (pz - yi)) / (yj - yi) + xi) {
          inside = !inside
        }
      }
      return inside
    }

    const result: PanelPos[] = []
    const stepX = PANEL_W + SPACING
    const stepZ = PANEL_H + SPACING

    // Large pool: allow many more panels than displayed (for add-panel mode)
    const maxPool = panelCount + 50

    for (const face of faces) {
      if (result.length >= maxPool) break
      const { geometry, normal, tiltDeg, azimuthDeg } = face
      if (!geometry.boundingBox) geometry.computeBoundingBox()
      const bb = geometry.boundingBox!

      for (let x = bb.min.x + PANEL_W / 2; x <= bb.max.x - PANEL_W / 2; x += stepX) {
        for (let z = bb.min.z + PANEL_H / 2; z <= bb.max.z - PANEL_H / 2; z += stepZ) {
          if (result.length >= maxPool) break
          if (!inPoly(x, z)) continue
          const y = normal.y > 1e-6
            ? wallHeight - (normal.x * x + normal.z * z) / normal.y
            : wallHeight
          result.push({ x, y: y + PANEL_THICKNESS / 2, z, tilt: tiltDeg, az: azimuthDeg, normal })
        }
        if (result.length >= maxPool) break
      }
    }

    return result
  }, [localPoly, roofType, pitch, azimuth, wallHeight, panelCount])

  const COLOR_REMOVED = new THREE.Color('#0F172A')
  const COLOR_GHOST = new THREE.Color('#22C55E')

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
      if (p.tilt > 0.5) {
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
      ref={meshRef}
      args={[undefined, undefined, Math.max(panels.length, 1)]}
      castShadow
      receiveShadow
      onClick={handleClick}
    >
      <boxGeometry args={[PANEL_W, PANEL_THICKNESS, PANEL_H]} />
      <meshStandardMaterial
        color={COLOR_NORMAL}
        roughness={0.25}
        metalness={0.65}
        transparent
        opacity={0.92}
      />
    </instancedMesh>
  )
}

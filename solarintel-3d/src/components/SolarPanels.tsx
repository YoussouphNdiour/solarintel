import { useMemo, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { LocalPolygon, RoofType } from '../types'
import { buildRoofGeometry } from '../utils/roof'
import { useStore } from '../store/useStore'

const PANEL_W = 1.72
const PANEL_H = 1.04
const PANEL_THICKNESS = 0.04
const SPACING = 0.08

const COLOR_NORMAL = new THREE.Color('#0EA5E9')
const COLOR_SELECTED = new THREE.Color('#F59E0B')

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
  const { panelCount, selectedPanel, setSelectedPanel, installType, removedPanels, sceneMode } = useStore()
  const meshRef = useRef<THREE.InstancedMesh>(null)

  const panels = useMemo<PanelPos[]>(() => {
    const { bbox, points } = localPoly
    const faces = buildRoofGeometry({
      type: roofType, pitch, azimuth, wallHeight,
      bboxW: Math.max(bbox.w, 1),
      bboxH: Math.max(bbox.h, 1),
      bboxAngle: bbox.angle,
    })

    // polygon in XZ (Three.js X = geo X, Three.js Z = geo Y)
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

    for (const face of faces) {
      if (result.length >= panelCount) break
      const { geometry, normal, tiltDeg, azimuthDeg } = face
      if (!geometry.boundingBox) geometry.computeBoundingBox()
      const bb = geometry.boundingBox!

      for (let x = bb.min.x + PANEL_W / 2; x <= bb.max.x - PANEL_W / 2; x += stepX) {
        for (let z = bb.min.z + PANEL_H / 2; z <= bb.max.z - PANEL_H / 2; z += stepZ) {
          if (result.length >= panelCount) break
          if (!inPoly(x, z)) continue
          // Y on roof face plane passing through (0, wallHeight, 0)
          const y = normal.y > 1e-6
            ? wallHeight - (normal.x * x + normal.z * z) / normal.y
            : wallHeight
          result.push({ x, y: y + PANEL_THICKNESS / 2, z, tilt: tiltDeg, az: azimuthDeg, normal })
        }
        if (result.length >= panelCount) break
      }
    }

    return result
  }, [localPoly, roofType, pitch, azimuth, wallHeight, panelCount])

  const COLOR_REMOVED = new THREE.Color('#1E293B')

  // Set instance matrices + colors when panels or removedPanels change
  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh) return
    const dummy = new THREE.Object3D()
    const up = new THREE.Vector3(0, 1, 0)

    for (let i = 0; i < panels.length; i++) {
      const p = panels[i]
      const isRemoved = removedPanels.has(i)

      // Hide removed panels by scaling to 0
      if (isRemoved) {
        dummy.position.set(0, -100, 0)
        dummy.scale.setScalar(0)
      } else {
        dummy.position.set(p.x, p.y, p.z)
        dummy.scale.setScalar(1)
        dummy.rotation.set(0, 0, 0)
        if (p.tilt > 0.5) {
          const q = new THREE.Quaternion().setFromUnitVectors(up, p.normal.clone().normalize())
          dummy.quaternion.copy(q)
        }
      }
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)
      mesh.setColorAt(i, isRemoved ? COLOR_REMOVED : i === selectedPanel ? COLOR_SELECTED : COLOR_NORMAL)
    }
    mesh.instanceMatrix.needsUpdate = true
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
  }, [panels, selectedPanel, removedPanels])

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation()
    // Ignore clicks in obstacle-placement mode
    if (sceneMode !== 'view') return
    const idx = e.instanceId
    if (idx === undefined || !panels[idx]) return

    const p = panels[idx]
    const isDeselect = selectedPanel === idx
    setSelectedPanel(isDeselect ? null : idx)

    if (!isDeselect) {
      // Estimate panel production (kWh/year)
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

import { useMemo } from 'react'
import * as THREE from 'three'
import { ThreeEvent } from '@react-three/fiber'
import { LocalPolygon, RoofType, RoofMaterial } from '../types'
import { buildRoofFromPolygon } from '../utils/roof'
import { useStore } from '../store/useStore'

const MATERIAL_COLORS: Record<RoofMaterial, string[]> = {
  'tuile-rouge':  ['#8B3A2A', '#7A2E20', '#7A2E20', '#8B3A2A'],
  'tuile-grise':  ['#2D3D52', '#263244', '#263244', '#2D3D52'],
  'zinc':         ['#5B6E7A', '#4E6070', '#4E6070', '#5B6E7A'],
  'bac-acier':    ['#374151', '#2D3748', '#2D3748', '#374151'],
  'beton':        ['#6B7280', '#5A6170', '#5A6170', '#6B7280'],
}

// Highlight color for selected face (slightly lighter/tinted)
const FACE_SELECTED_COLOR = '#3B5070'

interface Props {
  localPoly: LocalPolygon
  roofType: RoofType
  pitch: number
  azimuth: number
  wallHeight: number
}

export default function Roof({ localPoly, roofType, pitch, azimuth, wallHeight }: Props) {
  const { roofMaterial, selectedRoofFaces, toggleRoofFace } = useStore()
  const colors = MATERIAL_COLORS[roofMaterial] ?? MATERIAL_COLORS['tuile-grise']
  const isMetallic = roofMaterial === 'zinc' || roofMaterial === 'bac-acier'
  const isMultiFace = roofType === 'gable' || roofType === 'hip'

  // All roof types use polygon-clipped geometry (flat included)
  const faces = useMemo(() => {
    if (localPoly.points.length < 3) return []
    const { bbox, points } = localPoly
    return buildRoofFromPolygon(
      points,
      roofType,
      pitch,
      azimuth,
      bbox.angle,
      Math.max(bbox.w, 1),
      Math.max(bbox.h, 1),
    )
  }, [localPoly, roofType, pitch, azimuth])

  function handleFaceClick(e: ThreeEvent<MouseEvent>, idx: number) {
    e.stopPropagation()
    if (isMultiFace) toggleRoofFace(idx)
  }

  return (
    <group position={[0, wallHeight, 0]}>
      {faces.map((face, i) => {
        const isSelected = selectedRoofFaces.has(i)
        const baseColor = colors[i % colors.length] ?? colors[0]
        const color = isMultiFace && isSelected ? FACE_SELECTED_COLOR : baseColor
        return (
          <mesh
            key={i}
            geometry={face.geometry}
            castShadow
            receiveShadow
            onClick={(e) => handleFaceClick(e, i)}
          >
            <meshStandardMaterial
              color={color}
              roughness={isMetallic ? 0.3 : 0.85}
              metalness={isMetallic ? 0.6 : 0.05}
              side={THREE.DoubleSide}
              emissive={isMultiFace && isSelected ? new THREE.Color('#0EA5E9') : undefined}
              emissiveIntensity={isMultiFace && isSelected ? 0.12 : 0}
            />
          </mesh>
        )
      })}
    </group>
  )
}

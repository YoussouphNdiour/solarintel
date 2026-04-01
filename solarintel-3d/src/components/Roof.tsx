import { useMemo } from 'react'
import * as THREE from 'three'
import { LocalPolygon, RoofType, RoofMaterial } from '../types'
import { buildRoofGeometry } from '../utils/roof'
import { useStore } from '../store/useStore'

const MATERIAL_COLORS: Record<RoofMaterial, [string, string]> = {
  'tuile-rouge':  ['#8B3A2A', '#7A2E20'],
  'tuile-grise':  ['#2D3D52', '#263244'],
  'zinc':         ['#5B6E7A', '#4E6070'],
  'bac-acier':    ['#374151', '#2D3748'],
  'beton':        ['#6B7280', '#5A6170'],
}

interface Props {
  localPoly: LocalPolygon
  roofType: RoofType
  pitch: number
  azimuth: number
  wallHeight: number
}

export default function Roof({ localPoly, roofType, pitch, azimuth, wallHeight }: Props) {
  const { roofMaterial } = useStore()
  const [c0, c1] = MATERIAL_COLORS[roofMaterial] ?? MATERIAL_COLORS['tuile-grise']
  const isMetallic = roofMaterial === 'zinc' || roofMaterial === 'bac-acier'

  // Flat roof: use actual polygon shape so it doesn't extend beyond the drawn zone
  const flatGeo = useMemo(() => {
    if (roofType !== 'flat' || localPoly.points.length < 3) return null
    // Negate Y so after rotateX(-π/2) world Z = +North (same as Building.tsx fix)
    const shape = new THREE.Shape(localPoly.points.map(([x, y]) => new THREE.Vector2(x, -y)))
    const geo = new THREE.ShapeGeometry(shape)
    geo.rotateX(-Math.PI / 2)
    return geo
  }, [localPoly, roofType])

  // Tilted roofs: bbox-based geometry
  const faces = useMemo(() => {
    if (roofType === 'flat') return []
    const { bbox } = localPoly
    return buildRoofGeometry({
      type: roofType,
      pitch,
      azimuth,
      wallHeight,
      bboxW: Math.max(bbox.w, 1),
      bboxH: Math.max(bbox.h, 1),
      bboxAngle: bbox.angle,
    })
  }, [localPoly, roofType, pitch, azimuth, wallHeight])

  if (roofType === 'flat' && flatGeo) {
    return (
      <group position={[0, wallHeight, 0]}>
        <mesh geometry={flatGeo} castShadow receiveShadow>
          <meshStandardMaterial
            color={c0}
            roughness={isMetallic ? 0.3 : 0.85}
            metalness={isMetallic ? 0.6 : 0.05}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
    )
  }

  return (
    <group position={[0, wallHeight, 0]}>
      {faces.map((face, i) => (
        <mesh key={i} geometry={face.geometry} castShadow receiveShadow>
          <meshStandardMaterial
            color={i === 0 ? c0 : c1}
            roughness={isMetallic ? 0.3 : 0.85}
            metalness={isMetallic ? 0.6 : 0.05}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  )
}

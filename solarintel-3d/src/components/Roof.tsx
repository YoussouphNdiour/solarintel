import { useMemo } from 'react'
import * as THREE from 'three'
import { LocalPolygon, RoofType } from '../types'
import { buildRoofGeometry } from '../utils/roof'

interface Props {
  localPoly: LocalPolygon
  roofType: RoofType
  pitch: number
  azimuth: number
  wallHeight: number
}

export default function Roof({ localPoly, roofType, pitch, azimuth, wallHeight }: Props) {
  const faces = useMemo(() => {
    const { bbox } = localPoly
    // Azimuth in roof.ts is the down-slope direction; the bbox angle is the principal axis
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

  return (
    <group position={[0, wallHeight, 0]}>
      {faces.map((face, i) => (
        <mesh
          key={i}
          geometry={face.geometry}
          castShadow
          receiveShadow
        >
          <meshStandardMaterial
            color={i === 0 ? '#2D3D52' : '#263244'}
            roughness={0.85}
            metalness={0.05}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  )
}

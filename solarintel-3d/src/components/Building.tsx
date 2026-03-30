import { useMemo } from 'react'
import * as THREE from 'three'
import { LocalPolygon } from '../types'

interface Props {
  localPoly: LocalPolygon
  wallHeight: number
}

export default function Building({ localPoly, wallHeight }: Props) {
  const geometry = useMemo(() => {
    const pts = localPoly.points
    if (pts.length < 3) return null

    // Create Shape in XY plane — will be rotated to XZ
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)))

    const extGeo = new THREE.ExtrudeGeometry(shape, {
      depth: wallHeight,
      bevelEnabled: false,
    })

    // Rotate so the extrusion goes upward (Y axis)
    // ExtrudeGeometry extrudes along Z, so we rotate -90° around X
    extGeo.rotateX(-Math.PI / 2)

    return extGeo
  }, [localPoly, wallHeight])

  if (!geometry) return null

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#1E293B"
        roughness={0.8}
        metalness={0.1}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

import { useMemo } from 'react'
import * as THREE from 'three'
import { LocalPolygon } from '../types'

interface Props {
  localPoly: LocalPolygon
  wallHeight: number
}

export default function Building({ localPoly, wallHeight }: Props) {
  // Outer wall faces only — no floor/ceiling caps to avoid z-fighting with roof
  const wallGeo = useMemo(() => {
    const pts = localPoly.points
    if (pts.length < 3) return null

    const positions: number[] = []
    const normals: number[] = []
    const n = pts.length

    for (let i = 0; i < n; i++) {
      const [x0, y0] = pts[i]
      const [x1, y1] = pts[(i + 1) % n]

      // Local polygon [x,y] maps to world (x, height, y) — same convention as Roof/SolarPanels
      // Outward normal in XZ plane (assuming CCW winding viewed from above +Y)
      const dx = x1 - x0
      const dz = y1 - y0
      const len = Math.sqrt(dx * dx + dz * dz) || 1
      const nx = dz / len
      const nz = -dx / len

      // Two triangles per wall segment
      // v0=(x0,0,y0), v1=(x1,0,y1), v2=(x1,wh,y1), v3=(x0,wh,y0)
      positions.push(x0, 0, y0,  x1, 0, y1,  x1, wallHeight, y1)
      normals.push(nx, 0, nz,  nx, 0, nz,  nx, 0, nz)
      positions.push(x0, 0, y0,  x1, wallHeight, y1,  x0, wallHeight, y0)
      normals.push(nx, 0, nz,  nx, 0, nz,  nx, 0, nz)
    }

    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3))
    return geo
  }, [localPoly, wallHeight])

  // Floor slab — polygon filled at ground level (y=0)
  const floorGeo = useMemo(() => {
    const pts = localPoly.points
    if (pts.length < 3) return null
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, -y)))
    const geo = new THREE.ShapeGeometry(shape)
    geo.rotateX(-Math.PI / 2)
    return geo
  }, [localPoly])

  if (!wallGeo || !floorGeo) return null

  return (
    <group>
      {/* Outer walls */}
      <mesh geometry={wallGeo} castShadow receiveShadow>
        <meshStandardMaterial
          color="#1E293B"
          roughness={0.8}
          metalness={0.1}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Ground slab */}
      <mesh geometry={floorGeo} receiveShadow>
        <meshStandardMaterial
          color="#0F172A"
          roughness={0.9}
          metalness={0.05}
        />
      </mesh>
    </group>
  )
}

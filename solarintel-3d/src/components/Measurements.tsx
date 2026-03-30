import { Html } from '@react-three/drei'
import { LocalPolygon } from '../types'

interface Props {
  localPoly: LocalPolygon
  wallHeight: number
}

function distLabel(meters: number): string {
  return meters >= 1 ? `${meters.toFixed(1)} m` : `${(meters * 100).toFixed(0)} cm`
}

export default function Measurements({ localPoly, wallHeight }: Props) {
  const { bbox } = localPoly

  // Compute the 4 corners of the bounding box in world XZ space
  const cos = Math.cos(bbox.angle)
  const sin = Math.sin(bbox.angle)
  const hw = bbox.w / 2
  const hh = bbox.h / 2

  function rotated(lx: number, lz: number): [number, number] {
    return [
      bbox.cx + lx * cos - lz * sin,
      bbox.cy + lx * sin + lz * cos,
    ]
  }

  const [x0, z0] = rotated(-hw, -hh)
  const [x1, z1] = rotated( hw, -hh)
  const [x2, z2] = rotated( hw,  hh)
  const [x3, z3] = rotated(-hw,  hh)

  const Y = wallHeight + 0.1  // just above roof

  // Mid-points of each edge for label placement
  const midBottom : [number, number, number] = [(x0 + x1) / 2, Y, (z0 + z1) / 2]
  const midRight  : [number, number, number] = [(x1 + x2) / 2, Y, (z1 + z2) / 2]
  const midTop    : [number, number, number] = [(x2 + x3) / 2, Y, (z2 + z3) / 2]
  const midLeft   : [number, number, number] = [(x3 + x0) / 2, Y, (z3 + z0) / 2]

  const tagClass =
    'bg-[#0F172A]/90 border border-[#334155] text-white text-[10px] font-mono px-1.5 py-0.5 rounded pointer-events-none whitespace-nowrap'

  return (
    <group>
      {/* Width (bottom edge) */}
      <Html position={midBottom} center occlude={false}>
        <div className={tagClass}>{distLabel(bbox.w)}</div>
      </Html>

      {/* Depth (right edge) */}
      <Html position={midRight} center occlude={false}>
        <div className={tagClass}>{distLabel(bbox.h)}</div>
      </Html>

      {/* Width (top edge) */}
      <Html position={midTop} center occlude={false}>
        <div className={tagClass}>{distLabel(bbox.w)}</div>
      </Html>

      {/* Depth (left edge) */}
      <Html position={midLeft} center occlude={false}>
        <div className={tagClass}>{distLabel(bbox.h)}</div>
      </Html>

      {/* Area label — center of roof */}
      <Html position={[bbox.cx, Y + 0.3, bbox.cy]} center occlude={false}>
        <div className="bg-[#0EA5E9]/20 border border-[#0EA5E9]/40 text-[#38BDF8] text-[10px] font-semibold px-2 py-0.5 rounded pointer-events-none">
          {(bbox.w * bbox.h).toFixed(1)} m²
        </div>
      </Html>

      {/* Edge lines (dashed visual guides) */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[
              new Float32Array([
                x0, Y, z0,  x1, Y, z1,
                x1, Y, z1,  x2, Y, z2,
                x2, Y, z2,  x3, Y, z3,
                x3, Y, z3,  x0, Y, z0,
              ]),
              3,
            ]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#334155" transparent opacity={0.6} />
      </lineSegments>
    </group>
  )
}

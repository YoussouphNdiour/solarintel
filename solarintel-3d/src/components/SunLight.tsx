import { useRef, useMemo } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { useStore } from '../store/useStore'
import { getSunPosition, getSunPathArc, sunToDirection } from '../utils/solar'

export default function SunLight() {
  const lightRef = useRef<THREE.DirectionalLight>(null)
  const sphereRef = useRef<THREE.Mesh>(null)

  const { lat, lon, simDate, simHour } = useStore()

  const sunPos = useMemo(
    () => getSunPosition(lat, lon, simDate, simHour),
    [lat, lon, simDate, simHour]
  )

  const isDay = sunPos.elevation > 0

  const [lx, ly, lz] = useMemo(
    () => (isDay ? sunToDirection(sunPos.azimuth, sunPos.elevation, 60) : [20, 40, -20]),
    [sunPos, isDay]
  )

  // Sun path arc points
  const arcPoints = useMemo(() => {
    const arc = getSunPathArc(lat, lon, simDate)
    return arc.map(({ azimuth, elevation }) => {
      const [x, y, z] = sunToDirection(azimuth, elevation, 55)
      return new THREE.Vector3(x, y, z)
    })
  }, [lat, lon, simDate])

  const arcLine = useMemo(() => {
    if (arcPoints.length < 2) return null
    const geo = new THREE.BufferGeometry().setFromPoints(arcPoints)
    return geo
  }, [arcPoints])

  // Sun sphere position
  const [sx, sy, sz] = useMemo(
    () => sunToDirection(sunPos.azimuth, Math.max(sunPos.elevation, 0), 55),
    [sunPos]
  )

  useFrame(() => {
    if (lightRef.current) {
      lightRef.current.position.set(lx, ly, lz)
      lightRef.current.intensity = isDay
        ? Math.max(0, Math.sin((sunPos.elevation * Math.PI) / 180)) * 2.5 + 0.3
        : 0
    }
    if (sphereRef.current) {
      sphereRef.current.position.set(sx, sy, sz)
      const mat = sphereRef.current.material as THREE.MeshBasicMaterial
      mat.color.set(isDay ? (sunPos.elevation < 10 ? '#FFA500' : '#FFF5CC') : '#334155')
      mat.opacity = isDay ? 1 : 0.3
    }
  })

  return (
    <>
      {/* Main sun directional light */}
      <directionalLight
        ref={lightRef}
        position={[lx, ly, lz]}
        intensity={isDay ? 2.0 : 0}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-near={0.5}
        shadow-camera-far={200}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
        shadow-bias={-0.0005}
        color={sunPos.elevation < 10 ? '#FFC896' : '#FFF5EE'}
      />

      {/* Ambient fill */}
      <ambientLight
        intensity={isDay ? 0.25 : 0.08}
        color={isDay ? '#9EC8FF' : '#1A2540'}
      />

      {/* Sky hemisphere */}
      <hemisphereLight
        args={[
          isDay ? '#87CEEB' : '#0F172A',
          '#1E293B',
          isDay ? 0.4 : 0.1,
        ]}
      />

      {/* Sun sphere */}
      <mesh ref={sphereRef} position={[sx, sy, sz]}>
        <sphereGeometry args={[1.5, 16, 16]} />
        <meshBasicMaterial color="#FFF5CC" transparent opacity={1} />
      </mesh>

      {/* Sun path arc */}
      {arcLine && (
        <line>
          <primitive object={arcLine} />
          <lineBasicMaterial color="#F59E0B" opacity={0.35} transparent linewidth={1} />
        </line>
      )}
    </>
  )
}

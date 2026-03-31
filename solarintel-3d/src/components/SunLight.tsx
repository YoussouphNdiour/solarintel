import { useRef, useMemo, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import { Sky, Stars } from '@react-three/drei'
import { useStore } from '../store/useStore'
import { getSunPosition, getSunPathArc, sunToDirection } from '../utils/solar'

const WEATHER_SKY: Record<string, { turbidity: number; rayleigh: number; mieCoeff: number; mieG: number }> = {
  clear:   { turbidity: 2,  rayleigh: 1,   mieCoeff: 0.002, mieG: 0.8 },
  cloudy:  { turbidity: 8,  rayleigh: 3,   mieCoeff: 0.01,  mieG: 0.7 },
  overcast:{ turbidity: 20, rayleigh: 0.5, mieCoeff: 0.04,  mieG: 0.9 },
}

export const WEATHER_INTENSITY: Record<string, number> = {
  clear: 1.0,
  cloudy: 0.55,
  overcast: 0.20,
}

export default function SunLight() {
  const lightRef = useRef<THREE.DirectionalLight>(null)
  const sphereRef = useRef<THREE.Mesh>(null)
  const { setGlCanvas } = useStore()

  const { gl } = useThree()
  useEffect(() => {
    setGlCanvas(gl.domElement)
  }, [gl, setGlCanvas])

  const { lat, lon, simDate, simHour, weatherMode } = useStore()

  const sunPos = useMemo(
    () => getSunPosition(lat, lon, simDate, simHour),
    [lat, lon, simDate, simHour]
  )

  const isDay = sunPos.elevation > -4
  const isAboveHorizon = sunPos.elevation > 0
  const weatherFactor = WEATHER_INTENSITY[weatherMode] ?? 1.0
  const skyPreset = WEATHER_SKY[weatherMode] ?? WEATHER_SKY.clear

  const [lx, ly, lz] = useMemo(
    () => isAboveHorizon ? sunToDirection(sunPos.azimuth, sunPos.elevation, 60) : [20, 40, -20],
    [sunPos, isAboveHorizon]
  )

  const skyPos = useMemo(() => {
    if (!isAboveHorizon) return new THREE.Vector3(0, -1, 0)
    const [x, y, z] = sunToDirection(sunPos.azimuth, Math.max(sunPos.elevation, 0.5), 1)
    return new THREE.Vector3(x, y, z)
  }, [sunPos, isAboveHorizon])

  const arcLine = useMemo(() => {
    const arc = getSunPathArc(lat, lon, simDate)
    if (arc.length < 2) return null
    const pts = arc.map(({ azimuth, elevation }) => {
      const [x, y, z] = sunToDirection(azimuth, elevation, 55)
      return new THREE.Vector3(x, y, z)
    })
    return new THREE.BufferGeometry().setFromPoints(pts)
  }, [lat, lon, simDate])

  const [sx, sy, sz] = useMemo(
    () => sunToDirection(sunPos.azimuth, Math.max(sunPos.elevation, 0), 55),
    [sunPos]
  )

  const skyBg = useMemo(() => {
    if (sunPos.elevation > 10) return '#0F172A'
    if (sunPos.elevation > -5) return '#1a0a2e'
    return '#040810'
  }, [sunPos.elevation])

  useFrame(() => {
    if (!lightRef.current) return
    lightRef.current.position.set(lx, ly, lz)
    const baseIntensity = isAboveHorizon
      ? (Math.sin((sunPos.elevation * Math.PI) / 180) * 2.5 + 0.5) * weatherFactor
      : isDay ? 0.15 * weatherFactor : 0
    lightRef.current.intensity = Math.max(0, baseIntensity)
    lightRef.current.color.set(sunPos.elevation < 10 ? '#FFC896' : '#FFF8F0')

    if (sphereRef.current) {
      sphereRef.current.position.set(sx, sy, sz)
      const mat = sphereRef.current.material as THREE.MeshBasicMaterial
      mat.color.set(
        sunPos.elevation < 3 ? '#FF7043' :
        sunPos.elevation < 15 ? '#FFAB40' : '#FFF9C4'
      )
      mat.opacity = isAboveHorizon ? Math.min(1, sunPos.elevation / 5 + 0.3) : 0
    }
  })

  return (
    <>
      {isAboveHorizon && weatherMode !== 'overcast' && (
        <Sky
          distance={450000}
          sunPosition={skyPos}
          turbidity={skyPreset.turbidity}
          rayleigh={skyPreset.rayleigh}
          mieCoefficient={skyPreset.mieCoeff}
          mieDirectionalG={skyPreset.mieG}
        />
      )}
      {(!isAboveHorizon || weatherMode === 'overcast') && (
        <color attach="background" args={[weatherMode === 'overcast' ? '#7B8FA1' : skyBg]} />
      )}
      {!isAboveHorizon && (
        <Stars radius={120} depth={60} count={4000} factor={4} saturation={0} fade speed={0.5} />
      )}
      <directionalLight
        ref={lightRef}
        position={[lx, ly, lz]}
        intensity={isAboveHorizon ? 2.0 * weatherFactor : 0}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-near={0.5}
        shadow-camera-far={200}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
        shadow-bias={-0.0005}
      />
      <ambientLight
        intensity={(isDay ? 0.3 : 0.06) * weatherFactor}
        color={isDay ? '#B0C8E8' : '#1A2540'}
      />
      <hemisphereLight
        args={[
          isDay ? (weatherMode === 'overcast' ? '#9EB5C8' : '#87CEEB') : '#0F172A',
          '#1E293B',
          (isDay ? 0.5 : 0.08) * weatherFactor,
        ]}
      />
      {weatherMode !== 'clear' && (
        <fog attach="fog" args={[weatherMode === 'overcast' ? '#9BB0C0' : '#6B8A9B', 40, 120]} />
      )}
      <mesh ref={sphereRef} position={[sx, sy, sz]}>
        <sphereGeometry args={[1.5, 16, 16]} />
        <meshBasicMaterial color="#FFF9C4" transparent opacity={isAboveHorizon ? 1 : 0} />
      </mesh>
      {arcLine && (
        <line>
          <primitive object={arcLine} />
          <lineBasicMaterial color="#F59E0B" opacity={0.3} transparent linewidth={1} />
        </line>
      )}
    </>
  )
}

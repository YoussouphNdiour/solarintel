import { useRef, useEffect, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'
import { useStore } from '../store/useStore'
import { polygonToLocal, defaultPolygon } from '../utils/geo'
import Building from './Building'
import Roof from './Roof'
import SolarPanels from './SolarPanels'
import SunLight from './SunLight'
import PanelPopup from './PanelPopup'
import Obstacles from './Obstacles'
import ObstaclePopup from './ObstaclePopup'
import Measurements from './Measurements'

function SceneContent() {
  const { polygon, roofType, pitch, azimuth, wallHeight, tickSimulation, isPlaying } = useStore()

  useEffect(() => {
    if (!isPlaying) return
    const id = setInterval(tickSimulation, 50)
    return () => clearInterval(id)
  }, [isPlaying, tickSimulation])

  const localPoly = polygon ? polygonToLocal(polygon) : defaultPolygon()

  const grid = (
    <Grid
      args={[60, 60]}
      position={[0, -0.01, 0]}
      cellColor="#1E293B"
      sectionColor="#334155"
      sectionSize={5}
      cellSize={1}
      fadeDistance={50}
      fadeStrength={2}
      infiniteGrid
    />
  )

  if (roofType === null) {
    return (
      <>
        <SunLight />
        <ambientLight intensity={0.3} />
        <Building localPoly={localPoly} wallHeight={wallHeight} />
        {grid}
      </>
    )
  }

  return (
    <>
      <SunLight />
      <ambientLight intensity={0.2} />
      <Building localPoly={localPoly} wallHeight={wallHeight} />
      <Roof
        localPoly={localPoly}
        roofType={roofType}
        pitch={pitch}
        azimuth={azimuth}
        wallHeight={wallHeight}
      />
      <SolarPanels
        localPoly={localPoly}
        roofType={roofType}
        pitch={pitch}
        azimuth={azimuth}
        wallHeight={wallHeight}
      />
      <Obstacles localPoly={localPoly} wallHeight={wallHeight} />
      <Measurements localPoly={localPoly} wallHeight={wallHeight} />
      {grid}
    </>
  )
}

// ── Escape key cancels placement mode ──────────────────────────────────────
function EscapeHandler() {
  const { sceneMode, setSceneMode } = useStore()
  useEffect(() => {
    if (sceneMode === 'view') return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setSceneMode('view')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [sceneMode, setSceneMode])
  return null
}

// ── Placement mode cursor overlay ──────────────────────────────────────────
function PlacementCursor() {
  const { sceneMode, obstacleTypeToPlace } = useStore()
  if (sceneMode !== 'place-obstacle' || !obstacleTypeToPlace) return null
  return (
    <div className="absolute inset-0 pointer-events-none z-10" style={{ cursor: 'crosshair' }}>
      <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-[#F59E0B]/90 text-black text-xs font-semibold px-3 py-1.5 rounded-full shadow-lg">
        Cliquez sur le toit pour placer • Échap pour annuler
      </div>
    </div>
  )
}

// ── Reset camera button ────────────────────────────────────────────────────
function ResetCameraButton({ controlsRef }: { controlsRef: React.RefObject<any> }) {
  return (
    <button
      onClick={() => controlsRef.current?.reset()}
      className="absolute bottom-4 left-4 z-20 flex items-center gap-2 bg-[#1E293B]/90 border border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#0EA5E9] px-3 py-2 rounded-lg text-xs transition-all backdrop-blur-sm"
    >
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Réinitialiser vue
    </button>
  )
}

export default function RoofScene() {
  const controlsRef = useRef<any>(null)
  const { sceneMode } = useStore()

  return (
    <div className="absolute inset-0">
      <EscapeHandler />

      <Canvas
        shadows
        camera={{ position: [15, 12, 15], fov: 45, near: 0.1, far: 1000 }}
        gl={{ antialias: true, shadowMapType: 2 /* PCFSoftShadowMap */ }}
        style={{ background: 'transparent' }}
        // Disable orbit while placing obstacles so click doesn't also orbit
        onPointerDown={(e) => {
          if (sceneMode === 'place-obstacle') e.stopPropagation()
        }}
      >
        <color attach="background" args={['#0F172A']} />

        <Suspense fallback={null}>
          <SceneContent />
        </Suspense>

        <OrbitControls
          ref={controlsRef}
          enabled={sceneMode === 'view'}
          enablePan
          enableZoom
          enableRotate
          minDistance={3}
          maxDistance={80}
          maxPolarAngle={Math.PI / 2.1}
        />
      </Canvas>

      {/* HTML overlays */}
      <PlacementCursor />
      <PanelPopup />
      <ObstaclePopup />
      <ResetCameraButton controlsRef={controlsRef} />
    </div>
  )
}

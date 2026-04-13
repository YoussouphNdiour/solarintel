import { useMemo } from 'react'
import { Html } from '@react-three/drei'
import { polygonToLocal, defaultPolygon } from '../utils/geo'
import Building from './Building'
import Roof from './Roof'
import SolarPanels from './SolarPanels'
import type { ZoneConfig } from '../types'

interface Props {
  zone: ZoneConfig
  zoneIndex: number
  offsetX: number
  offsetZ: number
  isSelected: boolean
  onClick: () => void
}

export default function BuildingGroup({ zone, zoneIndex, offsetX, offsetZ, isSelected, onClick }: Props) {
  // Use only zone-local values with sensible defaults — never fall back to global
  // (global state mutations from other zones must not bleed here)
  const roofType   = zone.roofType   ?? null
  const pitch      = zone.pitch      ?? 15
  const azimuth    = zone.azimuth    ?? 180
  const wallHeight = zone.wallHeight ?? 3

  const localPoly = useMemo(
    () => zone.polygon ? polygonToLocal(zone.polygon) : defaultPolygon(),
    [zone.polygon]
  )

  return (
    <group position={[offsetX, 0, offsetZ]} onClick={onClick}>
      {/* Indicateur de selection : anneau legerement sureleve */}
      {isSelected && (
        <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[
            Math.max(localPoly.bbox.w, localPoly.bbox.h) * 0.55,
            Math.max(localPoly.bbox.w, localPoly.bbox.h) * 0.60,
            32
          ]} />
          <meshBasicMaterial color="#0EA5E9" transparent opacity={0.6} />
        </mesh>
      )}

      {/* Floating zone label */}
      <Html
        position={[0, wallHeight + 2.5, 0]}
        center
        occlude={false}
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        <div style={{
          background: 'rgba(30,41,59,0.88)',
          border: `1px solid ${isSelected ? '#0EA5E9' : '#334155'}`,
          borderRadius: '8px',
          padding: '3px 10px',
          fontSize: '11px',
          fontWeight: 700,
          color: isSelected ? '#38BDF8' : '#94A3B8',
          whiteSpace: 'nowrap',
          backdropFilter: 'blur(4px)',
          boxShadow: isSelected ? '0 0 8px rgba(14,165,233,0.3)' : 'none',
          transition: 'all 0.2s',
        }}>
          Zone {zoneIndex + 1}
          {zone.panelCount > 0 && (
            <span style={{ color: '#F59E0B', marginLeft: '6px', fontWeight: 400, fontSize: '10px' }}>
              {zone.panelCount} pann.
            </span>
          )}
        </div>
      </Html>

      <Building localPoly={localPoly} wallHeight={wallHeight} />

      {roofType && (
        <>
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
            overridePanelCount={zone.panelCount}
            overridePanelPositions={zone.panelPositions}
            overrideHolePolygons={zone.holePolygons}
          />
        </>
      )}
    </group>
  )
}

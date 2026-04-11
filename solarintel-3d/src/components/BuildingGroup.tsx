import { useMemo } from 'react'
import { polygonToLocal, defaultPolygon } from '../utils/geo'
import Building from './Building'
import Roof from './Roof'
import SolarPanels from './SolarPanels'
import type { ZoneConfig } from '../types'

interface Props {
  zone: ZoneConfig
  offsetX: number
  offsetZ: number
  isSelected: boolean
  onClick: () => void
}

export default function BuildingGroup({ zone, offsetX, offsetZ, isSelected, onClick }: Props) {
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

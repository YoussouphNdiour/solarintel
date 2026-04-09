import { useMemo } from 'react'
import { useStore } from '../store/useStore'
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
  const { roofType: globalRoofType, pitch: globalPitch, azimuth: globalAzimuth,
          wallHeight: globalWallHeight } = useStore()

  // Utilise la config de la zone si definie, sinon fallback global
  const roofType  = zone.roofType  ?? globalRoofType
  const pitch     = zone.pitch     ?? globalPitch
  const azimuth   = zone.azimuth   ?? globalAzimuth
  const wallHeight = zone.wallHeight ?? globalWallHeight

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

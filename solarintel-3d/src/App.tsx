import { useEffect } from 'react'
import { useStore } from './store/useStore'
import { ParentMessage } from './types'
import RoofTypeModal from './components/RoofTypeModal'
import RoofScene from './components/RoofScene'
import ControlsPanel from './components/ControlsPanel'
import StatsPanel from './components/StatsPanel'

export default function App() {
  const { roofType, setFromParent } = useStore()

  // Listen for messages from parent SolarIntel iframe
  useEffect(() => {
    function handleMessage(e: MessageEvent<ParentMessage>) {
      if (!e.data || typeof e.data !== 'object') return
      if (e.data.type === 'INIT') {
        setFromParent({
          polygon: e.data.polygon,
          panelCount: e.data.panelCount,
          panelPositions: e.data.panelPositions,
          holePolygons: e.data.holePolygons,
          lat: e.data.lat,
          lon: e.data.lon,
          annualConsumption: e.data.annualConsumption,
          installType: e.data.installType,
          panelWidthMm: e.data.panelWidthMm,
          panelHeightMm: e.data.panelHeightMm,
          orientation: e.data.orientation,
          spacingHCm: e.data.spacingHCm,
          spacingVCm: e.data.spacingVCm,
        })
      }
      if (e.data.type === 'UPDATE_PANELS') {
        if (e.data.panelCount !== undefined) {
          useStore.getState().setPanelCount(e.data.panelCount)
        }
      }
      if (e.data.type === 'SET_AZIMUTH' && typeof e.data.azimuth === 'number') {
        useStore.getState().setAzimuth(e.data.azimuth)
      }
      if (e.data.type === 'REQUEST_SCREENSHOTS') {
        useStore.getState().requestScreenshots()
      }
    }

    window.addEventListener('message', handleMessage)

    // Signal parent that we're ready
    window.parent.postMessage({ type: 'READY' }, '*')

    return () => window.removeEventListener('message', handleMessage)
  }, [setFromParent])

  return (
    <div className="w-full h-full relative overflow-hidden bg-background">
      {/* 3D Scene always mounted */}
      <RoofScene />

      {/* Controls panel (right overlay) */}
      <ControlsPanel />

      {/* Stats panel (bottom overlay) */}
      <StatsPanel />

      {/* Roof type selection modal (shown until user picks a type) */}
      {roofType === null && <RoofTypeModal />}
    </div>
  )
}

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
          lat: e.data.lat,
          lon: e.data.lon,
          annualConsumption: e.data.annualConsumption,
          installType: e.data.installType,
        })
      }
      if (e.data.type === 'UPDATE_PANELS') {
        if (e.data.panelCount !== undefined) {
          useStore.getState().setPanelCount(e.data.panelCount)
        }
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

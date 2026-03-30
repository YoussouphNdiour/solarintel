import { useStore } from '../store/useStore'

interface PopupData {
  index: number
  tilt: number
  azimuth: number
  estimatedProduction: number
}

function azimuthLabel(deg: number): string {
  const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSO','SO','OSO','O','ONO','NO','NNO']
  const idx = Math.round(deg / 22.5) % 16
  return dirs[idx]
}

export default function PanelPopup() {
  const state = useStore() as any
  const popupData: PopupData | null = state._popupData ?? null
  const px: number = state._popupX ?? 0
  const py: number = state._popupY ?? 0
  const { setSelectedPanel, removeSelectedPanel } = useStore()

  if (!popupData) return null

  function close() {
    setSelectedPanel(null)
    useStore.setState({ _popupData: null } as any)
  }

  return (
    <div
      className="absolute z-30 pointer-events-auto"
      style={{
        left: Math.min(px + 12, window.innerWidth - 240),
        top: Math.max(py - 100, 8),
      }}
    >
      <div className="bg-[#1E293B] border border-[#334155] rounded-xl shadow-2xl p-4 w-56">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#0EA5E9]" />
            <span className="text-white font-semibold text-sm">Panneau #{popupData.index}</span>
          </div>
          <button
            onClick={close}
            className="text-[#475569] hover:text-white transition-colors text-lg leading-none"
          >
            ×
          </button>
        </div>

        {/* Metrics */}
        <div className="space-y-2 mb-3">
          <div className="flex items-center justify-between">
            <span className="text-[#94A3B8] text-xs">Inclinaison</span>
            <span className="text-white text-xs font-mono">{popupData.tilt.toFixed(0)}°</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[#94A3B8] text-xs">Azimut</span>
            <span className="text-white text-xs font-mono">
              {popupData.azimuth.toFixed(0)}° ({azimuthLabel(popupData.azimuth)})
            </span>
          </div>
          <div className="h-px bg-[#334155]" />
          <div className="flex items-center justify-between">
            <span className="text-[#94A3B8] text-xs">Production est.</span>
            <span className="text-[#F59E0B] text-xs font-semibold font-mono">
              ~{popupData.estimatedProduction.toLocaleString('fr-FR')} kWh/an
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[#94A3B8] text-xs">Puissance</span>
            <span className="text-[#0EA5E9] text-xs font-mono">545 Wc</span>
          </div>
        </div>

        {/* Delete button */}
        <button
          onClick={() => { removeSelectedPanel(); close() }}
          className="w-full flex items-center justify-center gap-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 py-1.5 rounded-lg text-xs font-medium transition-all"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Retirer ce panneau
        </button>
      </div>
    </div>
  )
}

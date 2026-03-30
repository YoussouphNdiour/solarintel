import { useStore } from '../store/useStore'
import { OBSTACLE_CFG } from './Obstacles'
import { ObstacleType } from '../types'

export default function ObstaclePopup() {
  const state = useStore() as any
  const id: number | null = state._obstaclePopupId ?? null
  const px: number = state._obstaclePopupX ?? 0
  const py: number = state._obstaclePopupY ?? 0

  const { obstacles, removeObstacle } = useStore()

  if (id === null) return null

  const obs = obstacles.find((o) => o.id === id)
  if (!obs) return null

  const cfg = OBSTACLE_CFG[obs.type as ObstacleType]

  function handleDelete() {
    removeObstacle(id!)
    useStore.setState({ _obstaclePopupId: null } as any)
  }

  return (
    <div
      className="absolute z-30 pointer-events-auto"
      style={{
        left: Math.min(px + 12, window.innerWidth - 220),
        top: Math.max(py - 60, 8),
      }}
    >
      <div className="bg-[#1E293B] border border-[#334155] rounded-xl shadow-2xl p-4 w-52">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#F59E0B]" />
            <span className="text-white font-semibold text-sm">{cfg.label}</span>
          </div>
          <button
            onClick={() => {
              useStore.setState({ _obstaclePopupId: null } as any)
              useStore.getState().setSelectedObstacle(null)
            }}
            className="text-[#475569] hover:text-white transition-colors text-lg leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-1.5 mb-3">
          <div className="flex justify-between">
            <span className="text-[#94A3B8] text-xs">Largeur</span>
            <span className="text-white text-xs font-mono">{cfg.w} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#94A3B8] text-xs">Hauteur</span>
            <span className="text-white text-xs font-mono">{cfg.h} m</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#94A3B8] text-xs">Impact ombrage</span>
            <span className="text-[#F59E0B] text-xs font-mono">visible sur toit</span>
          </div>
        </div>

        <button
          onClick={handleDelete}
          className="w-full flex items-center justify-center gap-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 py-1.5 rounded-lg text-xs font-medium transition-all"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Supprimer l'obstacle
        </button>
      </div>
    </div>
  )
}

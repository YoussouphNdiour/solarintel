import { useEffect, useRef, useState } from 'react'
import { useStore } from '../store/useStore'
import { DrawTool } from '../types'

let _drawnBuildingIdCounter = 0

const BUILDING_COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16',
]

interface ToolDef {
  tool: DrawTool
  label: string
  shortcut: string
  icon: React.ReactNode
}

function SelectIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-5.196 5.196A1 1 0 018 19.5V4.5a1 1 0 011.707-.707L15 9" />
    </svg>
  )
}

function MoveIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L4 7m3-3l3 3M17 8v12m0 0l3-3m-3 3l-3-3M4 12h16" />
    </svg>
  )
}

function RectangleIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <rect x="3" y="5" width="18" height="14" rx="1" />
    </svg>
  )
}

function LineIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" d="M3 21L21 3" />
      <circle cx="3" cy="21" r="1.5" fill="currentColor" />
      <circle cx="21" cy="3" r="1.5" fill="currentColor" />
    </svg>
  )
}

function PushPullIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <rect x="4" y="12" width="16" height="8" rx="1" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 12V4m0 0l-3 3m3-3l3 3" />
    </svg>
  )
}

function EraseIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  )
}

function TapeIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 6h18M3 12h6m-6 6h18" />
      <rect x="14" y="9" width="7" height="6" rx="1" />
    </svg>
  )
}

function OrbitIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="3" />
      <ellipse cx="12" cy="12" rx="9" ry="4" />
      <path strokeLinecap="round" d="M12 3v18" />
    </svg>
  )
}

const TOOLS: ToolDef[] = [
  { tool: 'select',    label: 'Sélectionner', shortcut: 'S', icon: <SelectIcon /> },
  { tool: 'move',      label: 'Déplacer',     shortcut: 'M', icon: <MoveIcon /> },
  { tool: 'rectangle', label: 'Rectangle',    shortcut: 'R', icon: <RectangleIcon /> },
  { tool: 'line',      label: 'Ligne',        shortcut: 'L', icon: <LineIcon /> },
  { tool: 'push-pull', label: 'Pousser/tirer', shortcut: 'P', icon: <PushPullIcon /> },
  { tool: 'erase',     label: 'Effacer',      shortcut: 'E', icon: <EraseIcon /> },
  { tool: 'select',    label: 'Mesurer',      shortcut: 'T', icon: <TapeIcon /> }, // tape = select + hint
]

const SHORTCUTS: Record<string, DrawTool> = {
  s: 'select', m: 'move', r: 'rectangle', l: 'line',
  p: 'push-pull', e: 'erase', t: 'select', o: 'orbit',
}

function getHint(tool: DrawTool, phase: string): string {
  if (tool === 'orbit')      return 'Clic gauche: orbiter · Clic droit: panoramique · Molette: zoom'
  if (tool === 'select')     return 'Cliquez sur un bâtiment pour le sélectionner'
  if (tool === 'erase')      return 'Cliquez sur un bâtiment pour le supprimer'
  if (tool === 'move')       return 'Cliquez sur un bâtiment et faites glisser pour le déplacer'
  if (tool === 'push-pull')  return 'Cliquez sur un bâtiment et faites glisser pour modifier la hauteur'
  if (tool === 'rectangle') {
    if (phase === 'idle')        return 'Cliquez pour placer le premier coin du rectangle'
    if (phase === 'rect-corner2') return 'Cliquez pour placer le second coin'
    if (phase === 'rect-height')  return 'Définissez la hauteur et validez'
    return 'Outil rectangle actif'
  }
  if (tool === 'line') {
    if (phase === 'idle')         return 'Cliquez pour ajouter des points · Clic sur le départ pour fermer'
    if (phase === 'line-placing') return 'Continuez à cliquer · Cliquez sur le premier point pour fermer'
    if (phase === 'line-height')  return 'Définissez la hauteur et validez'
    return 'Outil ligne actif'
  }
  return ''
}

export default function DrawingToolbar() {
  const {
    drawTool, drawPhase, drawPreviewHeight, drawFootprint, drawCorner1, drawPreviewPos,
    setDrawTool, setDrawPhase, setDrawPreviewHeight, setDrawFootprint,
    setDrawCorner1, setDrawLinePoints,
    addDrawnBuilding,
    drawnBuildings,
  } = useStore()

  const [heightInput, setHeightInput] = useState(drawPreviewHeight)
  const heightInputRef = useRef<HTMLInputElement>(null)

  const showHeightPanel = drawPhase === 'rect-height' || drawPhase === 'line-height'

  // Sync height input when entering height phase
  useEffect(() => {
    if (showHeightPanel) {
      setHeightInput(drawPreviewHeight)
      setTimeout(() => heightInputRef.current?.focus(), 50)
    }
  }, [showHeightPanel])

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Don't intercept when typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const key = e.key.toLowerCase()
      if (key in SHORTCUTS) {
        setDrawTool(SHORTCUTS[key])
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [setDrawTool])

  function handleValidate() {
    let footprint: [number, number][] | null = drawFootprint

    // If footprint wasn't saved yet (rect mode), build it from corner1 + previewPos
    if (!footprint && drawPhase === 'rect-height' && drawCorner1 && drawPreviewPos) {
      const [x1, y1] = drawCorner1
      const [x2, y2] = drawPreviewPos
      footprint = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    }

    if (!footprint || footprint.length < 3) return

    const color = BUILDING_COLORS[drawnBuildings.length % BUILDING_COLORS.length]
    const id = `drawn-${++_drawnBuildingIdCounter}`
    addDrawnBuilding({ id, footprint, height: heightInput, color })

    // Reset drawing state
    setDrawPhase('idle')
    setDrawCorner1(null)
    setDrawLinePoints([])
    setDrawFootprint(null)
    setDrawPreviewHeight(3)
    setHeightInput(3)
  }

  function handleHeightKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleValidate()
    if (e.key === 'Escape') {
      setDrawPhase('idle')
      setDrawCorner1(null)
      setDrawLinePoints([])
      setDrawFootprint(null)
    }
  }

  function handleCancelDraw() {
    setDrawPhase('idle')
    setDrawCorner1(null)
    setDrawLinePoints([])
    setDrawFootprint(null)
  }

  const hint = getHint(drawTool, drawPhase)

  return (
    <>
      {/* Toolbar strip */}
      <div className="absolute left-4 top-1/2 -translate-y-1/2 z-20 flex flex-col gap-1 bg-[#1E293B]/95 border border-[#334155] rounded-xl p-1.5 shadow-2xl backdrop-blur-sm">
        {TOOLS.map((def, idx) => {
          const isActive = drawTool === def.tool && !(def.shortcut === 'T' && drawTool !== 'select')
          // For tape tool, only highlight when it's 'T' shortcut and tool is select but that's tricky
          // Simpler: just compare tool identity for non-tape, skip tape highlight
          const highlight =
            def.shortcut !== 'T'
              ? drawTool === def.tool
              : false

          return (
            <div key={idx} className="relative group">
              <button
                onClick={() => setDrawTool(def.tool)}
                className={`
                  w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-150
                  ${highlight
                    ? 'bg-[#0EA5E9] text-white shadow-md'
                    : 'text-[#94A3B8] hover:text-white hover:bg-[#334155]'
                  }
                `}
                title={`${def.label} (${def.shortcut})`}
              >
                {def.icon}
              </button>
              {/* Keyboard badge */}
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-[#0F172A] border border-[#475569] text-[#64748B] text-[8px] font-mono flex items-center justify-center rounded pointer-events-none">
                {def.shortcut}
              </span>
              {/* Tooltip */}
              <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap bg-[#0F172A] text-white text-xs px-2 py-1 rounded shadow-lg border border-[#334155] z-30">
                {def.label}
              </div>
            </div>
          )
        })}

        {/* Separator */}
        <div className="w-full h-px bg-[#334155] my-0.5" />

        {/* Orbit button */}
        <div className="relative group">
          <button
            onClick={() => setDrawTool('orbit')}
            className={`
              w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-150
              ${drawTool === 'orbit'
                ? 'bg-[#0EA5E9] text-white shadow-md'
                : 'text-[#94A3B8] hover:text-white hover:bg-[#334155]'
              }
            `}
            title="Orbiter (O)"
          >
            <OrbitIcon />
          </button>
          <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-[#0F172A] border border-[#475569] text-[#64748B] text-[8px] font-mono flex items-center justify-center rounded pointer-events-none">
            O
          </span>
          <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap bg-[#0F172A] text-white text-xs px-2 py-1 rounded shadow-lg border border-[#334155] z-30">
            Orbiter / Panoramique
          </div>
        </div>
      </div>

      {/* Height input panel */}
      {showHeightPanel && (
        <div className="absolute top-12 left-1/2 -translate-x-1/2 z-30 bg-[#1E293B]/95 border border-[#334155] rounded-xl p-4 shadow-2xl backdrop-blur-sm flex flex-col gap-3 min-w-[260px]">
          <p className="text-[#94A3B8] text-sm font-medium">Hauteur du bâtiment</p>
          <div className="flex items-center gap-2">
            <input
              ref={heightInputRef}
              type="number"
              min={1}
              max={30}
              step={0.5}
              value={heightInput}
              onChange={(e) => {
                const v = parseFloat(e.target.value)
                if (!isNaN(v)) {
                  setHeightInput(v)
                  setDrawPreviewHeight(v)
                }
              }}
              onKeyDown={handleHeightKeyDown}
              className="flex-1 bg-[#0F172A] border border-[#475569] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
            />
            <span className="text-[#64748B] text-sm">m</span>
            <button
              onClick={handleValidate}
              className="bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Valider
            </button>
          </div>
          <button
            onClick={handleCancelDraw}
            className="text-[#64748B] hover:text-[#94A3B8] text-xs text-center transition-colors"
          >
            Annuler (Échap)
          </button>
        </div>
      )}

      {/* Cancel button when in progress */}
      {drawPhase !== 'idle' && !showHeightPanel && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20">
          <button
            onClick={handleCancelDraw}
            className="bg-[#1E293B]/90 border border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#EF4444] text-xs px-3 py-1.5 rounded-lg transition-all backdrop-blur-sm"
          >
            Annuler (Échap)
          </button>
        </div>
      )}

      {/* Hint bar at bottom */}
      {hint && (
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
          <div className="bg-[#0F172A]/85 border border-[#334155] text-[#94A3B8] text-xs px-4 py-1.5 rounded-full backdrop-blur-sm whitespace-nowrap">
            {hint}
          </div>
        </div>
      )}
    </>
  )
}

import { useStore } from '../store/useStore'
import { RoofType, ObstacleType } from '../types'
import { OBSTACLE_CFG } from './Obstacles'

const ROOF_LABELS: Record<RoofType, string> = {
  flat: 'Plat',
  shed: 'Mono-pente',
  gable: 'Bi-pente',
  hip: '4 pans',
}

function Slider({
  label, value, min, max, step = 1, unit, onChange,
}: {
  label: string; value: number; min: number; max: number; step?: number; unit: string
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[#94A3B8] text-xs">{label}</span>
        <span className="text-white text-xs font-mono tabular-nums">{value.toFixed(step < 1 ? 1 : 0)}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(+e.target.value)}
        className="w-full h-1.5 rounded-full accent-[#0EA5E9] cursor-pointer"
      />
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="text-[#64748B] text-[10px] uppercase tracking-widest font-semibold">{title}</div>
      {children}
    </div>
  )
}

export default function ControlsPanel() {
  const {
    roofType, setRoofType,
    pitch, setPitch,
    azimuth, setAzimuth,
    wallHeight, setWallHeight,
    simDate, setSimDate,
    simHour, setSimHour,
    isPlaying, setIsPlaying,
    panelCount, annualConsumption, installType,
    controlsOpen, toggleControls,
    sceneMode, setSceneMode, obstacleTypeToPlace,
    obstacles, removedPanels,
  } = useStore()

  const SPECIFIC_YIELD = 1700
  const selfUse = installType === 'autonome' ? 1.0 : installType === 'hybride' ? 0.85 : 0.70
  const peakKwc = (panelCount * 0.545).toFixed(2)
  const annualProduction = Math.round(panelCount * 0.545 * SPECIFIC_YIELD * (roofType === 'flat' ? 0.88 : 0.95))
  const coverage = annualConsumption > 0
    ? Math.min(100, Math.round((annualProduction * selfUse) / annualConsumption * 100))
    : null

  const simHourDisplay = `${String(Math.floor(simHour)).padStart(2, '0')}h${String(Math.round((simHour % 1) * 60)).padStart(2, '0')}`

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={toggleControls}
        className="absolute top-4 right-4 z-20 flex items-center gap-1.5 bg-[#1E293B]/90 border border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#0EA5E9] px-3 py-2 rounded-lg text-xs transition-all backdrop-blur-sm"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
        </svg>
        {controlsOpen ? 'Masquer' : 'Contrôles'}
      </button>

      {/* Panel */}
      {controlsOpen && (
        <div className="absolute top-14 right-4 z-20 w-64 bg-[#1E293B]/95 border border-[#334155] rounded-xl shadow-2xl backdrop-blur-sm overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-[#334155] flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#0EA5E9] animate-pulse" />
            <span className="text-white text-sm font-semibold">Contrôles 3D</span>
          </div>

          <div className="p-4 space-y-5 max-h-[calc(100vh-120px)] overflow-y-auto scrollbar-thin">

            {/* Roof */}
            <Section title="Toiture">
              {/* Roof type */}
              <div className="space-y-1.5">
                <div className="text-[#94A3B8] text-xs">Type de toit</div>
                <div className="grid grid-cols-4 gap-1">
                  {(['flat', 'shed', 'gable', 'hip'] as RoofType[]).map((type) => (
                    <button
                      key={type}
                      onClick={() => setRoofType(type)}
                      className={`py-1.5 px-1 rounded text-[10px] font-medium transition-all ${
                        roofType === type
                          ? 'bg-[#0EA5E9] text-white'
                          : 'bg-[#0F172A] text-[#64748B] hover:text-white border border-[#334155] hover:border-[#0EA5E9]'
                      }`}
                    >
                      {ROOF_LABELS[type]}
                    </button>
                  ))}
                </div>
              </div>

              <Slider label="Inclinaison" value={pitch} min={0} max={45} unit="°" onChange={setPitch} />
              <Slider label="Azimut" value={azimuth} min={0} max={360} unit="°" onChange={setAzimuth} />
              <Slider label="Hauteur des murs" value={wallHeight} min={2} max={10} step={0.5} unit=" m" onChange={setWallHeight} />

              {/* Azimuth compass indicator */}
              <div className="flex items-center gap-2 mt-1">
                <div className="relative w-8 h-8 flex-shrink-0">
                  <div className="absolute inset-0 rounded-full border border-[#334155]" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div
                      className="w-0.5 h-3 bg-[#0EA5E9] origin-bottom rounded-full"
                      style={{ transform: `rotate(${azimuth}deg)`, transformOrigin: '50% 100%' }}
                    />
                  </div>
                  <span className="absolute -top-1 left-1/2 -translate-x-1/2 text-[8px] text-[#475569]">N</span>
                </div>
                <span className="text-[#64748B] text-[10px]">
                  {azimuth === 180 ? 'Orienté plein Sud (optimal)' :
                   azimuth < 135 || azimuth > 225 ? 'Sous-optimal — préférer ≈180°' :
                   'Orientation proche du Sud'}
                </span>
              </div>
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Sun simulation */}
            <Section title="Simulation solaire">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Date</span>
                  <input
                    type="date"
                    value={simDate.toISOString().split('T')[0]}
                    onChange={(e) => setSimDate(new Date(e.target.value + 'T12:00:00'))}
                    className="bg-[#0F172A] border border-[#334155] text-white text-xs rounded px-2 py-1 w-32"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Heure</span>
                  <span className="text-white text-xs font-mono tabular-nums">{simHourDisplay}</span>
                </div>
                <input
                  type="range" min={0} max={23.99} step={0.25} value={simHour}
                  onChange={(e) => setSimHour(+e.target.value)}
                  className="w-full h-1.5 rounded-full accent-[#F59E0B] cursor-pointer"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                    isPlaying
                      ? 'bg-[#F59E0B] text-black'
                      : 'bg-[#0F172A] text-[#94A3B8] border border-[#334155] hover:border-[#F59E0B] hover:text-[#F59E0B]'
                  }`}
                >
                  {isPlaying ? (
                    <>
                      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                      </svg>
                      Pause
                    </>
                  ) : (
                    <>
                      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                      Animer
                    </>
                  )}
                </button>
                <button
                  onClick={() => { setSimHour(12); setIsPlaying(false) }}
                  className="px-3 py-2 rounded-lg text-xs text-[#64748B] hover:text-white bg-[#0F172A] border border-[#334155] hover:border-[#334155] transition-all"
                >
                  12h
                </button>
              </div>
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Obstacles */}
            <Section title="Obstacles / Ombres">
              <p className="text-[#64748B] text-[10px] leading-snug">
                Placez des obstacles qui projettent des ombres sur les panneaux.
              </p>
              <div className="grid grid-cols-3 gap-1.5">
                {(Object.keys(OBSTACLE_CFG) as ObstacleType[]).map((type) => {
                  const cfg = OBSTACLE_CFG[type]
                  const isActive = sceneMode === 'place-obstacle' && obstacleTypeToPlace === type
                  return (
                    <button
                      key={type}
                      onClick={() =>
                        isActive
                          ? setSceneMode('view')
                          : setSceneMode('place-obstacle', type)
                      }
                      title={`Placer : ${cfg.label}`}
                      className={`flex flex-col items-center gap-1 py-2 px-1 rounded-lg border text-[10px] font-medium transition-all ${
                        isActive
                          ? 'bg-[#F59E0B]/15 border-[#F59E0B]/60 text-[#F59E0B]'
                          : 'bg-[#0F172A] border-[#334155] text-[#64748B] hover:text-white hover:border-[#475569]'
                      }`}
                    >
                      <span className="text-base leading-none">{cfg.icon}</span>
                      <span>{cfg.label}</span>
                    </button>
                  )
                })}
              </div>
              {sceneMode === 'place-obstacle' && (
                <div className="flex items-center gap-1.5 bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-lg px-2.5 py-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-pulse flex-shrink-0" />
                  <span className="text-[#F59E0B] text-[10px]">
                    Cliquez sur le toit pour placer. Appuyez sur Échap pour annuler.
                  </span>
                </div>
              )}
              {obstacles.length > 0 && (
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-[#64748B]">{obstacles.length} obstacle{obstacles.length > 1 ? 's' : ''} placé{obstacles.length > 1 ? 's' : ''}</span>
                  <button
                    onClick={() => {
                      const ids = useStore.getState().obstacles.map(o => o.id)
                      ids.forEach(id => useStore.getState().removeObstacle(id))
                    }}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
                    Tout effacer
                  </button>
                </div>
              )}
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Results */}
            <Section title="Résultats estimés">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Panneaux</span>
                  <span className="text-white text-xs font-mono font-semibold">
                    {panelCount - removedPanels.size}
                    {removedPanels.size > 0 && (
                      <span className="text-[#475569] ml-1">(-{removedPanels.size})</span>
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Puissance crête</span>
                  <span className="text-[#0EA5E9] text-xs font-mono font-semibold">{peakKwc} kWc</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Production est.</span>
                  <span className="text-[#F59E0B] text-xs font-mono font-semibold">
                    ~{annualProduction.toLocaleString('fr-FR')} kWh/an
                  </span>
                </div>
                {coverage !== null && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-[#94A3B8] text-xs">Taux de couverture</span>
                      <span className={`text-xs font-mono font-semibold ${
                        coverage >= 80 ? 'text-green-400' : coverage >= 50 ? 'text-[#F59E0B]' : 'text-red-400'
                      }`}>{coverage}%</span>
                    </div>
                    <div className="relative h-1.5 bg-[#0F172A] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          coverage >= 80 ? 'bg-green-400' : coverage >= 50 ? 'bg-[#F59E0B]' : 'bg-red-400'
                        }`}
                        style={{ width: `${Math.min(coverage, 100)}%` }}
                      />
                    </div>
                  </>
                )}
              </div>
            </Section>

          </div>
        </div>
      )}
    </>
  )
}

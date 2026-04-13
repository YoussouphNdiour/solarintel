import { useStore } from '../store/useStore'
import { RoofType, ObstacleType, WeatherMode, RoofMaterial } from '../types'
import { OBSTACLE_CFG } from './Obstacles'

const ROOF_LABELS: Record<RoofType, string> = {
  flat: 'Plat', shed: 'Mono-pente', gable: 'Bi-pente', hip: '4 pans',
}

const WEATHER_CFG: { mode: WeatherMode; label: string; icon: string }[] = [
  { mode: 'clear', label: 'Dégagé', icon: '☀️' },
  { mode: 'cloudy', label: 'Nuageux', icon: '⛅' },
  { mode: 'overcast', label: 'Couvert', icon: '☁️' },
]

const MATERIAL_CFG: { mat: RoofMaterial; label: string; color: string }[] = [
  { mat: 'tuile-rouge', label: 'Tuile rouge', color: '#8B3A2A' },
  { mat: 'tuile-grise', label: 'Tuile grise', color: '#2D3D52' },
  { mat: 'zinc',        label: 'Zinc',        color: '#5B6E7A' },
  { mat: 'bac-acier',   label: 'Bac acier',   color: '#374151' },
  { mat: 'beton',       label: 'Béton',       color: '#6B7280' },
]

const SEASON_PRESETS = [
  { label: 'Été', icon: '☀️',  month: 6, day: 21 },
  { label: 'Éqx', icon: '🌍', month: 3, day: 21 },
  { label: 'Hiver', icon: '❄️', month: 12, day: 21 },
]

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
    roofMaterial, setRoofMaterial,
    weatherMode, setWeatherMode,
    simDate, setSimDate,
    simHour, setSimHour,
    simSpeed, setSimSpeed,
    isPlaying, setIsPlaying,
    panelCount, annualConsumption, installType,
    controlsOpen, toggleControls,
    showStats, toggleStats,
    irradianceMode, toggleIrradiance,
    sceneMode, setSceneMode, obstacleTypeToPlace,
    obstacles, removedPanels,
    shadingPct,
    takeScreenshot,
    zones, selectedZoneId, selectZone,
    selectedRoofFaces, toggleRoofFace,
  } = useStore()

  const SPECIFIC_YIELD = 1700
  const selfUse = installType === 'autonome' ? 1.0 : installType === 'hybride' ? 0.85 : 0.70
  const activeCount = panelCount - removedPanels.size
  const peakKwc = (activeCount * 0.545).toFixed(2)
  // Meme formule que StatsPanel (pitch-aware) + facteur d'ombrage obstacles
  const pitchFactor = roofType === 'flat' ? 0.88 : (0.9 + 0.1 * Math.sin((pitch * Math.PI) / 180))
  const annualProduction = Math.round(activeCount * 0.545 * SPECIFIC_YIELD * pitchFactor * (1 - (shadingPct || 0) / 100))
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

      {/* Action buttons row (top-left area) */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
        {/* Add panel mode */}
        <button
          onClick={() => setSceneMode(sceneMode === 'add-panel' ? 'view' : 'add-panel')}
          title="Ajouter un panneau"
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs border transition-all backdrop-blur-sm ${
            sceneMode === 'add-panel'
              ? 'bg-green-500/20 border-green-500/60 text-green-400'
              : 'bg-[#1E293B]/90 border-[#334155] text-[#94A3B8] hover:text-white hover:border-green-500/60'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {sceneMode === 'add-panel' ? 'Annuler' : 'Ajouter'}
        </button>

        {/* Irradiance toggle */}
        <button
          onClick={toggleIrradiance}
          title="Mode irradiance / ombrage"
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs border transition-all backdrop-blur-sm ${
            irradianceMode
              ? 'bg-[#F59E0B]/20 border-[#F59E0B]/60 text-[#F59E0B]'
              : 'bg-[#1E293B]/90 border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#F59E0B]/60'
          }`}
        >
          🌡️ Irradiance
        </button>

        {/* Stats toggle */}
        <button
          onClick={toggleStats}
          title="Statistiques de production"
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs border transition-all backdrop-blur-sm ${
            showStats
              ? 'bg-[#0EA5E9]/20 border-[#0EA5E9]/60 text-[#0EA5E9]'
              : 'bg-[#1E293B]/90 border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#0EA5E9]/60'
          }`}
        >
          📊 Stats
        </button>

        {/* Screenshot */}
        <button
          onClick={takeScreenshot}
          title="Capturer une image"
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs border bg-[#1E293B]/90 border-[#334155] text-[#94A3B8] hover:text-white hover:border-[#0EA5E9] transition-all backdrop-blur-sm"
        >
          📷
        </button>
      </div>

      {/* Add-panel mode banner */}
      {sceneMode === 'add-panel' && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-green-500/90 text-black text-xs font-semibold px-4 py-2 rounded-full shadow-lg">
          <div className="w-1.5 h-1.5 rounded-full bg-black/50 animate-pulse" />
          Cliquez sur le panneau vert pour l'ajouter
        </div>
      )}

      {/* Irradiance legend */}
      {irradianceMode && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-[#1E293B]/90 border border-[#334155] rounded-lg px-3 py-2 backdrop-blur-sm">
          <span className="text-[#64748B] text-[10px]">Ombre</span>
          <div className="w-32 h-2 rounded-full" style={{
            background: 'linear-gradient(to right, #1E293B, #1D4ED8, #0EA5E9, #22C55E, #FBBF24)'
          }} />
          <span className="text-[#64748B] text-[10px]">Plein soleil</span>
        </div>
      )}

      {/* Main panel */}
      {controlsOpen && (
        <div className="absolute top-14 right-4 z-20 w-64 bg-[#1E293B]/95 border border-[#334155] rounded-xl shadow-2xl backdrop-blur-sm overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-[#334155] flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#0EA5E9] animate-pulse" />
            <span className="text-white text-sm font-semibold">Contrôles 3D</span>
          </div>

          {/* Building selector (multi-zone) */}
          {zones.length > 1 && (
            <div className="px-3 pt-2 pb-1 border-b border-[#1E293B]">
              <p className="text-[10px] text-[#64748B] uppercase tracking-wide mb-1.5 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                Batiment actif
              </p>
              <div className="flex flex-wrap gap-1.5">
                {zones.map((zone, i) => (
                  <button
                    key={zone.id}
                    onClick={() => selectZone(zone.id)}
                    className={`text-[10px] px-2 py-1 rounded font-medium transition-colors ${
                      selectedZoneId === zone.id
                        ? 'bg-[#0EA5E9] text-white'
                        : 'bg-[#1E293B] text-[#94A3B8] hover:bg-[#334155]'
                    }`}
                  >
                    Bat. {i + 1}{zone.label ? ` — ${zone.label}` : ''}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected zone info */}
          {zones.length > 0 && selectedZoneId && (() => {
            const selectedZone = zones.find(z => z.id === selectedZoneId)
            if (!selectedZone) return null
            return (
              <div className="px-3 py-1.5 bg-[#0EA5E9]/5 border-b border-[#1E293B] text-[10px] text-[#94A3B8] flex gap-3 flex-wrap">
                <span>{selectedZone.panelCount} panneaux</span>
                {selectedZone.roofType && <span>Toit: {selectedZone.roofType}</span>}
                <span>Incl: {selectedZone.pitch}° / Az: {selectedZone.azimuth}°</span>
              </div>
            )
          })()}

          <div className="p-4 space-y-5 max-h-[calc(100vh-120px)] overflow-y-auto scrollbar-thin">

            {/* Zone switcher — shown only in multi-zone mode */}
              {zones.length > 1 && (
                <div className="space-y-2">
                  <div className="text-[#64748B] text-[10px] uppercase tracking-widest font-semibold">Zones</div>
                  <div className="space-y-1">
                    {zones.map((zone, i) => {
                      const ROOF_SHORT: Record<string, string> = {
                        flat: 'Plat', shed: '1 pan', gable: '2 pans', hip: '4 pans',
                      }
                      const isActive = selectedZoneId === zone.id
                      return (
                        <button
                          key={zone.id}
                          onClick={() => selectZone(zone.id)}
                          className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all ${
                            isActive
                              ? 'bg-[#0EA5E9]/15 border border-[#0EA5E9]/40 text-white'
                              : 'bg-[#1E293B] border border-transparent text-[#94A3B8] hover:text-white hover:border-[#334155]'
                          }`}
                        >
                          <div className={`w-2 h-2 rounded-full shrink-0 ${isActive ? 'bg-[#0EA5E9]' : 'bg-[#475569]'}`} />
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-semibold leading-none mb-0.5">Zone {i + 1}</div>
                            <div className="text-[#64748B] text-[9px] leading-none truncate">
                              {zone.panelCount > 0 ? `${zone.panelCount} pann.` : 'Aucun panneau'}
                              {zone.roofType ? ` · ${ROOF_SHORT[zone.roofType] ?? zone.roofType}` : ''}
                              {zone.pitch !== undefined ? ` · ${zone.pitch}°` : ''}
                            </div>
                          </div>
                          {isActive && (
                            <svg className="w-3 h-3 text-[#0EA5E9] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </button>
                      )
                    })}
                  </div>
                  <div className="h-px bg-[#1E293B]" />
                </div>
              )}

            {/* Roof */}
            <Section title="Toiture">
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

              {/* Face selector — shown for gable (2 faces) and hip (4 faces) */}
              {(roofType === 'gable' || roofType === 'hip') && (() => {
                const faceLabels = roofType === 'gable'
                  ? [{ label: 'Avant', idx: 0 }, { label: 'Arrière', idx: 1 }]
                  : [{ label: 'S', idx: 0 }, { label: 'N', idx: 1 }, { label: 'O', idx: 2 }, { label: 'E', idx: 3 }]
                return (
                  <div className="space-y-1.5">
                    <div className="text-[#94A3B8] text-xs">Pans actifs (panneaux)</div>
                    <div className={`grid gap-1 ${roofType === 'gable' ? 'grid-cols-2' : 'grid-cols-4'}`}>
                      {faceLabels.map(({ label, idx }) => (
                        <button
                          key={idx}
                          onClick={() => toggleRoofFace(idx)}
                          className={`py-1.5 px-1 rounded text-[10px] font-medium transition-all ${
                            selectedRoofFaces.has(idx)
                              ? 'bg-[#0EA5E9] text-white'
                              : 'bg-[#0F172A] text-[#64748B] hover:text-white border border-[#334155] hover:border-[#0EA5E9]'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    <p className="inline-flex items-center gap-1 bg-[#0EA5E9]/10 border border-[#0EA5E9]/30 text-[#38BDF8] text-[9px] px-1.5 py-0.5 rounded-full">
                      <svg className="w-2.5 h-2.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Cliquez aussi sur un pan dans la vue 3D
                    </p>
                  </div>
                )
              })()}

              <Slider label="Inclinaison" value={pitch} min={0} max={45} unit="°" onChange={setPitch} />
              {/* Azimuth quick-presets */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Azimut</span>
                  <input
                    type="number" min={0} max={360} step={1} value={Math.round(azimuth)}
                    onChange={(e) => setAzimuth(((+e.target.value % 360) + 360) % 360)}
                    className="w-16 bg-[#0F172A] border border-[#334155] text-white text-xs font-mono rounded px-2 py-1 text-right"
                  />
                </div>
                <div className="grid grid-cols-8 gap-0.5">
                  {([
                    { label: 'N', az: 0 }, { label: 'NE', az: 45 }, { label: 'E', az: 90 }, { label: 'SE', az: 135 },
                    { label: 'S', az: 180 }, { label: 'SO', az: 225 }, { label: 'O', az: 270 }, { label: 'NO', az: 315 },
                  ] as { label: string; az: number }[]).map(({ label, az }) => (
                    <button
                      key={az}
                      onClick={() => setAzimuth(az)}
                      title={`Azimut ${az}°`}
                      className={`py-1 rounded text-[9px] font-medium transition-all ${
                        Math.abs(azimuth - az) < 23
                          ? 'bg-[#0EA5E9] text-white'
                          : 'bg-[#0F172A] text-[#64748B] hover:text-white border border-[#334155] hover:border-[#0EA5E9]'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <input
                  type="range" min={0} max={360} step={1} value={azimuth}
                  onChange={(e) => setAzimuth(+e.target.value)}
                  className="w-full h-1.5 rounded-full accent-[#0EA5E9] cursor-pointer"
                />
                <div className="flex items-center gap-2">
                  <div className="relative w-8 h-8 flex-shrink-0">
                    <div className="absolute inset-0 rounded-full border border-[#334155]" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-0.5 h-3 bg-[#0EA5E9] origin-bottom rounded-full"
                        style={{ transform: `rotate(${azimuth}deg)`, transformOrigin: '50% 100%' }}
                      />
                    </div>
                    <span className="absolute -top-1 left-1/2 -translate-x-1/2 text-[8px] text-[#475569]">N</span>
                  </div>
                  <span className="text-[#64748B] text-[10px]">
                    {azimuth === 180 ? 'Plein Sud (optimal)' :
                     Math.abs(azimuth - 180) <= 45 ? 'Proche du Sud' :
                     Math.abs(azimuth - 90) <= 45 || Math.abs(azimuth - 270) <= 45 ? 'Est/Ouest — sous-optimal' :
                     'Sous-optimal — préférer ≈180°'}
                  </span>
                </div>
              </div>
              <Slider label="Hauteur des murs" value={wallHeight} min={2} max={10} step={0.5} unit=" m" onChange={setWallHeight} />
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Roof material */}
            <Section title="Matériau de couverture">
              <div className="space-y-1">
                {MATERIAL_CFG.map(({ mat, label, color }) => (
                  <button
                    key={mat}
                    onClick={() => setRoofMaterial(mat)}
                    className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-all ${
                      roofMaterial === mat
                        ? 'bg-[#0EA5E9]/15 border border-[#0EA5E9]/50 text-white'
                        : 'border border-transparent text-[#64748B] hover:text-white hover:bg-[#0F172A]'
                    }`}
                  >
                    <div className="w-4 h-4 rounded-sm flex-shrink-0 border border-white/10" style={{ background: color }} />
                    {label}
                  </button>
                ))}
              </div>
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Weather */}
            <Section title="Météo">
              <div className="grid grid-cols-3 gap-1">
                {WEATHER_CFG.map(({ mode, label, icon }) => (
                  <button
                    key={mode}
                    onClick={() => setWeatherMode(mode)}
                    className={`flex flex-col items-center gap-0.5 py-2 rounded-lg text-[10px] border transition-all ${
                      weatherMode === mode
                        ? 'bg-[#0EA5E9]/15 border-[#0EA5E9]/50 text-white'
                        : 'bg-[#0F172A] border-[#334155] text-[#64748B] hover:text-white hover:border-[#475569]'
                    }`}
                  >
                    <span className="text-base">{icon}</span>
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </Section>

            <div className="h-px bg-[#334155]" />

            {/* Sun simulation */}
            <Section title="Simulation solaire">
              {/* Season presets */}
              <div className="space-y-1.5">
                <div className="text-[#94A3B8] text-xs">Saison</div>
                <div className="grid grid-cols-3 gap-1">
                  {SEASON_PRESETS.map(({ label, icon, month, day }) => (
                    <button
                      key={label}
                      onClick={() => {
                        const d = new Date(new Date().getFullYear(), month - 1, day, 12)
                        setSimDate(d)
                      }}
                      className="flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[10px] bg-[#0F172A] border border-[#334155] text-[#64748B] hover:text-white hover:border-[#475569] transition-all"
                    >
                      <span>{icon}</span>
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>

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
                    <><svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>Pause</>
                  ) : (
                    <><svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>Animer</>
                  )}
                </button>
                <button
                  onClick={() => { setSimHour(12); setIsPlaying(false) }}
                  className="px-3 py-2 rounded-lg text-xs text-[#64748B] hover:text-white bg-[#0F172A] border border-[#334155] transition-all"
                >
                  12h
                </button>
              </div>

              {/* Animation speed */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Vitesse</span>
                  <span className="text-white text-xs font-mono">×{simSpeed.toFixed(1)}</span>
                </div>
                <input
                  type="range" min={0.5} max={5} step={0.5} value={simSpeed}
                  onChange={(e) => setSimSpeed(+e.target.value)}
                  className="w-full h-1.5 rounded-full accent-[#94A3B8] cursor-pointer"
                />
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
                      onClick={() => isActive ? setSceneMode('view') : setSceneMode('place-obstacle', type)}
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
                  <span className="text-[#F59E0B] text-[10px]">Cliquez sur le toit pour placer. Échap pour annuler.</span>
                </div>
              )}
              {obstacles.length > 0 && (
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-[#64748B]">{obstacles.length} obstacle{obstacles.length > 1 ? 's' : ''}</span>
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
                  <span className="text-[#94A3B8] text-xs">Panneaux actifs</span>
                  <span className="text-white text-xs font-mono font-semibold">
                    {activeCount}
                    {removedPanels.size > 0 && <span className="text-[#475569] ml-1">(-{removedPanels.size})</span>}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Puissance crête</span>
                  <span className="text-[#0EA5E9] text-xs font-mono font-semibold">{peakKwc} kWc</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#94A3B8] text-xs">Production est.</span>
                  <span className="text-[#F59E0B] text-xs font-mono font-semibold">~{annualProduction.toLocaleString('fr-FR')} kWh/an</span>
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

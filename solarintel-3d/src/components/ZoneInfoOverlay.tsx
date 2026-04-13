import { useStore } from '../store/useStore'

const ROOF_LABELS: Record<string, string> = {
  flat: 'Toit plat', shed: 'Mono-pente', gable: 'Bi-pente', hip: '4 pans',
}

export default function ZoneInfoOverlay() {
  const { zones, selectedZoneId, panelCount, removedPanels } = useStore()
  const zone = zones.find(z => z.id === selectedZoneId)
  if (!zone || !selectedZoneId) return null

  const zoneIndex = zones.indexOf(zone)
  const activeCount = panelCount - removedPanels.size
  const kWc = (activeCount * 0.545).toFixed(2)
  const roofLabel = ROOF_LABELS[zone.roofType ?? ''] ?? '—'
  const pitch = zone.pitch ?? 15
  const azimuth = zone.azimuth ?? 180
  const area = zone.area ? zone.area.toFixed(1) : '—'

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
      <div className="bg-[#1E293B]/90 border border-[#0EA5E9]/40 rounded-xl px-4 py-2.5 shadow-xl backdrop-blur-sm flex items-center gap-4">
        {/* Zone badge */}
        <div className="flex items-center gap-1.5 shrink-0">
          <div className="w-2 h-2 rounded-full bg-[#0EA5E9] animate-pulse" />
          <span className="text-[#0EA5E9] text-xs font-bold uppercase tracking-widest">
            Zone {zoneIndex + 1}
          </span>
        </div>
        <div className="w-px h-5 bg-[#334155]" />
        {/* Roof type */}
        <Chip label="Toit" value={roofLabel} />
        <Chip label="Incl." value={`${pitch}°`} />
        <Chip label="Azimut" value={`${azimuth}°`} />
        {area !== '—' && <Chip label="Surface" value={`${area} m²`} />}
        <div className="w-px h-5 bg-[#334155]" />
        <Chip label="Panneaux" value={`${activeCount}`} color="text-[#F59E0B]" />
        <Chip label="Puissance" value={`${kWc} kWc`} color="text-green-400" />
      </div>
    </div>
  )
}

function Chip({ label, value, color = 'text-white' }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col items-center leading-none gap-0.5">
      <span className="text-[#64748B] text-[9px] uppercase tracking-wider">{label}</span>
      <span className={`text-xs font-semibold font-mono ${color}`}>{value}</span>
    </div>
  )
}

import { useMemo } from 'react'
import { useStore } from '../store/useStore'

// Monthly peak sun hours for Dakar, Senegal (lat ~14.7°N)
const DAKAR_PSH = [5.5, 6.2, 6.5, 6.9, 6.8, 6.4, 5.7, 5.8, 6.2, 6.3, 6.0, 5.3]
const MONTHS_FR = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']
const SYSTEM_EFF = 0.77
const CO2_KG_PER_KWH = 0.55  // Senegal grid
const FCFA_PER_KWH = 110      // approx. Senelec tariff

export default function StatsPanel() {
  const { panelCount, removedPanels, annualConsumption, installType, showStats, roofType, pitch } = useStore()

  const activeCount = panelCount - removedPanels.size
  const peakKwc = activeCount * 0.545

  const selfUse = installType === 'autonome' ? 1.0 : installType === 'hybride' ? 0.85 : 0.70
  const pitchFactor = roofType === 'flat' ? 0.88 : (0.9 + 0.1 * Math.sin((pitch * Math.PI) / 180))

  const monthly = useMemo(() =>
    DAKAR_PSH.map((psh, i) => ({
      label: MONTHS_FR[i],
      kwh: Math.round(peakKwc * psh * 30.5 * SYSTEM_EFF * pitchFactor),
    })),
    [peakKwc, pitchFactor]
  )

  const annual = useMemo(() => monthly.reduce((a, m) => a + m.kwh, 0), [monthly])
  const co2 = Math.round(annual * CO2_KG_PER_KWH)
  const savings = Math.round(annual * selfUse * FCFA_PER_KWH)
  const coverage = annualConsumption > 0
    ? Math.min(100, Math.round((annual * selfUse) / annualConsumption * 100))
    : null

  const maxMonthly = Math.max(...monthly.map(m => m.kwh))

  if (!showStats) return null

  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 bg-[#0F172A]/95 border-t border-[#334155] backdrop-blur-sm">
      <div className="px-4 py-3 max-w-5xl mx-auto">
        {/* Header row */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#0EA5E9] animate-pulse" />
            <span className="text-white text-sm font-semibold">Statistiques de production</span>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-[#94A3B8]">{activeCount} panneaux · {peakKwc.toFixed(2)} kWc</span>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Monthly chart */}
          <div className="flex-1">
            <div className="text-[#64748B] text-[10px] uppercase tracking-widest mb-2">Production mensuelle (kWh)</div>
            <div className="flex items-end gap-1 h-16">
              {monthly.map((m, i) => {
                const h = maxMonthly > 0 ? (m.kwh / maxMonthly) * 100 : 0
                const isCurrentMonth = i === new Date().getMonth()
                return (
                  <div key={m.label} className="flex-1 flex flex-col items-center gap-0.5 group">
                    <div className="relative w-full" style={{ height: '48px' }}>
                      <div
                        className={`absolute bottom-0 w-full rounded-t transition-all duration-300 ${
                          isCurrentMonth ? 'bg-[#F59E0B]' : 'bg-[#0EA5E9]/60 group-hover:bg-[#0EA5E9]'
                        }`}
                        style={{ height: `${h}%` }}
                      />
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block bg-[#1E293B] text-white text-[9px] px-1.5 py-0.5 rounded whitespace-nowrap border border-[#334155] z-10">
                        {m.kwh.toLocaleString('fr-FR')} kWh
                      </div>
                    </div>
                    <span className={`text-[8px] ${isCurrentMonth ? 'text-[#F59E0B] font-semibold' : 'text-[#475569]'}`}>
                      {m.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 gap-3 w-72 shrink-0">
            <Metric
              label="Production annuelle"
              value={annual.toLocaleString('fr-FR')}
              unit="kWh/an"
              color="text-[#F59E0B]"
            />
            <Metric
              label="CO₂ économisé"
              value={co2.toLocaleString('fr-FR')}
              unit="kg/an"
              color="text-green-400"
            />
            <Metric
              label="Économies est."
              value={savings.toLocaleString('fr-FR')}
              unit="FCFA/an"
              color="text-[#0EA5E9]"
            />
            {coverage !== null && (
              <Metric
                label="Taux couverture"
                value={`${coverage}`}
                unit="%"
                color={coverage >= 80 ? 'text-green-400' : coverage >= 50 ? 'text-[#F59E0B]' : 'text-red-400'}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value, unit, color }: { label: string; value: string; unit: string; color: string }) {
  return (
    <div className="bg-[#1E293B] rounded-lg px-3 py-2">
      <div className="text-[#64748B] text-[9px] uppercase tracking-wider mb-1">{label}</div>
      <div className={`font-mono font-bold text-sm ${color}`}>
        {value}
        <span className="text-[#475569] text-[10px] font-normal ml-1">{unit}</span>
      </div>
    </div>
  )
}

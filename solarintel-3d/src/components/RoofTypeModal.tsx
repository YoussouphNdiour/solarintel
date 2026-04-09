import { RoofType } from '../types'
import { useStore } from '../store/useStore'

interface RoofCard {
  type: RoofType
  label: string
  description: string
  icon: React.ReactNode
}

function FlatIcon() {
  return (
    <svg viewBox="0 0 80 60" className="w-16 h-12" fill="none">
      <rect x="8" y="32" width="64" height="4" fill="#334155" rx="1"/>
      <rect x="14" y="36" width="8" height="16" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
      <rect x="36" y="36" width="8" height="16" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
      <rect x="58" y="36" width="8" height="16" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
      {/* Flat roof top */}
      <rect x="8" y="28" width="64" height="4" fill="#0EA5E9" rx="1" opacity="0.8"/>
    </svg>
  )
}

function ShedIcon() {
  return (
    <svg viewBox="0 0 80 60" className="w-16 h-12" fill="none">
      <polygon points="8,48 72,48 72,36 8,20" fill="#334155" stroke="#475569" strokeWidth="1"/>
      <polygon points="8,20 72,36 72,28 8,12" fill="#0EA5E9" opacity="0.8"/>
      <rect x="14" y="48" width="10" height="10" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
      <rect x="56" y="48" width="10" height="10" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
    </svg>
  )
}

function GableIcon() {
  return (
    <svg viewBox="0 0 80 60" className="w-16 h-12" fill="none">
      {/* Left slope */}
      <polygon points="40,10 8,32 8,48 40,48" fill="#334155" stroke="#475569" strokeWidth="1"/>
      {/* Right slope */}
      <polygon points="40,10 72,32 72,48 40,48" fill="#2D3D52" stroke="#475569" strokeWidth="1"/>
      {/* Left slope highlight */}
      <polygon points="40,10 8,32 8,24 40,10" fill="#0EA5E9" opacity="0.7"/>
      {/* Right slope highlight */}
      <polygon points="40,10 72,32 72,24 40,10" fill="#0EA5E9" opacity="0.4"/>
      <rect x="14" y="40" width="8" height="8" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
      <rect x="58" y="40" width="8" height="8" fill="#1E293B" stroke="#334155" strokeWidth="1"/>
    </svg>
  )
}

function HipIcon() {
  return (
    <svg viewBox="0 0 80 60" className="w-16 h-12" fill="none">
      {/* Front face */}
      <polygon points="12,42 68,42 60,26 20,26" fill="#334155" stroke="#475569" strokeWidth="1"/>
      {/* Left triangle */}
      <polygon points="12,42 20,26 12,34" fill="#2D3D52" stroke="#475569" strokeWidth="1"/>
      {/* Right triangle */}
      <polygon points="68,42 60,26 68,34" fill="#2D3D52" stroke="#475569" strokeWidth="1"/>
      {/* Top highlight */}
      <polygon points="20,26 60,26 60,20 20,20" fill="#0EA5E9" opacity="0.7" rx="1"/>
      <line x1="20" y1="26" x2="60" y2="26" stroke="#0EA5E9" strokeWidth="2"/>
    </svg>
  )
}

const ROOF_CARDS: RoofCard[] = [
  {
    type: 'flat',
    label: 'Toit plat',
    description: 'Terrasse horizontale. Idéal pour Dakar, panneaux inclinables.',
    icon: <FlatIcon />,
  },
  {
    type: 'shed',
    label: 'Mono-pente',
    description: 'Une seule pente. Optimale pour une orientation sud fixe.',
    icon: <ShedIcon />,
  },
  {
    type: 'gable',
    label: 'Bi-pente',
    description: 'Deux versants avec faîtage. Architecture résidentielle classique.',
    icon: <GableIcon />,
  },
  {
    type: 'hip',
    label: 'Toit à 4 pans',
    description: 'Quatre versants convergents. Résistant au vent.',
    icon: <HipIcon />,
  },
]

interface Props {
  zoneId?: string
}

export default function RoofTypeModal({ zoneId }: Props) {
  const setRoofType = useStore((s) => s.setRoofType)
  const updateZone = useStore((s) => s.updateZone)

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-surface border border-[#334155] rounded-2xl p-8 w-full max-w-2xl mx-4 shadow-2xl">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 bg-[#0EA5E9]/10 border border-[#0EA5E9]/30 rounded-full px-4 py-1.5 mb-4">
            <svg className="w-4 h-4 text-[#0EA5E9]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span className="text-[#0EA5E9] text-sm font-medium">Visualisation 3D</span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Quel est le type de votre toiture ?</h2>
          <p className="text-[#94A3B8] text-sm">
            La géométrie 3D et le placement des panneaux s'adaptent automatiquement.
          </p>
        </div>

        {/* Cards grid */}
        <div className="grid grid-cols-2 gap-3">
          {ROOF_CARDS.map((card) => (
            <button
              key={card.type}
              onClick={() => {
                if (zoneId) {
                  updateZone(zoneId, { roofType: card.type })
                } else {
                  setRoofType(card.type)
                }
              }}
              className="group flex flex-col items-center gap-3 p-5 rounded-xl border border-[#334155] bg-[#0F172A] hover:border-[#0EA5E9] hover:bg-[#0EA5E9]/5 transition-all duration-200 text-left"
            >
              <div className="flex items-center justify-center w-full py-2 opacity-80 group-hover:opacity-100 transition-opacity">
                {card.icon}
              </div>
              <div className="w-full">
                <div className="font-semibold text-white text-sm mb-1">{card.label}</div>
                <div className="text-[#94A3B8] text-xs leading-snug">{card.description}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Footer */}
        <p className="text-center text-[#475569] text-xs mt-5">
          Vous pourrez modifier le type de toit à tout moment dans le panneau de contrôle
        </p>
      </div>
    </div>
  )
}

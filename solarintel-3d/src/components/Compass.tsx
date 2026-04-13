import { useStore } from '../store/useStore'

export default function Compass() {
  const azimuth = useStore((s) => s.azimuth)

  // Rotate so that the N label aligns with the roof's orientation relative to North
  const roofAngle = azimuth - 180  // panels face this direction

  return (
    <div className="absolute bottom-4 left-4 z-20 select-none opacity-70 hover:opacity-100 transition-opacity pointer-events-none">
      <div className="relative w-10 h-10">
        {/* Outer ring */}
        {/* pointer-events-none prevents browser extension SVGAnimatedString className errors */}
        <svg viewBox="0 0 56 56" className="w-full h-full drop-shadow-lg" style={{ pointerEvents: 'none' }}>
          {/* Dark background */}
          <circle cx="28" cy="28" r="27" fill="#1E293B" stroke="#334155" strokeWidth="1" />

          {/* Tick marks */}
          {[0,45,90,135,180,225,270,315].map((angle) => {
            const rad = (angle * Math.PI) / 180
            const isCardinal = angle % 90 === 0
            const r1 = isCardinal ? 20 : 22
            const r2 = 26
            return (
              <line
                key={angle}
                x1={28 + r1 * Math.sin(rad)}
                y1={28 - r1 * Math.cos(rad)}
                x2={28 + r2 * Math.sin(rad)}
                y2={28 - r2 * Math.cos(rad)}
                stroke={isCardinal ? '#64748B' : '#334155'}
                strokeWidth={isCardinal ? 1.5 : 1}
              />
            )
          })}

          {/* Cardinal letters */}
          {[
            { label: 'N', angle: 0, color: '#EF4444' },
            { label: 'E', angle: 90, color: '#94A3B8' },
            { label: 'S', angle: 180, color: '#94A3B8' },
            { label: 'O', angle: 270, color: '#94A3B8' },
          ].map(({ label, angle, color }) => {
            const rad = (angle * Math.PI) / 180
            const r = 14
            return (
              <text
                key={label}
                x={28 + r * Math.sin(rad)}
                y={28 - r * Math.cos(rad) + 3.5}
                textAnchor="middle"
                fontSize="7"
                fontWeight="700"
                fill={color}
                fontFamily="system-ui, sans-serif"
              >
                {label}
              </text>
            )
          })}

          {/* Rotating needle — points toward panel azimuth */}
          <g transform={`rotate(${roofAngle}, 28, 28)`}>
            {/* South half (blue) */}
            <polygon points="28,28 25,38 28,34 31,38" fill="#0EA5E9" opacity="0.9" />
            {/* North half (accent) */}
            <polygon points="28,28 25,18 28,22 31,18" fill="#0EA5E9" opacity="0.5" />
            <circle cx="28" cy="28" r="2" fill="#0EA5E9" />
          </g>
        </svg>

        {/* Label below */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[#475569] text-[8px] whitespace-nowrap">
          {azimuth}°
        </div>
      </div>
    </div>
  )
}

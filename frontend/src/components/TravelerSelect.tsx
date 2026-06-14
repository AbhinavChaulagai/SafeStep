import type { TravelerType } from '../types'

const OPTIONS: { value: TravelerType; label: string; icon: string }[] = [
  { value: 'solo', label: 'Solo', icon: '🚶' },
  { value: 'couple', label: 'Couple', icon: '👫' },
  { value: 'family', label: 'Family', icon: '👨‍👩‍👧' },
  { value: 'nightlife', label: 'Nightlife', icon: '🎉' },
]

interface Props {
  value: TravelerType
  onChange: (type: TravelerType) => void
}

export default function TravelerSelect({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Traveler type</p>
      <div className="flex gap-2">
        {OPTIONS.map((o) => (
          <button
            key={o.value}
            onClick={() => onChange(o.value)}
            className={`flex flex-col items-center px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
              value === o.value
                ? 'bg-slate-800 text-white border-slate-800'
                : 'border-slate-200 text-slate-600 hover:border-slate-400'
            }`}
          >
            <span className="text-lg">{o.icon}</span>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

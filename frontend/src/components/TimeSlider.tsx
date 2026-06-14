import type { TimeBucket } from '../types'

const BUCKETS: { value: TimeBucket; label: string }[] = [
  { value: 'morning', label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'evening', label: 'Evening' },
  { value: 'late_night', label: 'Late Night' },
]

interface Props {
  value: TimeBucket
  onChange: (bucket: TimeBucket) => void
}

export default function TimeSlider({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-1 bg-white/90 backdrop-blur rounded-full px-3 py-1.5 shadow-md">
      {BUCKETS.map((b) => (
        <button
          key={b.value}
          onClick={() => onChange(b.value)}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            value === b.value
              ? 'bg-slate-800 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          {b.label}
        </button>
      ))}
    </div>
  )
}

import { useState } from 'react'
import type { NewsAlert } from '../types'

interface Props {
  alerts: NewsAlert[]
  onAlertClick: (neighborhood: string) => void
}

export default function AlertBanner({ alerts, onAlertClick }: Props) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed || alerts.length === 0) return null

  const top = alerts[0]

  return (
    <div className="absolute top-0 left-0 right-0 z-20 bg-red-600 text-white px-4 py-2 flex items-center justify-between shadow-md">
      <button
        className="text-sm font-medium hover:underline text-left flex-1"
        onClick={() => onAlertClick(top.neighborhood)}
      >
        <span className="mr-2">⚠</span>
        Active situation reported in <strong>{top.neighborhood}</strong> — {top.headline}
      </button>
      <button
        onClick={() => setDismissed(true)}
        className="ml-4 text-white/80 hover:text-white text-lg leading-none"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}

import { useState } from 'react'
import type { TimeBucket, RiskBand } from '../types'
import { compareNeighborhoods } from '../api/client'
import type { CompareResponse } from '../types'

const BAND_COLORS: Record<RiskBand, string> = {
  Low: 'text-green-600',
  Moderate: 'text-yellow-600',
  Elevated: 'text-orange-600',
  High: 'text-red-600',
}

interface Props {
  city: string
  timeBucket: TimeBucket
  onClose: () => void
}

export default function CompareMode({ city, timeBucket, onClose }: Props) {
  const [areaA, setAreaA] = useState('')
  const [areaB, setAreaB] = useState('')
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCompare() {
    if (!areaA || !areaB) return
    setLoading(true)
    setError(null)
    try {
      const data = await compareNeighborhoods(city, [areaA, areaB], timeBucket)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="absolute inset-0 bg-black/50 z-30 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-2xl w-[700px] max-h-[90vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-slate-800">Compare Neighborhoods</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-2xl">×</button>
        </div>

        <div className="flex gap-3 mb-4">
          <input
            value={areaA}
            onChange={(e) => setAreaA(e.target.value)}
            placeholder="First neighborhood"
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm"
          />
          <input
            value={areaB}
            onChange={(e) => setAreaB(e.target.value)}
            placeholder="Second neighborhood"
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm"
          />
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg text-sm font-medium hover:bg-slate-700 disabled:opacity-50"
          >
            {loading ? '…' : 'Compare'}
          </button>
        </div>

        {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

        {result && (
          <>
            <div className="bg-slate-50 rounded-xl p-3 mb-4 text-center">
              <p className="text-sm font-medium text-slate-700">
                Lower risk at this time:{' '}
                <strong className="text-slate-900">{result.lower_risk_at_time || '—'}</strong>
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {result.areas.map((area) => (
                <div key={area.neighborhood} className="border border-slate-200 rounded-xl p-4">
                  <h3 className="font-semibold text-slate-800">{area.neighborhood}</h3>
                  <p className={`text-lg font-bold ${BAND_COLORS[area.risk_band]}`}>
                    {area.risk_band}
                  </p>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">{area.llm_briefing}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

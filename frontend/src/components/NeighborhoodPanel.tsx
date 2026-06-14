import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import type { SafetyResponse, TimeBucket, TravelerType, RiskBand } from '../types'
import TravelerSelect from './TravelerSelect'

const BAND_COLORS: Record<RiskBand, string> = {
  Low: 'bg-green-500',
  Moderate: 'bg-yellow-500',
  Elevated: 'bg-orange-500',
  High: 'bg-red-500',
}

interface Props {
  neighborhoodName: string
  data: SafetyResponse | null
  loading: boolean
  timeBucket: TimeBucket
  travelerType: TravelerType
  onTravelerChange: (t: TravelerType) => void
  onClose: () => void
}

export default function NeighborhoodPanel({
  neighborhoodName,
  data,
  loading,
  travelerType,
  onTravelerChange,
  onClose,
}: Props) {
  const crimeChartData = data
    ? [
        { name: 'Violent',  rate: data.crime_stats.violent_rate },
        { name: 'Theft',    rate: data.crime_stats.theft_rate },
        { name: 'Property', rate: data.crime_stats.property_crime_rate },
      ]
    : []

  return (
    <aside className="absolute right-0 top-0 bottom-0 w-96 bg-white shadow-xl z-10 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b">
        <div>
          <h2 className="text-lg font-bold text-slate-800">
            {data ? data.neighborhood : neighborhoodName}
          </h2>
          {data && (
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-white text-xs font-semibold ${BAND_COLORS[data.risk_band]}`}
              >
                {data.risk_band}
              </span>
              <span className="text-xs text-slate-500">{data.crime_stats.yoy_trend}</span>
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-700 text-2xl leading-none"
          aria-label="Close panel"
        >
          ×
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
        {/* LLM briefing / loading state */}
        {loading ? (
          <div className="space-y-2">
            <div className="h-3 bg-slate-100 rounded animate-pulse w-full" />
            <div className="h-3 bg-slate-100 rounded animate-pulse w-5/6" />
            <div className="h-3 bg-slate-100 rounded animate-pulse w-4/6" />
            <p className="text-xs text-slate-400 mt-2">Generating safety briefing…</p>
          </div>
        ) : data ? (
          <>
            <p className="text-sm text-slate-700 leading-relaxed">{data.llm_briefing}</p>

            {/* Crime breakdown */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Crime breakdown (per 1,000 residents / year)
              </p>
              <ResponsiveContainer width="100%" height={100}>
                <BarChart data={crimeChartData} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <XAxis type="number" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={55} />
                  <Tooltip formatter={(v: number) => `${v.toFixed(2)}/1k`} />
                  <Bar dataKey="rate" fill="#334155" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* News alerts */}
            {data.news_alerts.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  Recent alerts
                </p>
                <ul className="space-y-2">
                  {data.news_alerts.slice(0, 3).map((a) => (
                    <li key={a.id}>
                      <a
                        href={a.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-slate-700 hover:text-blue-600 underline"
                      >
                        {a.headline}
                      </a>
                      <span className="text-xs text-slate-400 ml-1">— {a.source}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Reddit signal */}
            {data.reddit_summary.post_count_30d > 0 && (
              <p className="text-xs text-slate-500">
                {data.reddit_summary.post_count_30d} locals discussed safety in the past 30 days —
                sentiment mostly <strong>{data.reddit_summary.dominant_sentiment}</strong>
              </p>
            )}

            {/* Nearby safer */}
            {data.nearby_safer.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                  Nearby lower-risk areas
                </p>
                <div className="flex gap-2 flex-wrap">
                  {data.nearby_safer.map((n) => (
                    <span
                      key={n}
                      className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded-full border border-green-200"
                    >
                      {n}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <TravelerSelect value={travelerType} onChange={onTravelerChange} />
          </>
        ) : null}
      </div>
    </aside>
  )
}

import { useState } from 'react'
import Map from './components/Map'
import NeighborhoodPanel from './components/NeighborhoodPanel'
import TimeSlider from './components/TimeSlider'
import AlertBanner from './components/AlertBanner'
import CompareMode from './components/CompareMode'
import { useNeighborhood } from './hooks/useNeighborhood'
import { useSafety } from './hooks/useSafety'
import type { TimeBucket, TravelerType } from './types'

const CITY = 'nyc'

export default function App() {
  const [timeBucket, setTimeBucket] = useState<TimeBucket>('evening')
  const [travelerType, setTravelerType] = useState<TravelerType>('solo')
  const [selectedNeighborhood, setSelectedNeighborhood] = useState<string | null>(null)
  const [compareOpen, setCompareOpen] = useState(false)

  // timeBucket passed so the choropleth re-fetches when time changes
  const { geojson } = useNeighborhood(CITY, timeBucket)

  const { data: safetyData, loading: safetyLoading } = useSafety(
    CITY,
    selectedNeighborhood,
    timeBucket,
    travelerType
  )

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-slate-900">
      <AlertBanner alerts={[]} onAlertClick={(name) => setSelectedNeighborhood(name)} />

      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <TimeSlider value={timeBucket} onChange={setTimeBucket} />
      </div>

      <button
        onClick={() => setCompareOpen(true)}
        className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full text-sm font-medium text-slate-700 shadow-md hover:bg-white"
      >
        Compare areas
      </button>

      <Map
        geojson={geojson}
        onNeighborhoodClick={setSelectedNeighborhood}
        highlightedNeighborhood={selectedNeighborhood}
      />

      {/* Panel appears immediately on click; skeleton shows while loading */}
      {selectedNeighborhood && (
        <NeighborhoodPanel
          neighborhoodName={selectedNeighborhood}
          data={safetyData}
          loading={safetyLoading}
          timeBucket={timeBucket}
          travelerType={travelerType}
          onTravelerChange={setTravelerType}
          onClose={() => setSelectedNeighborhood(null)}
        />
      )}

      {compareOpen && (
        <CompareMode
          city={CITY}
          timeBucket={timeBucket}
          onClose={() => setCompareOpen(false)}
        />
      )}
    </div>
  )
}

import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import type { GeoJSONFeatureCollection, RiskBand } from '../types'

const BAND_FILL: Record<RiskBand, string> = {
  Low: '#22c55e',
  Moderate: '#eab308',
  Elevated: '#f97316',
  High: '#ef4444',
}

const MAPTILER_KEY = (import.meta.env.VITE_MAPTILER_KEY as string | undefined) ?? ''

interface Props {
  geojson: GeoJSONFeatureCollection | null
  onNeighborhoodClick: (name: string) => void
  highlightedNeighborhood: string | null
}

export default function Map({ geojson, onNeighborhoodClick, highlightedNeighborhood }: Props) {
  if (!MAPTILER_KEY) {
    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-100 gap-3">
        <p className="text-2xl">🗺️</p>
        <p className="text-slate-600 font-medium">MapTiler key not configured</p>
        <p className="text-slate-400 text-sm">
          Add <code className="bg-slate-200 px-1 rounded">VITE_MAPTILER_KEY=your_key</code> to{' '}
          <code className="bg-slate-200 px-1 rounded">frontend/.env</code> and restart the dev server.
        </p>
      </div>
    )
  }

  return (
    <MapCanvas
      geojson={geojson}
      onNeighborhoodClick={onNeighborhoodClick}
      highlightedNeighborhood={highlightedNeighborhood}
    />
  )
}

// Separate component so hooks are only called when a key is present
function MapCanvas({ geojson, onNeighborhoodClick, highlightedNeighborhood }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: `https://api.maptiler.com/maps/dataviz-light/style.json?key=${MAPTILER_KEY}`,
      center: [-73.9857, 40.7484],
      zoom: 11,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-left')
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !geojson) return

    const onLoad = () => {
      if (map.getSource('neighborhoods')) {
        ;(map.getSource('neighborhoods') as maplibregl.GeoJSONSource).setData(
          geojson as unknown as Parameters<maplibregl.GeoJSONSource['setData']>[0]
        )
        return
      }

      map.addSource('neighborhoods', {
        type: 'geojson',
        data: geojson as unknown as Parameters<maplibregl.GeoJSONSource['setData']>[0],
      })

      map.addLayer({
        id: 'neighborhoods-fill',
        type: 'fill',
        source: 'neighborhoods',
        paint: {
          'fill-color': [
            'match',
            ['get', 'risk_band'],
            'Low',      BAND_FILL.Low,
            'Moderate', BAND_FILL.Moderate,
            'Elevated', BAND_FILL.Elevated,
            'High',     BAND_FILL.High,
            '#94a3b8',
          ],
          'fill-opacity': 0.55,
        },
      })

      map.addLayer({
        id: 'neighborhoods-outline',
        type: 'line',
        source: 'neighborhoods',
        paint: { 'line-color': '#ffffff', 'line-width': 1 },
      })

      map.on('click', 'neighborhoods-fill', (e) => {
        const name = e.features?.[0]?.properties?.name as string | undefined
        if (name) onNeighborhoodClick(name)
      })
      map.on('mouseenter', 'neighborhoods-fill', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'neighborhoods-fill', () => {
        map.getCanvas().style.cursor = ''
      })
    }

    if (map.isStyleLoaded()) onLoad()
    else map.once('load', onLoad)
  }, [geojson, onNeighborhoodClick])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.getLayer('neighborhoods-fill')) return
    map.setPaintProperty('neighborhoods-fill', 'fill-opacity', [
      'case',
      ['==', ['get', 'name'], highlightedNeighborhood ?? ''],
      0.85,
      0.55,
    ])
  }, [highlightedNeighborhood])

  return <div ref={containerRef} className="absolute inset-0" />
}

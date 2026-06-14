import { useState, useEffect } from 'react'
import { getNeighborhoodsGeoJSON } from '../api/client'
import type { GeoJSONFeatureCollection, TimeBucket } from '../types'

interface UseNeighborhoodResult {
  geojson: GeoJSONFeatureCollection | null
  loading: boolean
  error: string | null
}

export function useNeighborhood(city: string, timeBucket: TimeBucket): UseNeighborhoodResult {
  const [geojson, setGeojson] = useState<GeoJSONFeatureCollection | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getNeighborhoodsGeoJSON(city, timeBucket)
      .then((data) => {
        if (!cancelled) setGeojson(data)
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : 'Failed to load neighborhoods')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [city, timeBucket])

  return { geojson, loading, error }
}

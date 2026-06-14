import { useState, useEffect } from 'react'
import { getSafety } from '../api/client'
import type { SafetyResponse, TimeBucket, TravelerType } from '../types'

interface UseSafetyResult {
  data: SafetyResponse | null
  loading: boolean
  error: string | null
}

export function useSafety(
  city: string,
  neighborhood: string | null,
  timeBucket: TimeBucket,
  travelerType: TravelerType
): UseSafetyResult {
  const [data, setData] = useState<SafetyResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!neighborhood) return
    let cancelled = false
    setLoading(true)
    setError(null)
    getSafety(city, neighborhood, timeBucket, travelerType)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? 'Failed to load safety data')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [city, neighborhood, timeBucket, travelerType])

  return { data, loading, error }
}

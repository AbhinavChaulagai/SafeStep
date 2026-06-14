import axios from 'axios'
import type {
  SafetyResponse,
  GeoJSONFeatureCollection,
  NewsAlert,
  CompareResponse,
  TimeBucket,
  TravelerType,
} from '../types'

const api = axios.create({ baseURL: '/api' })

export const getSafety = (
  city: string,
  neighborhood: string,
  timeBucket: TimeBucket,
  travelerType: TravelerType
): Promise<SafetyResponse> =>
  api
    .get<SafetyResponse>(`/safety/${city}/${encodeURIComponent(neighborhood)}`, {
      params: { time_bucket: timeBucket, traveler_type: travelerType },
    })
    .then((r) => r.data)

export const getNeighborhoodsGeoJSON = (
  city: string,
  timeBucket: TimeBucket
): Promise<GeoJSONFeatureCollection> =>
  api
    .get<GeoJSONFeatureCollection>(`/neighborhoods/${city}/geojson`, {
      params: { time_bucket: timeBucket },
    })
    .then((r) => r.data)

export const getCityAlerts = (city: string): Promise<NewsAlert[]> =>
  api.get<NewsAlert[]>(`/alerts/${city}`).then((r) => r.data)

export const compareNeighborhoods = (
  city: string,
  areas: [string, string],
  timeBucket: TimeBucket
): Promise<CompareResponse> =>
  api
    .get<CompareResponse>('/safety/compare', {
      params: { city, areas: areas.join(','), time_bucket: timeBucket },
    })
    .then((r) => r.data)

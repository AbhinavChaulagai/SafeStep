export type TimeBucket = 'morning' | 'afternoon' | 'evening' | 'late_night';
export type RiskBand = 'Low' | 'Moderate' | 'Elevated' | 'High';
export type TravelerType = 'solo' | 'couple' | 'family' | 'nightlife';
export type Sentiment = 'positive' | 'neutral' | 'negative' | 'concerned';

export interface CrimeStats {
  violent_rate: number;
  theft_rate: number;
  property_crime_rate: number;
  top_offense: string;
  yoy_trend: string;
}

export interface NewsAlert {
  id: number;
  neighborhood: string;
  headline: string;
  source: string;
  url: string;
  published_at: string;
  relevance_score: number;
}

export interface RedditSummary {
  summary: string;
  post_count_30d: number;
  dominant_sentiment: Sentiment;
}

export interface DemographicContext {
  population_density: string;
  late_night_activity: string;
  transit_isolation: string;
  tourist_density: string;
}

export interface SafetyResponse {
  neighborhood: string;
  city: string;
  risk_band: RiskBand;
  crime_stats: CrimeStats;
  news_alerts: NewsAlert[];
  reddit_summary: RedditSummary;
  llm_briefing: string;
  nearby_safer: string[];
}

export interface CompareResponse {
  areas: SafetyResponse[];
  lower_risk_at_time: string;
}

export interface NeighborhoodGeoProperties {
  id: number;
  name: string;
  borough: string | null;
  risk_band: RiskBand;
  composite_score: number;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: { type: string; coordinates: unknown };
    properties: NeighborhoodGeoProperties;
  }>;
}

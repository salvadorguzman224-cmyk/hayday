export interface PricePoint {
  report_date: string;
  price_wtavg: number;
  price_low?: number | null;
  price_high?: number | null;
  volume_tons?: number | null;
}

export interface Forecast {
  id: number;
  generated_at: string;
  target_date: string;
  region: string;
  hay_type: string;
  grade: string;
  horizon_weeks: number;
  price_predicted: number;
  price_low_80?: number | null;
  price_high_80?: number | null;
  price_low_95?: number | null;
  price_high_95?: number | null;
  model_version?: string | null;
  feature_importance?: Record<string, number> | null;
  mape_estimate?: number | null;
}

export interface Alert {
  id: number;
  user_email: string;
  region: string;
  hay_type: string;
  grade: string;
  threshold_price: number;
  direction: "above" | "below";
  is_active: boolean;
  created_at: string;
  last_triggered_at?: string | null;
}

export interface LatestPrice {
  region: string;
  hay_type: string;
  grade: string;
  report_date: string;
  price_wtavg: number;
  price_low?: number | null;
  price_high?: number | null;
}

export interface PriceSummary {
  region: string;
  hay_type: string;
  grade: string;
  current_price: number | null;
  vs_4_weeks: { absolute: number; pct: number } | null;
  vs_1_year: { absolute: number; pct: number } | null;
}

export interface MetaOption {
  value: string;
  label: string;
}

export interface Meta {
  regions: MetaOption[];
  hay_types: string[];
  grades: string[];
}

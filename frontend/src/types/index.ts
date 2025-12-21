// Type definitions for GPU Market application

export interface GPU {
  id: number;
  model: string;
  price: number;
  source: string;
  created_at?: string;
}

export interface PriceStats {
  min: number;
  max: number;
  median: number;
  mean: number;
  count: number;
  percentile_25?: number;
}

export interface ModelStats {
  [model: string]: PriceStats;
}

export interface SummaryStats {
  total_listings: number;
  unique_models: number;
  avg_price: number;
  min_price?: number;
  max_price?: number;
}

export interface ValueAnalysis {
  model: string;
  fps: number;
  price: number;
  fps_per_lv: number;
}

export interface WebSocketMessage {
  type: 'connection' | 'scrape_started' | 'scrape_completed' | 'stats_update' | 'price_drop';
  data?: any;
  message?: string;
  timestamp?: number;
}

export interface PriceDropAlert {
  model: string;
  old_price: number;
  new_price: number;
  drop_percent: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationParams {
  page?: number;
  size?: number;
}

export interface FilterParams {
  model?: string;
  min_price?: number;
  max_price?: number;
  source?: string;
}

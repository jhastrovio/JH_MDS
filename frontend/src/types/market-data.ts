// Market data types matching the backend API

export interface Tick {
  symbol: string;
  bid: number;
  ask: number;
  timestamp: string;
}

export interface PriceResponse {
  symbol: string;
  price: number;
  timestamp: string;
}

export interface MarketData extends Tick {
  change?: number;
  changePercent?: number;
  dayHigh?: number;
  dayLow?: number;
  volume?: number;
  sparklineData?: number[];
}

export interface DailyMover {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  category: 'fx' | 'rates' | 'indices';
}

export interface SnapshotRequest {
  symbols: string[];
}

export interface SnapshotResponse {
  detail: string;
  path: string;
}

// WebSocket message types
export interface WSMessage {
  type: 'tick' | 'price' | 'error' | 'connected' | 'disconnected';
  data?: any;
  symbol?: string;
  error?: string;
}

// UI state types
export interface ConnectionStatus {
  connected: boolean;
  lastUpdate?: Date;
  reconnecting?: boolean;
}

export interface MarketSummary {
  totalSymbols: number;
  activeStreams: number;
  lastUpdate: Date;
  dailyMovers: DailyMover[];
}

// Asset categories for the dashboard
export const FX_MAJORS = [
  'EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 
  'USD-CHF', 'USD-CAD', 'NZD-USD'
];

export const RATES = [
  'UST-2Y', 'UST-10Y', 'UST-30Y', 
  'BUND-10Y', 'GILT-10Y', 'JGB-10Y'
];

export const INDICES = [
  'SPX', 'NDX', 'DAX', 'FTSE', 'NIKKEI', 'HSI'
]; 
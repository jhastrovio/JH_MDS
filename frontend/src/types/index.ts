export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastUpdated?: Date;
}

// re-export MarketSummary so all types are available from '@/types'
export type { MarketSummary } from './market-data';
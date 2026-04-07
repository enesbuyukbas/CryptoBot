import { Signal } from './signal.model';

export interface SignalFilter {
  timeframe: '15m' | '1h' | '4h' | '1d';
  symbol?: string;
  direction?: 'BUY' | 'SELL';
  minStrength?: number;
  page: number;
  pageSize: number;
}

export interface SignalPagedResponse {
  items: Signal[];
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  timeframe: string;
}


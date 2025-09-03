export interface MetricCard {
  key: 'fng' | 'marketCap' | 'altseason' | 'avgRsi';
  label: string;
  value: number;
  unit?: string | null;
  change24h?: number | null;
  updatedAt: string; // ISO
}

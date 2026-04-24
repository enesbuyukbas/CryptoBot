export interface Signal {
  symbol: string;
  timeframe: string;
  direction: string;
  strength: number;
  reason: string[];
  price: number;
  firstPrice?: number | null;   // sinyalin ilk açıldığı fiyat (eski EC2 sinyallerinde yok)
  stopLoss: number;
  targetPrice: number;
  riskReward: number;
  riskAmount: number;
  rewardAmount: number;
  atr: number;
  openedAt: string; // ISO datetime
  createdAt: string;
  updatedAt: string;
  tpHit?: boolean | null;
  slHit?: boolean | null;
  outcomePrice?: number | null;
}

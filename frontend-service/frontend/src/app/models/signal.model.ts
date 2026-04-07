export interface Signal {
  symbol: string;
  timeframe: string;
  direction: string;
  strength: number;
  reason: string[];
  price: number;
  stopLoss: number;
  targetPrice: number;
  riskReward: number;
  riskAmount: number;
  rewardAmount: number;
  atr: number;
  openedAt: string; // ISO datetime
  createdAt: string;
  updatedAt: string;
}

import { Component, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricsService } from '../../services/metrics.service';
import { MetricCard } from '../../models/metric-card.model';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hero.component.html',
  styleUrls: ['./hero.component.css']
})
export class HeroComponent implements OnDestroy {
  // 0 = metin sayfası, 1 = kartlar sayfası
  current = signal<0 | 1>(0);
  direction = signal<'left' | 'right' | null>(null); // null = ilk yükleme, animasyon yok

  // FNG kart verisi (ilk kart)
  fng = signal<MetricCard | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);

  // Market Cap verisi
  market= signal<MetricCard | null>(null);
  loadingMcap = signal(true);
  errorMcap = signal<string | null>(null);

  // Altseason verisi
  alt = signal<MetricCard | null>(null);
  loadingAlt = signal(true);
  errorAlt = signal<string | null>(null);

  // Average RSI verisi
  avgRsi = signal<MetricCard | null>(null);
  loadingAvgRsi = signal(true);
  errorAvgRsi = signal<string | null>(null);

  // Per-card flip state — her kart bağımsız
  flippedCards = signal<Record<string, boolean>>({});

  // Market cap bar chart verileri (veri gelince change24h'ye göre güncellenir)
  mcapBars = signal<number[]>([0.55, 0.58, 0.61, 0.59, 0.63, 0.66, 0.65]);

  // Refresh interval ID'leri (cleanup için)
  private timers: ReturnType<typeof setInterval>[] = [];

  // Tüm metrikler günde 1 kez güncellenir — yük minimumda
  private static readonly REFRESH = 24 * 60 * 60 * 1000; // 24 saat

  constructor(private metrics: MetricsService) {
    // İlk yükleme: kademeli (CoinGecko rate-limit koruması)
    this.loadFng();
    this.loadMarket();
    setTimeout(() => this.loadAltseason(), 3000);
    setTimeout(() => this.loadAvgRsi(), 6000);

    // 24 saatte bir tümünü yenile (kademeli)
    this.timers.push(setInterval(() => {
      this.loadFng();
      this.loadMarket();
      setTimeout(() => this.loadAltseason(), 3000);
      setTimeout(() => this.loadAvgRsi(), 6000);
    }, HeroComponent.REFRESH));
  }

  ngOnDestroy() {
    this.timers.forEach(t => clearInterval(t));
  }

  private loadFng() {
    this.loading.set(true);
    this.metrics.getFng().subscribe({
      next: d => { this.fng.set(d); this.loading.set(false); this.error.set(null); },
      error: _ => { this.error.set('Veri alınamadı'); this.loading.set(false); }
    });
  }

  private loadMarket() {
    this.loadingMcap.set(true);
    this.metrics.getMarketCap().subscribe({
      next: d => {
        this.market.set(d);
        this.mcapBars.set(this.generateBars(d.change24h ?? 0));
        this.loadingMcap.set(false);
        this.errorMcap.set(null);
      },
      error: _ => { this.errorMcap.set('Veri alınamadı'); this.loadingMcap.set(false); }
    });
  }

  private loadAltseason() {
    this.loadingAlt.set(true);
    this.metrics.getAltseason().subscribe({
      next: d => { this.alt.set(d); this.loadingAlt.set(false); this.errorAlt.set(null); },
      error: (err) => { console.error(err); this.errorAlt.set('Veri alınamadı'); this.loadingAlt.set(false); }
    });
  }

  private loadAvgRsi(){
  this.loadingAvgRsi.set(true);
  this.metrics.getAverageRsi().subscribe({
    next: d => { this.avgRsi.set(d); this.loadingAvgRsi.set(false); this.errorAvgRsi.set(null); },
    error: e => { console.error(e); this.errorAvgRsi.set('Veri alınamadı'); this.loadingAvgRsi.set(false); }
  });
}

  // ==================== COLOR TOKENS ====================
  // Anlamsal renk haritası — chart zone renkleriyle birebir eşleşir
  private static readonly ALT_TOKENS = {
    altseason:    { bg: '#7c3aed', text: '#fff', label: 'Altseason'     }, // mor — zone rengiyle uyumlu
    neutral:      { bg: '#4b5563', text: '#fff', label: 'Neutral'       }, // nötr gri
    bitcoin:      { bg: '#92400e', text: '#fff', label: 'Bitcoin Season'}, // kahve — zone rengiyle uyumlu
  } as const;

  private static readonly RSI_TOKENS = {
    overbought: { bg: '#b91c1c', text: '#fff', label: 'Overbought' }, // kırmızı — zone rengiyle uyumlu
    neutral:    { bg: '#4b5563', text: '#fff', label: 'Neutral'    }, // nötr gri
    oversold:   { bg: '#0284c7', text: '#fff', label: 'Oversold'   }, // mavi — zone rengiyle uyumlu
  } as const;

  private static readonly FNG_TOKENS = {
    extremeFear:  { bg: '#b91c1c', text: '#fff', label: 'Extreme Fear'  },
    fear:         { bg: '#c2410c', text: '#fff', label: 'Fear'          },
    neutral:      { bg: '#a16207', text: '#fff', label: 'Neutral'       },
    greed:        { bg: '#15803d', text: '#fff', label: 'Greed'         },
    extremeGreed: { bg: '#166534', text: '#fff', label: 'Extreme Greed' },
  } as const;

  private getAltToken(v?: number | null) {
    const T = HeroComponent.ALT_TOKENS;
    if (v == null)  return T.neutral;
    if (v >= 75)    return T.altseason;
    if (v <= 25)    return T.bitcoin;
    return T.neutral;
  }

  private getRsiToken(v?: number | null) {
    const T = HeroComponent.RSI_TOKENS;
    if (v == null)  return T.neutral;
    if (v >= 70)    return T.overbought;
    if (v <= 30)    return T.oversold;
    return T.neutral;
  }

  private getFngToken(v?: number | null) {
    const T = HeroComponent.FNG_TOKENS;
    if (v == null)  return T.neutral;
    if (v <= 25)    return T.extremeFear;
    if (v <= 45)    return T.fear;
    if (v <= 55)    return T.neutral;
    if (v <= 75)    return T.greed;
    return T.extremeGreed;
  }

  // Public helpers tüketen template'e açık
  badgeText(v?: number | null): string  { return this.getAltToken(v).label; }
  badgeColor(v?: number | null): string { return this.getAltToken(v).bg;    }

  go(idx: 0 | 1) {
    if (idx === this.current()) return;
    this.direction.set(idx > this.current() ? 'right' : 'left');
    this.current.set(idx);
  }
  // Sağ ok: silindir sola döner → mevcut sola çıkar, yeni sağdan gelir
  next() { this.direction.set('left'); this.current.set(this.current() === 0 ? 1 : 0); }
  // Sol ok: silindir sağa döner → mevcut sağa çıkar, yeni soldan gelir
  prev() { this.direction.set('right'); this.current.set(this.current() === 0 ? 1 : 0); }

  toggleFlip(card: string): void {
    this.flippedCards.update(s => ({ ...s, [card]: !s[card] }));
  }

  // RSI status label — token'dan gelir, zone rengiyle uyumlu
  getRsiLabel(v?: number | null): string    { return this.getRsiToken(v).label; }
  getRsiBgColor(v?: number | null): string  { return this.getRsiToken(v).bg;    }

  // FNG badge helpers — gauge segment rengiyle uyumlu
  getFngBadgeLabel(v?: number | null): string   { return this.getFngToken(v).label; }
  getFngBadgeColor(v?: number | null): string   { return this.getFngToken(v).bg;    }


  //basit kısaltma helper'ı (1.2K / 3.4M / 1.1B / 2.0T)
  short(n?: number | null): string {
    if (n == null) return '-';
    const abs = Math.abs(n);
    const sign = n < 0 ? '-' : '';
    if (abs >= 1e12) return sign + (abs / 1e12).toFixed(2) + 'T';
    if (abs >= 1e9)  return sign + (abs / 1e9 ).toFixed(2) + 'B';
    if (abs >= 1e6)  return sign + (abs / 1e6 ).toFixed(2) + 'M';
    if (abs >= 1e3)  return sign + (abs / 1e3 ).toFixed(2) + 'K';
    return sign + abs.toFixed(0);
  }

  // ==================== SVG HELPER METHODS ====================

  /**
   * Calculate needle rotation for FNG gauge (0-100 → -90 to +90 degrees)
   * 0 = left (-90°), 50 = middle (0°), 100 = right (+90°)
   */
  calculateFngNeedle(value?: number | null): number {
    if (value == null) return -90;
    const normalized = Math.max(0, Math.min(100, value));
    return -90 + (normalized * 1.8); // 0-100 → -90 to +90 (semicircle from left to right)
  }

  /**
   * Get Fear & Greed label based on value — token ile senkronize
   */
  getFngLabel(value?: number | null): string {
    return this.getFngToken(value).label;
  }

  /**
   * Get progress dot color based on altseason value — zone rengiyle uyumlu
   */
  getAltProgressColor(value?: number | null): string {
    return this.getAltToken(value).bg;
  }

  /**
   * Generate 7 bar heights for market cap chart (0-100 scale)
   * Last bar represents current value, others are simulated previous values
   */
  getMcapBars(): number[] {
    return this.mcapBars();
  }

  /**
   * change24h'ye göre yönsel olarak doğru bar grafiği üret.
   * Pozitif → barlar yükseliş trendi, Negatif → düşüş trendi.
   * Son bar her zaman güncel durumu temsil eder.
   */
  private generateBars(change24h: number = 0): number[] {
    const count = 7;
    const bars: number[] = [];

    // change24h'yi -10..+10 aralığında normalize et (aşırı değerleri sınırla)
    const clamped = Math.max(-10, Math.min(10, change24h));
    // Eğim faktörü: her bar arasındaki fark (0.02 ~ 0.06 arası)
    const slope = (clamped / 100) * 0.5;

    // Son barın yüksekliği (0.4 ~ 0.95 arası, change'e göre)
    const lastBar = 0.65 + (clamped / 10) * 0.25;
    const clampedLast = Math.max(0.3, Math.min(0.95, lastBar));

    for (let i = 0; i < count; i++) {
      // Son bardan geriye doğru hesapla
      const stepsFromEnd = count - 1 - i;
      const base = clampedLast - (slope * stepsFromEnd);
      // Küçük deterministik varyasyon ekle (seed: index)
      const jitter = ((i * 7 + 3) % 5 - 2) * 0.03;
      bars.push(Math.max(0.15, Math.min(1, base + jitter)));
    }

    return bars;
  }

  /**
   * Calculate progress bar position for Altseason (0-100 scale, maps to 0-200 SVG units)
   */
  calculateAltProgress(value?: number | null): number {
    if (value == null) return 100;
    const normalized = Math.max(0, Math.min(100, value));
    return (normalized / 100) * 200;
  }

  /**
   * Calculate RSI cursor position (0-100 scale, maps to 0-200 SVG units)
   */
  calculateRsiPosition(value?: number | null): number {
    if (value == null) return 100;
    const normalized = Math.max(0, Math.min(100, value));
    return (normalized / 100) * 200;
  }
}

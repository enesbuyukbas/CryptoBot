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

  badgeText(v?: number | null): 'Altseason' | 'Bitcoin Season' | 'Neutral' {
    if (v == null) return 'Neutral';
    if (v >= 75) return 'Altseason';
    if (v <= 25) return 'Bitcoin Season';
    return 'Neutral';
  }

  badgeColor(v?: number | null): string {
    if (v == null) return '#6b7280';      // gri
    if (v >= 75) return '#16a34a';        // yeşil
    if (v <= 25) return '#b42318';        // kırmızı
    return '#6b7280';
  }

  go(idx: 0 | 1) {
    if (idx === this.current()) return;
    this.direction.set(idx > this.current() ? 'right' : 'left');
    this.current.set(idx);
  }
  // Sağ ok: silindir sola döner → mevcut sola çıkar, yeni sağdan gelir
  next() { this.direction.set('left'); this.current.set(this.current() === 0 ? 1 : 0); }
  // Sol ok: silindir sağa döner → mevcut sağa çıkar, yeni soldan gelir
  prev() { this.direction.set('right'); this.current.set(this.current() === 0 ? 1 : 0); }

  // RSI status label
  getRsiLabel(v?: number | null): string {
    if (v == null) return 'Neutral';
    if (v >= 70) return 'Overbought';
    if (v <= 30) return 'Oversold';
    return 'Neutral';
  }

  // RSI background color
  getRsiBgColor(v?: number | null): string {
    if (v == null) return '#6b7280';       // gray
    if (v >= 70) return '#b45309';         // orange (overbought)
    if (v <= 30) return '#0ea5e9';         // cyan (oversold)
    return '#6b7280';                      // gray (neutral)
  }


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
   * Get Fear & Greed label based on value
   */
  getFngLabel(value?: number | null): string {
    if (value == null) return 'Neutral';
    if (value <= 25) return 'Extreme Fear';
    if (value <= 45) return 'Fear';
    if (value <= 55) return 'Neutral';
    if (value <= 75) return 'Greed';
    return 'Extreme Greed';
  }

  /**
   * Get progress dot color based on altseason value
   */
  getAltProgressColor(value?: number | null): string {
    if (value == null) return '#6b7280';
    if (value >= 75) return '#8b5cf6';  // Purple - Altcoin Season
    if (value >= 25) return '#eab308';  // Yellow - Mixed
    return '#f97316';                    // Orange - Bitcoin dominant
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

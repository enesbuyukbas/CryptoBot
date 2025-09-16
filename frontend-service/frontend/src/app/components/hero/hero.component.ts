import { Component, signal } from '@angular/core';
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
export class HeroComponent {
  // 0 = metin sayfası, 1 = kartlar sayfası
  current = signal<0 | 1>(0);

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


  constructor(private metrics: MetricsService) {
    this.loadAll();
    setInterval(() => this.loadAll(), 60000); // 60sn de bir yenile
  }

  private loadAll() {
    this.loadFng();
    this.loadMarket();
    this.loadAltseason();
    this.loadAvgRsi();
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
      next: d => { this.market.set(d); this.loadingMcap.set(false); this.errorMcap.set(null); },
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

  go(idx: 0 | 1) { this.current.set(idx); }
  next() { this.current.set(this.current() === 0 ? 1 : 0); }
  prev() { this.current.set(this.current() === 0 ? 1 : 0); }


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

}

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

  constructor(private metrics: MetricsService) {
    this.load();
    setInterval(() => this.load(), 60000);
  }

  private load() {
    this.loading.set(true);
    this.metrics.getFng().subscribe({
      next: d => { this.fng.set(d); this.loading.set(false); this.error.set(null); },
      error: _ => { this.error.set('Veri alınamadı'); this.loading.set(false); }
    });
  }

  go(idx: 0 | 1) { this.current.set(idx); }
  next() { this.current.set(this.current() === 0 ? 1 : 0); }
  prev() { this.current.set(this.current() === 0 ? 1 : 0); }
}

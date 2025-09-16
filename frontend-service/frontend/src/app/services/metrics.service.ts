import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MetricCard } from '../models/metric-card.model';

@Injectable({ providedIn: 'root' })
export class MetricsService {
  private http = inject(HttpClient);
  private base = '/api/metrics'; // proxy'li veya aynı origin

  getFng(): Observable<MetricCard> {
    return this.http.get<MetricCard>(`${this.base}/fng`);
  }

  getMarketCap() {
    return this.http.get<MetricCard>(`${this.base}/market-cap`);
  }

  getAltseason() {
    return this.http.get<MetricCard>(`${this.base}/altseason`);

  }

  // sıradaki sprintlerde:

  // getAvgRsi(params) { ... }
}


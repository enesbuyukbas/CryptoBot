import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Signal } from '../models/signal.model';
import { SignalFilter, SignalPagedResponse } from '../models/signal-filter.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = `${environment.apiBaseUrl}/api/signals`;

  constructor(private http: HttpClient) {}

  getSignals(): Observable<Signal[]> {
    return this.http.get<Signal[]>(`${this.apiUrl}`);
  }

  getTopSignals(): Observable<Signal[]> {
    return this.http.get<Signal[]>(`${this.apiUrl}/top`);
  }

  getFilteredSignals(filter: SignalFilter): Observable<SignalPagedResponse> {
    let url = `${this.apiUrl}/filtered?timeframe=${filter.timeframe}&page=${filter.page}&pageSize=${filter.pageSize}`;

    if (filter.symbol) {
      url += `&symbol=${encodeURIComponent(filter.symbol)}`;
    }

    if (filter.direction) {
      url += `&direction=${filter.direction}`;
    }

    if (filter.minStrength !== undefined && filter.minStrength !== null) {
      url += `&minStrength=${filter.minStrength}`;
    }

    if (filter.status) {
      url += `&status=${filter.status}`;
    }

    return this.http.get<SignalPagedResponse>(url);
  }
}


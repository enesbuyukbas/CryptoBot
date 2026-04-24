import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';

const CACHE_TTL_MS = 30_000; // 30 saniye

@Injectable({
  providedIn: 'root'
})
export class BinancePriceService {
  private readonly BASE_URL = 'https://api.binance.com/api/v3/ticker/price';

  private cache: Map<string, number> = new Map();
  private cacheTime: number = 0;
  private cachedSymbolsKey: string = '';

  constructor(private http: HttpClient) {}

  /**
   * Verilen sembollerin güncel fiyatlarını Binance'dan çeker.
   * 30 saniye boyunca aynı sembol seti için cache'den döner.
   */
  getPrices(symbols: string[]): Observable<Map<string, number>> {
    if (!symbols.length) {
      return of(new Map());
    }

    const key = [...symbols].sort().join(',');
    const now = Date.now();

    // Cache geçerliyse direkt döndür
    if (key === this.cachedSymbolsKey && now - this.cacheTime < CACHE_TTL_MS) {
      return of(new Map(this.cache));
    }

    const symbolsParam = JSON.stringify(symbols);
    const url = `${this.BASE_URL}?symbols=${encodeURIComponent(symbolsParam)}`;

    return this.http.get<{ symbol: string; price: string }[]>(url).pipe(
      tap(data => {
        this.cache = new Map(data.map(item => [item.symbol, parseFloat(item.price)]));
        this.cacheTime = Date.now();
        this.cachedSymbolsKey = key;
      }),
      map(() => new Map(this.cache)),
      catchError(() => of(new Map<string, number>()))
    );
  }
}

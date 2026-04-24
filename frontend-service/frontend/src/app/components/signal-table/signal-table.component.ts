import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SignalService } from '../../services/signal.service';
import { BinancePriceService } from '../../services/binance-price.service';
import { Signal } from '../../models/signal.model';
import { SignalFilter, SignalPagedResponse } from '../../models/signal-filter.model';

@Component({
  selector: 'app-signal-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signal-table.component.html',
  styleUrls: ['./signal-table.component.css']
})
export class SignalTableComponent implements OnInit, OnDestroy {
  // Top signals section (now derived from filtered results)
  top3Signals: Signal[] = [];

  // Main table data
  signals: Signal[] = [];
  pagedResponse: SignalPagedResponse | null = null;

  // All signals for multi-timeframe availability check
  allTimeframeSignals: Map<string, Signal[]> = new Map();

  // Filter state
  selectedTimeframe: '15m' | '1h' | '4h' | '1d' = '15m';
  symbolSearch: string = '';
  selectedDirection: 'BUY' | 'SELL' | '' = '';
  minStrength: number = 0;
  minStrengthPresets = [0, 60, 70, 80, 90]; // Quick filter presets
  currentPage: number = 1;
  pageSize: number = 10;

  // Loading state
  isLoading: boolean = false;

  // Binance güncel fiyatları
  currentPrices: Map<string, number> = new Map();
  private priceRefreshInterval: ReturnType<typeof setInterval> | null = null;
  private readonly PRICE_REFRESH_MS = 30_000;

  // Popover state for reasons display
  openPopoverId: string | null = null;
  popoverPosition: { top: number; left: number } | null = null;
  private scrollListener: (() => void) | null = null;

  private signalService = inject(SignalService);
  private binancePriceService = inject(BinancePriceService);

  ngOnInit() {
    this.loadFilteredSignals();
    this.loadMultiTimeframeData();
  }

  ngOnDestroy(): void {
    if (this.priceRefreshInterval) {
      clearInterval(this.priceRefreshInterval);
    }
  }

  loadMultiTimeframeData(): void {
    // Load all timeframes to show availability badges on symbols
    const timeframes: Array<'15m' | '1h' | '4h' | '1d'> = ['15m', '1h', '4h', '1d'];
    timeframes.forEach(tf => {
      const filter: SignalFilter = {
        timeframe: tf,
        page: 1,
        pageSize: 1000, // Get all available signals for this timeframe
        symbol: this.symbolSearch || undefined,
        direction: this.selectedDirection ? (this.selectedDirection as 'BUY' | 'SELL') : undefined
      };
      this.signalService.getFilteredSignals(filter).subscribe({
        next: (data) => {
          this.allTimeframeSignals.set(tf, data.items ?? []);
        },
        error: (err) => {
          console.error(`Error loading ${tf} signals:`, err);
          this.allTimeframeSignals.set(tf, []);
        }
      });
    });
  }

  loadFilteredSignals(): void {
    this.isLoading = true;

    const filter: SignalFilter = {
      timeframe: this.selectedTimeframe,
      symbol: this.symbolSearch || undefined,
      direction: this.selectedDirection ? (this.selectedDirection as 'BUY' | 'SELL') : undefined,
      minStrength: this.minStrength > 0 ? this.minStrength : undefined,
      page: this.currentPage,
      pageSize: this.pageSize
    };

    this.signalService.getFilteredSignals(filter).subscribe({
      next: (data) => {
        this.pagedResponse = data;
        this.signals = data.items ?? [];
        this.isLoading = false;
        // Sayfa/filtre değişse bile yeni sembollerin fiyatını çek
        this.refreshPrices();
        // İlk yüklemede interval'i başlat
        if (!this.priceRefreshInterval) {
          this.priceRefreshInterval = setInterval(() => this.refreshPrices(), this.PRICE_REFRESH_MS);
        }
      },
      error: (err) => {
        console.error('Error loading filtered signals:', err);
        this.signals = [];
        this.pagedResponse = null;
        this.isLoading = false;
      }
    });

    // Load top 3 from full filtered result (independent of pagination)
    // Query page 1 with large pageSize to get all matching signals
    const topFilter: SignalFilter = {
      timeframe: this.selectedTimeframe,
      symbol: this.symbolSearch || undefined,
      direction: this.selectedDirection ? (this.selectedDirection as 'BUY' | 'SELL') : undefined,
      minStrength: this.minStrength > 0 ? this.minStrength : undefined,
      page: 1,
      pageSize: 1000 // Get many items to find true top 3
    };

    this.signalService.getFilteredSignals(topFilter).subscribe({
      next: (data) => {
        this.updateTop3Signals(data.items ?? []);
      },
      error: (err) => {
        console.error('Error loading top signals:', err);
        this.top3Signals = [];
      }
    });
  }

  updateTop3Signals(allFilteredItems: Signal[]): void {
    // Derive top 3 from FULL filtered result (before pagination)
    // Receives all items matching current filters from first large page request
    if (!allFilteredItems || allFilteredItems.length === 0) {
      this.top3Signals = [];
      return;
    }
    // Sort by strength desc, then openedAt desc (same as backend logic)
    const sorted = [...allFilteredItems]
      .sort((a, b) => {
        const strengthDiff = b.strength - a.strength;
        if (strengthDiff !== 0) return strengthDiff;
        return new Date(b.openedAt).getTime() - new Date(a.openedAt).getTime();
      })
      .slice(0, 3);
    this.top3Signals = sorted;
  }

  onTimeframeChange(timeframe: '15m' | '1h' | '4h' | '1d'): void {
    this.selectedTimeframe = timeframe;
    this.currentPage = 1; // Reset to first page
    this.loadFilteredSignals();
  }

  onSymbolSearchChange(): void {
    this.currentPage = 1;
    this.loadFilteredSignals();
  }

  onDirectionChange(): void {
    this.currentPage = 1;
    this.loadFilteredSignals();
  }

  onStrengthChange(): void {
    this.currentPage = 1;
    this.loadFilteredSignals();
  }

  onStrengthPresetChange(preset: number): void {
    this.minStrength = preset;
    this.currentPage = 1;
    this.loadFilteredSignals();
  }

  onPageChange(newPage: number): void {
    if (newPage >= 1 && (this.pagedResponse?.totalPages || 0) >= newPage) {
      this.currentPage = newPage;
      this.loadFilteredSignals();
    }
  }

  formatPrice(value: number): string {
    if (value === 0) return '0.00000';
    if (value < 0.00001) return value.toFixed(8);
    return value.toFixed(5);
  }

  formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: '2-digit',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  }

  formatRiskReward(value: number): string {
    return value.toFixed(2);
  }

  getDirectionLabel(direction: string): string {
    // Map BUY->LONG, SELL->SHORT for display
    return direction === 'BUY' ? 'LONG' : direction === 'SELL' ? 'SHORT' : direction;
  }

  // Reason labels mapping (English code → English label)
  private reasonLabels: { [key: string]: string } = {
    // Trend
    'TREND_PERFECT': 'Perfect Trend',
    'TREND_UP': 'Uptrend',
    'TREND_DOWN': 'Downtrend',
    'TREND_STRONG': 'Strong Trend',
    'TREND_WEAK': 'Weak Trend',

    // Momentum
    'MOMENTUM_STRONG': 'Strong Momentum',
    'MOMENTUM_GOOD': 'Good Momentum',
    'MOMENTUM_WEAK': 'Weak Momentum',
    'MOMENTUM_BULLISH': 'Bullish Momentum',
    'MOMENTUM_BEARISH': 'Bearish Momentum',

    // ADX
    'ADX_VERY_STRONG': 'Very Strong',
    'ADX_STRONG': 'Strong Signal',
    'ADX_MODERATE': 'Moderate Signal',
    'ADX_WEAK': 'Weak Signal',

    // RSI
    'RSI_OPTIMAL': 'Optimal RSI',
    'RSI_HEALTHY': 'Healthy RSI',
    'RSI_OVERSOLD': 'Oversold',
    'RSI_OVERBOUGHT': 'Overbought',
    'RSI_NEUTRAL': 'Neutral RSI',

    // MACD
    'MACD_BULLISH': 'Bullish MACD',
    'MACD_BEARISH': 'Bearish MACD',
    'MACD_CROSS_UP': 'MACD Crossover Up',
    'MACD_CROSS_DOWN': 'MACD Crossover Down',

    // Volume
    'VOLUME_HIGH': 'High Volume',
    'VOLUME_LOW': 'Low Volume',
    'VOLUME_SPIKE': 'Volume Spike'
  };

  // Reason color mapping by category
  private reasonColors: { [key: string]: { bg: string; color: string; border: string } } = {
    TREND: {
      bg: 'rgba(0, 211, 149, 0.12)',
      color: '#00d395',
      border: 'rgba(0, 211, 149, 0.25)'
    },
    MOMENTUM: {
      bg: 'rgba(139, 92, 246, 0.12)',
      color: '#a78bfa',
      border: 'rgba(139, 92, 246, 0.25)'
    },
    ADX: {
      bg: 'rgba(251, 146, 60, 0.12)',
      color: '#fb923c',
      border: 'rgba(251, 146, 60, 0.25)'
    },
    RSI: {
      bg: 'rgba(250, 204, 21, 0.12)',
      color: '#fbbf24',
      border: 'rgba(250, 204, 21, 0.25)'
    },
    MACD: {
      bg: 'rgba(56, 189, 248, 0.12)',
      color: '#38bdf8',
      border: 'rgba(56, 189, 248, 0.25)'
    },
    VOLUME: {
      bg: 'rgba(244, 114, 182, 0.12)',
      color: '#f472b6',
      border: 'rgba(244, 114, 182, 0.25)'
    }
  };

  getDirectionClass(direction: string): string {
    if (direction === 'BUY') return 'badge-success';
    if (direction === 'SELL') return 'badge-danger';
    return 'badge-secondary';
  }

  // Get Turkish label for reason code with fallback
  getReasonLabel(reason: string): string {
    if (this.reasonLabels[reason]) {
      return this.reasonLabels[reason];
    }
    // Fallback: replace underscores with spaces and capitalize
    return reason
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  // Get category of reason (TREND, MOMENTUM, ADX, RSI, MACD, VOLUME)
  getReasonCategory(reason: string): string {
    if (reason.startsWith('TREND')) return 'TREND';
    if (reason.startsWith('MOMENTUM')) return 'MOMENTUM';
    if (reason.startsWith('ADX')) return 'ADX';
    if (reason.startsWith('RSI')) return 'RSI';
    if (reason.startsWith('MACD')) return 'MACD';
    if (reason.startsWith('VOLUME')) return 'VOLUME';
    return 'MACD'; // default
  }

  // Get CSS class for reason badge based on category
  getReasonBadgeClass(reason: string): string {
    const category = this.getReasonCategory(reason);
    return `reason-badge-${category.toLowerCase()}`;
  }

  // Get inline styles for reason badge
  getReasonBadgeStyle(reason: string) {
    const category = this.getReasonCategory(reason);
    const colors = this.reasonColors[category];
    return {
      background: colors.bg,
      color: colors.color,
      borderColor: colors.border
    };
  }

  getReasonSummary(reasons: string[]): string {
    if (!reasons || reasons.length === 0) return '-';
    if (reasons.length === 1) return this.getReasonLabel(reasons[0]);
    return `${this.getReasonLabel(reasons[0])} +${reasons.length - 1}`;
  }

  getReasonTooltip(reasons: string[]): string {
    return reasons.join(', ');
  }

  getRelativeFreshness(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }

  getActiveTimeframes(symbol: string): string[] {
    const active: string[] = [];
    const timeframes: Array<'15m' | '1h' | '4h' | '1d'> = ['15m', '1h', '4h', '1d'];
    timeframes.forEach(tf => {
      if (tf !== this.selectedTimeframe) {
        const signals = this.allTimeframeSignals.get(tf) ?? [];
        if (signals.some(s => s.symbol === symbol)) {
          active.push(tf);
        }
      }
    });
    return active;
  }

  /**
   * Desktop pagination — always returns exactly 7 items when totalPages > 7.
   * Layout stays stable as the user navigates.
   *
   *  cur ≤ 4        → [1, 2, 3, 4, 5, -1, total]
   *  cur ≥ total-3  → [1, -1, t-4, t-3, t-2, t-1, total]
   *  middle         → [1, -1, cur-1, cur, cur+1, -1, total]
   */
  getPageNumbers(): number[] {
    if (!this.pagedResponse) return [1];
    const total = this.pagedResponse.totalPages;
    const cur   = this.currentPage;
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    if (cur <= 4)          return [1, 2, 3, 4, 5, -1, total];
    if (cur >= total - 3)  return [1, -1, total - 4, total - 3, total - 2, total - 1, total];
    return [1, -1, cur - 1, cur, cur + 1, -1, total];
  }

  /**
   * Mobile pagination — always returns exactly 5 items when totalPages > 5.
   * Page 1 is always pinned as the first button.
   *
   *  cur <= 2       → [1, 2, 3, -1, total]
   *  cur >= total-1 → [1, -1, total-2, total-1, total]
   *  middle         → [1, -1, cur, -1, total]
   */
  getMobilePageNumbers(): number[] {
    if (!this.pagedResponse) return [1];
    const total = this.pagedResponse.totalPages;
    const cur   = this.currentPage;
    if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
    if (cur <= 2)          return [1, 2, 3, -1, total];
    if (cur >= total - 1)  return [1, -1, total - 2, total - 1, total];
    return [1, -1, cur, -1, total];
  }

  getMin = Math.min;

  trackBySymbol = (_: number, item: Signal) => item?.symbol ?? _;

  // Popover position for fixed positioning

  // Popover methods for reasons display
  toggleReasonPopover(popoverId: string, event?: Event): void {
    if (event && event.target && this.openPopoverId !== popoverId) {
      const element = event.target as HTMLElement;
      const rect = element.getBoundingClientRect();

      // Position popover below the badge, centered
      const popoverWidth = 280;
      const centerX = rect.left + rect.width / 2 - popoverWidth / 2;
      const topY = rect.bottom + 8; // 8px gap below button

      this.popoverPosition = {
        top: topY,
        left: centerX
      };

      // Add scroll listener to update position
      this.setupScrollListener();
      this.openPopoverId = popoverId;
    } else {
      this.closeReasonPopover();
    }
  }

  private setupScrollListener(): void {
    if (this.scrollListener) return; // Already set up

    this.scrollListener = () => {
      // Update popover position on scroll
      const badge = document.querySelector(`[data-popover-id="${this.openPopoverId}"]`) as HTMLElement;
      if (badge) {
        const rect = badge.getBoundingClientRect();
        const popoverWidth = 280;
        const centerX = rect.left + rect.width / 2 - popoverWidth / 2;
        const topY = rect.bottom + 8;

        if (this.popoverPosition) {
          this.popoverPosition.top = topY;
          this.popoverPosition.left = centerX;
        }
      }
    };

    window.addEventListener('scroll', this.scrollListener, true);
  }

  closeReasonPopover(): void {
    this.openPopoverId = null;
    this.popoverPosition = null;

    // Remove scroll listener
    if (this.scrollListener) {
      window.removeEventListener('scroll', this.scrollListener, true);
      this.scrollListener = null;
    }
  }

  getReasonPopoverId(symbol: string, timeframe: string): string {
    return `reasons-${symbol}-${timeframe}`;
  }

  // Get color for strength value
  getStrengthColor(strength?: number | null): string {
    if (strength == null) return '#94a3b8';
    if (strength >= 80) return '#00d395';  // Green - strong signal
    if (strength >= 60) return '#eab308';  // Yellow - moderate signal
    return '#94a3b8';                      // Gray - weak signal
  }

  // ==================== BİNANCE FİYAT ====================

  loadBinancePrices(signals: Signal[]): void {
    const symbols = [...new Set(signals.map(s => s.symbol))];
    if (!symbols.length) return;
    this.binancePriceService.getPrices(symbols).subscribe(priceMap => {
      this.currentPrices = priceMap;
    });
  }

  /** 30s interval ile çağrılır — sadece mevcut tablodaki sembolleri ister */
  private refreshPrices(): void {
    const symbols = [...new Set(this.signals.map(s => s.symbol))];
    if (!symbols.length) return;
    this.binancePriceService.getPrices(symbols).subscribe(priceMap => {
      this.currentPrices = priceMap;
    });
  }

  getEntryPrice(signal: Signal): number {
    return signal.firstPrice ?? signal.price;
  }

  getCurrentPrice(signal: Signal): number | null {
    return this.currentPrices.get(signal.symbol) ?? null;
  }

  getPriceChange(signal: Signal): number | null {
    const current = this.getCurrentPrice(signal);
    const entry = this.getEntryPrice(signal);
    if (current == null || entry === 0) return null;
    return ((current - entry) / entry) * 100;
  }

  getPriceChangeClass(signal: Signal): string {
    const change = this.getPriceChange(signal);
    if (change == null) return 'text-secondary';
    return change >= 0 ? 'text-success' : 'text-danger';
  }

  // ==================== OUTCOME ====================

  getOutcomeLabel(signal: Signal): string {
    if (signal.tpHit === true) return 'TP Hit';
    if (signal.slHit === true) return 'SL Hit';
    return 'Open';
  }

  getOutcomeClass(signal: Signal): string {
    if (signal.tpHit === true) return 'outcome-badge outcome-tp';
    if (signal.slHit === true) return 'outcome-badge outcome-sl';
    return 'outcome-badge outcome-open';
  }
}


import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SignalService } from '../../services/signal.service';
import { Signal } from '../../models/signal.model';
import { SignalFilter, SignalPagedResponse } from '../../models/signal-filter.model';

@Component({
  selector: 'app-signal-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signal-table.component.html',
  styleUrls: ['./signal-table.component.css']
})
export class SignalTableComponent implements OnInit {
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
  pageSize: number = 25;

  // Loading state
  isLoading: boolean = false;

  // Popover state for reasons display
  openPopoverId: string | null = null;

  private signalService = inject(SignalService);

  ngOnInit() {
    // Load filtered signals with current filter
    this.loadFilteredSignals();
    // Load multi-timeframe data for availability indicators
    this.loadMultiTimeframeData();
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

  // Reason labels mapping (English code → Turkish label)
  private reasonLabels: { [key: string]: string } = {
    // Trend kategorisi
    'TREND_PERFECT': 'Trend Mükemmel',
    'TREND_UP': 'Trend Yükseliyor',

    // Momentum kategorisi
    'MOMENTUM_STRONG': 'Momentum Güçlü',
    'MOMENTUM_GOOD': 'Momentum İyi',

    // ADX kategorisi
    'ADX_VERY_STRONG': 'Çok Güçlü',
    'ADX_STRONG': 'Güçlü Sinyal',
    'ADX_MODERATE': 'Orta Sinyal',

    // RSI kategorisi
    'RSI_OPTIMAL': 'RSI İdeal',
    'RSI_HEALTHY': 'RSI Sağlıklı',

    // MACD kategorisi
    'MACD_BULLISH': 'MACD Yükseliş',
    'MACD_CROSS_UP': 'MACD Kesişim ↑',

    // Volume kategorisi
    'VOLUME_HIGH': 'Hacim Yüksek'
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

  // Get Turkish label for reason code
  getReasonLabel(reason: string): string {
    return this.reasonLabels[reason] || reason;
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

  getPageNumbers(): number[] {
    if (!this.pagedResponse) return [1];

    const totalPages = this.pagedResponse.totalPages;
    const current = this.currentPage;
    const pages: number[] = [];

    // Show page numbers around current page
    const start = Math.max(1, current - 2);
    const end = Math.min(totalPages, current + 2);

    if (start > 1) pages.push(1);
    if (start > 2) pages.push(-1); // -1 represents ellipsis

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (end < totalPages - 1) pages.push(-1); // -1 represents ellipsis
    if (end < totalPages) pages.push(totalPages);

    return pages;
  }

  getMin = Math.min;

  trackBySymbol = (_: number, item: Signal) => item?.symbol ?? _;

  // Popover methods for reasons display
  toggleReasonPopover(popoverId: string): void {
    this.openPopoverId = this.openPopoverId === popoverId ? null : popoverId;
  }

  closeReasonPopover(): void {
    this.openPopoverId = null;
  }

  getReasonPopoverId(symbol: string, timeframe: string): string {
    return `reasons-${symbol}-${timeframe}`;
  }
}


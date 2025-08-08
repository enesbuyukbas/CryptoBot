import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SignalService } from '../../services/signal.service';

@Component({
  selector: 'app-signal-table',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './signal-table.component.html',
  styleUrls: ['./signal-table.component.css']
})
export class SignalTableComponent implements OnInit {
  signals: any[] = [];
  top3Signals: any[] = []; // <-- kartlar için
  private signalService = inject(SignalService);

  ngOnInit() {
    // 1) Önce top3'ü backend'den iste
    this.signalService.getTopSignals().subscribe({
      next: (data) => {
        this.top3Signals = (data ?? []).slice(0, 3);
      },
      error: () => { this.top3Signals = []; } // fallback için boş bırak
    });

    // 2) Ardından tüm sinyaller
    this.signalService.getSignals().subscribe({
      next: (data) => {
        this.signals = data ?? [];
        // Fallback: top endpoint boş döndüyse local sort ile ilk 3'ü hesapla
        if (!this.top3Signals.length && this.signals.length) {
          this.top3Signals = [...this.signals]
            .sort((a, b) => Number(b?.strength ?? 0) - Number(a?.strength ?? 0))
            .slice(0, 3);
        }
      },
      error: (err) => console.error('API Hatası:', err),
    });
  }

  trackBySymbol = (_: number, item: any) => item?.symbol ?? _;
}

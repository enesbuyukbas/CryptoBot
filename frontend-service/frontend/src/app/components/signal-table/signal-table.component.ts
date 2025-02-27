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
  private signalService = inject(SignalService);

  constructor() {}

  ngOnInit() {
    this.signalService.getSignals().subscribe({
      next: (data) => {
        console.log('API’den Gelen Veriler:', data);
        this.signals = data;
      },
      error: (err) => console.error('API Hatası:', err),
    });
  }
}

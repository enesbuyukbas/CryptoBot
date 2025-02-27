import { Component } from '@angular/core';
import { SignalTableComponent } from './components/signal-table/signal-table.component'; // ✅ SignalTable bileşenini içe aktardık

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [SignalTableComponent] // ✅ Buraya ekledik
})
export class AppComponent {
  title = 'Crypto Signal Dashboard';
}

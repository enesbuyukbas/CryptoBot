import { Routes } from '@angular/router';
import { SignalTableComponent } from './components/signal-table/signal-table.component';
import { GuideComponent } from './pages/guide/guide.component';

export const routes: Routes = [
  { path: '', component: SignalTableComponent },
  { path: 'guide', component: GuideComponent },
];

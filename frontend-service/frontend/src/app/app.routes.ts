import { Routes } from '@angular/router';
import { SignalTableComponent } from './components/signal-table/signal-table.component';
import { GuideComponent } from './pages/guide/guide.component';
import { ContactComponent } from './pages/contact/contact.component';

export const routes: Routes = [
  { path: 'home', component: SignalTableComponent },
  { path: '', component: SignalTableComponent },
  { path: 'guide', component: GuideComponent },
  { path: 'contact', component: ContactComponent },
];

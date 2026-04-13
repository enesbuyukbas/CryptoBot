import { Component } from '@angular/core';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { HeroComponent } from "./components/hero/hero.component";
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [RouterOutlet, RouterLink, RouterLinkActive, HeroComponent, CommonModule]
})
export class AppComponent {
  title = 'Crypto Signal Dashboard';

  constructor(public router: Router) {}

  get showHero(): boolean {
    return this.router.url === '/' || this.router.url === '';
  }
}

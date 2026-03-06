import { Component } from '@angular/core';
import { AppHeaderComponent } from './shared/components/header/header';
import { TicketsPageComponent } from './modules/tickets/pages/tickets-page/tickets-page';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AppHeaderComponent, TicketsPageComponent],
  template: `
    <app-header></app-header>
    <app-tickets-page></app-tickets-page>
  `
})
export class App {}
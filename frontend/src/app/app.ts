import { Component } from '@angular/core';
import { AppHeaderComponent } from './shared/components/header/header';
import { TicketsPageComponent } from './modules/tickets/pages/tickets-page/tickets-page';
import { ViewMode } from './core/models/ticket.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AppHeaderComponent, TicketsPageComponent],
  template: `
    <app-header (viewModeChange)="onViewModeChange($event)"></app-header>
    <app-tickets-page [viewMode]="viewMode"></app-tickets-page>
  `
})
export class AppComponent {
  viewMode: ViewMode = 'MORADOR';

  onViewModeChange(mode: ViewMode): void {
    this.viewMode = mode;
  }
}
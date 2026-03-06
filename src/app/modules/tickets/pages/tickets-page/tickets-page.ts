import { Component, Input } from '@angular/core';
import { Ticket, TicketFilter, ViewMode } from '../../../../core/models/ticket.model';
import { TICKETS_MOCK } from '../../../../mocks/tickets.mock';
import { TicketListComponent } from '../../components/ticket-list/ticket-list';
import { TicketFiltersComponent } from '../../components/ticket-filters/ticket-filters';
import { PageHeaderComponent } from '../../components/page-header/page-header';

@Component({
  selector: 'app-tickets-page',
  standalone: true,
  imports: [
    TicketListComponent,
    TicketFiltersComponent,
    PageHeaderComponent
  ],
  templateUrl: './tickets-page.html',
  styleUrl: './tickets-page.css'
})
export class TicketsPageComponent {
  @Input() viewMode: ViewMode = 'MORADOR';

  tickets: Ticket[] = TICKETS_MOCK;
  search = '';
  activeFilter: TicketFilter = 'TODOS';

  onSearchChange(value: string): void {
    this.search = value;
  }

  onFilterChange(filter: TicketFilter): void {
    this.activeFilter = filter;
  }

  onNewTicket(): void {
    console.log('Abrir fluxo de novo chamado');
  }

  get filteredTickets(): Ticket[] {
    return this.tickets.filter((ticket) => {
      const normalizedSearch = this.search.trim().toLowerCase();

      const matchesSearch =
        !normalizedSearch ||
        ticket.title.toLowerCase().includes(normalizedSearch) ||
        ticket.description.toLowerCase().includes(normalizedSearch) ||
        ticket.residentName.toLowerCase().includes(normalizedSearch) ||
        ticket.apartment.toLowerCase().includes(normalizedSearch);

      const matchesFilter =
        this.activeFilter === 'TODOS' || ticket.status === this.activeFilter;

      return matchesSearch && matchesFilter;
    });
  }
}
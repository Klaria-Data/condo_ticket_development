import { Component, Input } from '@angular/core';
import { Ticket, TicketFilter, ViewMode } from '../../../../core/models/ticket.model';
import { TICKETS_MOCK } from '../../../../mocks/tickets.mock';
import { TicketListComponent } from '../../components/ticket-list/ticket-list';
import { TicketFiltersComponent } from '../../components/ticket-filters/ticket-filters';
import { PageHeaderComponent } from '../../components/page-header/page-header';
import { NewTicketModalComponent } from '../../components/new-ticket-modal/new-ticket-modal';
import { CommonModule } from '@angular/common';
import { TicketsSummaryComponent } from '../../components/tickets-summary/tickets-summary';

@Component({
  selector: 'app-tickets-page',
  standalone: true,
  imports: [
    TicketListComponent,
    TicketFiltersComponent,
    PageHeaderComponent,
    NewTicketModalComponent,
    CommonModule,
    TicketsSummaryComponent
  ],
  templateUrl: './tickets-page.html',
  styleUrls: ['./tickets-page.css']
})
export class TicketsPageComponent {
  @Input() viewMode: ViewMode = 'MORADOR';

  tickets: Ticket[] = TICKETS_MOCK;
  search = '';
  activeFilter: TicketFilter = 'TODOS';
  isNewTicketModalOpen = false;

  onSearchChange(value: string): void {
    this.search = value;
  }

  onFilterChange(filter: TicketFilter): void {
    this.activeFilter = filter;
  }

  onNewTicket(): void {
    alert('clicou');
    this.isNewTicketModalOpen = true;
  }

  closeNewTicketModal(): void {
    this.isNewTicketModalOpen = false;
  }

  createTicket(ticket: Ticket): void {
    this.tickets = [ticket, ...this.tickets];
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
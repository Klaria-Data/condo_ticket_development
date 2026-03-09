import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Ticket, TicketFilter, TicketStatus, ViewMode } from '../../../../core/models/ticket.model';
import { TicketListComponent } from '../../components/ticket-list/ticket-list';
import { TicketFiltersComponent } from '../../components/ticket-filters/ticket-filters';
import { PageHeaderComponent } from '../../components/page-header/page-header';
import { NewTicketModalComponent } from '../../components/new-ticket-modal/new-ticket-modal';
import { CommonModule } from '@angular/common';
import { AppHeaderComponent } from '../../../../shared/components/header/header';
import { TicketsService } from '../../../../core/services/tickets.service';
import { AuthService } from '../../../../core/services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';
import { TicketsSummaryComponent } from '../../components/tickets-summary/tickets-summary';

@Component({
  selector: 'app-tickets-page',
  standalone: true,
  imports: [
    AppHeaderComponent,
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
export class TicketsPageComponent implements OnInit {
  viewMode: ViewMode = 'MORADOR';

  tickets: Ticket[] = [];
  search = '';
  activeFilter: TicketFilter = 'TODOS';
  isNewTicketModalOpen = false;
  errorMessage = '';

  constructor(
    private readonly ticketsService: TicketsService,
    private readonly authService: AuthService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.viewMode = user.perfil === 'ADMIN' ? 'SINDICO' : 'MORADOR';
    this.loadTickets();
  }

  onViewModeChange(mode: ViewMode): void {
    this.viewMode = mode;
  }

  onSearchChange(value: string): void {
    this.search = value;
  }

  onFilterChange(filter: TicketFilter): void {
    this.activeFilter = filter;
  }

  onNewTicket(): void {
    this.isNewTicketModalOpen = true;
  }

  closeNewTicketModal(): void {
    this.isNewTicketModalOpen = false;
  }

  createTicket(ticket: Ticket): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.ticketsService
      .createTicket(
        {
          titulo: ticket.title,
          descricao: ticket.description,
          imagem_url: null,
        },
        user.nome,
        user.unidade,
      )
      .subscribe({
        next: () => {
          this.errorMessage = '';
          this.loadTickets();
          this.cdr.detectChanges();
        },
        error: (err: HttpErrorResponse) => {
          if (err.status === 401 || err.status === 403) {
            this.authService.logout();
            return;
          }

          this.errorMessage = 'Falha ao criar chamado no backend.';
          this.cdr.detectChanges();
        },
      });
  }

  updateTicketStatus(event: { ticketId: number; status: TicketStatus }): void {
    console.log('[TicketsPage] updateTicketStatus called:', event);
    
    const user = this.authService.getCurrentUser();
    if (!user) {
      console.log('[TicketsPage] No user found, logging out');
      this.authService.logout();
      return;
    }

    console.log('[TicketsPage] Calling ticketsService.updateTicketStatus');
    this.ticketsService
      .updateTicketStatus(event.ticketId, event.status, user.nome, user.unidade)
      .subscribe({
        next: () => {
          console.log('[TicketsPage] Status update successful');
          this.errorMessage = '';
          this.loadTickets();
          this.cdr.detectChanges();
        },
        error: (err: HttpErrorResponse) => {
          console.error('[TicketsPage] Status update error:', err);
          
          if (err.status === 401 || err.status === 403) {
            this.authService.logout();
            return;
          }

          this.errorMessage =
            err.status === 400
              ? 'Transicao de status invalida. Siga ABERTO -> EM_ANDAMENTO -> RESOLVIDO.'
              : 'Falha ao atualizar status do ticket.';
          this.loadTickets();
          this.cdr.detectChanges();
        },
      });
  }

  private loadTickets(): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.ticketsService.listTickets(user.nome, user.unidade).subscribe({
      next: (tickets) => {
        this.tickets = tickets;
        this.cdr.detectChanges();
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 401 || err.status === 403) {
          this.authService.logout();
          return;
        }

        this.errorMessage = 'Falha ao carregar chamados do backend.';
        this.cdr.detectChanges();
      },
    });
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
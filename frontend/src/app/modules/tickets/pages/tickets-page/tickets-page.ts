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

/**
 * Página principal do sistema de tickets.
 *
 * Orquestra a listagem, criação e atualização de status dos chamados.
 * O viewMode (MORADOR ou SINDICO) é determinado pelo perfil do usuário logado:
 *   - ADMIN → visão SINDICO (vê todos os tickets, pode mudar status)
 *   - MORADOR → visão MORADOR (vê apenas seus próprios tickets)
 */
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
    TicketsSummaryComponent,
  ],
  templateUrl: './tickets-page.html',
  styleUrls: ['./tickets-page.css'],
})
export class TicketsPageComponent implements OnInit {
  viewMode: ViewMode = 'MORADOR';

  tickets: Ticket[] = [];
  search = '';
  activeFilter: TicketFilter = 'TODOS';
  isNewTicketModalOpen = false;
  errorMessage = '';
  currentPage = 1;
  readonly pageSize = 6;

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
    if (mode === 'SINDICO' && this.authService.getCurrentUser()?.perfil !== 'ADMIN') {
      return;
    }
    this.viewMode = mode;
  }

  onSearchChange(value: string): void {
    this.search = value;
    this.currentPage = 1;
  }

  onFilterChange(filter: TicketFilter): void {
    this.activeFilter = filter;
    this.currentPage = 1;
  }

  onNewTicket(): void {
    this.isNewTicketModalOpen = true;
  }

  closeNewTicketModal(): void {
    this.isNewTicketModalOpen = false;
  }

  /** Cria um novo ticket a partir dos dados informados no modal. */
  createTicket(ticket: Ticket): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    if (ticket.imageFile) {
      this.ticketsService.uploadImage(ticket.imageFile).subscribe({
        next: (imageUrl) => this.persistTicket(ticket, imageUrl),
        error: () => {
          this.errorMessage = 'Falha ao enviar a imagem do chamado.';
          this.cdr.detectChanges();
        },
      });
      return;
    }

    this.persistTicket(ticket, null);
  }

  private persistTicket(ticket: Ticket, imageUrl: string | null): void {
    this.ticketsService
      .createTicket({
        titulo: ticket.title,
        descricao: ticket.description,
        imagem_url: imageUrl,
      })
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

  /** Atualiza o status de um ticket seguindo o fluxo ABERTO → EM_ANDAMENTO → RESOLVIDO. */
  updateTicketStatus(event: { ticketId: number; status: TicketStatus }): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.ticketsService.updateTicketStatus(event.ticketId, event.status).subscribe({
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

        this.errorMessage =
          err.status === 400
            ? 'Transição de status inválida. Siga ABERTO → EM_ANDAMENTO → RESOLVIDO.'
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

    this.ticketsService.listTickets().subscribe({
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

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.filteredTickets.length / this.pageSize));
  }

  get paginatedTickets(): Ticket[] {
    const page = Math.min(this.currentPage, this.totalPages);
    const start = (page - 1) * this.pageSize;
    return this.filteredTickets.slice(start, start + this.pageSize);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
    }
  }
}

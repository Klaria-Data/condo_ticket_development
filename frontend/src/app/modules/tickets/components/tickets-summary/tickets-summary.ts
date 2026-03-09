import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Ticket } from '../../../../core/models/ticket.model';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-tickets-summary',
  standalone: true,
  imports: [CommonModule,MatIconModule],
  templateUrl: './tickets-summary.html',
  styleUrls: ['./tickets-summary.css']
})
export class TicketsSummaryComponent {
  @Input() tickets: Ticket[] = [];

  get total(): number {
    return this.tickets.length;
  }

  get open(): number {
    return this.tickets.filter(ticket => ticket.status === 'ABERTO').length;
  }

  get inProgress(): number {
    return this.tickets.filter(ticket => ticket.status === 'EM_ANDAMENTO').length;
  }

  get resolved(): number {
    return this.tickets.filter(ticket => ticket.status === 'RESOLVIDO').length;
  }
}
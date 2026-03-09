import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Ticket, TicketStatus, ViewMode } from '../../../../core/models/ticket.model';
import { getInitials } from '../../../../utils/initials.util';
import { StatusBadgeComponent } from '../status-badge/status-badge';

@Component({
  selector: 'app-ticket-card',
  standalone: true,
  imports: [CommonModule, FormsModule, StatusBadgeComponent],
  templateUrl: './ticket-card.html',
  styleUrl: './ticket-card.css'
})
export class TicketCardComponent {
  @Input({ required: true }) ticket!: Ticket;
  @Input() viewMode: ViewMode = 'MORADOR';

  get initials(): string {
    return getInitials(this.ticket.residentName);
  }

  changeStatus(newStatus: TicketStatus): void {
    this.ticket.status = newStatus;
    this.ticket.updatedAt = '05 de dez.';
  }
}
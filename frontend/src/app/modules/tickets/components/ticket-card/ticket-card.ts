import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
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
  @Output() statusChange = new EventEmitter<{ ticketId: number; status: TicketStatus }>();

  get initials(): string {
    return getInitials(this.ticket.residentName);
  }

  changeStatus(newStatus: TicketStatus): void {
    console.log('[TicketCard] changeStatus called:', { ticketId: this.ticket.id, oldStatus: this.ticket.status, newStatus });
    
    if (newStatus === this.ticket.status) {
      console.log('[TicketCard] Status unchanged, skipping emit');
      return;
    }

    console.log('[TicketCard] Emitting statusChange event');
    this.statusChange.emit({ ticketId: this.ticket.id, status: newStatus });
  }
}
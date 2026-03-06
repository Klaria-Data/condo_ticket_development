import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Ticket } from '../../../../core/models/ticket.model';
import { getInitials } from '../../../../utils/initials.util';
import { StatusBadgeComponent } from '../status-badge/status-badge';

@Component({
  selector: 'app-ticket-card',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  templateUrl: './ticket-card.html',
  styleUrl: './ticket-card.css'
})
export class TicketCardComponent {
  @Input({ required: true }) ticket!: Ticket;

  get initials(): string {
    return getInitials(this.ticket.residentName);
  }
}
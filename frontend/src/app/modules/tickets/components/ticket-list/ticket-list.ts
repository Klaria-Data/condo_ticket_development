import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Ticket, TicketStatus, ViewMode } from '../../../../core/models/ticket.model';
import { TicketCardComponent } from '../ticket-card/ticket-card';

@Component({
  selector: 'app-ticket-list',
  standalone: true,
  imports: [CommonModule, TicketCardComponent],
  templateUrl: './ticket-list.html',
  styleUrl: './ticket-list.css'
})
export class TicketListComponent {
  @Input() tickets: Ticket[] = [];
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() statusChange = new EventEmitter<{ ticketId: number; status: TicketStatus }>();

  onStatusChange(event: { ticketId: number; status: TicketStatus }): void {
    console.log('[TicketList] onStatusChange called:', event);
    this.statusChange.emit(event);
  }
}
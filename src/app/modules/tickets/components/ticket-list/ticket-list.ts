import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Ticket } from '../../../../core/models/ticket.model';
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
}
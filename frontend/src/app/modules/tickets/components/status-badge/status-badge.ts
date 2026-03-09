import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { TicketStatus } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.css'
})
export class StatusBadgeComponent {
  @Input({ required: true }) status!: TicketStatus;

  get label(): string {
    switch (this.status) {
      case 'ABERTO':
        return 'Aberto';
      case 'EM_ANDAMENTO':
        return 'Em Andamento';
      case 'RESOLVIDO':
        return 'Resolvido';
      default:
        return this.status;
    }
  }
}
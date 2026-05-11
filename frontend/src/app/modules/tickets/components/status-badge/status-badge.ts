import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { LucideAngularModule, CircleDot, Clock, CheckCircle2, LucideIconData } from 'lucide-angular';
import { TicketStatus } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.css'
})
export class StatusBadgeComponent {
  @Input({ required: true }) status!: TicketStatus;

  get icon(): LucideIconData {
    switch (this.status) {
      case 'ABERTO': return CircleDot;
      case 'EM_ANDAMENTO': return Clock;
      case 'RESOLVIDO': return CheckCircle2;
      default: return CircleDot;
    }
  }

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
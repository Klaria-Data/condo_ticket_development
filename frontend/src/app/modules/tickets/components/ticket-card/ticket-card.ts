import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Home, Clock, ChevronDown, ChevronRight, CheckCircle2 } from 'lucide-angular';
import { Ticket, TicketStatus, ViewMode } from '../../../../core/models/ticket.model';
import { getInitials } from '../../../../utils/initials.util';
import { StatusBadgeComponent } from '../status-badge/status-badge';
import { TicketCommentsComponent } from '../ticket-comments/ticket-comments';

@Component({
  selector: 'app-ticket-card',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule, StatusBadgeComponent, TicketCommentsComponent],
  templateUrl: './ticket-card.html',
  styleUrl: './ticket-card.css'
})
export class TicketCardComponent {
  @Input({ required: true }) ticket!: Ticket;
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() statusChange = new EventEmitter<{ ticketId: number; status: TicketStatus }>();

  readonly Home = Home;
  readonly Clock = Clock;
  readonly ChevronDown = ChevronDown;
  readonly ChevronRight = ChevronRight;
  readonly CheckCircle2 = CheckCircle2;

  showComments = false;

  get initials(): string {
    return getInitials(this.ticket.residentName);
  }

  changeStatus(newStatus: TicketStatus): void {
    if (newStatus === this.ticket.status) {
      return;
    }
    this.statusChange.emit({ ticketId: this.ticket.id, status: newStatus });
  }

  toggleComments(): void {
    this.showComments = !this.showComments;
  }
}
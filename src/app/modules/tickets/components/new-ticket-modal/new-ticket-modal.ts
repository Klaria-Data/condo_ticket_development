import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Ticket } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-new-ticket-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './new-ticket-modal.html',
  styleUrls: ['./new-ticket-modal.css']
})
export class NewTicketModalComponent {
  @Output() close = new EventEmitter<void>();
  @Output() create = new EventEmitter<Ticket>();

  title = '';
  description = '';
  residentName = '';
  apartment = '';
  selectedFileName = '';

  onClose(): void {
    this.close.emit();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (file) {
      this.selectedFileName = file.name;
    }
  }

  onSubmit(): void {
    const newTicket: Ticket = {
      id: Date.now(),
      title: this.title,
      description: this.description,
      residentName: this.residentName,
      apartment: this.apartment,
      status: 'ABERTO',
      createdAt: 'Hoje',
      avatarColor: '#8b5cf6'
    };

    this.create.emit(newTicket);
    this.onClose();
  }
}
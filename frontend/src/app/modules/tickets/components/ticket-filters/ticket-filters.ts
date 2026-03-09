import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TicketFilter } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-ticket-filters',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ticket-filters.html',
  styleUrl: './ticket-filters.css'
})
export class TicketFiltersComponent {
  @Input() search = '';
  @Input() activeFilter: TicketFilter = 'TODOS';

  @Output() searchChange = new EventEmitter<string>();
  @Output() activeFilterChange = new EventEmitter<TicketFilter>();

  filters: TicketFilter[] = ['TODOS', 'ABERTO', 'EM_ANDAMENTO', 'RESOLVIDO'];

  onSearchChange(value: string): void {
    this.searchChange.emit(value);
  }

  selectFilter(filter: TicketFilter): void {
    this.activeFilterChange.emit(filter);
  }

  getFilterLabel(filter: TicketFilter): string {
    switch (filter) {
      case 'TODOS':
        return 'Todos';
      case 'ABERTO':
        return 'Abertos';
      case 'EM_ANDAMENTO':
        return 'Em Andamento';
      case 'RESOLVIDO':
        return 'Resolvidos';
      case 'CANCELADO':
        return 'Cancelados';
      default:
        return filter;
    }
  }
}
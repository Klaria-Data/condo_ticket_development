import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { UserRole } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-view-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './view-switcher.html',
  styleUrl: './view-switcher.css'
})
export class ViewSwitcherComponent {
  @Input() selected: UserRole = 'MORADOR';
  @Output() selectedChange = new EventEmitter<UserRole>();

  select(role: UserRole): void {
    this.selectedChange.emit(role);
  }
}
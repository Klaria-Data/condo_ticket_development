import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ViewMode} from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-view-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './view-switcher.html',
  styleUrl: './view-switcher.css'
})
export class ViewSwitcherComponent {
  @Input() selected: ViewMode = 'MORADOR';
  @Output() selectedChange = new EventEmitter<ViewMode>();

  select(role: ViewMode): void {
    this.selectedChange.emit(role);
  }
}
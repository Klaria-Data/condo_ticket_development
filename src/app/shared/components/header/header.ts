import { Component, EventEmitter, Output } from '@angular/core';
import { ViewMode } from '../../../core/models/ticket.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.html',
  styleUrl: './header.css'
})
export class AppHeaderComponent {
  viewMode: ViewMode = 'MORADOR';

  @Output() viewModeChange = new EventEmitter<ViewMode>();

  setMode(mode: ViewMode): void {
    this.viewMode = mode;
    this.viewModeChange.emit(mode);
  }
}
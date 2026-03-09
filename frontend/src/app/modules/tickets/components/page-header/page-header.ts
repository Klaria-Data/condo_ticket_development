import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ViewMode } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './page-header.html',
  styleUrl: './page-header.css'
})
export class PageHeaderComponent {
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() newTicket = new EventEmitter<void>();
}
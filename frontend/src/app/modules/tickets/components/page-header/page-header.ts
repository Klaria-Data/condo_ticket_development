import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { LucideAngularModule, Plus } from 'lucide-angular';
import { ViewMode } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './page-header.html',
  styleUrl: './page-header.css'
})
export class PageHeaderComponent {
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() newTicket = new EventEmitter<void>();

  readonly Plus = Plus;
}
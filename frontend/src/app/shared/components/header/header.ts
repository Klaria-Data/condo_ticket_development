import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Building2, UserRound, ShieldCheck } from 'lucide-angular';
import { ViewMode } from '../../../core/models/ticket.model';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class AppHeaderComponent {
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() viewModeChange = new EventEmitter<ViewMode>();

  readonly Building2 = Building2;
  readonly UserRound = UserRound;
  readonly ShieldCheck = ShieldCheck;

  setMode(mode: ViewMode): void {
    this.viewMode = mode;
    this.viewModeChange.emit(mode);
  }
}
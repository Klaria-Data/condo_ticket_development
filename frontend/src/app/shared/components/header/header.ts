import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import {
  CalendarDays,
  LucideAngularModule,
  Building2,
  UserRound,
  ShieldCheck,
  UsersRound,
  Wrench,
} from 'lucide-angular';
import { ViewMode } from '../../../core/models/ticket.model';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink, RouterLinkActive],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class AppHeaderComponent {
  @Input() viewMode: ViewMode = 'MORADOR';
  @Output() viewModeChange = new EventEmitter<ViewMode>();

  readonly Building2 = Building2;
  readonly CalendarDays = CalendarDays;
  readonly UserRound = UserRound;
  readonly ShieldCheck = ShieldCheck;
  readonly UsersRound = UsersRound;
  readonly Wrench = Wrench;

  setMode(mode: ViewMode): void {
    this.viewMode = mode;
    this.viewModeChange.emit(mode);
  }
}

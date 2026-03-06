import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-page-header',
  standalone: true,
  templateUrl: './page-header.html',
  styleUrl: './page-header.css'
})
export class PageHeaderComponent {
  @Output() newTicket = new EventEmitter<void>();
}
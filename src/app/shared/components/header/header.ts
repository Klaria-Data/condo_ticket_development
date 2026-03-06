import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.html',
  styleUrl: './header.css'
})
export class AppHeaderComponent {
  viewMode: 'MORADOR' | 'SINDICO' = 'MORADOR';

  setMode(mode: 'MORADOR' | 'SINDICO') {
    this.viewMode = mode;
  }
}
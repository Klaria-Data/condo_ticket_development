import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { LucideAngularModule, Building2 } from 'lucide-angular';

import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './login-page.html',
  styleUrl: './login-page.css',
})
export class LoginPageComponent {
  readonly Building2 = Building2;

  email = '';
  senha = '';
  loading = false;
  submitted = false;
  errorMessage = '';
  fieldErrors = {
    email: '',
    senha: '',
  };

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  onSubmit(): void {
    this.submitted = true;
    this.errorMessage = '';

    if (!this.validateForm()) {
      return;
    }

    this.loading = true;

    this.authService.login({ email: this.email.trim(), senha: this.senha }).subscribe({
      next: () => {
        this.loading = false;
        void this.router.navigate(['/']);
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Falha no login. Verifique email/senha.';
      },
    });
  }

  private validateForm(): boolean {
    this.fieldErrors = {
      email: '',
      senha: '',
    };

    let isValid = true;

    if (!this.email.trim()) {
      this.fieldErrors.email = 'Informe o e-mail para continuar.';
      isValid = false;
    }

    if (!this.senha.trim()) {
      this.fieldErrors.senha = 'Informe a senha para continuar.';
      isValid = false;
    }

    return isValid;
  }
}

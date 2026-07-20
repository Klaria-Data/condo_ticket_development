import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Building2, KeyRound, LucideAngularModule } from 'lucide-angular';

import { AuthUser, LoginResponse } from '../../../../core/models/auth.model';
import { PublicResidentInvite } from '../../../../core/models/resident-invite.model';
import { ResidentInvitesService } from '../../../../core/services/resident-invites.service';

@Component({
  selector: 'app-accept-invite-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './accept-invite-page.html',
  styleUrl: './accept-invite-page.css',
})
export class AcceptInvitePageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);

  readonly Building2 = Building2;
  readonly KeyRound = KeyRound;

  invite: PublicResidentInvite | null = null;
  token = '';
  errorMessage = '';
  loading = false;

  readonly passwordForm = this.fb.nonNullable.group({
    senha: ['', [Validators.required, Validators.minLength(8)]],
    confirmarSenha: ['', [Validators.required, Validators.minLength(8)]],
  });

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly residentInvitesService: ResidentInvitesService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token') ?? '';
    if (!this.token) {
      this.errorMessage = 'Convite inválido.';
      return;
    }

    this.residentInvitesService.getInvite(this.token).subscribe({
      next: (invite) => {
        this.invite = invite;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errorMessage = 'Convite inválido ou expirado.';
        this.cdr.detectChanges();
      },
    });
  }

  acceptInvite(): void {
    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    const form = this.passwordForm.getRawValue();
    if (form.senha !== form.confirmarSenha) {
      this.errorMessage = 'As senhas precisam ser iguais.';
      return;
    }

    this.loading = true;
    this.residentInvitesService.acceptInvite(this.token, form.senha).subscribe({
      next: (response) => {
        this.saveSession(response);
        this.loading = false;
        this.cdr.detectChanges();
        void this.router.navigate(['/']);
      },
      error: (err) => this.handleError(err),
    });
  }

  private saveSession(response: LoginResponse): void {
    localStorage.setItem('condoticket.jwt', response.access_token);
    const user: AuthUser = {
      id: response.usuario_id,
      nome: response.nome,
      unidade: response.unidade,
      perfil: response.perfil,
    };
    localStorage.setItem('condoticket.user', JSON.stringify(user));
  }

  private handleError(err: HttpErrorResponse): void {
    this.loading = false;
    this.errorMessage = err.error?.detail ?? 'Falha ao aceitar convite.';
    this.cdr.detectChanges();
  }
}

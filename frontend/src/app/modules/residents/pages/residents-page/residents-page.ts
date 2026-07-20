import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  Copy,
  LucideAngularModule,
  MailPlus,
  Send,
  UserPlus,
  UsersRound,
} from 'lucide-angular';

import { AuthService } from '../../../../core/services/auth.service';
import { ResidentInvitesService } from '../../../../core/services/resident-invites.service';
import { ResidentInvite } from '../../../../core/models/resident-invite.model';
import { AppHeaderComponent } from '../../../../shared/components/header/header';
import { ViewMode } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-residents-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, AppHeaderComponent],
  templateUrl: './residents-page.html',
  styleUrl: './residents-page.css',
})
export class ResidentsPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);

  readonly Copy = Copy;
  readonly MailPlus = MailPlus;
  readonly Send = Send;
  readonly UserPlus = UserPlus;
  readonly UsersRound = UsersRound;

  viewMode: ViewMode = 'SINDICO';
  invites: ResidentInvite[] = [];
  latestInviteUrl = '';
  errorMessage = '';
  successMessage = '';
  isLoading = false;

  readonly inviteForm = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(120)]],
    email: ['', [Validators.required, Validators.email]],
    unidade: ['', [Validators.required, Validators.maxLength(30)]],
  });

  constructor(
    private readonly authService: AuthService,
    private readonly residentInvitesService: ResidentInvitesService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.viewMode = user.perfil === 'ADMIN' ? 'SINDICO' : 'MORADOR';
    if (user.perfil !== 'ADMIN') {
      this.errorMessage = 'Apenas o síndico pode cadastrar moradores.';
      return;
    }

    this.loadInvites();
  }

  onViewModeChange(mode: ViewMode): void {
    if (mode === 'SINDICO' && this.authService.getCurrentUser()?.perfil !== 'ADMIN') {
      return;
    }
    this.viewMode = mode;
  }

  createInvite(): void {
    if (this.inviteForm.invalid) {
      this.inviteForm.markAllAsTouched();
      return;
    }

    const form = this.inviteForm.getRawValue();
    this.residentInvitesService
      .createInvite({
        nome: form.nome.trim(),
        email: form.email.trim(),
        unidade: form.unidade.trim(),
      })
      .subscribe({
        next: (invite) => {
          this.inviteForm.reset();
          this.latestInviteUrl = invite.convite_url ?? '';
          this.successMessage = 'Convite enviado para o morador.';
          this.errorMessage = '';
          this.loadInvites();
        },
        error: (err) => this.handleError(err, 'Falha ao criar convite.'),
      });
  }

  copyLatestInvite(): void {
    if (!this.latestInviteUrl) {
      return;
    }

    void navigator.clipboard.writeText(this.latestInviteUrl);
    this.successMessage = 'Link do convite copiado.';
  }

  formatDate(value: string): string {
    return new Date(value).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'America/Sao_Paulo',
    });
  }

  private loadInvites(): void {
    this.isLoading = true;
    this.residentInvitesService.listInvites().subscribe({
      next: (invites) => {
        this.invites = invites;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => this.handleError(err, 'Falha ao carregar convites.'),
    });
  }

  private handleError(err: HttpErrorResponse, fallback: string): void {
    this.isLoading = false;
    this.successMessage = '';

    if (err.status === 401) {
      this.authService.logout();
      return;
    }

    this.errorMessage = err.error?.detail ?? fallback;
    this.cdr.detectChanges();
  }
}

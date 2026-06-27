import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import {
  Ban,
  CalendarDays,
  Camera,
  Check,
  Clock3,
  Dumbbell,
  Landmark,
  ListOrdered,
  LucideAngularModule,
  MapPin,
  Plus,
  Timer,
  Trash2,
  Users,
  Waves,
  X,
} from 'lucide-angular';

import { AuthService } from '../../../../core/services/auth.service';
import { SchedulingService } from '../../../../core/services/scheduling.service';
import {
  BookablePlace,
  DashboardReservation,
  GuestPayload,
  Reservation,
  StatusReserva,
} from '../../../../core/models/scheduling.model';
import { AppHeaderComponent } from '../../../../shared/components/header/header';
import { ViewMode } from '../../../../core/models/ticket.model';

/** Grupo de formulário de um convidado (Nome + CPF). */
type GuestGroup = FormGroup<{ nome: FormControl<string>; cpf: FormControl<string> }>;

/** Validador de CPF: formato (11 dígitos) + dígitos verificadores. Espelha o backend. */
function cpfValidator(control: AbstractControl): ValidationErrors | null {
  const raw = String(control.value ?? '').replace(/\D/g, '');
  if (!raw) {
    return null; // ausência é tratada pelo Validators.required
  }
  if (raw.length !== 11 || /^(\d)\1{10}$/.test(raw)) {
    return { cpf: true };
  }
  for (const len of [9, 10]) {
    let soma = 0;
    for (let i = 0; i < len; i += 1) {
      soma += parseInt(raw[i], 10) * (len + 1 - i);
    }
    let digito = (soma * 10) % 11;
    if (digito === 10) {
      digito = 0;
    }
    if (digito !== parseInt(raw[len], 10)) {
      return { cpf: true };
    }
  }
  return null;
}

@Component({
  selector: 'app-scheduling-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, AppHeaderComponent],
  templateUrl: './scheduling-page.html',
  styleUrl: './scheduling-page.css',
})
export class SchedulingPageComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);

  readonly Ban = Ban;
  readonly CalendarDays = CalendarDays;
  readonly Camera = Camera;
  readonly Check = Check;
  readonly Clock3 = Clock3;
  readonly Dumbbell = Dumbbell;
  readonly Landmark = Landmark;
  readonly ListOrdered = ListOrdered;
  readonly MapPin = MapPin;
  readonly Plus = Plus;
  readonly Timer = Timer;
  readonly Trash2 = Trash2;
  readonly Users = Users;
  readonly Waves = Waves;
  readonly X = X;

  viewMode: ViewMode = 'MORADOR';
  currentUserId: number | null = null;
  places: BookablePlace[] = [];
  reservations: Reservation[] = [];
  myReservations: DashboardReservation[] = [];
  errorMessage = '';
  successMessage = '';
  isLoading = false;

  /** Pré-visualizações das fotos dos convidados (apenas exibição; não são enviadas). */
  guestPhotos: (string | null)[] = [];

  /** "Relógio" atualizado a cada segundo para os cronômetros regressivos. */
  now = Date.now();
  private timer?: ReturnType<typeof setInterval>;

  readonly placeForm = this.fb.nonNullable.group({
    nome: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(120)]],
    descricao: [''],
  });

  readonly reservationForm = this.fb.nonNullable.group({
    local_id: [0, [Validators.required, Validators.min(1)]],
    data: ['', Validators.required],
    inicio: ['', Validators.required],
    fim: ['', Validators.required],
    observacao: [''],
    convidados: this.fb.array<GuestGroup>([]),
  });

  constructor(
    private readonly schedulingService: SchedulingService,
    private readonly authService: AuthService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    if (!user) {
      this.authService.logout();
      return;
    }

    this.currentUserId = user.id;
    this.viewMode = user.perfil === 'ADMIN' ? 'SINDICO' : 'MORADOR';
    this.loadData();

    // Atualiza os cronômetros regressivos uma vez por segundo.
    this.timer = setInterval(() => {
      this.now = Date.now();
      this.cdr.detectChanges();
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  onViewModeChange(mode: ViewMode): void {
    this.viewMode = mode;
  }

  // --- Convidados (lista dinâmica) ---

  get convidados(): FormArray<GuestGroup> {
    return this.reservationForm.controls.convidados;
  }

  createGuestGroup(): GuestGroup {
    return this.fb.nonNullable.group({
      nome: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
      cpf: ['', [Validators.required, cpfValidator]],
    });
  }

  addGuest(): void {
    this.convidados.push(this.createGuestGroup());
    this.guestPhotos.push(null);
  }

  removeGuest(index: number): void {
    this.convidados.removeAt(index);
    this.guestPhotos.splice(index, 1);
  }

  /** Lê a foto apenas para pré-visualização local — não é enviada ao backend. */
  onGuestPhoto(event: Event, index: number): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      this.guestPhotos[index] = reader.result as string;
      this.cdr.detectChanges();
    };
    reader.readAsDataURL(file);
  }

  /** Aplica a máscara 000.000.000-00 enquanto o usuário digita. */
  maskCpf(index: number): void {
    const control = this.convidados.at(index).controls.cpf;
    const digits = String(control.value ?? '').replace(/\D/g, '').slice(0, 11);
    let masked = digits;
    if (digits.length > 9) {
      masked = `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
    } else if (digits.length > 6) {
      masked = `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
    } else if (digits.length > 3) {
      masked = `${digits.slice(0, 3)}.${digits.slice(3)}`;
    }
    control.setValue(masked, { emitEvent: false });
  }

  // --- Ações de reserva ---

  createPlace(): void {
    if (this.placeForm.invalid) {
      this.placeForm.markAllAsTouched();
      return;
    }

    const payload = this.placeForm.getRawValue();
    this.schedulingService
      .createPlace({
        nome: payload.nome.trim(),
        descricao: payload.descricao.trim() || null,
      })
      .subscribe({
        next: () => {
          this.placeForm.reset();
          this.successMessage = 'Local cadastrado com sucesso.';
          this.errorMessage = '';
          this.loadData();
        },
        error: (err) => this.handleError(err, 'Falha ao cadastrar local agendavel.'),
      });
  }

  createReservation(): void {
    if (this.reservationForm.invalid) {
      this.reservationForm.markAllAsTouched();
      this.errorMessage = 'Verifique os campos da reserva e os CPFs dos convidados.';
      this.successMessage = '';
      return;
    }

    const form = this.reservationForm.getRawValue();
    const inicio = `${form.data}T${form.inicio}:00`;
    const fim = `${form.data}T${form.fim}:00`;

    if (fim <= inicio) {
      this.errorMessage = 'O horario final precisa ser maior que o inicial.';
      this.successMessage = '';
      return;
    }

    if (new Date(inicio).getTime() <= Date.now()) {
      this.errorMessage = 'A reserva deve comecar em uma data/horario futuro.';
      this.successMessage = '';
      return;
    }

    const convidados: GuestPayload[] = form.convidados.map((g) => ({
      nome: g.nome.trim(),
      cpf: String(g.cpf).replace(/\D/g, ''),
    }));

    this.schedulingService
      .createReservation({
        local_id: Number(form.local_id),
        inicio,
        fim,
        observacao: form.observacao.trim() || null,
        convidados,
      })
      .subscribe({
        next: (reserva) => {
          this.reservationForm.patchValue({ inicio: '', fim: '', observacao: '' });
          this.convidados.clear();
          this.guestPhotos = [];
          this.successMessage = this.statusCreationMessage(reserva.status);
          this.errorMessage = '';
          this.loadData();
        },
        error: (err) => this.handleError(err, 'Falha ao criar reserva.'),
      });
  }

  confirmReservation(id: number): void {
    this.schedulingService.confirmReservation(id).subscribe({
      next: () => {
        this.successMessage = 'Reserva confirmada com sucesso.';
        this.errorMessage = '';
        this.loadData();
      },
      error: (err) => this.handleError(err, 'Falha ao confirmar a reserva.'),
    });
  }

  cancelReservation(id: number, override = false): void {
    const pergunta = override
      ? 'Revogar esta reserva (Hard Cancel)? Esta ação ignora regras de fila e tempo.'
      : 'Deseja realmente cancelar esta reserva?';
    if (!confirm(pergunta)) {
      return;
    }

    this.schedulingService.cancelReservation(id).subscribe({
      next: () => {
        this.successMessage = override ? 'Reserva revogada pelo sindico.' : 'Reserva cancelada.';
        this.errorMessage = '';
        this.loadData();
      },
      error: (err) => this.handleError(err, 'Falha ao cancelar a reserva.'),
    });
  }

  // --- Helpers de exibição ---

  formatDateTime(value: string): string {
    return new Date(value).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  formatTimeRange(reservation: Reservation): string {
    const start = new Date(reservation.inicio).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    });
    const end = new Date(reservation.fim).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    });

    return `${start} - ${end}`;
  }

  statusLabel(status: StatusReserva): string {
    switch (status) {
      case 'AGUARDANDO_FILA':
        return 'Aguardando na fila';
      case 'AGENDADO':
        return 'Agendado';
      case 'PENDENTE_CONFIRMACAO':
        return 'Ação necessária';
      case 'CONFIRMADO':
        return 'Confirmado';
      case 'EXPIRADO':
        return 'Expirado';
      case 'LIVRE_DEMANDA':
        return 'Livre demanda';
      case 'CANCELADO':
        return 'Cancelado';
      default:
        return status;
    }
  }

  /** Classe CSS do badge conforme o status. */
  statusClass(status: StatusReserva): string {
    switch (status) {
      case 'CONFIRMADO':
        return 'ok';
      case 'PENDENTE_CONFIRMACAO':
      case 'LIVRE_DEMANDA':
        return 'warn';
      case 'EXPIRADO':
      case 'CANCELADO':
        return 'danger';
      default:
        return 'info';
    }
  }

  /** Reservas que pedem ação imediata do morador (confirmação). */
  canConfirm(status: StatusReserva): boolean {
    return status === 'PENDENTE_CONFIRMACAO' || status === 'LIVRE_DEMANDA';
  }

  canCancel(status: StatusReserva): boolean {
    return status !== 'CANCELADO' && status !== 'EXPIRADO';
  }

  /** Cronômetro regressivo até o prazo de confirmação (em UTC). */
  countdown(prazo: string | null): string {
    if (!prazo) {
      return '';
    }
    const restante = this.parseUtc(prazo) - this.now;
    if (restante <= 0) {
      return 'Prazo encerrado';
    }
    const totalSeg = Math.floor(restante / 1000);
    const h = Math.floor(totalSeg / 3600);
    const m = Math.floor((totalSeg % 3600) / 60);
    const s = totalSeg % 60;
    const pad = (n: number) => String(n).padStart(2, '0');
    return h > 0 ? `${h}h ${pad(m)}m ${pad(s)}s` : `${pad(m)}m ${pad(s)}s`;
  }

  isOwner(reservation: Reservation): boolean {
    return this.currentUserId !== null && reservation.usuario_id === this.currentUserId;
  }

  get isAdmin(): boolean {
    return this.viewMode === 'SINDICO' && this.authService.getCurrentUser()?.perfil === 'ADMIN';
  }

  get upcomingReservations(): Reservation[] {
    return [...this.reservations].sort(
      (a, b) => new Date(a.inicio).getTime() - new Date(b.inicio).getTime(),
    );
  }

  private statusCreationMessage(status: StatusReserva): string {
    switch (status) {
      case 'AGUARDANDO_FILA':
        return 'Horario ja disputado: voce entrou na fila. Acompanhe sua posicao em "Minhas Reservas".';
      case 'LIVRE_DEMANDA':
        return 'Reserva criada em Livre Demanda. Confirme agora em "Minhas Reservas".';
      default:
        return 'Reserva criada. Confirme dentro do prazo quando solicitado.';
    }
  }

  /** Datas naive do backend são UTC; força a interpretação correta para o cronômetro. */
  private parseUtc(value: string): number {
    const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value);
    return new Date(hasZone ? value : `${value}Z`).getTime();
  }

  private loadData(): void {
    this.isLoading = true;
    this.schedulingService.listPlaces().subscribe({
      next: (places) => {
        this.places = places;
        if (places.length && !this.reservationForm.controls.local_id.value) {
          this.reservationForm.patchValue({ local_id: places[0].id });
        }
        this.loadReservations();
      },
      error: (err) => this.handleError(err, 'Falha ao carregar locais agendaveis.'),
    });
  }

  private loadReservations(): void {
    this.schedulingService.listReservations().subscribe({
      next: (reservations) => {
        this.reservations = reservations;
        this.loadMyReservations();
      },
      error: (err) => this.handleError(err, 'Falha ao carregar agendamentos.'),
    });
  }

  private loadMyReservations(): void {
    this.schedulingService.listMyReservations().subscribe({
      next: (mine) => {
        this.myReservations = mine;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => this.handleError(err, 'Falha ao carregar suas reservas.'),
    });
  }

  private handleError(err: HttpErrorResponse, fallback: string): void {
    this.isLoading = false;
    this.successMessage = '';

    if (err.status === 401 || err.status === 403) {
      if (err.status === 401) {
        this.authService.logout();
        return;
      }
      this.errorMessage = 'Seu perfil nao permite esta acao.';
    } else if (err.error?.detail) {
      this.errorMessage = typeof err.error.detail === 'string' ? err.error.detail : 'Dados invalidos.';
    } else {
      this.errorMessage = fallback;
    }

    this.cdr.detectChanges();
  }
}

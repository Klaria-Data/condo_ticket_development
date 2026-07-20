import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  CalendarDays,
  Clock3,
  Dumbbell,
  Landmark,
  LucideAngularModule,
  MapPin,
  Plus,
  Waves,
} from 'lucide-angular';

import { AuthService } from '../../../../core/services/auth.service';
import { SchedulingService } from '../../../../core/services/scheduling.service';
import { BookablePlace, Reservation } from '../../../../core/models/scheduling.model';
import { AppHeaderComponent } from '../../../../shared/components/header/header';
import { ViewMode } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-scheduling-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LucideAngularModule, AppHeaderComponent],
  templateUrl: './scheduling-page.html',
  styleUrl: './scheduling-page.css',
})
export class SchedulingPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);

  readonly CalendarDays = CalendarDays;
  readonly Clock3 = Clock3;
  readonly Dumbbell = Dumbbell;
  readonly Landmark = Landmark;
  readonly MapPin = MapPin;
  readonly Plus = Plus;
  readonly Waves = Waves;

  viewMode: ViewMode = 'MORADOR';
  places: BookablePlace[] = [];
  reservations: Reservation[] = [];
  errorMessage = '';
  successMessage = '';
  isLoading = false;
  selectedDuration = 1;

  readonly durations = [1, 2, 3];
  readonly openingHour = 8;
  readonly closingHour = 22;

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

    this.viewMode = user.perfil === 'ADMIN' ? 'SINDICO' : 'MORADOR';
    this.loadData();
  }

  onViewModeChange(mode: ViewMode): void {
    if (mode === 'SINDICO' && this.authService.getCurrentUser()?.perfil !== 'ADMIN') {
      return;
    }
    this.viewMode = mode;
  }

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
      return;
    }

    const form = this.reservationForm.getRawValue();
    const inicio = `${form.data}T${form.inicio}:00`;
    const fim = `${form.data}T${form.fim}:00`;

    if (fim <= inicio) {
      this.errorMessage = 'O horário final precisa ser maior que o inicial.';
      this.successMessage = '';
      return;
    }

    this.schedulingService
      .createReservation({
        local_id: Number(form.local_id),
        inicio,
        fim,
        observacao: form.observacao.trim() || null,
      })
      .subscribe({
        next: () => {
          this.reservationForm.patchValue({ inicio: '', fim: '', observacao: '' });
          this.successMessage = 'Reserva confirmada automaticamente.';
          this.errorMessage = '';
          this.loadData();
        },
        error: (err) => this.handleError(err, 'Falha ao criar reserva.'),
      });
  }

  get minBookingDate(): string {
    return this.formatDateForInput(new Date());
  }

  get availableSlots(): string[] {
    const slots: string[] = [];
    for (let hour = this.openingHour; hour < this.closingHour; hour += 1) {
      const slot = `${String(hour).padStart(2, '0')}:00`;
      if (!this.isSlotUnavailable(slot)) {
        slots.push(slot);
      }
    }
    return slots;
  }

  selectDuration(hours: number): void {
    this.selectedDuration = hours;
    const start = this.reservationForm.controls.inicio.value;
    if (start && this.isSlotUnavailable(start)) {
      this.clearSelectedTime();
    } else if (start) {
      this.setEndTime(start);
    }
  }

  selectSlot(start: string): void {
    if (this.isSlotUnavailable(start)) {
      return;
    }
    this.reservationForm.patchValue({ inicio: start });
    this.setEndTime(start);
    this.errorMessage = '';
  }

  onDateOrPlaceChange(): void {
    this.clearSelectedTime();
  }

  isSlotUnavailable(start: string): boolean {
    const form = this.reservationForm.getRawValue();
    if (!form.local_id || !form.data) {
      return true;
    }

    const startMinutes = this.toMinutes(start);
    const endMinutes = startMinutes + this.selectedDuration * 60;
    if (endMinutes > this.closingHour * 60) {
      return true;
    }

    return this.reservations.some((reservation) => {
      if (reservation.local_id !== Number(form.local_id) || this.reservationDate(reservation.inicio) !== form.data) {
        return false;
      }
      const reservedStart = this.toMinutes(this.reservationTime(reservation.inicio));
      const reservedEnd = this.toMinutes(this.reservationTime(reservation.fim));
      return startMinutes < reservedEnd && endMinutes > reservedStart;
    });
  }

  formatDateTime(value: string): string {
    return new Date(value).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Sao_Paulo',
    });
  }

  formatTimeRange(reservation: Reservation): string {
    const start = new Date(reservation.inicio).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Sao_Paulo',
    });
    const end = new Date(reservation.fim).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Sao_Paulo',
    });

    return `${start} - ${end}`;
  }

  get upcomingReservations(): Reservation[] {
    return [...this.reservations].sort(
      (a, b) => new Date(a.inicio).getTime() - new Date(b.inicio).getTime(),
    );
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

  private setEndTime(start: string): void {
    this.reservationForm.patchValue({ fim: this.toTime(this.toMinutes(start) + this.selectedDuration * 60) });
  }

  private clearSelectedTime(): void {
    this.reservationForm.patchValue({ inicio: '', fim: '' });
  }

  private toMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }

  private toTime(minutes: number): string {
    return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
  }

  private formatDateForInput(date: Date): string {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit',
    }).format(date);
  }

  private reservationDate(value: string): string {
    return this.formatDateForInput(new Date(value));
  }

  private reservationTime(value: string): string {
    return new Intl.DateTimeFormat('pt-BR', {
      timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
    }).format(new Date(value));
  }

  private loadReservations(): void {
    this.schedulingService.listReservations().subscribe({
      next: (reservations) => {
        this.reservations = reservations;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => this.handleError(err, 'Falha ao carregar agendamentos.'),
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
      this.errorMessage = 'Seu perfil não permite esta ação.';
    } else if (err.status === 409) {
      this.errorMessage = 'Horário indisponível para este local.';
    } else if (err.error?.detail) {
      this.errorMessage = err.error.detail;
    } else {
      this.errorMessage = fallback;
    }

    this.cdr.detectChanges();
  }
}

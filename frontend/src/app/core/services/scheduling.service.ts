import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  BookablePlace,
  CreateBookablePlacePayload,
  CreateReservationPayload,
  DashboardReservation,
  Reservation,
  UpdateReservationPayload,
} from '../models/scheduling.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class SchedulingService {
  private readonly apiBaseUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  listPlaces(): Observable<BookablePlace[]> {
    return this.http.get<BookablePlace[]>(`${this.apiBaseUrl}/locais-agendaveis`);
  }

  createPlace(payload: CreateBookablePlacePayload): Observable<BookablePlace> {
    return this.http.post<BookablePlace>(`${this.apiBaseUrl}/locais-agendaveis`, payload);
  }

  listReservations(): Observable<Reservation[]> {
    return this.http.get<Reservation[]>(`${this.apiBaseUrl}/agendamentos`);
  }

  /** Reservas do usuário logado, com posição na fila e prazo de confirmação. */
  listMyReservations(): Observable<DashboardReservation[]> {
    return this.http.get<DashboardReservation[]>(`${this.apiBaseUrl}/agendamentos/me`);
  }

  createReservation(payload: CreateReservationPayload): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiBaseUrl}/agendamentos`, payload);
  }

  updateReservation(id: number, payload: UpdateReservationPayload): Observable<Reservation> {
    return this.http.put<Reservation>(`${this.apiBaseUrl}/agendamentos/${id}`, payload);
  }

  /** Confirma a reserva (janela de 48h ou Livre Demanda / FCFS). */
  confirmReservation(id: number): Observable<Reservation> {
    return this.http.put<Reservation>(`${this.apiBaseUrl}/agendamentos/${id}/confirmar`, {});
  }

  /** Cancela a própria reserva ou, para o síndico, faz o Hard Cancel de qualquer reserva. */
  cancelReservation(id: number): Observable<Reservation> {
    return this.http.delete<Reservation>(`${this.apiBaseUrl}/agendamentos/${id}`);
  }
}

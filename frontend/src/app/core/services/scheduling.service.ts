import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  BookablePlace,
  CreateBookablePlacePayload,
  CreateReservationPayload,
  Reservation,
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

  createReservation(payload: CreateReservationPayload): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiBaseUrl}/agendamentos`, payload);
  }
}

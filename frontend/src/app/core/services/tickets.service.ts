import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Ticket } from '../models/ticket.model';

interface ApiTicket {
  id: number;
  usuario_id: number;
  titulo: string;
  descricao: string;
  imagem_url: string | null;
  status: 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO';
  data_criacao: string;
  data_atualizacao: string;
}

export interface CreateTicketPayload {
  titulo: string;
  descricao: string;
  imagem_url?: string | null;
}

@Injectable({ providedIn: 'root' })
export class TicketsService {
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';

  constructor(private readonly http: HttpClient) {}

  listTickets(residentName: string, apartment: string): Observable<Ticket[]> {
    return this.http.get<ApiTicket[]>(`${this.apiBaseUrl}/tickets`).pipe(
      map((tickets) => tickets.map((ticket) => this.toUiTicket(ticket, residentName, apartment))),
    );
  }

  createTicket(
    payload: CreateTicketPayload,
    residentName: string,
    apartment: string,
  ): Observable<Ticket> {
    return this.http.post<ApiTicket>(`${this.apiBaseUrl}/tickets`, payload).pipe(
      map((ticket) => this.toUiTicket(ticket, residentName, apartment)),
    );
  }

  private toUiTicket(ticket: ApiTicket, residentName: string, apartment: string): Ticket {
    return {
      id: ticket.id,
      title: ticket.titulo,
      description: ticket.descricao,
      status: ticket.status,
      residentName,
      apartment,
      createdAt: this.toShortDate(ticket.data_criacao),
      updatedAt: this.toShortDate(ticket.data_atualizacao),
      avatarColor: '#10bcd6',
    };
  }

  private toShortDate(rawDate: string): string {
    const date = new Date(rawDate);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
    });
  }
}

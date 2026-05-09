import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Ticket, TicketStatus } from '../models/ticket.model';

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
    // MOCK: Retorna dados fake para testar sem backend
    const mockTickets: Ticket[] = [
      {
        id: 1,
        title: 'Vazamento no banheiro',
        description: 'Há um vazamento contínuo na torneira do banheiro principal',
        status: 'ABERTO',
        residentName,
        apartment,
        createdAt: '09 mai',
        updatedAt: '09 mai',
        createdAtRaw: new Date().toISOString(),
        updatedAtRaw: new Date().toISOString(),
        avatarColor: '#10bcd6',
      },
      {
        id: 2,
        title: 'Lâmpada queimada no corredor',
        description: 'A lâmpada do corredor do terceiro andar queimou',
        status: 'EM_ANDAMENTO',
        residentName,
        apartment,
        createdAt: '08 mai',
        updatedAt: '08 mai',
        createdAtRaw: new Date().toISOString(),
        updatedAtRaw: new Date().toISOString(),
        avatarColor: '#ffa726',
      },
      {
        id: 3,
        title: 'Pintura da fachada',
        description: 'Necessário repintar a fachada do prédio',
        status: 'RESOLVIDO',
        residentName,
        apartment,
        createdAt: '07 mai',
        updatedAt: '07 mai',
        createdAtRaw: new Date().toISOString(),
        updatedAtRaw: new Date().toISOString(),
        avatarColor: '#66bb6a',
      },
    ];
    
    return new Observable((observer) => {
      observer.next(mockTickets);
      observer.complete();
    });
    
    // DESCOMENTE para usar a API real:
    // return this.http.get<ApiTicket[]>(`${this.apiBaseUrl}/tickets`).pipe(
    //   map((tickets) => tickets.map((ticket) => this.toUiTicket(ticket, residentName, apartment))),
    // );
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

  updateTicketStatus(
    ticketId: number,
    status: TicketStatus,
    residentName: string,
    apartment: string,
  ): Observable<Ticket> {
    console.log('[TicketsService] updateTicketStatus called:', { ticketId, status, url: `${this.apiBaseUrl}/tickets/${ticketId}/status` });
    
    return this.http
      .put<ApiTicket>(`${this.apiBaseUrl}/tickets/${ticketId}/status`, { status })
      .pipe(map((ticket) => this.toUiTicket(ticket, residentName, apartment)));
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
      createdAtRaw: ticket.data_criacao,
      updatedAtRaw: ticket.data_atualizacao,
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

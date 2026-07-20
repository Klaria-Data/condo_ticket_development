import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Ticket, TicketStatus } from '../models/ticket.model';
import { environment } from '../../../environments/environment';

/** Estrutura de um ticket retornada pela API (snake_case). */
interface ApiTicket {
  id: number;
  usuario_id: number;
  titulo: string;
  descricao: string;
  imagem_url: string | null;
  status: 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO';
  data_criacao: string;
  data_atualizacao: string;
  usuario_nome: string | null;
  unidade: string | null;
}

/** Payload para criar um novo ticket. */
export interface CreateTicketPayload {
  titulo: string;
  descricao: string;
  imagem_url?: string | null;
}

/**
 * Serviço de tickets — lista, cria e atualiza status dos chamados de suporte.
 *
 * Toda comunicação usa o token JWT injetado automaticamente pelo AuthInterceptor.
 */
@Injectable({ providedIn: 'root' })
export class TicketsService {
  private readonly apiBaseUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  /**
   * Lista todos os tickets visíveis para o usuário autenticado.
   * ADMIN vê todos; MORADOR vê apenas os seus.
   */
  listTickets(): Observable<Ticket[]> {
    return this.http.get<ApiTicket[]>(`${this.apiBaseUrl}/tickets`).pipe(
      map((tickets) => tickets.map((ticket) => this.toUiTicket(ticket))),
    );
  }

  /**
   * Cria um novo ticket de suporte.
   * O ticket sempre inicia com status ABERTO.
   */
  createTicket(payload: CreateTicketPayload): Observable<Ticket> {
    return this.http.post<ApiTicket>(`${this.apiBaseUrl}/tickets`, payload).pipe(
      map((ticket) => this.toUiTicket(ticket)),
    );
  }

  uploadImage(file: File): Observable<string> {
    const formData = new FormData();
    formData.append('image', file);
    return this.http
      .post<{ image_url: string }>(`${this.apiBaseUrl}/tickets/images`, formData)
      .pipe(map((response) => this.resolveImageUrl(response.image_url)));
  }

  /**
   * Atualiza o status de um ticket seguindo o fluxo ABERTO → EM_ANDAMENTO → RESOLVIDO.
   * Apenas usuários com perfil ADMIN podem executar esta ação.
   */
  updateTicketStatus(ticketId: number, status: TicketStatus): Observable<Ticket> {
    return this.http
      .put<ApiTicket>(`${this.apiBaseUrl}/tickets/${ticketId}/status`, { status })
      .pipe(map((ticket) => this.toUiTicket(ticket)));
  }

  /** Converte um ticket no formato da API para o formato usado pela UI. */
  private toUiTicket(ticket: ApiTicket): Ticket {
    return {
      id: ticket.id,
      title: ticket.titulo,
      description: ticket.descricao,
      status: ticket.status,
      residentName: ticket.usuario_nome ?? 'Desconhecido',
      apartment: ticket.unidade ?? '---',
      createdAt: this.toShortDate(ticket.data_criacao),
      updatedAt: this.toShortDate(ticket.data_atualizacao),
      createdAtRaw: ticket.data_criacao,
      updatedAtRaw: ticket.data_atualizacao,
      imageUrl: ticket.imagem_url ? this.resolveImageUrl(ticket.imagem_url) : undefined,
      avatarColor: '#10bcd6',
    };
  }

  /** Formata uma data ISO para exibição curta (ex: "09 mai"). */
  private toShortDate(rawDate: string): string {
    const date = new Date(rawDate);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      timeZone: 'America/Sao_Paulo',
    });
  }

  private resolveImageUrl(url: string): string {
    return url.startsWith('http') ? url : `${this.apiBaseUrl}${url}`;
  }
}

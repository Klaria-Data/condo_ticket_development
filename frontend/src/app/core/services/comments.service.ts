import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

/** Representa um comentário/mensagem de chat de um ticket. */
export interface Comment {
  id: number;
  ticket_id: number;
  usuario_id: number;
  mensagem: string;
  data_envio: string;
  usuario_nome: string | null;
}

/** Payload para criar um comentário. */
export interface CreateCommentPayload {
  mensagem: string;
}

/** Payload para editar um comentário existente. */
export interface UpdateCommentPayload {
  mensagem: string;
}

/**
 * Serviço de comentários — gerencia o chat dos tickets de suporte.
 *
 * Regras de permissão do backend:
 *   - Qualquer usuário autenticado pode listar e criar comentários.
 *   - Apenas o autor ou um ADMIN pode editar ou deletar.
 */
@Injectable({ providedIn: 'root' })
export class CommentsService {
  private readonly apiBaseUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  /**
   * Retorna todos os comentários de um ticket em ordem cronológica crescente.
   */
  getTicketComments(ticketId: number): Observable<Comment[]> {
    return this.http.get<Comment[]>(`${this.apiBaseUrl}/tickets/${ticketId}/comentarios`);
  }

  /**
   * Adiciona um novo comentário ao chat do ticket.
   * O comentário é automaticamente associado ao usuário autenticado.
   */
  createComment(ticketId: number, payload: CreateCommentPayload): Observable<Comment> {
    return this.http.post<Comment>(`${this.apiBaseUrl}/tickets/${ticketId}/comentarios`, payload);
  }

  /**
   * Edita a mensagem de um comentário existente.
   * Apenas o autor do comentário ou um ADMIN podem editar.
   */
  updateComment(ticketId: number, comentarioId: number, payload: UpdateCommentPayload): Observable<Comment> {
    return this.http.put<Comment>(
      `${this.apiBaseUrl}/tickets/${ticketId}/comentarios/${comentarioId}`,
      payload,
    );
  }

  /**
   * Remove permanentemente um comentário.
   * Apenas o autor do comentário ou um ADMIN podem deletar.
   * Retorna void em caso de sucesso (204 No Content).
   */
  deleteComment(ticketId: number, comentarioId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.apiBaseUrl}/tickets/${ticketId}/comentarios/${comentarioId}`,
    );
  }
}

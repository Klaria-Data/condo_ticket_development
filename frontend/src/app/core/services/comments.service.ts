import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Comment {
  id: number;
  ticket_id: number;
  usuario_id: number;
  mensagem: string;
  data_envio: string;
  usuario_nome: string | null;
}

export interface CreateCommentPayload {
  mensagem: string;
}

@Injectable({ providedIn: 'root' })
export class CommentsService {
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';
  private commentCounter = 100;

  constructor(private readonly http: HttpClient) {}

  getTicketComments(ticketId: number): Observable<Comment[]> {
    // MOCK: Retorna dados fake para testar sem backend
    const mockComments: Comment[] = [
      {
        id: 1,
        ticket_id: ticketId,
        usuario_id: 1,
        mensagem: 'O técnico foi acionado. Ele virá amanhã às 10:00.',
        data_envio: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 dias atrás
        usuario_nome: 'João Silva (Síndico)',
      },
      {
        id: 2,
        ticket_id: ticketId,
        usuario_id: 2,
        mensagem: 'Obrigado pela atenção! Fico aguardando o técnico.',
        data_envio: new Date(Date.now() - 1.8 * 24 * 60 * 60 * 1000).toISOString(),
        usuario_nome: 'Maria Santos (Morador)',
      },
      {
        id: 3,
        ticket_id: ticketId,
        usuario_id: 1,
        mensagem: 'Problema identificado! O vazamento vem do encanamento do andar acima. Estamos encaminhando a cobrança para o responsável.',
        data_envio: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 dia atrás
        usuario_nome: 'João Silva (Síndico)',
      },
    ];

    return new Observable((observer) => {
      observer.next(mockComments);
      observer.complete();
    });

    // DESCOMENTE para usar a API real:
    // return this.http.get<Comment[]>(`${this.apiBaseUrl}/tickets/${ticketId}/comentarios`);
  }

  createComment(ticketId: number, payload: CreateCommentPayload): Observable<Comment> {
    // MOCK: Retorna dados fake
    const newComment: Comment = {
      id: this.commentCounter++,
      ticket_id: ticketId,
      usuario_id: 1,
      mensagem: payload.mensagem,
      data_envio: new Date().toISOString(),
      usuario_nome: 'João Silva (Síndico)',
    };

    return new Observable((observer) => {
      observer.next(newComment);
      observer.complete();
    });

    // DESCOMENTE para usar a API real:
    // return this.http.post<Comment>(`${this.apiBaseUrl}/tickets/${ticketId}/comentarios`, payload);
  }
}

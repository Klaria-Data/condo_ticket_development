import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { of } from 'rxjs';
import { environment } from '../../../environments/environment';

/**
 * Interceptor de mock para desenvolvimento sem backend.
 *
 * Quando `environment.useMock = true`, intercepta todas as chamadas HTTP
 * e retorna dados falsos localmente, sem precisar do backend rodando.
 *
 * Para ligar o backend real, altere `useMock` para `false` em environment.ts.
 */

// ── Dados fixos de mock ───────────────────────────────────────────────────────

const MOCK_USER = {
  access_token: 'mock-jwt-token-dev',
  token_type: 'bearer',
  usuario_id: 1,
  nome: 'João Silva',
  unidade: '101',
  perfil: 'ADMIN',
};

const MOCK_TICKETS = [
  {
    id: 1,
    usuario_id: 1,
    titulo: 'Vazamento no banheiro',
    descricao: 'Há um vazamento contínuo na torneira do banheiro principal do corredor.',
    imagem_url: null,
    status: 'ABERTO',
    data_criacao: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    data_atualizacao: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    usuario_nome: 'Maria Santos',
    unidade: '202',
  },
  {
    id: 2,
    usuario_id: 2,
    titulo: 'Lâmpada queimada no corredor',
    descricao: 'A lâmpada do corredor do terceiro andar queimou e está sem iluminação.',
    imagem_url: null,
    status: 'EM_ANDAMENTO',
    data_criacao: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    data_atualizacao: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    usuario_nome: 'Carlos Oliveira',
    unidade: '305',
  },
  {
    id: 3,
    usuario_id: 3,
    titulo: 'Pintura da fachada',
    descricao: 'Necessário repintar a fachada do prédio — descascando em vários pontos.',
    imagem_url: null,
    status: 'RESOLVIDO',
    data_criacao: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    data_atualizacao: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    usuario_nome: 'Ana Roling',
    unidade: '410',
  },
];

const MOCK_COMMENTS: Record<number, unknown[]> = {
  1: [
    {
      id: 1,
      ticket_id: 1,
      usuario_id: 1,
      mensagem: 'O técnico foi acionado. Ele virá amanhã às 10:00.',
      data_envio: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      usuario_nome: 'João Silva',
    },
    {
      id: 2,
      ticket_id: 1,
      usuario_id: 2,
      mensagem: 'Obrigado pela atenção! Fico aguardando.',
      data_envio: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      usuario_nome: 'Maria Santos',
    },
  ],
  2: [
    {
      id: 3,
      ticket_id: 2,
      usuario_id: 1,
      mensagem: 'Trocar lâmpada agendado para esta semana.',
      data_envio: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      usuario_nome: 'João Silva',
    },
  ],
  3: [],
};

let nextCommentId = 100;
let nextTicketId = 10;

// ── Helpers ───────────────────────────────────────────────────────────────────

function ok(body: unknown, status = 200): HttpResponse<unknown> {
  return new HttpResponse({ status, body });
}

function noContent(): HttpResponse<unknown> {
  return new HttpResponse({ status: 204, body: null });
}

// ── Interceptor ───────────────────────────────────────────────────────────────

export const mockInterceptor: HttpInterceptorFn = (req, next) => {
  if (!environment.useMock) {
    return next(req);
  }

  const url = req.url.replace(/^https?:\/\/[^/]+/, '');
  const method = req.method;

  // POST /login
  if (method === 'POST' && url === '/login') {
    return of(ok(MOCK_USER));
  }

  // POST /registro
  if (method === 'POST' && url === '/registro') {
    const body = req.body as Record<string, unknown>;
    return of(ok({ id: 99, nome: body['nome'], email: body['email'], unidade: body['unidade'], perfil: body['perfil'] ?? 'MORADOR' }, 201));
  }

  // GET /tickets
  if (method === 'GET' && url === '/tickets') {
    return of(ok(MOCK_TICKETS));
  }

  // POST /tickets
  if (method === 'POST' && url === '/tickets') {
    const body = req.body as Record<string, string | null>;
    const novo = {
      id: nextTicketId++,
      usuario_id: 1,
      titulo: body['titulo'] ?? '',
      descricao: body['descricao'] ?? '',
      imagem_url: body['imagem_url'] ?? null,
      status: 'ABERTO',
      data_criacao: new Date().toISOString(),
      data_atualizacao: new Date().toISOString(),
      usuario_nome: MOCK_USER.nome,
      unidade: MOCK_USER.unidade,
    };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    MOCK_TICKETS.unshift(novo as any);
    return of(ok(novo, 201));
  }

  // PUT /tickets/{id}/status
  const statusMatch = url.match(/^\/tickets\/(\d+)\/status$/);
  if (method === 'PUT' && statusMatch) {
    const ticketId = parseInt(statusMatch[1]);
    const ticket = MOCK_TICKETS.find((t) => t.id === ticketId);
    if (ticket) {
      const body = req.body as Record<string, unknown>;
      ticket.status = body['status'] as string;
      ticket.data_atualizacao = new Date().toISOString();
    }
    return of(ok(ticket ?? null));
  }

  // GET /tickets/{id}/comentarios
  const commentsGetMatch = url.match(/^\/tickets\/(\d+)\/comentarios$/);
  if (method === 'GET' && commentsGetMatch) {
    const ticketId = parseInt(commentsGetMatch[1]);
    return of(ok(MOCK_COMMENTS[ticketId] ?? []));
  }

  // POST /tickets/{id}/comentarios
  if (method === 'POST' && commentsGetMatch) {
    const ticketId = parseInt(commentsGetMatch[1]);
    const body = req.body as Record<string, unknown>;
    const novo = {
      id: nextCommentId++,
      ticket_id: ticketId,
      usuario_id: MOCK_USER.usuario_id,
      mensagem: body['mensagem'],
      data_envio: new Date().toISOString(),
      usuario_nome: MOCK_USER.nome,
    };
    if (!MOCK_COMMENTS[ticketId]) MOCK_COMMENTS[ticketId] = [];
    MOCK_COMMENTS[ticketId].push(novo);
    return of(ok(novo, 201));
  }

  // PUT /tickets/{id}/comentarios/{cid}
  const commentEditMatch = url.match(/^\/tickets\/(\d+)\/comentarios\/(\d+)$/);
  if (method === 'PUT' && commentEditMatch) {
    const ticketId = parseInt(commentEditMatch[1]);
    const commentId = parseInt(commentEditMatch[2]);
    const body = req.body as Record<string, unknown>;
    const list = (MOCK_COMMENTS[ticketId] ?? []) as Array<Record<string, unknown>>;
    const comment = list.find((c) => c['id'] === commentId);
    if (comment) comment['mensagem'] = body['mensagem'];
    return of(ok(comment ?? null));
  }

  // DELETE /tickets/{id}/comentarios/{cid}
  if (method === 'DELETE' && commentEditMatch) {
    const ticketId = parseInt(commentEditMatch[1]);
    const commentId = parseInt(commentEditMatch[2]);
    const list = (MOCK_COMMENTS[ticketId] ?? []) as Array<Record<string, unknown>>;
    MOCK_COMMENTS[ticketId] = list.filter((c) => c['id'] !== commentId);
    return of(noContent());
  }

  return next(req);
};

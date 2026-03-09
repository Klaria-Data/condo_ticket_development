# CondoTicket Frontend

Aplicacao Angular responsavel por login, visualizacao e criacao de chamados.

## Stack

- Angular 21 (standalone)
- Angular Router
- HttpClient
- Interceptor para JWT

## Estrutura

```text
frontend/
  src/app/
    app.routes.ts
    app.config.ts
    core/
      guards/auth.guard.ts
      interceptors/auth.interceptor.ts
      services/
        auth.service.ts
        tickets.service.ts
    modules/
      auth/pages/login-page/
      tickets/pages/tickets-page/
```

## Setup

```bash
cd frontend
npm install
```

## Executar

```bash
cd frontend
npm start
```

Aplicacao em `http://localhost:4200`.

## Rotas

- `/login`: pagina publica de login
- `/`: pagina de tickets protegida por `authGuard`

Se nao autenticado, usuario e redirecionado para `/login`.

## Fluxo de autenticacao

1. Login envia credenciais para `POST /login`.
2. `AuthService` salva token e usuario no `localStorage`.
3. `auth.interceptor` injeta `Authorization: Bearer <token>` nas chamadas.
4. `auth.guard` protege a rota principal.
5. Respostas `401/403` levam a logout e redirecionamento.

Chaves no localStorage:

- `condoticket.jwt`
- `condoticket.user`

## Integracao com backend

`TicketsService` consome:

- `GET /tickets`
- `POST /tickets`

URL base atual no codigo:

- `http://127.0.0.1:8000`

## Modo de visualizacao

- `MORADOR`
- `SINDICO`

O modo inicial pode ser derivado do perfil retornado no login (`ADMIN` -> `SINDICO`).

## Build e testes

```bash
cd frontend
npm run build
npm test
```

## Problemas comuns

Erro de CORS no login:

- Garanta que o backend esteja com `CORS_ALLOW_ORIGINS` incluindo `http://localhost:4200`.

Erro 401/403 nas requisicoes:

- Token expirado/invalido remove sessao e redireciona para login.

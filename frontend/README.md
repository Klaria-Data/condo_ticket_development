# CondoTicket Frontend

Aplicacao Angular responsavel pela experiencia web do CondoTicket.

## Stack

- Angular 21 com standalone components
- Angular Router
- HttpClient
- Interceptors para JWT
- Lucide Angular para icones

## Estrutura

```text
frontend/src/app/
  core/
    guards/          # authGuard e adminGuard
    interceptors/    # JWT nas chamadas HTTP
    models/          # contratos usados pela UI
    services/        # clientes HTTP
  modules/
    auth/            # login
    tickets/         # chamados
    scheduling/      # agendamentos de areas compartilhadas
    residents/       # convites e aceite de moradores
  shared/
    components/      # header compartilhado
```

## Rotas

| Rota | Acesso | Descricao |
| --- | --- | --- |
| `/login` | Publico | Login |
| `/` | Autenticado | Chamados |
| `/agendamentos` | Autenticado | Reservas de areas compartilhadas |
| `/moradores` | ADMIN | Cadastro de moradores por convite |
| `/convite/:token` | Publico | Morador define sua senha |

## Permissoes na UI

- `authGuard` bloqueia rotas autenticadas.
- `adminGuard` bloqueia rotas exclusivas do sindico.
- O link `Moradores` aparece apenas para usuario com perfil `ADMIN`.
- O modo visual `MORADOR`/`SINDICO` nao substitui a permissao real do usuario.

## Integracao com a API

A URL base fica em `src/environments/environment.ts`.

Em desenvolvimento:

```ts
apiUrl: 'http://127.0.0.1:8000'
```

No fluxo de microservicos, `8000` e o nginx/API Gateway, que roteia para `auth`, `tickets` e `comments`.

Servicos HTTP principais:

| Service | Rotas usadas |
| --- | --- |
| `AuthService` | `/login` |
| `TicketsService` | `/tickets` |
| `CommentsService` | `/tickets/{id}/comentarios` |
| `SchedulingService` | `/locais-agendaveis`, `/agendamentos` |
| `ResidentInvitesService` | `/moradores/convites`, `/convites/{token}` |

## Executar

```bash
cd frontend
npm install
npm start
```

Aplicacao: http://localhost:4200

## Build

```bash
cd frontend
npm run build
```

## Observacoes

- O frontend espera que a API Gateway esteja em `http://127.0.0.1:8000`.
- Para apontar o frontend para outro backend, troque a `apiUrl` em
  `src/environments/environment.ts`. Ex.: monolito `backend/` na porta 8080 →
  `apiUrl: 'http://127.0.0.1:8080'`.
- Se a aplicacao se comportar como uma versao antiga da API, confirme quem atende a
  porta 8000 com `curl -s -I http://127.0.0.1:8000/login`. O header `server` mostra se
  e o gateway (`nginx`) ou um processo local (`uvicorn`) — os dois podem escutar a
  mesma porta, e o local ganha.
- Para testar convites sem SMTP, use o link retornado pela API ao criar o convite.
- Chaves usadas no `localStorage`:
  - `condoticket.jwt`
  - `condoticket.user`

# CondoTicket

Sistema de gestao de condominios com abertura e acompanhamento de chamados.

Repositorio em formato monorepo com:
- `frontend/`: SPA Angular 21
- `backend/`: API REST FastAPI + SQLAlchemy + MySQL + JWT

## Sumario

- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Tecnologias](#tecnologias)
- [Pre-requisitos](#pre-requisitos)
- [Configuracao Rapida](#configuracao-rapida)
- [Como Rodar](#como-rodar)
- [Autenticacao e Permissoes](#autenticacao-e-permissoes)
- [API](#api)
- [Fluxo do Frontend](#fluxo-do-frontend)
- [Comandos Uteis](#comandos-uteis)
- [Troubleshooting](#troubleshooting)

## Arquitetura

O projeto segue arquitetura cliente-servidor:

- Frontend Angular consome a API FastAPI via HTTP.
- Backend emite JWT no login e protege endpoints com Bearer Token.
- SQLAlchemy mapeia entidades e persiste no MySQL.
- Senhas sao armazenadas com hash Bcrypt (Passlib).

## Estrutura do Projeto

```text
condo_ticket_development/
	backend/
		app/
			database.py
			models.py
			schemas.py
			main.py
		requirements.txt
	frontend/
		src/
			app/
				core/
					guards/
					interceptors/
					models/
					services/
				modules/
					auth/
					tickets/
	README.md
```

## Tecnologias

Backend:
- FastAPI
- SQLAlchemy
- Pydantic
- PyJWT
- Passlib + Bcrypt
- PyMySQL

Frontend:
- Angular 21 (standalone components)
- Angular Router
- HttpClient + interceptor JWT

Banco:
- MySQL

## Pre-requisitos

- Python 3.11+ (ambiente testado com Python launcher `py`)
- Node.js 20+ (LTS recomendado)
- npm
- MySQL em execucao

## Configuracao Rapida

### 1. Backend

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Variaveis de ambiente (exemplo):

```bash
export DATABASE_URL="mysql+pymysql://root:senha@localhost:3306/condoticket"
export JWT_SECRET_KEY="troque-esta-chave"
export JWT_EXPIRE_MINUTES="60"
export CORS_ALLOW_ORIGINS="http://localhost:4200,http://127.0.0.1:4200"
```

### 2. Frontend

```bash
cd frontend
npm install
```

## Como Rodar

### Backend

```bash
cd backend
source .venv/Scripts/activate
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm start
```

- App: `http://localhost:4200`

### Execute com Docker Compose

```bash
docker compose up --build
```

Isso inicia:
- `backend` em `http://127.0.0.1:8000`
- `frontend` em `http://localhost:4200`
- `mysql` em `mysql:8.0` com banco `condoticket`

> O backend e o frontend são serviços independentes conectados via HTTP.

## Autenticacao e Permissoes

Perfis:
- `ADMIN` (sindico/gestao)
- `MORADOR`

Fluxo de autenticacao:
1. Usuario faz `POST /login`.
2. Backend retorna `access_token` JWT + dados do usuario.
3. Front salva token e usuario no `localStorage`.
4. Interceptor adiciona `Authorization: Bearer <token>` nas requisicoes.
5. Guards e tratamento de `401/403` redirecionam para `/login`.

Regra de visibilidade de chamados:
- `ADMIN`: lista todos os tickets.
- `MORADOR`: lista apenas tickets proprios.

## API

Endpoints principais:

- `POST /registro`
	Registra usuario com senha hasheada.

- `POST /login`
	Retorna JWT e dados do usuario.

- `GET /tickets` (protegido)
	Lista tickets conforme perfil.

- `POST /tickets` (protegido)
	Cria ticket com status inicial `ABERTO`.

Exemplo de login:

```bash
curl -X POST "http://127.0.0.1:8000/login" \
	-H "Content-Type: application/json" \
	-d '{"email":"user@teste.com","senha":"senha123456"}'
```

Exemplo de listagem com token:

```bash
curl -X GET "http://127.0.0.1:8000/tickets" \
	-H "Authorization: Bearer <TOKEN>"
```

## Fluxo do Frontend

- Roteamento:
	- `/login`: pagina publica de autenticacao
	- `/`: pagina de tickets protegida por `authGuard`

- Tickets:
	- Carregados via backend (sem uso de mock em runtime)
	- Criacao de ticket chama API protegida

## Comandos Uteis

Frontend:

```bash
cd frontend
npm start
npm run build
npm test
```

Backend:

```bash
cd backend
source .venv/Scripts/activate
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Troubleshooting

Erro de CORS:
- Verifique `CORS_ALLOW_ORIGINS` no backend.
- Garanta que frontend esteja em `http://localhost:4200`.

Erro de login sem redirecionamento:
- O guard exige token + usuario no `localStorage`.
- `401/403` no backend acionam `logout()` e redirecionamento.

Erro de conexao com MySQL:
- Verifique `DATABASE_URL`.
- Confirme se MySQL e banco `condoticket` estao ativos.

---

Documentacao detalhada adicional:
- `backend/README.md`
- `frontend/README.md`

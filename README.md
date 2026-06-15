# CondoTicket

Sistema de gestão de condomínios com abertura, acompanhamento e chat de chamados de suporte.

Monorepo com arquitetura de microsserviços:
- `services/auth/` — autenticação e emissão de tokens JWT
- `services/tickets/` — gestão de tickets de suporte
- `services/comments/` — chat/comentários dos tickets
- `services/shared/` — modelos e utilitários compartilhados
- `frontend/` — SPA Angular 21
- `nginx/` — API Gateway (roteamento entre microsserviços)

---

## Arquitetura

```
Browser (Angular :4200)
        │
        │  http://localhost:8000
        ▼
┌─────────────────────────────────────────────────────────┐
│                  nginx  (API Gateway)                   │
│                      porta 8000                         │
└──────────┬────────────────┬────────────────┬────────────┘
           │                │                │
    /registro, /login   /tickets/**    /tickets/*/comentarios
           │                │                │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │  auth       │  │  tickets    │  │  comments   │
    │  :8001      │  │  :8002      │  │  :8003      │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                │
           └────────────────┴────────────────┘
                            │
                     MySQL :3306
```

O frontend sempre aponta para `http://localhost:8000`. O nginx decide qual microsserviço responde com base na URL.

---

## Estrutura do Projeto

```
condo_ticket_development/
├── services/
│   ├── shared/              # Código compartilhado (ORM, JWT, banco)
│   │   ├── database.py
│   │   ├── models.py
│   │   └── auth_utils.py
│   ├── auth/                # POST /registro, POST /login
│   │   ├── app/main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── tickets/             # GET/POST /tickets, PUT /tickets/{id}/status
│   │   ├── app/main.py
│   │   ├── Dockerfile
│   │   └── README.md
│   └── comments/            # GET/POST/PUT/DELETE /tickets/{id}/comentarios
│       ├── app/main.py
│       ├── Dockerfile
│       └── README.md
├── nginx/
│   ├── nginx.conf           # Configuração do API Gateway
│   └── README.md
├── frontend/
│   └── src/
│       ├── environments/    # URLs de API por ambiente
│       └── app/
│           ├── core/        # Services, guards, interceptors, models
│           └── modules/     # Auth e Tickets (com chat de comentários)
├── docker-compose.yml       # Orquestra todos os 6 serviços
├── backend/                 # Código legado (referência histórica)
└── README.md
```

---

## Tecnologias

| Camada     | Tecnologia                                      |
|------------|-------------------------------------------------|
| Frontend   | Angular 21, standalone components, RxJS         |
| API Gateway| Nginx 1.25                                      |
| Microsserviços | FastAPI 0.116, Uvicorn                     |
| ORM        | SQLAlchemy 2.0                                  |
| Validação  | Pydantic 2.11                                   |
| Auth       | PyJWT 2.10, Passlib + Bcrypt                    |
| Banco      | MySQL 8.0, PyMySQL                              |
| Containers | Docker, Docker Compose                          |

---

## Pré-requisitos

Para rodar com Docker (recomendado): **Docker Desktop**

Para rodar localmente sem Docker:
- Python 3.11+
- Node.js 20+ e npm
- MySQL 8.0 em execução

---

## Como Rodar com Docker Compose

```bash
docker compose up --build
```

Serviços iniciados:
| Serviço   | URL pública                  |
|-----------|------------------------------|
| Frontend  | http://localhost:4200        |
| API       | http://localhost:8000        |
| MySQL     | localhost:3306               |

> **Nota:** O serviço `auth` é o único que cria as tabelas no banco (`create_all`).
> Os demais serviços aguardam o MySQL ficar saudável antes de iniciar.

---

## Como Rodar Localmente (sem Docker)

### 1. MySQL

Certifique-se de que o MySQL está rodando com o banco `condoticket` criado:

```sql
CREATE DATABASE IF NOT EXISTS condoticket;
```

### 2. Microsserviços Python

A partir da **raiz do monorepo**, execute cada serviço em um terminal diferente:

```bash
# Auth Service
PYTHONPATH=. uvicorn services.auth.app.main:app --port 8001 --reload

# Tickets Service
PYTHONPATH=. uvicorn services.tickets.app.main:app --port 8002 --reload

# Comments Service
PYTHONPATH=. uvicorn services.comments.app.main:app --port 8003 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm start
```

> Sem nginx local, aponte o `apiUrl` diretamente para um dos serviços conforme necessidade,
> ou use um proxy reverso local.

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz (ou exporte individualmente):

```env
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/condoticket
JWT_SECRET_KEY=troque-esta-chave-em-producao
JWT_EXPIRE_MINUTES=60
CORS_ALLOW_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
MYSQL_ROOT_PASSWORD=root
```

> **Importante:** `JWT_SECRET_KEY` deve ser a **mesma** em todos os microsserviços.

---

## Autenticação e Perfis

| Perfil    | Permissões                                                    |
|-----------|---------------------------------------------------------------|
| `ADMIN`   | Vê todos os tickets, atualiza status, edita/deleta qualquer comentário |
| `MORADOR` | Vê apenas seus tickets, cria tickets, comenta e edita/deleta os próprios comentários |

**Fluxo:**
1. `POST /login` → retorna `access_token` JWT
2. Frontend salva o token no `localStorage`
3. `AuthInterceptor` injeta `Authorization: Bearer <token>` em todas as requisições
4. `401/403` do backend acionam logout automático

---

## API — Referência de Endpoints

### Auth Service (`/registro`, `/login`)

| Método | Rota       | Auth | Descrição                         |
|--------|------------|:----:|------------------------------------|
| POST   | /registro  | Não  | Registra novo usuário              |
| POST   | /login     | Não  | Autentica e retorna token JWT      |

### Tickets Service (`/tickets`)

| Método | Rota                    | Auth | Perfil  | Descrição                                    |
|--------|-------------------------|:----:|:-------:|----------------------------------------------|
| GET    | /tickets                | Sim  | Qualquer| Lista tickets (ADMIN vê todos)               |
| POST   | /tickets                | Sim  | Qualquer| Cria ticket com status `ABERTO`              |
| PUT    | /tickets/{id}/status    | Sim  | ADMIN   | Avança status: ABERTO→EM_ANDAMENTO→RESOLVIDO |

### Comments Service (`/tickets/{id}/comentarios`)

| Método | Rota                                  | Auth | Perfil       | Descrição                    |
|--------|---------------------------------------|:----:|:------------:|------------------------------|
| GET    | /tickets/{id}/comentarios             | Sim  | Qualquer     | Lista comentários do ticket  |
| POST   | /tickets/{id}/comentarios             | Sim  | Qualquer     | Adiciona comentário          |
| PUT    | /tickets/{id}/comentarios/{cid}       | Sim  | Autor/ADMIN  | Edita mensagem do comentário |
| DELETE | /tickets/{id}/comentarios/{cid}       | Sim  | Autor/ADMIN  | Remove comentário (204)      |

**Documentação interativa:** cada serviço expõe `/docs` (Swagger UI) na sua porta local.

---

## Exemplos de uso com curl

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@teste.com","senha":"senha123456"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Listar tickets
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tickets

# Criar comentário
curl -X POST http://localhost:8000/tickets/1/comentarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mensagem":"Problema identificado, enviando técnico."}'

# Editar comentário
curl -X PUT http://localhost:8000/tickets/1/comentarios/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mensagem":"Técnico agendado para amanhã às 10h."}'

# Deletar comentário
curl -X DELETE http://localhost:8000/tickets/1/comentarios/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

**CORS error no browser:**
Verifique `CORS_ALLOW_ORIGINS` — deve incluir a origem do frontend (`http://localhost:4200`).

**502 Bad Gateway no nginx:**
Um dos microsserviços não subiu. Verifique os logs: `docker compose logs auth` / `tickets` / `comments`.

**MySQL não pronto (serviços caem no início):**
O `healthcheck` do MySQL aguarda até 100 segundos. Se persistir, verifique `MYSQL_ROOT_PASSWORD`.

**Token inválido / logout automático:**
O token expirou (padrão: 60 min) ou `JWT_SECRET_KEY` é diferente entre os serviços.

---

Documentação detalhada de cada serviço:
- [`services/auth/README.md`](services/auth/README.md)
- [`services/tickets/README.md`](services/tickets/README.md)
- [`services/comments/README.md`](services/comments/README.md)
- [`nginx/README.md`](nginx/README.md)

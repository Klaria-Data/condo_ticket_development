# CondoTicket

Sistema de gestao de condominio em monorepo, com frontend Angular e backend em microservicos FastAPI.

O projeto permite:
- abrir e acompanhar chamados de manutencao;
- comentar chamados em formato de conversa;
- reservar areas compartilhadas, como piscina e academia;
- convidar moradores por email para criarem a propria senha;
- separar permissoes entre sindico (`ADMIN`) e morador (`MORADOR`).

## Arquitetura Oficial

A arquitetura principal do projeto e a de microservicos em `services/`.

```text
frontend/ Angular (:4200)
        |
        | HTTP http://localhost:8000
        v
nginx/ API Gateway (:8000)
        |
        |-- services/auth     (:8001) login, registro e convites de moradores
        |-- services/tickets  (:8002) tickets, status e agendamentos
        |-- services/comments (:8003) comentarios dos tickets
        |
        v
mysql (:3306)
```

O diretorio `backend/` e mantido como backend monolitico de apoio para desenvolvimento local e testes rapidos. Ele nao e o desenho principal de producao do projeto.

## Estrutura

```text
condo_ticket_development/
  frontend/                 # SPA Angular
  nginx/                    # API Gateway dos microservicos
  services/
    shared/                 # ORM, banco e utilitarios de autenticacao
    auth/                   # /registro, /login, /moradores/convites, /convites
    tickets/                # /tickets, /locais-agendaveis, /agendamentos
    comments/               # /tickets/{id}/comentarios
  backend/                  # monolito de apoio/testes locais
  docker-compose.yml
```

## Como Rodar com Docker Compose

Recomendado para validar a arquitetura de microservicos:

```bash
docker compose up --build
```

Servicos publicos:

| Servico | URL |
| --- | --- |
| Frontend | http://localhost:4200 |
| API Gateway | http://localhost:8000 |
| MySQL | interno no Docker como `mysql:3306` |

Primeiro acesso local criado automaticamente pelo `auth` quando usar o `docker-compose.yml` padrao:

```text
Email: sindico@teste.com
Senha: senha123456
```

Essas credenciais sao apenas para desenvolvimento local. Em outro ambiente, sobrescreva as variaveis `SEED_ADMIN_*`.

## Como Rodar Localmente Sem Docker

Suba o MySQL com o banco `condoticket` criado:

```sql
CREATE DATABASE IF NOT EXISTS condoticket;
```

Em terminais separados, a partir da raiz do repositorio:

```bash
# Auth
PYTHONPATH=. uvicorn services.auth.app.main:app --host 127.0.0.1 --port 8001 --reload

# Tickets e agendamentos
PYTHONPATH=. uvicorn services.tickets.app.main:app --host 127.0.0.1 --port 8002 --reload

# Comentarios
PYTHONPATH=. uvicorn services.comments.app.main:app --host 127.0.0.1 --port 8003 --reload
```

Para usar as mesmas rotas do frontend, rode tambem o nginx ou um proxy equivalente na porta `8000`.

Frontend:

```bash
cd frontend
npm install
npm start
```

## Variaveis de Ambiente

Variaveis compartilhadas pelos servicos:

```env
DATABASE_URL=mysql+pymysql://root:root@mysql:3306/condoticket
JWT_SECRET_KEY=troque-esta-chave-em-producao
JWT_EXPIRE_MINUTES=60
CORS_ALLOW_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
MYSQL_ROOT_PASSWORD=root
```

Convites de moradores:

```env
FRONTEND_BASE_URL=http://localhost:4200
INVITE_EXPIRE_DAYS=7
SMTP_HOST=smtp.exemplo.com
SMTP_PORT=587
SMTP_USER=usuario
SMTP_PASSWORD=senha
SMTP_FROM=no-reply@condoticket.com
SEED_ADMIN_NAME=Sindico Teste
SEED_ADMIN_EMAIL=sindico@teste.com
SEED_ADMIN_PASSWORD=senha123456
SEED_ADMIN_UNIDADE=301
```

Se `SMTP_HOST` nao estiver configurado, o backend nao envia email real. Nesse caso, o link do convite e retornado pela API e registrado nos logs, o que ajuda no desenvolvimento local.

As variaveis `SEED_ADMIN_*` criam um sindico inicial se o e-mail ainda nao existir. Isso evita que um banco novo fique sem usuario administrador.

O MySQL nao e publicado no host por padrao para evitar conflito com instalacoes locais na porta `3306`. Para acessar o banco manualmente:

```bash
docker compose exec mysql mysql -uroot -proot condoticket
```

## Perfis

| Perfil | Permissoes |
| --- | --- |
| `ADMIN` | ve todos os chamados, atualiza status, cadastra locais agendaveis, convida moradores |
| `MORADOR` | cria chamados, ve seus chamados, comenta, reserva locais disponiveis |

## Principais Rotas da API

### Auth Service

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| POST | `/registro` | Nao | - | Registra usuario diretamente |
| POST | `/login` | Nao | - | Autentica e retorna JWT |
| POST | `/moradores/convites` | Sim | ADMIN | Cria convite para morador |
| GET | `/moradores/convites` | Sim | ADMIN | Lista convites enviados |
| GET | `/convites/{token}` | Nao | - | Consulta convite valido |
| POST | `/convites/{token}/aceitar` | Nao | - | Cria senha e ativa morador |

### Tickets Service

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| GET | `/tickets` | Sim | Qualquer | Lista chamados visiveis |
| POST | `/tickets` | Sim | Qualquer | Abre chamado |
| PUT | `/tickets/{id}/status` | Sim | ADMIN | Avanca status |
| GET | `/locais-agendaveis` | Sim | Qualquer | Lista locais reservaveis |
| POST | `/locais-agendaveis` | Sim | ADMIN | Cadastra local reservavel |
| GET | `/agendamentos` | Sim | Qualquer | Lista reservas |
| POST | `/agendamentos` | Sim | Qualquer | Reserva local se horario estiver livre |

### Comments Service

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| GET | `/tickets/{id}/comentarios` | Sim | Qualquer | Lista comentarios |
| POST | `/tickets/{id}/comentarios` | Sim | Qualquer | Cria comentario |
| PUT | `/tickets/{id}/comentarios/{cid}` | Sim | Autor/ADMIN | Edita comentario |
| DELETE | `/tickets/{id}/comentarios/{cid}` | Sim | Autor/ADMIN | Remove comentario |

## Frontend

Rotas principais:

| Rota | Acesso | Descricao |
| --- | --- | --- |
| `/login` | Publico | Login |
| `/` | Autenticado | Chamados |
| `/agendamentos` | Autenticado | Reservas de areas compartilhadas |
| `/moradores` | ADMIN | Cadastro de moradores por convite |
| `/convite/:token` | Publico | Morador define senha pelo convite |

## Testes e Build

Backend monolitico de apoio:

```bash
python -m pytest backend/tests
```

Frontend:

```bash
cd frontend
npm run build
```

## Observacoes de Manutencao

- A pasta `services/` deve ser a fonte principal para novas regras de backend.
- A pasta `backend/` existe para compatibilidade e testes locais; evite adicionar features novas apenas nela.
- Sempre que criar rota nova, atualize `nginx/nginx.conf` e este README.
- Sempre que adicionar tela nova, atualize `frontend/README.md`.

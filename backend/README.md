# CondoTicket Backend

API REST em FastAPI para autenticacao e gestao de tickets do CondoTicket.

## Stack

- FastAPI
- SQLAlchemy
- Pydantic
- PyJWT
- Passlib (Bcrypt)
- MySQL (PyMySQL)

## Estrutura

```text
backend/
  app/
    database.py   # conexao SQLAlchemy
    models.py     # entidades e relacionamentos
    schemas.py    # validacao/serializacao
    main.py       # endpoints e regras de auth
  requirements.txt
```

## Variaveis de ambiente

- `DATABASE_URL`
  Exemplo: `mysql+pymysql://root:senha@localhost:3306/condoticket`
- `JWT_SECRET_KEY`
- `JWT_EXPIRE_MINUTES`
- `CORS_ALLOW_ORIGINS`
  Exemplo: `http://localhost:4200,http://127.0.0.1:4200`

## Setup

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

## Executar

```bash
cd backend
source .venv/Scripts/activate
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

## Endpoints

### `POST /registro`

Cria usuario com senha hasheada.

Request:

```json
{
  "nome": "Joao Silva",
  "email": "joao@teste.com",
  "senha": "senha123456",
  "unidade": "101",
  "perfil": "MORADOR"
}
```

### `POST /login`

Autentica usuario e retorna token.

Response (exemplo):

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "usuario_id": 1,
  "nome": "Joao Silva",
  "unidade": "101",
  "perfil": "MORADOR"
}
```

### `GET /tickets` (protegido)

- `ADMIN`: todos os tickets
- `MORADOR`: apenas tickets do proprio usuario

Header:

```text
Authorization: Bearer <jwt>
```

### `POST /tickets` (protegido)

Cria ticket para o usuario logado.

Request:

```json
{
  "titulo": "Vazamento no banheiro",
  "descricao": "Descricao detalhada do problema",
  "imagem_url": null
}
```

## Regras de negocio implementadas

- Perfis: `ADMIN` e `MORADOR`
- Senha com hash Bcrypt
- Status de ticket: `ABERTO`, `EM_ANDAMENTO`, `RESOLVIDO`
- Novo ticket inicia em `ABERTO`
- Endpoints protegidos exigem JWT Bearer

## Banco de dados

Tabelas mapeadas:

- `USUARIO`
- `TICKET`
- `POSTAGEM_FORUM`
- `COMENTARIO_TICKET`
- `COMENTARIO_FORUM`

Observacao: `Base.metadata.create_all()` cria estrutura inicial automaticamente ao subir a API.

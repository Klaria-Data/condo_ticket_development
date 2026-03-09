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

As tabelas podem ser criadas a partir do sequinte script SQL:

CREATE DATABASE condoticket;
USE condoticket;
-- 1. Tabela USUARIO
CREATE TABLE USUARIO (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL COMMENT 'Nome completo do morador/síndico',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT 'Login único no sistema',
    senha_hash VARCHAR(255) NOT NULL COMMENT 'Senha encriptada (Bcrypt)',
    unidade VARCHAR(50) NOT NULL COMMENT 'Identificação (Ex: Apt 101 Bloco B)',
    perfil ENUM('ADMIN', 'MORADOR') NOT NULL DEFAULT 'MORADOR' COMMENT 'Define permissões',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data de registo no sistema'
);

-- 2. Tabela TICKET
CREATE TABLE TICKET (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL COMMENT 'Quem abriu o ticket',
    titulo VARCHAR(100) NOT NULL COMMENT 'Resumo curto do problema',
    descricao TEXT NOT NULL COMMENT 'Detalhamento completo da ocorrência',
    imagem_url VARCHAR(255) DEFAULT NULL COMMENT 'Link da imagem salva no S3 (Opcional)',
    status ENUM('ABERTO', 'EM_ANDAMENTO', 'RESOLVIDO') NOT NULL DEFAULT 'ABERTO' COMMENT 'Fluxo de status',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Quando foi aberto',
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última mudança',
    FOREIGN KEY (usuario_id) REFERENCES USUARIO(id) ON DELETE CASCADE
);

-- 3. Tabela POSTAGEM_FORUM
CREATE TABLE POSTAGEM_FORUM (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL COMMENT 'Quem criou o tópico',
    titulo VARCHAR(150) NOT NULL COMMENT 'Assunto principal',
    conteudo TEXT NOT NULL COMMENT 'Texto da postagem',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data da publicação',
    FOREIGN KEY (usuario_id) REFERENCES USUARIO(id) ON DELETE CASCADE
);

-- 4. Tabela COMENTARIO_TICKET
CREATE TABLE COMENTARIO_TICKET (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL COMMENT 'Vínculo com o ticket',
    usuario_id INT NOT NULL COMMENT 'Autor do comentário',
    mensagem TEXT NOT NULL COMMENT 'Conteúdo da resposta',
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data e hora da mensagem',
    FOREIGN KEY (ticket_id) REFERENCES TICKET(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES USUARIO(id) ON DELETE CASCADE
);

-- 5. Tabela COMENTARIO_FORUM
CREATE TABLE COMENTARIO_FORUM (
    id INT AUTO_INCREMENT PRIMARY KEY,
    postagem_id INT NOT NULL COMMENT 'Vínculo com o tópico',
    usuario_id INT NOT NULL COMMENT 'Quem respondeu',
    conteudo TEXT NOT NULL COMMENT 'Texto da resposta',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data da resposta',
    FOREIGN KEY (postagem_id) REFERENCES POSTAGEM_FORUM(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES USUARIO(id) ON DELETE CASCADE
);


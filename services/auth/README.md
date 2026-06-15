# Auth Service

Responsável pelo registro de usuários e emissão de tokens JWT.

## Endpoints

| Método | Rota       | Autenticação | Descrição                        |
|--------|------------|:------------:|----------------------------------|
| POST   | /registro  | Não          | Registra novo usuário            |
| POST   | /login     | Não          | Autentica e retorna token JWT    |

## Variáveis de Ambiente

| Variável            | Padrão                                          | Descrição                          |
|---------------------|-------------------------------------------------|------------------------------------|
| `DATABASE_URL`      | `mysql+pymysql://root:root@localhost:3306/condoticket` | URL de conexão MySQL        |
| `JWT_SECRET_KEY`    | `change-me-in-production`                       | Chave de assinatura JWT (**troque em prod!**) |
| `JWT_EXPIRE_MINUTES`| `60`                                            | Duração do token em minutos        |
| `CORS_ALLOW_ORIGINS`| `http://localhost:4200,http://127.0.0.1:4200`   | Origins permitidas para CORS       |

## Rodando Localmente (sem Docker)

A partir da raiz do monorepo:

```bash
PYTHONPATH=. uvicorn services.auth.app.main:app --port 8001 --reload
```

## Notas de Arquitetura

- Este é o **único** serviço que chama `Base.metadata.create_all` — ele cria todas as tabelas no banco ao subir.
- O token JWT gerado aqui é validado pelos demais serviços via `services/shared/auth_utils.py`.
- A mesma `JWT_SECRET_KEY` deve ser configurada em todos os serviços.

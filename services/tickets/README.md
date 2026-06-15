# Tickets Service

Responsável pela criação, listagem e atualização de status dos tickets de suporte.

## Endpoints

| Método | Rota                        | Auth  | Perfil     | Descrição                             |
|--------|-----------------------------|:-----:|:----------:|---------------------------------------|
| GET    | /tickets                    | Sim   | Qualquer   | Lista tickets (ADMIN vê todos)        |
| POST   | /tickets                    | Sim   | Qualquer   | Abre novo ticket (status = ABERTO)    |
| PUT    | /tickets/{id}/status        | Sim   | ADMIN      | Avança status do ticket               |

## Fluxo de Status

```
ABERTO → EM_ANDAMENTO → RESOLVIDO
```

Pular etapas (ex: ABERTO → RESOLVIDO) retorna `400 Bad Request`.

## Campos Retornados em `GET /tickets`

O campo `usuario_nome` e `unidade` são incluídos na resposta para que o frontend
possa exibir o nome do morador sem precisar fazer uma segunda requisição.

## Variáveis de Ambiente

| Variável            | Padrão                                          | Descrição                    |
|---------------------|-------------------------------------------------|------------------------------|
| `DATABASE_URL`      | `mysql+pymysql://root:root@localhost:3306/condoticket` | URL de conexão MySQL  |
| `JWT_SECRET_KEY`    | `change-me-in-production`                       | Mesma chave do auth service  |
| `JWT_EXPIRE_MINUTES`| `60`                                            | Duração do token             |
| `CORS_ALLOW_ORIGINS`| `http://localhost:4200,http://127.0.0.1:4200`   | Origins CORS permitidas      |

## Rodando Localmente

```bash
PYTHONPATH=. uvicorn services.tickets.app.main:app --port 8002 --reload
```

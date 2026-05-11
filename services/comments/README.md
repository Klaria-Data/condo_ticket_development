# Comments Service

Responsável pelo chat/comentários dos tickets — listar, criar, editar e deletar mensagens.

## Endpoints

| Método | Rota                                          | Auth | Perfil        | Descrição                              |
|--------|-----------------------------------------------|:----:|:-------------:|----------------------------------------|
| GET    | /tickets/{id}/comentarios                     | Sim  | Qualquer      | Lista comentários do ticket            |
| POST   | /tickets/{id}/comentarios                     | Sim  | Qualquer      | Adiciona comentário ao ticket          |
| PUT    | /tickets/{id}/comentarios/{cid}               | Sim  | Autor / ADMIN | Edita mensagem do comentário           |
| DELETE | /tickets/{id}/comentarios/{cid}               | Sim  | Autor / ADMIN | Remove comentário (204 No Content)     |

## Regras de Permissão

- **Listar e criar**: qualquer usuário autenticado (MORADOR ou ADMIN).
- **Editar e deletar**: apenas o **autor** do comentário ou um **ADMIN**.
  - Retorna `403 Forbidden` se o usuário não tiver permissão.
  - Retorna `404 Not Found` se o comentário não existir no ticket informado.

## Variáveis de Ambiente

| Variável            | Padrão                                          | Descrição                    |
|---------------------|-------------------------------------------------|------------------------------|
| `DATABASE_URL`      | `mysql+pymysql://root:root@localhost:3306/condoticket` | URL de conexão MySQL  |
| `JWT_SECRET_KEY`    | `change-me-in-production`                       | Mesma chave do auth service  |
| `JWT_EXPIRE_MINUTES`| `60`                                            | Duração do token             |
| `CORS_ALLOW_ORIGINS`| `http://localhost:4200,http://127.0.0.1:4200`   | Origins CORS permitidas      |

## Rodando Localmente

```bash
PYTHONPATH=. uvicorn services.comments.app.main:app --port 8003 --reload
```

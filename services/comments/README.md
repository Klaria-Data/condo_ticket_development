# Comments Service

Microsservico responsavel pelos comentarios dos chamados.

Porta interna: `8003`.

## Responsabilidades

- Listar comentarios de um chamado visivel ao usuario.
- Criar comentarios em um chamado visivel ao usuario.
- Editar comentarios do proprio autor ou de qualquer usuario quando o perfil for `ADMIN`.
- Remover comentarios do proprio autor ou de qualquer usuario quando o perfil for `ADMIN`.

A visibilidade segue a mesma regra de `GET /tickets`: o `MORADOR` so acessa os
comentarios dos chamados que ele abriu; o `ADMIN` acessa os de todos. Chamado de
outro morador responde `403`.

## Endpoints

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| GET | `/tickets/{id}/comentarios` | Sim | Dono/ADMIN | Lista comentarios |
| POST | `/tickets/{id}/comentarios` | Sim | Dono/ADMIN | Cria comentario |
| PUT | `/tickets/{id}/comentarios/{cid}` | Sim | Autor/ADMIN | Edita comentario |
| DELETE | `/tickets/{id}/comentarios/{cid}` | Sim | Autor/ADMIN | Remove comentario |

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
| --- | --- | --- |
| `DATABASE_URL` | `mysql+pymysql://root:root@localhost:3306/condoticket` | URL do MySQL |
| `JWT_SECRET_KEY` | `change-me-in-production` | Mesma chave do auth service |
| `JWT_EXPIRE_MINUTES` | `60` | Duracao do token |
| `CORS_ALLOW_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | Origins permitidas |

## Rodar Localmente

A partir da raiz do monorepo:

```bash
PYTHONPATH=. uvicorn services.comments.app.main:app --host 127.0.0.1 --port 8003 --reload
```

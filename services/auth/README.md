# Auth Service

Microsservico responsavel por autenticacao, registro direto e convites de moradores.

Porta interna: `8001`.

## Responsabilidades

- Registrar usuarios via `/registro`.
- Autenticar usuarios via `/login`.
- Gerar convites para moradores.
- Permitir que o morador aceite o convite e defina a propria senha.
- Criar as tabelas do banco ao iniciar (`Base.metadata.create_all`).

## Endpoints

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| POST | `/registro` | Nao | - | Registra usuario diretamente (sempre como MORADOR) |
| POST | `/login` | Nao | - | Retorna JWT |
| POST | `/moradores/convites` | Sim | ADMIN | Cria convite para morador |
| GET | `/moradores/convites` | Sim | ADMIN | Lista convites enviados |
| GET | `/convites/{token}` | Nao | - | Consulta dados publicos do convite |
| POST | `/convites/{token}/aceitar` | Nao | - | Cria morador com senha escolhida |

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
| --- | --- | --- |
| `DATABASE_URL` | `mysql+pymysql://root:root@localhost:3306/condoticket` | URL do MySQL |
| `JWT_SECRET_KEY` | `change-me-in-production` | Chave de assinatura JWT |
| `JWT_EXPIRE_MINUTES` | `60` | Duracao do token |
| `CORS_ALLOW_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | Origins permitidas |
| `FRONTEND_BASE_URL` | `http://127.0.0.1:4200` | Base para montar link de convite |
| `INVITE_EXPIRE_DAYS` | `7` | Validade do convite |
| `SMTP_HOST` | vazio | Host SMTP para envio real de email |
| `SMTP_PORT` | `587` | Porta SMTP |
| `SMTP_USER` | vazio | Usuario SMTP |
| `SMTP_PASSWORD` | vazio | Senha SMTP |
| `SMTP_FROM` | usuario SMTP ou fallback | Remetente do email |
| `SEED_ADMIN_NAME` | vazio | Nome do sindico inicial |
| `SEED_ADMIN_EMAIL` | vazio | Email do sindico inicial |
| `SEED_ADMIN_PASSWORD` | vazio | Senha do sindico inicial |
| `SEED_ADMIN_UNIDADE` | `000` | Unidade do sindico inicial |
| `SEED_RESIDENT_NAME` | vazio | Nome do morador inicial |
| `SEED_RESIDENT_EMAIL` | vazio | E-mail do morador inicial |
| `SEED_RESIDENT_PASSWORD` | vazio | Senha do morador inicial |
| `SEED_RESIDENT_UNIDADE` | `000` | Unidade do morador inicial |

Sem `SMTP_HOST`, o convite nao e enviado por email real. O link e retornado na resposta e registrado em log para desenvolvimento.

Quando as variáveis de seed estão configuradas, o serviço cria os usuários na inicialização se os e-mails ainda não existirem. O `docker-compose.yml` já define um administrador e um morador locais:

```text
Síndico
Email: sindico@teste.com
Senha: senha123456

Morador
Email: morador@teste.com
Senha: senha123456
```

## Rodar Localmente

A partir da raiz do monorepo:

```bash
PYTHONPATH=. uvicorn services.auth.app.main:app --host 127.0.0.1 --port 8001 --reload
```

## Exemplo de Convite

```bash
curl -X POST http://localhost:8000/moradores/convites \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria Silva","email":"maria@teste.com","unidade":"302"}'
```

Resposta inclui `convite_url` quando o convite e criado.

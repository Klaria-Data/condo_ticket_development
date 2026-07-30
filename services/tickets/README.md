# Tickets Service

Microsservico responsavel por chamados de suporte e agendamentos de areas compartilhadas.

Porta interna: `8002`.

## Responsabilidades

- Criar e listar chamados.
- Atualizar status de chamados seguindo o fluxo permitido.
- Cadastrar locais agendaveis, como piscina, academia ou salao.
- Listar e criar reservas de locais compartilhados.
- Bloquear reservas com horarios sobrepostos para o mesmo local.

## Endpoints de Chamados

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| GET | `/tickets` | Sim | Qualquer | Lista todos os chamados do condominio |
| POST | `/tickets` | Sim | Qualquer | Cria chamado com status `ABERTO` |
| PUT | `/tickets/{id}/status` | Sim | ADMIN | Avanca status do chamado |

## Fluxo de Status

```text
ABERTO -> EM_ANDAMENTO -> RESOLVIDO
```

Pular etapas retorna `400 Bad Request`.

## Endpoints de Agendamento

| Metodo | Rota | Auth | Perfil | Descricao |
| --- | --- | --- | --- | --- |
| GET | `/locais-agendaveis` | Sim | Qualquer | Lista locais ativos |
| POST | `/locais-agendaveis` | Sim | ADMIN | Cadastra local agendavel |
| GET | `/agendamentos` | Sim | Qualquer | Lista reservas |
| POST | `/agendamentos` | Sim | Qualquer | Cria reserva se horario estiver livre |

## Regra de Conflito

Uma reserva e recusada com `409 Conflict` quando existe outra reserva do mesmo local com sobreposicao de horario:

```text
reserva_existente.inicio < novo_fim
reserva_existente.fim > novo_inicio
```

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
PYTHONPATH=. uvicorn services.tickets.app.main:app --host 127.0.0.1 --port 8002 --reload
```

## Exemplos

Criar local agendavel:

```bash
curl -X POST http://localhost:8000/locais-agendaveis \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Piscina","descricao":"Area externa"}'
```

Criar reserva:

```bash
curl -X POST http://localhost:8000/agendamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"local_id":1,"inicio":"2027-01-02T13:00:00","fim":"2027-01-02T17:00:00"}'
```

# Nginx API Gateway

O nginx e o ponto de entrada publico da API na arquitetura de microservicos.

Porta publica: `8000`.

O frontend chama `http://localhost:8000` e o nginx encaminha a requisicao para o microsservico correto.

## Mapa de Rotas

| URL | Servico destino | Porta interna |
| --- | --- | --- |
| `/registro` | auth | 8001 |
| `/login` | auth | 8001 |
| `/moradores/convites` | auth | 8001 |
| `/convites/{token}` | auth | 8001 |
| `/tickets` | tickets | 8002 |
| `/tickets/{id}/status` | tickets | 8002 |
| `/locais-agendaveis` | tickets | 8002 |
| `/agendamentos` | tickets | 8002 |
| `/tickets/{id}/comentarios` | comments | 8003 |

## Ordem dos Blocos `location`

A ordem importa.

Rotas especificas devem vir antes de rotas mais gerais. Por isso:

- `/tickets/{id}/comentarios` vem antes de `/tickets`;
- rotas de auth e convite ficam antes das rotas de tickets;
- agendamentos e locais ficam apontados para `tickets`.

## Como Adicionar Nova Rota

1. Confirme qual microsservico e dono da regra.
2. Adicione o `location` no `nginx/nginx.conf`.
3. Atualize este README e o README raiz.
4. Se for um novo servico, adicione tambem no `docker-compose.yml`.

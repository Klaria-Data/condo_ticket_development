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

## Solucao de Problemas

### `502 Bad Gateway` depois de recriar um servico

O nginx resolve o nome dos upstreams uma unica vez, na inicializacao, e guarda o IP.
Quando um container e recriado ele ganha um IP novo e o gateway continua tentando o
antigo (`connect() failed (111: Connection refused)` no log). Reinicie o gateway:

```bash
docker compose restart nginx
```

### As respostas nao passam pelo nginx

Se um processo local escutar em `127.0.0.1:8000`, ele vence o `0.0.0.0:8000` publicado
pelo Docker, porque o bind e mais especifico. O gateway fica de pe, sem receber nada, e
o log de acesso do nginx fica vazio. Confirme quem responde:

```bash
curl -s -I http://127.0.0.1:8000/login
```

O header `server: nginx/1.25.5` confirma o gateway. `server: uvicorn` indica um
processo local na porta — normalmente o monolito de apoio `backend/`.

Para rodar os dois ao mesmo tempo, deixe o gateway na `8000` e o monolito em outra
porta, apontando a `apiUrl` do frontend para ela. As duas configuracoes estao
descritas em `backend/README.md`.

## Como Adicionar Nova Rota

1. Confirme qual microsservico e dono da regra.
2. Adicione o `location` no `nginx/nginx.conf`.
3. Atualize este README e o README raiz.
4. Se for um novo servico, adicione tambem no `docker-compose.yml`.

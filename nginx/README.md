# Nginx — API Gateway

O nginx atua como ponto de entrada único para toda a API (porta 8000).
O frontend sempre chama `http://localhost:8000`; o nginx roteia internamente para o microsserviço correto.

## Mapa de Roteamento

| URL Pattern                          | Serviço destino    | Porta interna |
|--------------------------------------|--------------------|:-------------:|
| `/registro`, `/login`                | auth-service       | 8001          |
| `/tickets/{id}/comentarios/**`       | comments-service   | 8003          |
| `/tickets/**`                        | tickets-service    | 8002          |

## Atenção: Ordem dos Blocos `location`

O bloco de comentários **deve** aparecer antes do bloco de tickets no arquivo de configuração.
O nginx usa correspondência por prefixo mais longo para blocos `location ~` (regex),
então se `/tickets` vier primeiro, as rotas de comentários nunca serão alcançadas.

## Adicionando um Novo Serviço

1. Defina o upstream no início do arquivo:
   ```nginx
   upstream nome_service {
       server nome:8004;
   }
   ```
2. Adicione um bloco `location` na ordem correta (prefixos mais longos primeiro):
   ```nginx
   location /nova-rota {
       proxy_pass http://nome_service;
   }
   ```
3. Adicione o serviço no `docker-compose.yml` com `expose: ['8004']`.

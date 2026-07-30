# Backend Monolitico de Apoio

Este diretorio contem uma versao monolitica FastAPI usada para desenvolvimento local rapido e testes automatizados.

Ele **nao e a arquitetura principal** do projeto.

A arquitetura oficial do CondoTicket fica em:

```text
services/auth/
services/tickets/
services/comments/
services/shared/
nginx/
frontend/
```

## Quando Usar

Use `backend/` para:

- rodar a suite `backend/tests` rapidamente;
- testar regras de negocio sem subir todos os containers;
- manter compatibilidade com os testes ja existentes.

Para validar o projeto como microservicos, use `docker compose up --build`.

## Executar Localmente

Prepare o ambiente uma vez:

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

O monolito le a `DATABASE_URL`, que por padrao aponta para
`mysql+pymysql://root:root@localhost:3306/condoticket`.

Se voce tem MySQL instalado na maquina, basta criar o banco:

```sql
CREATE DATABASE IF NOT EXISTS condoticket;
```

Para reaproveitar o MySQL do compose, publique a porta dele no host — o
`docker-compose.yml` nao publica por padrao, para nao conflitar com instalacoes
locais. Adicione ao servico `mysql`:

```yaml
    ports:
      - '3306:3306'
```

E suba de novo com `docker compose up -d mysql`.

Escolha uma das duas formas de subir. As duas funcionam — a diferenca e quem
atende a porta `8000`, que e a porta que o frontend chama por padrao.

### Opcao 1 — Monolito na porta 8000

Use quando quiser o monolito no lugar dos microservicos, sem mexer no frontend.

Libere a porta parando o gateway:

```bash
docker compose stop nginx
```

Suba o monolito:

```bash
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O frontend ja aponta para `http://127.0.0.1:8000`, entao nao ha nada a ajustar.
Para voltar aos microservicos:

```bash
docker compose start nginx
```

### Opcao 2 — Monolito na porta 8080, lado a lado com o stack

Use quando quiser alternar entre os dois backends sem derrubar nada.

```bash
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Aponte o frontend para ele em `frontend/src/environments/environment.ts`:

```ts
apiUrl: 'http://127.0.0.1:8080'
```

O gateway continua de pe na `8000`. Trocar de backend passa a ser trocar essa
linha.

### Suba apenas um servidor por porta

Com o gateway de pe **e** um uvicorn na `8000`, os dois ficam escutando e o
uvicorn ganha: o bind em `127.0.0.1` e mais especifico que o `0.0.0.0` publicado
pelo Docker. Nao aparece erro na tela — o frontend simplesmente passa a conversar
com o monolito, e as correcoes feitas em `services/` parecem nao ter efeito.

Confira quem esta atendendo antes de investigar qualquer comportamento estranho:

```bash
curl -s -I http://127.0.0.1:8000/login
```

| Header `server` | Quem esta respondendo |
| --- | --- |
| `nginx/1.25.5` | API Gateway dos microservicos |
| `uvicorn` | Processo local — este monolito |

Para ter certeza, `curl -s http://127.0.0.1:8000/openapi.json`: o monolito se
identifica como `CondoTicket API`, os microservicos como `CondoTicket — Auth Service`
e afins.

## Rotas Ausentes no Monolito

O monolito cobre a maior parte da API, mas nao tudo. Estas rotas existem apenas em
`services/` e falham aqui:

| Rota | Efeito na tela |
| --- | --- |
| `POST /tickets/images` | Anexar foto ao chamado nao funciona |
| `/tickets/uploads/{arquivo}` | Imagens ja anexadas nao carregam |
| `PUT /tickets/{id}/comentarios/{cid}` | Editar comentario falha |
| `DELETE /tickets/{id}/comentarios/{cid}` | Excluir comentario falha |

Para testar esses fluxos, use os microservicos.

## Testes

A partir da raiz do repositorio:

```bash
python -m pytest backend/tests
```

## Regras de Manutencao

- Novas features de backend devem ser implementadas primeiro em `services/`.
- Se os testes em `backend/tests` dependerem da feature, espelhe o comportamento no monolito de apoio.
- Nao documente `backend/` como caminho principal de deploy.

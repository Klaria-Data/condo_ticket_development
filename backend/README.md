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

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API local: http://127.0.0.1:8000

## Testes

A partir da raiz do repositorio:

```bash
python -m pytest backend/tests
```

## Regras de Manutencao

- Novas features de backend devem ser implementadas primeiro em `services/`.
- Se os testes em `backend/tests` dependerem da feature, espelhe o comportamento no monolito de apoio.
- Nao documente `backend/` como caminho principal de deploy.

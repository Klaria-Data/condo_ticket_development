FROM python:3.11-slim

WORKDIR /app

# Instala dependências antes de copiar o código (aproveita cache do Docker)
COPY services/auth/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia a camada compartilhada e o código deste serviço
COPY services/shared ./shared
COPY services/auth/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

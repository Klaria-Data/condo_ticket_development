"""Configuração do banco de dados compartilhada entre todos os microsserviços.

Cada serviço importa ``engine``, ``Base`` e ``get_db`` deste módulo.
A URL de conexão é lida da variável de ambiente DATABASE_URL para permitir
configuração diferente em desenvolvimento, staging e produção.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Formato esperado: mysql+pymysql://usuario:senha@host:3306/banco
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/condoticket",
)

# pool_pre_ping evita conexões obsoletas do MySQL em processos de longa duração.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Fornece uma sessão de banco de dados por requisição via injeção de dependência do FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

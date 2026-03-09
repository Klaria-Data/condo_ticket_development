"""Quick test script to verify MySQL connection before starting the API."""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/condoticket",
)

print(f"Tentando conectar ao banco de dados...")
print(f"URL: {DATABASE_URL.replace('root:root', 'root:***')}")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✓ Conexão com MySQL estabelecida com sucesso!")
        print(f"✓ Resultado do teste: {result.fetchone()}")
        
        # Try to check if database exists
        result = connection.execute(text("SELECT DATABASE()"))
        db_name = result.fetchone()[0]
        print(f"✓ Banco de dados em uso: {db_name}")
        
except Exception as e:
    print(f"✗ Erro ao conectar ao banco de dados:")
    print(f"  {type(e).__name__}: {e}")
    print("\nVerifique se:")
    print("  1. MySQL está rodando")
    print("  2. O banco 'condoticket' existe (ou ajuste DATABASE_URL)")
    print("  3. As credenciais estão corretas")
    print("  4. PyMySQL está instalado")

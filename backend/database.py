import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


DB_USER_RAW = os.getenv("DB_USER_RAW")
DB_PASSWORD_RAW = os.getenv("DB_PASSWORD_RAW")
DB_HOST = os.getenv("DB_HOST", "localhost") 
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# Validação para garantir que as variáveis foram carregadas
if not all([DB_USER_RAW, DB_PASSWORD_RAW, DB_NAME]):
    print("ERRO: Variáveis de banco de dados (DB_USER_RAW, DB_PASSWORD_RAW, DB_NAME) não configuradas no .env ou ambiente.")
    # Você pode querer levantar uma exceção aqui para parar a execução se forem críticas
    # raise EnvironmentError("Variáveis de banco de dados não configuradas.")
    # Por enquanto, vamos permitir que continue para ver se o engine falha (o que vai acontecer)

DB_USER_ENCODED = quote_plus(DB_USER_RAW) if DB_USER_RAW else ''
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD_RAW) if DB_PASSWORD_RAW else ''

DATABASE_URL = f"postgresql://{DB_USER_ENCODED}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"DEBUG: DATABASE_URL formatada (senha omitida no log): postgresql://{DB_USER_ENCODED}:******@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
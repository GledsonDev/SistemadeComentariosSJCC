# Em backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus 

# Configure estas com seus valores REAIS
DB_USER_RAW = os.getenv("DB_USER_RAW", "postgres") # Seu nome de usuário real do PostgreSQL
DB_PASSWORD_RAW = os.getenv("DB_PASSWORD_RAW", "8294") # Sua senha real
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sjcc") # Você confirmou que este é o nome do seu banco

# Codifica o nome de usuário e a senha para serem seguros na URL
DB_USER_ENCODED = quote_plus(DB_USER_RAW)
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD_RAW)

DATABASE_URL = f"postgresql://{DB_USER_ENCODED}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"DEBUG: Conectando com DATABASE_URL: postgresql://{DB_USER_ENCODED}:******@{DB_HOST}:{DB_PORT}/{DB_NAME}") # Debug para ver a URL (sem mostrar a senha no log)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
import os
from datetime import datetime, timedelta, timezone # Adicionado timezone para datetime.now(timezone.utc)
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Configurações do Token JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256") # Default para HS256 se não definido
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # Default para 30 minutos

if not SECRET_KEY:
    # Em um cenário real, você poderia gerar uma chave automaticamente se não existir,
    # mas para desenvolvimento/produção é melhor que seja uma chave fixa e forte.
    print("ALERTA DE SEGURANÇA: SECRET_KEY não configurada no ambiente ou .env! Usando uma chave padrão insegura para desenvolvimento.")
    print("Execute 'import secrets; print(secrets.token_hex(32))' para gerar uma chave segura e defina-a no seu .env")
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # NÃO USE ESTA EM PRODUÇÃO

# Configuração para hashing de senha com passlib e bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica uma senha em texto plano contra um hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
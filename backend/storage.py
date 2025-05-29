# backend/storage.py
from pydantic import BaseModel
from typing import List, Dict, Optional
import hashlib
import uuid

# --- Pydantic Models ---

class UserBase(BaseModel):
    nome: str
    imagem: Optional[str] = None # Default é None se não houver imagem

class UserCreate(BaseModel):
    nome: str
    senha: str
    imagem: Optional[str] = None

class UserLogin(BaseModel):
    nome: str
    senha: str

class UserOutput(UserBase): # Herda 'imagem' opcional de UserBase
    pass

class ComentarioBase(BaseModel):
    nome: str
    imagem: Optional[str] # Imagem do usuário no momento do comentário, pode ser None
    texto: str

class ComentarioInput(ComentarioBase):
    pass

class ComentarioStored(ComentarioBase):
    id: int
    aprovado: bool

# --- In-memory Storage ---
users: Dict[str, Dict] = {}
comentarios: List[ComentarioStored] = []
next_comment_id: int = 0

# --- Helper Functions ---

def criar_usuario(user_data: UserCreate) -> UserOutput:
    if user_data.nome in users:
        raise ValueError("Usuário já existe")
    senha_hash = hashlib.sha256(user_data.senha.encode()).hexdigest()
    
    # imagem_final será a imagem fornecida (user_data.imagem) ou None
    users[user_data.nome] = {"senha_hash": senha_hash, "imagem": user_data.imagem}
    return UserOutput(nome=user_data.nome, imagem=user_data.imagem)

def autenticar_usuario(user_data: UserLogin) -> UserOutput:
    user_stored_data = users.get(user_data.nome)
    if not user_stored_data:
        raise ValueError("Usuário não encontrado")
    
    senha_hash = hashlib.sha256(user_data.senha.encode()).hexdigest()
    if user_stored_data["senha_hash"] != senha_hash:
        raise ValueError("Senha incorreta")
    
    # Retorna a imagem armazenada (que pode ser None)
    return UserOutput(nome=user_data.nome, imagem=user_stored_data.get("imagem"))

def adicionar_comentario_db(comentario_data: ComentarioInput, aprovado_status: bool) -> ComentarioStored:
    global next_comment_id
    
    # A imagem do comentário será a que veio com o input (do localStorage, que pode ser None)
    comentario_db = ComentarioStored(
        id=next_comment_id,
        nome=comentario_data.nome,
        imagem=comentario_data.imagem, # Pode ser None
        texto=comentario_data.texto,
        aprovado=aprovado_status
    )
    comentarios.append(comentario_db)
    next_comment_id += 1
    return comentario_db

def obter_comentarios_aprovados_db() -> List[ComentarioStored]:
    return [c for c in comentarios if c.aprovado]

def obter_todos_comentarios_db() -> List[ComentarioStored]:
    return comentarios
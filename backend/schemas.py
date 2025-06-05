from pydantic import BaseModel, ConfigDict # ConfigDict para Pydantic V2+
from typing import Optional, List
from datetime import datetime

# --- Esquemas de Usuário ---
class UserBase(BaseModel):
    nome: str
    imagem: Optional[str] = None

class UserCreateInput(UserBase): # Para o payload de cadastro (recebido da API)
    senha: str

class UserLoginInput(BaseModel): # Para o payload de login
    nome: str
    senha: str
    
class UserOutput(UserBase): # Para retornar dados do usuário (enviado pela API)
    id: int
    
    # Para Pydantic V2 (recomendado)
    model_config = ConfigDict(from_attributes=True)
    # Para Pydantic V1 (descomente se estiver usando Pydantic < 2.0)
    # class Config:
    #     orm_mode = True

# --- Esquemas de Comentário ---
class ComentarioBase(BaseModel):
    texto: str

class ComentarioCreateInput(ComentarioBase):
    # Este schema é usado para criar o objeto que vai para a função crud.create_comment.
    # No endpoint, os dados (como nome_autor, imagem_autor) são pegos dos Form parameters
    # e o texto_comentario é usado para popular este schema.
    pass 
    
class ComentarioOutput(ComentarioBase): # Para retornar dados do comentário
    id: int
    aprovado: bool
    timestamp: datetime
    autor_nome: str
    autor_imagem: Optional[str] = None
    autor_id: int

    # Para Pydantic V2
    model_config = ConfigDict(from_attributes=True)
    # Para Pydantic V1
    # class Config:
    #     orm_mode = True
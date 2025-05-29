from pydantic import BaseModel
from typing import List
import hashlib

class UserLogin(BaseModel):
    nome: str
    senha: str
    imagem: str

class UserOutput(BaseModel):
    nome: str
    imagem: str

class ComentarioInput(BaseModel):
    nome: str
    imagem: str
    texto: str

class Comentario(BaseModel):
    nome: str
    imagem: str
    texto: str
    aprovado: bool

users = {}
comentarios: List[Comentario] = []

def criar_usuario(user: UserLogin) -> UserOutput:
    if user.nome in users:
        raise ValueError("Usuário já existe")
    senha_hash = hashlib.sha256(user.senha.encode()).hexdigest()
    users[user.nome] = {"senha": senha_hash, "imagem": user.imagem}
    return UserOutput(nome=user.nome, imagem=user.imagem)

def autenticar_usuario(user: UserLogin) -> UserOutput:
    if user.nome not in users:
        raise ValueError("Usuário não encontrado")
    senha_hash = hashlib.sha256(user.senha.encode()).hexdigest()
    if users[user.nome]["senha"] != senha_hash:
        raise ValueError("Senha incorreta")
    return UserOutput(nome=user.nome, imagem=users[user.nome]["imagem"])
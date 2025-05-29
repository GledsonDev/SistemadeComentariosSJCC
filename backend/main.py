from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import hashlib
import uuid
from typing import List
from backend.moderation import analisar_comentario
from backend.storage import users, comentarios, Comentario, ComentarioInput, UserLogin, UserOutput, criar_usuario, autenticar_usuario

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/cadastro", response_model=UserOutput)
def cadastro(user: UserLogin):
    return criar_usuario(user)

@app.post("/login", response_model=UserOutput)
def login(user: UserLogin):
    return autenticar_usuario(user)

@app.post("/comentario")
def comentar(dados: ComentarioInput):
    if dados.nome not in users:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")
    resultado = analisar_comentario(dados.texto)
    comentario = Comentario(
        nome=dados.nome,
        imagem=dados.imagem,
        texto=dados.texto,
        aprovado=not resultado
    )
    comentarios.append(comentario)
    return {"aprovado": comentario.aprovado}

@app.get("/comentarios", response_model=List[Comentario])
def listar():
    return [c for c in comentarios if c.aprovado]

@app.get("/", response_class=HTMLResponse)
def root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()
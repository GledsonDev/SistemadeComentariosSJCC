from fastapi import FastAPI, HTTPException, Request, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from pydantic import BaseModel

import shutil
import uuid
from pathlib import Path
import os

# Importações do seu projeto
from backend.storage import (
    UserCreate, UserLogin, UserOutput,
    ComentarioInput, ComentarioStored,
    criar_usuario, autenticar_usuario,
    adicionar_comentario_db, obter_comentarios_aprovados_db, obter_todos_comentarios_db, users
)
from backend.moderation import analisar_comentario

app = FastAPI(
    title="Sistema de Comentários API",
    description="API para gerenciar usuários e comentários com moderação por IA.",
    version="1.5.0" # Versão atualizada
)

# --- CORS Middleware ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Templates and Static Files ---
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend/templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend/static")), name="static")

USER_IMAGE_DIR = BASE_DIR / "frontend/static/user_images"
USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# --- HTML Page Endpoints (Servidos, mas ocultos do Swagger) ---

@app.get("/", response_class=HTMLResponse, include_in_schema=False) # Oculta do Swagger
async def read_index(request: Request):
    """Serve a página principal de comentários."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/loginpage", response_class=HTMLResponse, include_in_schema=False) # Oculta do Swagger
async def read_login_page(request: Request):
    """Serve a página de login."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/registerpage", response_class=HTMLResponse, include_in_schema=False) # Oculta do Swagger
async def read_register_page(request: Request):
    """Serve a página de cadastro."""
    return templates.TemplateResponse("cadastro.html", {"request": request})


# --- API Endpoints (Estes permanecem visíveis no Swagger) ---

@app.post("/api/v1/register", response_model=UserOutput, tags=["User Management"], summary="Registrar Novo Usuário com Upload de Imagem Opcional")
async def register_user(
    nome: str = Form(...),
    senha: str = Form(...),
    imagem_file: Optional[UploadFile] = File(None, alias="imagem")
):
    imagem_url_para_armazenar = None

    if imagem_file:
        if not imagem_file.content_type or not imagem_file.content_type.startswith("image/"):
            await imagem_file.close()
            raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Apenas imagens são permitidas.")
        
        file_extension = Path(imagem_file.filename).suffix.lower()
        if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            await imagem_file.close()
            raise HTTPException(status_code=400, detail=f"Extensão de arquivo '{file_extension}' não permitida. Use jpg, jpeg, png, gif, ou webp.")

        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = USER_IMAGE_DIR / unique_filename
        
        try:
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(imagem_file.file, file_object)
            imagem_url_para_armazenar = f"/static/user_images/{unique_filename}"
        except Exception as e:
            if file_location.exists():
                try:
                    os.remove(file_location)
                except OSError:
                    pass
            raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")
        finally:
            await imagem_file.close()

    user_data_model = UserCreate(nome=nome, senha=senha, imagem=imagem_url_para_armazenar)

    try:
        user = criar_usuario(user_data_model)
        return user
    except ValueError as e: 
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
             try:
                os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
             except OSError:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
            try:
                os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor durante cadastro: {str(e)}")


@app.post("/api/v1/login", response_model=UserOutput, tags=["User Management"], summary="Login do Usuário")
async def login_user(user_data: UserLogin):
    try:
        user = autenticar_usuario(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/v1/comments", status_code=201, tags=["Comments"], summary="Submeter um Novo Comentário")
async def submit_comment(comment_data: ComentarioInput):
    if comment_data.nome not in users:
        raise HTTPException(status_code=401, detail="Usuário não autenticado. Faça login ou cadastre-se.")

    print(f"DEBUG: Recebido novo comentário de {comment_data.nome}: '{comment_data.texto}' Imagem do usuário: {comment_data.imagem}")

    is_toxic = analisar_comentario(comment_data.texto)
    aprovado_status = not is_toxic
    
    print(f"DEBUG: Comentário '{comment_data.texto}' é (considerado) tóxico? {is_toxic}. Aprovado: {aprovado_status}")
    
    comentario_salvo = adicionar_comentario_db(comment_data, aprovado_status)
    
    return {"message": "Comentário recebido.", "aprovado": aprovado_status, "comment_id": comentario_salvo.id}

@app.get("/api/v1/comments", response_model=List[ComentarioStored], tags=["Comments"], summary="Listar Comentários Aprovados")
async def get_approved_comments():
    aprovados = obter_comentarios_aprovados_db()
    print(f"DEBUG: Enviando {len(aprovados)} comentários aprovados para o frontend: {aprovados}")
    return aprovados

@app.get("/api/v1/comments/all", response_model=List[ComentarioStored], tags=["Comments (Admin)"], summary="Listar Todos os Comentários (Incluindo Não Aprovados)")
async def get_all_comments_admin():
    todos = obter_todos_comentarios_db()
    print(f"DEBUG: Endpoint /all - Total de comentários no sistema: {len(todos)}")
    return todos
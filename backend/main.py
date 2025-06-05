from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from sqlalchemy.orm import Session # Importar Session
import hashlib
import shutil
import uuid
from pathlib import Path
import os

# Novas importações do nosso projeto
from . import crud, models, schemas # Nossos módulos CRUD, Models (SQLAlchemy), Schemas (Pydantic)
from .database import engine, get_db # Nossa configuração de DB e dependência get_db. SessionLocal não é mais importada diretamente aqui.
from .moderation import analisar_comentario # Moderação continua a mesma

# Cria todas as tabelas no banco de dados (se elas ainda não existirem)
# Isso é executado quando o módulo main.py é carregado pela primeira vez.
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Sistema de Comentários SJCC",
    description="API para gerenciar usuários e comentários com moderação por IA.",
    version="2.0.1" # Pequena atualização de versão
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
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/loginpage", response_class=HTMLResponse, include_in_schema=False)
async def read_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/registerpage", response_class=HTMLResponse, include_in_schema=False)
async def read_register_page(request: Request):
    return templates.TemplateResponse("cadastro.html", {"request": request})

# --- API Endpoints ---

@app.post("/api/v1/register", response_model=schemas.UserOutput, tags=["User Management"])
async def register_user_endpoint(
    db: Session = Depends(get_db),
    nome: str = Form(...),
    senha: str = Form(...),
    imagem_file: Optional[UploadFile] = File(None, alias="imagem")
):
    db_user = crud.get_user_by_nome(db, nome=nome)
    if db_user:
        # Se uma imagem foi enviada e o usuário já existe, remova o arquivo temporário se houver.
        if imagem_file: await imagem_file.close() # Fecha o arquivo caso não seja usado.
        raise HTTPException(status_code=400, detail="Nome de usuário já registrado")

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
                try: os.remove(file_location)
                except OSError: pass
            raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")
        finally:
            await imagem_file.close()
            
    user_input_schema = schemas.UserCreateInput(nome=nome, senha=senha, imagem=imagem_url_para_armazenar)
    try:
        return crud.create_user(db=db, user_input=user_input_schema)
    except ValueError as e: # Tratamento de erro duplicado do CRUD, caso get_user_by_nome falhe por condição de corrida
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
             try: os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
             except OSError: pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
            try: os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
            except OSError: pass
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor durante cadastro: {str(e)}")


@app.post("/api/v1/login", response_model=schemas.UserOutput, tags=["User Management"])
async def login_user_endpoint(user_credentials: schemas.UserLoginInput, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_nome(db, nome=user_credentials.nome)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    senha_hash_calculada = hashlib.sha256(user_credentials.senha.encode()).hexdigest()
    if db_user.senha_hash != senha_hash_calculada:
        raise HTTPException(status_code=400, detail="Senha incorreta")
    
    return db_user


@app.post("/api/v1/comments", status_code=201, tags=["Comments"])
async def submit_comment_endpoint(
    db: Session = Depends(get_db),
    nome_autor: str = Form(...), 
    # imagem_autor: Optional[str] = Form(None), # A imagem será pega do usuário no DB
    texto_comentario: str = Form(..., alias="texto")
):
    autor_user = crud.get_user_by_nome(db, nome=nome_autor)
    if not autor_user:
        raise HTTPException(status_code=401, detail="Usuário autor não encontrado. Faça login ou cadastre-se.")
    
    print(f"DEBUG: Recebido novo comentário de {autor_user.nome}: '{texto_comentario}' Imagem do usuário (do DB): {autor_user.imagem}")

    is_toxic = analisar_comentario(texto_comentario)
    aprovado_status = not is_toxic
    
    print(f"DEBUG: Comentário '{texto_comentario}' é (considerado) tóxico? {is_toxic}. Aprovado: {aprovado_status}")
    
    comentario_input_schema = schemas.ComentarioCreateInput(texto=texto_comentario)
    
    comentario_salvo = crud.create_comment(
        db=db, 
        comentario_input=comentario_input_schema, 
        autor_user=autor_user, # Passa o objeto User completo
        aprovado_status=aprovado_status
    )
    
    return {"message": "Comentário recebido.", "aprovado": comentario_salvo.aprovado, "comment_id": comentario_salvo.id}


@app.get("/api/v1/comments", response_model=List[schemas.ComentarioOutput], tags=["Comments"])
async def get_approved_comments_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    aprovados = crud.get_approved_comments(db, skip=skip, limit=limit)
    print(f"DEBUG: Enviando {len(aprovados)} comentários aprovados para o frontend: {aprovados}")
    return aprovados


@app.get("/api/v1/comments/all", response_model=List[schemas.ComentarioOutput], tags=["Comments (Admin)"])
async def get_all_comments_admin_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    todos = crud.get_all_comments(db, skip=skip, limit=limit)
    print(f"DEBUG: Endpoint /all - Total de comentários no sistema: {len(todos)}")
    return todos
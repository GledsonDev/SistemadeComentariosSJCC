from fastapi import (
    FastAPI, HTTPException, Depends, File,
    UploadFile, Form, Request, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel # Para TokenData
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone # Adicionado timezone

import shutil
import uuid
from pathlib import Path
import os

# Importações dos módulos do projeto
from . import crud, models, schemas
from .database import engine, get_db # get_db é a dependência da sessão do DB
from .moderation import analisar_comentario

# Importações de security.py
from .security import (
    create_access_token,
    verify_password,
    ALGORITHM,
    SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Cria tabelas no DB (se não existirem)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Comentários SJCC",
    description="API para gerenciar usuários e comentários com moderação por IA.",
    version="2.1.2" # Atualização de versão
)

# --- CORS Middleware ---
# Ajuste 'origins' para seus domínios de frontend em produção
origins = [
    "http://localhost:8000", # Necessário se o frontend for servido pela mesma origem/porta
    "http://127.0.0.1:8000",
    # Exemplo: "https://www.seufrontend.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- OAuth2 e Token Data Schema ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token") # Endpoint para obter o token

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Funções de Dependência para Usuário Atual ---
async def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_nome(db, nome=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    return current_user

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
        if imagem_file: await imagem_file.close() # Fecha o arquivo se não for usado
        raise HTTPException(status_code=400, detail="Nome de usuário já registrado")

    imagem_url_para_armazenar = None
    if imagem_file:
        if not imagem_file.content_type or not imagem_file.content_type.startswith("image/"):
            await imagem_file.close(); raise HTTPException(status_code=400, detail="Tipo de arquivo inválido.")
        file_extension = Path(imagem_file.filename).suffix.lower()
        if file_extension not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            await imagem_file.close(); raise HTTPException(status_code=400, detail=f"Extensão '{file_extension}' não permitida.")
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = USER_IMAGE_DIR / unique_filename
        try:
            with open(file_location, "wb+") as file_object: shutil.copyfileobj(imagem_file.file, file_object)
            imagem_url_para_armazenar = f"/static/user_images/{unique_filename}"
        except Exception as e_img:
            if file_location.exists(): 
                try: os.remove(file_location)
                except OSError: pass # Ignora erro na remoção se o arquivo já não existir
            print(f"Erro ao salvar imagem: {e_img}")
            raise HTTPException(status_code=500, detail="Erro ao salvar imagem.")
        finally: 
            if imagem_file and hasattr(imagem_file, 'file') and imagem_file.file and not imagem_file.file.closed:
                await imagem_file.close()
            
    user_input_schema = schemas.UserCreateInput(nome=nome, senha=senha, imagem=imagem_url_para_armazenar)
    try:
        return crud.create_user(db=db, user_input=user_input_schema)
    except ValueError as e: # Ex: Usuário já existe (redundante se get_user_by_nome já verificou, mas bom como fallback)
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
             try: os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
             except OSError: pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e_gen: # Outros erros
        if imagem_url_para_armazenar and (USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name).exists():
            try: os.remove(USER_IMAGE_DIR / Path(imagem_url_para_armazenar).name)
            except OSError: pass
        print(f"Erro geral no cadastro: {e_gen}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor durante cadastro.")

@app.post("/api/v1/token", tags=["User Management"]) 
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_nome(db, nome=form_data.username)
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.nome}, expires_delta=access_token_expires
    )
    # Para Pydantic V2: schemas.UserOutput.model_validate(user)
    # Para Pydantic V1: schemas.UserOutput.from_orm(user)
    user_output = schemas.UserOutput.model_validate(user) if hasattr(schemas.UserOutput, 'model_validate') else schemas.UserOutput.from_orm(user)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_info": user_output
    }

@app.get("/api/v1/users/me", response_model=schemas.UserOutput, tags=["User Management"])
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """
    Retorna as informações do usuário atualmente autenticado.
    Útil para o frontend verificar quem está logado e obter dados do perfil.
    """
    return current_user


@app.post("/api/v1/comments", response_model=schemas.ComentarioOutput, status_code=status.HTTP_201_CREATED, tags=["Comments"])
async def submit_comment_endpoint(
    db: Session = Depends(get_db),
    texto_comentario: str = Form(..., alias="texto"), # 'alias' é opcional se o nome do campo no FormData for 'texto_comentario'
    current_user: models.User = Depends(get_current_active_user)
):
    autor_user = current_user 
    
    print(f"DEBUG: Novo comentário de '{autor_user.nome}': '{texto_comentario}' | Imagem do usuário: {autor_user.imagem}")

    is_toxic = analisar_comentario(texto_comentario) # True se tóxico, False se não tóxico
    aprovado_status = not is_toxic # aprovado_status é True se NÃO tóxico
    
    print(f"DEBUG: Comentário '{texto_comentario}' é (considerado) tóxico pela IA? {is_toxic}. Status de Aprovação: {aprovado_status}")
    
    comentario_input_schema = schemas.ComentarioCreateInput(texto=texto_comentario)
    
    comentario_salvo_db = crud.create_comment(
        db=db, 
        comentario_input=comentario_input_schema, 
        autor_user=autor_user, 
        aprovado_status=aprovado_status
    )
    return comentario_salvo_db


@app.get("/api/v1/comments", response_model=List[schemas.ComentarioOutput], tags=["Comments"])
async def get_approved_comments_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    aprovados_db = crud.get_approved_comments(db, skip=skip, limit=limit)
    print(f"DEBUG: Enviando {len(aprovados_db)} comentários aprovados para o frontend.")
    return aprovados_db


@app.get("/api/v1/comments/all", response_model=List[schemas.ComentarioOutput], tags=["Comments (Admin)"])
async def get_all_comments_admin_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    todos_db = crud.get_all_comments(db, skip=skip, limit=limit)
    print(f"DEBUG: Endpoint /all - Total de comentários no sistema: {len(todos_db)}")
    return todos_db
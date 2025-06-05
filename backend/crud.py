from sqlalchemy.orm import Session
import hashlib
from typing import Optional, List # <--- ADICIONE ESTA LINHA

from . import models, schemas # models (SQLAlchemy), schemas (Pydantic)

# --- Funções CRUD para Usuários ---
def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_nome(db: Session, nome: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.nome == nome).first()

def create_user(db: Session, user_input: schemas.UserCreateInput) -> models.User:
    senha_hash_calculada = hashlib.sha256(user_input.senha.encode()).hexdigest()
    db_user = models.User(
        nome=user_input.nome,
        senha_hash=senha_hash_calculada,
        imagem=user_input.imagem
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Funções CRUD para Comentários ---
def create_comment(db: Session, comentario_input: schemas.ComentarioCreateInput, autor_user: models.User, aprovado_status: bool) -> models.Comentario:
    db_comentario = models.Comentario(
        texto=comentario_input.texto,
        autor_id=autor_user.id,
        autor_nome=autor_user.nome,
        autor_imagem=autor_user.imagem,
        aprovado=aprovado_status
    )
    db.add(db_comentario)
    db.commit()
    db.refresh(db_comentario)
    return db_comentario

def get_approved_comments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Comentario]:
    return db.query(models.Comentario)\
             .filter(models.Comentario.aprovado == True)\
             .order_by(models.Comentario.timestamp.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()

def get_all_comments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Comentario]:
    return db.query(models.Comentario)\
             .order_by(models.Comentario.timestamp.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()
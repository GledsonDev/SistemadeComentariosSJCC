from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # Para o timestamp padrão
from .database import Base # Importa a Base da nossa configuração de database

class User(Base):
    __tablename__ = "users" # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    imagem = Column(String, nullable=True) # Caminho para a imagem de perfil

    # Relacionamento: Um usuário pode ter muitos comentários
    comentarios = relationship("Comentario", back_populates="autor")

class Comentario(Base):
    __tablename__ = "comentarios" # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String, nullable=False)
    aprovado = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) # Data e hora do comentário

    # Chave estrangeira para o usuário que fez o comentário
    autor_id = Column(Integer, ForeignKey("users.id"))

    # Para facilitar a exibição, podemos armazenar o nome e imagem do autor no momento do comentário
    # Isso é uma forma de desnormalização, mas reflete o comportamento atual do seu sistema.
    autor_nome = Column(String, nullable=False)
    autor_imagem = Column(String, nullable=True)

    # Relacionamento: Um comentário pertence a um usuário
    autor = relationship("User", back_populates="comentarios")
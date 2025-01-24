from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    create_engine,
    Boolean,
    text,
    Text,
    DateTime,
    Table,
    MetaData,
    ForeignKey,
    Date, 
    Time,
    Float,
    )

from streamlit_auth.core.database.manager import default_engine as engine


Base = declarative_base()

class TbUsuarioStreamlit(Base):
    __tablename__ = 'TbUsuarioStreamlit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    nome = Column(String(255))  # Definindo limite para a coluna 'nome'
    email = Column(String(255))  # Definindo limite para a coluna 'email'
    
    username = Column(String(64), unique=True, nullable=False)  # 'username' com 64 caracteres
    password = Column(Text)  # Pode ser um 'Text' sem limite porque é a senha (normalmente criptografada)
    
    data_alteracao = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True)
    role = Column(String(32))  # Definindo limite para a coluna 'role' (32 caracteres é suficiente para 'admin', 'user' etc.)
    
    secret_tfa = Column(String(255))  # Limite de 255 caracteres para 'secret_tfa'
    
    reset_token = Column(String(255))  # Limite de 255 caracteres para 'reset_token'
    reset_token_expiry = Column(DateTime)

    # Relacionamento com TbSessaoStreamlit
    sessions = relationship('TbSessaoStreamlit', back_populates='user', cascade="all, delete-orphan")
    
    # Relacionamento com TbPermissaoUsuariosStreamlit
    perms = relationship('TbPermissaoUsuariosStreamlit', back_populates='user')
    
class TbSessaoStreamlit(Base):
    """
    Modelo para a tabela de sessões do Streamlit.
    Armazena informações sobre as sessões de autenticação dos usuários.
    """

    __tablename__ = 'TbSessaoStreamlit'

    session_id = Column(String(128), primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey(TbUsuarioStreamlit.id), nullable=False)
    authenticated_2fa = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    fingerprint = Column(String(255), nullable=False)

    user = relationship(TbUsuarioStreamlit, back_populates='sessions')

class TbPermissaoUsuariosStreamlit(Base):

    __tablename__ = 'TbPermissaoUsuariosStreamlit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    user_id = Column(Integer, ForeignKey(TbUsuarioStreamlit.id), nullable=False)
    username = Column(String(64), nullable=False)
    app_name = Column(Text, nullable=False)
    data = Column(DateTime, default=datetime.now)
    
    user = relationship(TbUsuarioStreamlit, back_populates='perms')

Base.metadata.create_all(engine)

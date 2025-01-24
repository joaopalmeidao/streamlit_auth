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


ROLES = ["user", "admin"]

Base = declarative_base()

class TbUsuarioStreamlit(Base):
    __tablename__ = 'TbUsuarioStreamlit'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    name = Column(String(255)) 
    email = Column(String(255))
    
    username = Column(String(64), unique=True, nullable=False)
    password = Column(Text)
    
    change_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    role = Column(String(32))
    
    secret_tfa = Column(String(255))
    
    reset_token = Column(String(255))
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
    date = Column(DateTime, default=datetime.now)
    
    user = relationship(TbUsuarioStreamlit, back_populates='perms')

Base.metadata.create_all(engine)

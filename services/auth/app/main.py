"""Microsserviço de Autenticação — CondoTicket.

Responsabilidade: registro de novos usuários e emissão de tokens JWT no login.
Porta padrão: 8001 (exposta internamente; o nginx roteia /registro e /login para cá).

Este serviço também é o único responsável por criar as tabelas no banco de dados
via ``Base.metadata.create_all``. Os demais serviços assumem que as tabelas já existem.
"""

import logging
import os
import sys

# Permite importar o pacote shared independente do diretório de trabalho
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from shared.auth_utils import create_access_token, hash_password, verify_password
from shared.database import Base, engine, get_db
from shared.models import PerfilUsuario, Usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria todas as tabelas na inicialização. Apenas este serviço chama create_all.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CondoTicket — Auth Service",
    description="Registro de usuários e autenticação via JWT.",
    version="1.0.0",
)

allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ──────────────────────────────────────────────────────────────────


class UsuarioRegistro(BaseModel):
    """Payload para registrar um novo usuário."""

    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    unidade: str = Field(min_length=1, max_length=30)
    perfil: PerfilUsuario = PerfilUsuario.MORADOR


class UsuarioResposta(BaseModel):
    """Dados públicos do usuário retornados após registro ou consulta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    unidade: str
    perfil: PerfilUsuario


class LoginEntrada(BaseModel):
    """Credenciais de login."""

    email: EmailStr
    senha: str


class LoginResposta(BaseModel):
    """Resposta do login contendo o token JWT e dados básicos do usuário."""

    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    nome: str
    unidade: str
    perfil: PerfilUsuario


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.post(
    "/registro",
    response_model=UsuarioResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
def registrar_usuario(payload: UsuarioRegistro, db: Session = Depends(get_db)) -> UsuarioResposta:
    """Cria um novo usuário no sistema.

    - Valida que o e-mail ainda não está cadastrado.
    - Armazena a senha como hash bcrypt (nunca em texto plano).
    - O perfil padrão é MORADOR; use ADMIN para síndicos/administradores.
    """
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    novo_usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        unidade=payload.unidade,
        perfil=payload.perfil,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    logger.info("Novo usuário registrado: id=%d email=%s", novo_usuario.id, novo_usuario.email)
    return novo_usuario


@app.post(
    "/login",
    response_model=LoginResposta,
    summary="Autenticar usuário",
)
def login(payload: LoginEntrada, db: Session = Depends(get_db)) -> LoginResposta:
    """Autentica o usuário com e-mail e senha.

    Retorna um token JWT Bearer que deve ser enviado no header
    ``Authorization: Bearer <token>`` nas demais requisições autenticadas.
    O token expira após JWT_EXPIRE_MINUTES minutos (padrão: 60).
    """
    user = db.query(Usuario).filter(Usuario.email == payload.email).first()

    if not user or not verify_password(payload.senha, user.senha_hash):
        logger.warning("Tentativa de login inválida para e-mail: %s", payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")

    access_token = create_access_token(subject=str(user.id))
    logger.info("Login bem-sucedido: usuario_id=%d", user.id)

    return LoginResposta(
        access_token=access_token,
        usuario_id=user.id,
        nome=user.nome,
        unidade=user.unidade,
        perfil=user.perfil,
    )

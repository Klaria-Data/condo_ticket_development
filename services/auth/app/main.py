"""Microsserviço de Autenticação — CondoTicket.

Responsabilidade: registro de novos usuários e emissão de tokens JWT no login.
Porta padrão: 8001 (exposta internamente; o nginx roteia /registro e /login para cá).

Este serviço também é o único responsável por criar as tabelas no banco de dados
via ``Base.metadata.create_all``. Os demais serviços assumem que as tabelas já existem.
"""

import logging
import os
import hashlib
import secrets
import smtplib
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage

# Permite importar o pacote shared independente do diretório de trabalho
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from shared.auth_utils import get_current_user
from shared.auth_utils import create_access_token, hash_password, verify_password
from shared.database import Base, SessionLocal, engine, get_db
from shared.models import ConviteMorador, PerfilUsuario, Usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
INVITE_EXPIRE_DAYS = int(os.getenv("INVITE_EXPIRE_DAYS", "7"))
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:4200")

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


class ConviteMoradorCriacao(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    unidade: str = Field(min_length=1, max_length=30)


class ConviteMoradorResposta(BaseModel):
    id: int
    nome: str
    email: EmailStr
    unidade: str
    usado: bool
    data_criacao: datetime
    data_expiracao: datetime
    data_uso: datetime | None = None
    convite_url: str | None = None


class ConviteMoradorPublico(BaseModel):
    nome: str
    email: EmailStr
    unidade: str
    data_expiracao: datetime


class AceitarConviteMorador(BaseModel):
    senha: str = Field(min_length=8, max_length=128)


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_invite_url(token: str) -> str:
    return f"{FRONTEND_BASE_URL.rstrip('/')}/convite/{token}"


def send_invite_email(email: str, nome: str, convite_url: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        logger.info("Convite para %s: %s", email, convite_url)
        return

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "no-reply@condoticket.local")

    message = EmailMessage()
    message["Subject"] = "Convite para acessar o CondoTicket"
    message["From"] = smtp_from
    message["To"] = email
    message.set_content(
        f"Olá, {nome}.\n\n"
        "Você recebeu um convite para acessar o CondoTicket.\n"
        f"Defina sua senha pelo link: {convite_url}\n\n"
        "Se você não esperava este convite, ignore este e-mail."
    )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem executar esta acao",
        )
    return current_user


def get_valid_invite(token: str, db: Session) -> ConviteMorador:
    convite = db.query(ConviteMorador).filter(ConviteMorador.token_hash == hash_invite_token(token)).first()
    if not convite or convite.usado or convite.data_expiracao < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite invalido ou expirado")
    return convite


def seed_default_admin() -> None:
    email = os.getenv("SEED_ADMIN_EMAIL")
    password = os.getenv("SEED_ADMIN_PASSWORD")
    if not email or not password:
        return

    db = SessionLocal()
    try:
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()
        if existing_user:
            return

        admin = Usuario(
            nome=os.getenv("SEED_ADMIN_NAME", "Sindico"),
            email=email,
            senha_hash=hash_password(password),
            unidade=os.getenv("SEED_ADMIN_UNIDADE", "000"),
            perfil=PerfilUsuario.ADMIN,
        )
        db.add(admin)
        db.commit()
        logger.info("Admin inicial criado: %s", email)
    finally:
        db.close()


seed_default_admin()


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


@app.post(
    "/moradores/convites",
    response_model=ConviteMoradorResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Convidar morador",
)
def criar_convite_morador(
    payload: ConviteMoradorCriacao,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ConviteMoradorResposta:
    email = str(payload.email).lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    convite_pendente = (
        db.query(ConviteMorador)
        .filter(
            ConviteMorador.email == email,
            ConviteMorador.usado.is_(False),
            ConviteMorador.data_expiracao >= datetime.utcnow(),
        )
        .first()
    )
    if convite_pendente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe convite pendente para este email")

    token = secrets.token_urlsafe(32)
    convite = ConviteMorador(
        nome=payload.nome.strip(),
        email=email,
        unidade=payload.unidade.strip(),
        token_hash=hash_invite_token(token),
        data_expiracao=datetime.utcnow() + timedelta(days=INVITE_EXPIRE_DAYS),
        criado_por_id=current_user.id,
    )

    db.add(convite)
    db.commit()
    db.refresh(convite)

    convite_url = build_invite_url(token)
    send_invite_email(convite.email, convite.nome, convite_url)

    return ConviteMoradorResposta(
        id=convite.id,
        nome=convite.nome,
        email=convite.email,
        unidade=convite.unidade,
        usado=convite.usado,
        data_criacao=convite.data_criacao,
        data_expiracao=convite.data_expiracao,
        data_uso=convite.data_uso,
        convite_url=convite_url,
    )


@app.get(
    "/moradores/convites",
    response_model=list[ConviteMoradorResposta],
    summary="Listar convites de moradores",
)
def listar_convites_moradores(
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ConviteMoradorResposta]:
    convites = db.query(ConviteMorador).order_by(ConviteMorador.data_criacao.desc()).all()
    return [
        ConviteMoradorResposta(
            id=convite.id,
            nome=convite.nome,
            email=convite.email,
            unidade=convite.unidade,
            usado=convite.usado,
            data_criacao=convite.data_criacao,
            data_expiracao=convite.data_expiracao,
            data_uso=convite.data_uso,
        )
        for convite in convites
    ]


@app.get(
    "/convites/{token}",
    response_model=ConviteMoradorPublico,
    summary="Consultar convite",
)
def consultar_convite_morador(token: str, db: Session = Depends(get_db)) -> ConviteMoradorPublico:
    convite = get_valid_invite(token, db)
    return ConviteMoradorPublico(
        nome=convite.nome,
        email=convite.email,
        unidade=convite.unidade,
        data_expiracao=convite.data_expiracao,
    )


@app.post(
    "/convites/{token}/aceitar",
    response_model=LoginResposta,
    summary="Aceitar convite",
)
def aceitar_convite_morador(
    token: str,
    payload: AceitarConviteMorador,
    db: Session = Depends(get_db),
) -> LoginResposta:
    convite = get_valid_invite(token, db)
    if db.query(Usuario).filter(Usuario.email == convite.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    novo_usuario = Usuario(
        nome=convite.nome,
        email=convite.email,
        senha_hash=hash_password(payload.senha),
        unidade=convite.unidade,
        perfil=PerfilUsuario.MORADOR,
    )
    convite.usado = True
    convite.data_uso = datetime.utcnow()

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    access_token = create_access_token(subject=str(novo_usuario.id))
    return LoginResposta(
        access_token=access_token,
        usuario_id=novo_usuario.id,
        nome=novo_usuario.nome,
        unidade=novo_usuario.unidade,
        perfil=novo_usuario.perfil,
    )

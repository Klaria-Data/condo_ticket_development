"""FastAPI entrypoint with auth and ticket creation endpoints."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .database import Base, engine, get_db

# Create tables on startup for the initial project bootstrap.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CondoTicket API", version="0.1.0")

allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.Usuario:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

    user = db.query(models.Usuario).filter(models.Usuario.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado")

    return user


def require_admin(current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
    if current_user.perfil != models.PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem executar esta acao",
        )

    return current_user


@app.post("/registro", response_model=schemas.UsuarioResposta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(payload: schemas.UsuarioRegistro, db: Session = Depends(get_db)):
    existing_user = db.query(models.Usuario).filter(models.Usuario.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    novo_usuario = models.Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        unidade=payload.unidade,
        perfil=payload.perfil,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario


@app.post("/login", response_model=schemas.LoginResposta)
def login(payload: schemas.LoginEntrada, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == payload.email).first()

    if not user or not verify_password(payload.senha, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")

    access_token = create_access_token(subject=str(user.id))
    return schemas.LoginResposta(
        access_token=access_token,
        usuario_id=user.id,
        nome=user.nome,
        unidade=user.unidade,
        perfil=user.perfil,
    )


@app.get("/tickets", response_model=list[schemas.TicketResposta])
def listar_tickets(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Ticket)

    if current_user.perfil != models.PerfilUsuario.ADMIN:
        query = query.filter(models.Ticket.usuario_id == current_user.id)

    return query.order_by(models.Ticket.data_criacao.desc()).all()


@app.post("/tickets", response_model=schemas.TicketResposta, status_code=status.HTTP_201_CREATED)
def criar_ticket(
    payload: schemas.TicketCriacao,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # New tickets always start as ABERTO to preserve the required status flow.
    novo_ticket = models.Ticket(
        usuario_id=current_user.id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        imagem_url=payload.imagem_url,
        status=models.StatusTicket.ABERTO,
    )

    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)

    return novo_ticket


@app.put("/tickets/{ticket_id}/status", response_model=schemas.TicketResposta)
def atualizar_status_ticket(
    ticket_id: int,
    payload: schemas.TicketStatusAtualizacao,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    print(f"[Backend] PUT /tickets/{ticket_id}/status called with payload: {payload.status}")
    print(f"[Backend] User: {current_user.email}, Perfil: {current_user.perfil}")
    
    if current_user.perfil != models.PerfilUsuario.ADMIN:
        print("[Backend] ERROR: User is not ADMIN, returning 403")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem atualizar status de tickets",
        )

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        print(f"[Backend] ERROR: Ticket {ticket_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nao encontrado")

    allowed_next_status = {
        models.StatusTicket.ABERTO: models.StatusTicket.EM_ANDAMENTO,
        models.StatusTicket.EM_ANDAMENTO: models.StatusTicket.RESOLVIDO,
        models.StatusTicket.RESOLVIDO: models.StatusTicket.RESOLVIDO,
    }

    print(f"[Backend] Current ticket status: {ticket.status}")
    print(f"[Backend] Requested new status: {payload.status}")
    
    expected_next = allowed_next_status[ticket.status]
    if payload.status != expected_next and payload.status != ticket.status:
        print(f"[Backend] ERROR: Invalid flow. Expected {expected_next}, got {payload.status}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fluxo invalido de status. Use ABERTO -> EM_ANDAMENTO -> RESOLVIDO",
        )

    print(f"[Backend] Updating ticket {ticket_id} status to {payload.status}")
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)

    print(f"[Backend] Ticket {ticket_id} updated successfully")
    return ticket


@app.get("/tickets/{ticket_id}/comentarios", response_model=list[schemas.ComentarioTicketResposta])
def listar_comentarios_ticket(
    ticket_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lista todos os comentários de um ticket.
    Qualquer usuário autenticado pode ver os comentários.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nao encontrado")

    comentarios = (
        db.query(models.ComentarioTicket)
        .filter(models.ComentarioTicket.ticket_id == ticket_id)
        .order_by(models.ComentarioTicket.data_envio.asc())
        .all()
    )

    return [schemas.ComentarioTicketResposta.from_orm_with_usuario(c) for c in comentarios]


@app.post("/tickets/{ticket_id}/comentarios", response_model=schemas.ComentarioTicketResposta, status_code=status.HTTP_201_CREATED)
def criar_comentario_ticket(
    ticket_id: int,
    payload: schemas.ComentarioTicketCriacao,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cria um novo comentário em um ticket.
    Qualquer usuário autenticado (ADMIN ou MORADOR) pode criar comentários.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nao encontrado")

    novo_comentario = models.ComentarioTicket(
        ticket_id=ticket_id,
        usuario_id=current_user.id,
        mensagem=payload.mensagem,
    )

    db.add(novo_comentario)
    db.commit()
    db.refresh(novo_comentario)

    return schemas.ComentarioTicketResposta.from_orm_with_usuario(novo_comentario)


@app.get("/locais-agendaveis", response_model=list[schemas.LocalAgendavelResposta])
def listar_locais_agendaveis(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.LocalAgendavel)
        .filter(models.LocalAgendavel.ativo.is_(True))
        .order_by(models.LocalAgendavel.nome.asc())
        .all()
    )


@app.post(
    "/locais-agendaveis",
    response_model=schemas.LocalAgendavelResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_local_agendavel(
    payload: schemas.LocalAgendavelCriacao,
    current_user: models.Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    nome_normalizado = payload.nome.strip()
    existing_local = (
        db.query(models.LocalAgendavel)
        .filter(models.LocalAgendavel.nome == nome_normalizado)
        .first()
    )
    if existing_local:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local ja cadastrado")

    novo_local = models.LocalAgendavel(
        nome=nome_normalizado,
        descricao=payload.descricao.strip() if payload.descricao else None,
    )

    db.add(novo_local)
    db.commit()
    db.refresh(novo_local)

    return novo_local


@app.get("/agendamentos", response_model=list[schemas.ReservaLocalResposta])
def listar_agendamentos(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservas = (
        db.query(models.ReservaLocal)
        .options(joinedload(models.ReservaLocal.local), joinedload(models.ReservaLocal.usuario))
        .order_by(models.ReservaLocal.inicio.asc())
        .all()
    )

    return [schemas.ReservaLocalResposta.from_orm_with_relations(reserva) for reserva in reservas]


@app.post(
    "/agendamentos",
    response_model=schemas.ReservaLocalResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento(
    payload: schemas.ReservaLocalCriacao,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    local = (
        db.query(models.LocalAgendavel)
        .filter(
            models.LocalAgendavel.id == payload.local_id,
            models.LocalAgendavel.ativo.is_(True),
        )
        .first()
    )
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local agendavel nao encontrado")

    reserva_conflitante = (
        db.query(models.ReservaLocal)
        .filter(
            models.ReservaLocal.local_id == payload.local_id,
            models.ReservaLocal.inicio < payload.fim,
            models.ReservaLocal.fim > payload.inicio,
        )
        .first()
    )
    if reserva_conflitante:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Horario indisponivel para este local",
        )

    nova_reserva = models.ReservaLocal(
        local_id=payload.local_id,
        usuario_id=current_user.id,
        inicio=payload.inicio,
        fim=payload.fim,
        observacao=payload.observacao.strip() if payload.observacao else None,
    )

    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)

    return schemas.ReservaLocalResposta.from_orm_with_relations(nova_reserva)

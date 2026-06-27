"""FastAPI entrypoint with auth and ticket creation endpoints."""

import asyncio
from contextlib import asynccontextmanager
import os
import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .database import Base, SessionLocal, engine, get_db

# Loop infinito não-bloqueante
async def worker_reservas():
    while True:
        # Envolve a função síncrona do SQLAlchemy no threadpool do Asyncio 
        # para não congelar o servidor web enquanto faz as queries
        await asyncio.to_thread(processar_filas_reserva)
        
        # Define o intervalo (ex: roda a cada 60 segundos)
        await asyncio.sleep(60)

# Gerenciador do ciclo de vida
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa no startup: cria a tarefa em background
    task = asyncio.create_task(worker_reservas())
    print("[Sistema] Worker de filas de reserva iniciado.")
    
    yield # O servidor FastAPI roda aqui
    
    # Executa no shutdown: cancela a tarefa
    task.cancel()
    print("[Sistema] Worker de filas de reserva encerrado.")

# Create tables on startup for the initial project bootstrap.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CondoTicket API", version="0.1.0", lifespan=lifespan)

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
INVITE_EXPIRE_DAYS = int(os.getenv("INVITE_EXPIRE_DAYS", "7"))
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:4200")

# --- Parametros da maquina de estados de reservas ---
# Janela em que o detentor entra em "Pendente Confirmacao" antes do evento.
RESERVA_JANELA_CONFIRMACAO_HORAS = int(os.getenv("RESERVA_JANELA_CONFIRMACAO_HORAS", "48"))
# Prazo do detentor original para confirmar apos entrar na janela de 48h.
RESERVA_PRAZO_INICIAL_HORAS = int(os.getenv("RESERVA_PRAZO_INICIAL_HORAS", "24"))
# Prazo restrito de cada proximo da fila promovido (confirmacao em cascata).
RESERVA_PRAZO_CASCATA_HORAS = int(os.getenv("RESERVA_PRAZO_CASCATA_HORAS", "12"))
# Janela considerada ao recalcular a prioridade da fila por historico de uso.
RESERVA_HISTORICO_MESES = int(os.getenv("RESERVA_HISTORICO_MESES", "6"))

# Status que representam um detentor "ativo" do slot (segurando a vaga).
STATUS_RESERVA_ATIVOS = (
    models.StatusReserva.AGENDADO,
    models.StatusReserva.PENDENTE_CONFIRMACAO,
    models.StatusReserva.CONFIRMADO,
    models.StatusReserva.LIVRE_DEMANDA,
)
# Status terminais: a reserva nao concorre mais pelo slot.
STATUS_RESERVA_TERMINAIS = (
    models.StatusReserva.EXPIRADO,
    models.StatusReserva.CANCELADO,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_invite_url(token: str) -> str:
    return f"{FRONTEND_BASE_URL.rstrip('/')}/convite/{token}"


def send_invite_email(email: str, nome: str, convite_url: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        print(f"[ConviteMorador] Convite para {email}: {convite_url}")
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


def get_valid_invite(token: str, db: Session) -> models.ConviteMorador:
    convite = (
        db.query(models.ConviteMorador)
        .filter(models.ConviteMorador.token_hash == hash_invite_token(token))
        .first()
    )
    if not convite or convite.usado or convite.data_expiracao < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite invalido ou expirado")

    return convite


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


@app.post(
    "/moradores/convites",
    response_model=schemas.ConviteMoradorResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_convite_morador(
    payload: schemas.ConviteMoradorCriacao,
    current_user: models.Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()
    if db.query(models.Usuario).filter(models.Usuario.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    convite_pendente = (
        db.query(models.ConviteMorador)
        .filter(
            models.ConviteMorador.email == email,
            models.ConviteMorador.usado.is_(False),
            models.ConviteMorador.data_expiracao >= datetime.utcnow(),
        )
        .first()
    )
    if convite_pendente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe convite pendente para este email")

    token = secrets.token_urlsafe(32)
    convite = models.ConviteMorador(
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

    return schemas.ConviteMoradorResposta(
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


@app.get("/moradores/convites", response_model=list[schemas.ConviteMoradorResposta])
def listar_convites_moradores(
    current_user: models.Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    convites = db.query(models.ConviteMorador).order_by(models.ConviteMorador.data_criacao.desc()).all()
    return [
        schemas.ConviteMoradorResposta(
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


@app.get("/convites/{token}", response_model=schemas.ConviteMoradorPublico)
def consultar_convite_morador(token: str, db: Session = Depends(get_db)):
    convite = get_valid_invite(token, db)
    return schemas.ConviteMoradorPublico(
        nome=convite.nome,
        email=convite.email,
        unidade=convite.unidade,
        data_expiracao=convite.data_expiracao,
    )


@app.post("/convites/{token}/aceitar", response_model=schemas.LoginResposta)
def aceitar_convite_morador(
    token: str,
    payload: schemas.AceitarConviteMorador,
    db: Session = Depends(get_db),
):
    convite = get_valid_invite(token, db)
    if db.query(models.Usuario).filter(models.Usuario.email == convite.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

    novo_usuario = models.Usuario(
        nome=convite.nome,
        email=convite.email,
        senha_hash=hash_password(payload.senha),
        unidade=convite.unidade,
        perfil=models.PerfilUsuario.MORADOR,
    )
    convite.usado = True
    convite.data_uso = datetime.utcnow()

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    access_token = create_access_token(subject=str(novo_usuario.id))
    return schemas.LoginResposta(
        access_token=access_token,
        usuario_id=novo_usuario.id,
        nome=novo_usuario.nome,
        unidade=novo_usuario.unidade,
        perfil=novo_usuario.perfil,
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


def reservas_concorrentes(db, local_id, inicio, fim, ignorar_id=None):
    """Reservas (nao terminais) que disputam o mesmo slot por sobreposicao de horario."""
    query = db.query(models.ReservaLocal).filter(
        models.ReservaLocal.local_id == local_id,
        models.ReservaLocal.inicio < fim,
        models.ReservaLocal.fim > inicio,
        models.ReservaLocal.status.notin_(STATUS_RESERVA_TERMINAIS),
    )
    if ignorar_id is not None:
        query = query.filter(models.ReservaLocal.id != ignorar_id)
    return query.all()


def decidir_status_inicial(db, local_id, inicio, fim, ignorar_id=None):
    """Decide o status de entrada de uma reserva conforme a disputa pelo slot.

    - Slot livre e dentro de 48h  -> LIVRE_DEMANDA (confirmacao instantanea, FCFS).
    - Slot livre e fora de 48h    -> AGENDADO (detentor aguardando a janela).
    - Slot ja disputado           -> AGUARDANDO_FILA (entra na fila).
    """
    concorrentes = reservas_concorrentes(db, local_id, inicio, fim, ignorar_id)
    ha_detentor = any(r.status in STATUS_RESERVA_ATIVOS for r in concorrentes)
    ha_fila = any(r.status == models.StatusReserva.AGUARDANDO_FILA for r in concorrentes)

    if ha_detentor or ha_fila:
        return models.StatusReserva.AGUARDANDO_FILA

    if (inicio - datetime.utcnow()) <= timedelta(hours=RESERVA_JANELA_CONFIRMACAO_HORAS):
        return models.StatusReserva.LIVRE_DEMANDA
    return models.StatusReserva.AGENDADO


def contar_reservas_usuario(db, usuario_id, desde):
    """Conta reservas efetivas do usuario (por inicio do evento) a partir de uma data."""
    return (
        db.query(models.ReservaLocal)
        .filter(
            models.ReservaLocal.usuario_id == usuario_id,
            models.ReservaLocal.inicio >= desde,
            models.ReservaLocal.status.in_(STATUS_RESERVA_ATIVOS),
        )
        .count()
    )


def chave_prioridade_fila(db, reserva, agora):
    """Chave de ordenacao da fila por historico de uso.

    Moradores com 0 reservas no mes atual assumem o topo; desempate por menos
    reservas na janela de 6 meses e, por fim, pela ordem cronologica original.
    """
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    janela = agora - timedelta(days=30 * RESERVA_HISTORICO_MESES)
    reservas_mes = contar_reservas_usuario(db, reserva.usuario_id, inicio_mes)
    reservas_janela = contar_reservas_usuario(db, reserva.usuario_id, janela)
    return (reservas_mes, reservas_janela, reserva.data_criacao)


def ordenar_fila(db, reservas, agora):
    return sorted(reservas, key=lambda r: chave_prioridade_fila(db, r, agora))


@app.get("/agendamentos", response_model=list[schemas.ReservaLocalResposta])
def listar_agendamentos(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Agenda compartilhada: mostra apenas reservas que efetivamente ocupam o slot.
    reservas = (
        db.query(models.ReservaLocal)
        .options(
            joinedload(models.ReservaLocal.local),
            joinedload(models.ReservaLocal.usuario),
            joinedload(models.ReservaLocal.convidados),
        )
        .filter(models.ReservaLocal.status.in_(STATUS_RESERVA_ATIVOS))
        .order_by(models.ReservaLocal.inicio.asc())
        .all()
    )

    is_admin = current_user.perfil == models.PerfilUsuario.ADMIN
    return [
        schemas.ReservaLocalResposta.from_orm_with_relations(
            reserva,
            # Dados de convidados (CPF) so para o dono da reserva ou para o sindico.
            incluir_convidados=is_admin or reserva.usuario_id == current_user.id,
        )
        for reserva in reservas
    ]


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
    local = db.query(models.LocalAgendavel).filter(
        models.LocalAgendavel.id == payload.local_id,
        models.LocalAgendavel.ativo.is_(True),
    ).first()

    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local agendavel nao encontrado")

    status_inicial = decidir_status_inicial(db, payload.local_id, payload.inicio, payload.fim)

    nova_reserva = models.ReservaLocal(
        local_id=payload.local_id,
        usuario_id=current_user.id,
        inicio=payload.inicio,
        fim=payload.fim,
        observacao=payload.observacao.strip() if payload.observacao else None,
        status=status_inicial,
        prazo_confirmacao=None,
        convidados=[
            models.Convidado(nome=c.nome.strip(), cpf=c.cpf) for c in payload.convidados
        ],
    )

    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)

    return schemas.ReservaLocalResposta.from_orm_with_relations(nova_reserva)



@app.put("/agendamentos/{reserva_id}/confirmar", response_model=schemas.ReservaLocalResposta)
def confirmar_agendamento(
    reserva_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reserva = db.query(models.ReservaLocal).filter(models.ReservaLocal.id == reserva_id).first()

    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")

    if reserva.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o locatario pode confirmar a reserva")

    # LIVRE_DEMANDA: fila esgotada -> confirmacao instantanea (First-Come, First-Served).
    # PENDENTE_CONFIRMACAO: precisa confirmar dentro do prazo (cronometro regressivo).
    if reserva.status == models.StatusReserva.PENDENTE_CONFIRMACAO:
        if reserva.prazo_confirmacao and datetime.utcnow() > reserva.prazo_confirmacao:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prazo de confirmacao expirado")
    elif reserva.status != models.StatusReserva.LIVRE_DEMANDA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reserva nao pode ser confirmada. Status atual: {reserva.status.value}",
        )

    reserva.status = models.StatusReserva.CONFIRMADO
    reserva.prazo_confirmacao = None  # Limpa o cronometro

    db.commit()
    db.refresh(reserva)

    return schemas.ReservaLocalResposta.from_orm_with_relations(reserva)


@app.put("/agendamentos/{reserva_id}", response_model=schemas.ReservaLocalResposta)
def atualizar_agendamento(
    reserva_id: int,
    payload: schemas.ReservaLocalAtualizacao,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edicao da reserva pelo dono (parte do CRUD).

    Observacao e convidados podem ser editados enquanto a reserva nao estiver
    confirmada/encerrada. Mudar local/horario so e permitido antes da reserva
    entrar na janela de confirmacao (status AGENDADO ou AGUARDANDO_FILA), pois
    altera a disputa pelo slot e exige recalculo do status.
    """
    reserva = (
        db.query(models.ReservaLocal)
        .options(joinedload(models.ReservaLocal.convidados))
        .filter(models.ReservaLocal.id == reserva_id)
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")
    if reserva.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o dono pode editar a reserva")
    if reserva.status in STATUS_RESERVA_TERMINAIS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reserva encerrada nao pode ser editada")

    novo_local = payload.local_id if payload.local_id is not None else reserva.local_id
    novo_inicio = payload.inicio if payload.inicio is not None else reserva.inicio
    novo_fim = payload.fim if payload.fim is not None else reserva.fim
    mudou_slot = (
        novo_local != reserva.local_id
        or novo_inicio != reserva.inicio
        or novo_fim != reserva.fim
    )

    if mudou_slot:
        if reserva.status not in (
            models.StatusReserva.AGENDADO,
            models.StatusReserva.AGUARDANDO_FILA,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local/horario so podem ser alterados antes da janela de confirmacao",
            )
        if novo_fim <= novo_inicio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Horario final deve ser posterior ao inicial")

        local = db.query(models.LocalAgendavel).filter(
            models.LocalAgendavel.id == novo_local,
            models.LocalAgendavel.ativo.is_(True),
        ).first()
        if not local:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local agendavel nao encontrado")

        reserva.local_id = novo_local
        reserva.inicio = novo_inicio
        reserva.fim = novo_fim
        reserva.status = decidir_status_inicial(db, novo_local, novo_inicio, novo_fim, ignorar_id=reserva.id)
        reserva.prazo_confirmacao = None

    if payload.observacao is not None:
        reserva.observacao = payload.observacao.strip() or None

    if payload.convidados is not None:
        reserva.convidados = [
            models.Convidado(nome=c.nome.strip(), cpf=c.cpf) for c in payload.convidados
        ]

    db.commit()
    db.refresh(reserva)
    return schemas.ReservaLocalResposta.from_orm_with_relations(reserva)


@app.delete("/agendamentos/{reserva_id}", response_model=schemas.ReservaLocalResposta)
def cancelar_agendamento(
    reserva_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancela uma reserva.

    - Dono: pode cancelar a propria reserva enquanto ela nao estiver encerrada.
    - Sindico (ADMIN): Hard Cancel -> revoga QUALQUER reserva em QUALQUER estado,
      ignorando regras de tempo e fila. A vaga liberada e repassada ao proximo da
      fila pelo worker em background.
    """
    reserva = db.query(models.ReservaLocal).filter(models.ReservaLocal.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")

    is_admin = current_user.perfil == models.PerfilUsuario.ADMIN
    if not is_admin:
        if reserva.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o dono ou o sindico podem cancelar")
        if reserva.status in STATUS_RESERVA_TERMINAIS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reserva ja encerrada")

    reserva.status = models.StatusReserva.CANCELADO
    reserva.prazo_confirmacao = None
    db.commit()
    db.refresh(reserva)
    return schemas.ReservaLocalResposta.from_orm_with_relations(reserva)

def processar_filas_reserva():
    """Executa a maquina de estados das reservas (worker em background).

    1. Expira detentores que nao confirmaram dentro do prazo (cronometro vencido).
    2. Abre a janela de confirmacao 48h antes do evento (timer inicial).
    3. Para cada slot sem detentor ativo, promove o topo da fila recalculada por
       historico de uso, iniciando um timer restrito (cascata).
    4. Liberacao de fila: se a fila esgota dentro de 48h e ninguem confirma, o
       slot vira LIVRE_DEMANDA (First-Come, First-Served).
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        limite_48h = now + timedelta(hours=RESERVA_JANELA_CONFIRMACAO_HORAS)

        # 1. Expira quem perdeu o prazo de confirmacao.
        omissos = db.query(models.ReservaLocal).filter(
            models.ReservaLocal.status == models.StatusReserva.PENDENTE_CONFIRMACAO,
            models.ReservaLocal.prazo_confirmacao.isnot(None),
            models.ReservaLocal.prazo_confirmacao < now,
        ).all()
        for reserva in omissos:
            reserva.status = models.StatusReserva.EXPIRADO
            reserva.prazo_confirmacao = None
        db.commit()

        # 2. Detentor entra na janela de 48h -> precisa confirmar (timer inicial).
        agendados = db.query(models.ReservaLocal).filter(
            models.ReservaLocal.status == models.StatusReserva.AGENDADO,
            models.ReservaLocal.inicio <= limite_48h,
            models.ReservaLocal.inicio > now,
        ).all()
        for reserva in agendados:
            reserva.status = models.StatusReserva.PENDENTE_CONFIRMACAO
            reserva.prazo_confirmacao = now + timedelta(hours=RESERVA_PRAZO_INICIAL_HORAS)
        db.commit()

        # 3. Promove a fila por historico de uso quando o slot fica sem detentor.
        aguardando = (
            db.query(models.ReservaLocal)
            .filter(
                models.ReservaLocal.status == models.StatusReserva.AGUARDANDO_FILA,
                models.ReservaLocal.inicio > now,
            )
            .order_by(models.ReservaLocal.data_criacao.asc())
            .all()
        )

        ja_processados: set[int] = set()
        for fila in aguardando:
            if fila.id in ja_processados:
                continue

            # Todos os concorrentes em fila para o mesmo slot.
            concorrentes = [
                r for r in aguardando
                if r.local_id == fila.local_id and r.inicio < fila.fim and r.fim > fila.inicio
            ]
            for r in concorrentes:
                ja_processados.add(r.id)

            dono_ativo = db.query(models.ReservaLocal).filter(
                models.ReservaLocal.local_id == fila.local_id,
                models.ReservaLocal.inicio < fila.fim,
                models.ReservaLocal.fim > fila.inicio,
                models.ReservaLocal.status.in_(STATUS_RESERVA_ATIVOS),
            ).first()
            if dono_ativo:
                continue

            # Sem detentor: o topo da fila recalculada assume a vaga.
            proximo = ordenar_fila(db, concorrentes, now)[0]
            if (proximo.inicio - now) <= timedelta(hours=RESERVA_JANELA_CONFIRMACAO_HORAS):
                proximo.status = models.StatusReserva.PENDENTE_CONFIRMACAO
                proximo.prazo_confirmacao = now + timedelta(hours=RESERVA_PRAZO_CASCATA_HORAS)
            else:
                proximo.status = models.StatusReserva.AGENDADO
                proximo.prazo_confirmacao = None
        db.commit()

        # Liberacao de fila: quando o slot esgota (todos EXPIRADO/sem fila) e ja
        # esta dentro de 48h, nao ha mais detentor ativo. A vaga fica livre e a
        # proxima SOLICITACAO entra direto como LIVRE_DEMANDA (FCFS) com
        # confirmacao instantanea -- ver decidir_status_inicial().

    except Exception as e:
        print(f"[Worker Error] Falha ao processar reservas: {e}")
        db.rollback()
    finally:
        db.close()


@app.get("/agendamentos/me", response_model=list[schemas.ReservaDashboardResposta])
def listar_minhas_reservas(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservas_usuario = (
        db.query(models.ReservaLocal)
        .options(
            joinedload(models.ReservaLocal.local),
            joinedload(models.ReservaLocal.convidados),
        )
        .filter(models.ReservaLocal.usuario_id == current_user.id)
        .order_by(models.ReservaLocal.inicio.asc())
        .all()
    )

    now = datetime.utcnow()
    resultados = []

    for reserva in reservas_usuario:
        posicao = None

        if reserva.status == models.StatusReserva.AGUARDANDO_FILA:
            # Posicao recalculada dinamicamente pela prioridade por historico de uso
            # (quem tem 0 reservas no mes atual vai ao topo), nao pela ordem cronologica.
            concorrentes = db.query(models.ReservaLocal).filter(
                models.ReservaLocal.local_id == reserva.local_id,
                models.ReservaLocal.inicio < reserva.fim,
                models.ReservaLocal.fim > reserva.inicio,
                models.ReservaLocal.status == models.StatusReserva.AGUARDANDO_FILA,
            ).all()
            ordenados = ordenar_fila(db, concorrentes, now)
            posicao = next(
                (i + 1 for i, r in enumerate(ordenados) if r.id == reserva.id),
                None,
            )

        resultados.append(
            schemas.ReservaDashboardResposta(
                id=reserva.id,
                local_id=reserva.local_id,
                local_nome=reserva.local.nome if reserva.local else "Desconhecido",
                inicio=reserva.inicio,
                fim=reserva.fim,
                status=reserva.status,
                prazo_confirmacao=reserva.prazo_confirmacao,
                posicao_fila=posicao,
                total_convidados=len(reserva.convidados),
            )
        )

    return resultados
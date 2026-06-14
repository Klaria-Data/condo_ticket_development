"""Microsserviço de Tickets — CondoTicket.

Responsabilidade: criação, listagem e atualização de status dos tickets de suporte.
Porta padrão: 8002 (exposta internamente; o nginx roteia /tickets para cá).

Regra de negócio do fluxo de status:
    ABERTO → EM_ANDAMENTO → RESOLVIDO
Apenas usuários com perfil ADMIN podem atualizar o status de um ticket.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models import LocalAgendavel, PerfilUsuario, ReservaLocal, StatusTicket, Ticket, Usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CondoTicket — Tickets Service",
    description="Gerenciamento de tickets de suporte do condomínio.",
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


class TicketCriacao(BaseModel):
    """Payload para criar um novo ticket."""

    titulo: str = Field(min_length=3, max_length=200)
    descricao: str = Field(min_length=5)
    imagem_url: str | None = Field(default=None, max_length=500)


class TicketStatusAtualizacao(BaseModel):
    """Payload para atualizar o status de um ticket (somente ADMIN)."""

    status: StatusTicket


class TicketResposta(BaseModel):
    """Dados completos de um ticket, incluindo nome e unidade do morador."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    titulo: str
    descricao: str
    imagem_url: str | None
    status: StatusTicket
    data_criacao: datetime
    data_atualizacao: datetime
    usuario_nome: str | None = None
    unidade: str | None = None

    @classmethod
    def from_orm_with_usuario(cls, ticket: Ticket) -> "TicketResposta":
        """Constrói a resposta incluindo nome e unidade do morador dono do ticket."""
        return cls(
            id=ticket.id,
            usuario_id=ticket.usuario_id,
            titulo=ticket.titulo,
            descricao=ticket.descricao,
            imagem_url=ticket.imagem_url,
            status=ticket.status,
            data_criacao=ticket.data_criacao,
            data_atualizacao=ticket.data_atualizacao,
            usuario_nome=ticket.usuario.nome if ticket.usuario else None,
            unidade=ticket.usuario.unidade if ticket.usuario else None,
        )


class LocalAgendavelCriacao(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)


class LocalAgendavelResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    ativo: bool
    data_criacao: datetime


class ReservaLocalCriacao(BaseModel):
    local_id: int
    inicio: datetime
    fim: datetime
    observacao: str | None = Field(default=None, max_length=500)

    @field_validator("fim")
    @classmethod
    def validar_periodo(cls, fim: datetime, info):
        inicio = info.data.get("inicio")
        if inicio and fim <= inicio:
            raise ValueError("Horario final deve ser posterior ao horario inicial")
        return fim


class ReservaLocalResposta(BaseModel):
    id: int
    local_id: int
    local_nome: str
    usuario_id: int
    usuario_nome: str
    unidade: str
    inicio: datetime
    fim: datetime
    observacao: str | None
    data_criacao: datetime

    @classmethod
    def from_orm_with_relations(cls, reserva: ReservaLocal) -> "ReservaLocalResposta":
        return cls(
            id=reserva.id,
            local_id=reserva.local_id,
            local_nome=reserva.local.nome if reserva.local else "",
            usuario_id=reserva.usuario_id,
            usuario_nome=reserva.usuario.nome if reserva.usuario else "",
            unidade=reserva.usuario.unidade if reserva.usuario else "",
            inicio=reserva.inicio,
            fim=reserva.fim,
            observacao=reserva.observacao,
            data_criacao=reserva.data_criacao,
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

# Fluxo de transição válido de status
_PROXIMO_STATUS_VALIDO = {
    StatusTicket.ABERTO: StatusTicket.EM_ANDAMENTO,
    StatusTicket.EM_ANDAMENTO: StatusTicket.RESOLVIDO,
    StatusTicket.RESOLVIDO: StatusTicket.RESOLVIDO,
}


@app.get(
    "/tickets",
    response_model=list[TicketResposta],
    summary="Listar tickets",
)
def listar_tickets(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TicketResposta]:
    """Retorna a lista de tickets visível para o usuário autenticado.

    - **ADMIN**: vê todos os tickets do condomínio.
    - **MORADOR**: vê apenas seus próprios tickets.

    Os resultados incluem nome e unidade do morador que abriu o ticket.
    """
    query = db.query(Ticket).options(joinedload(Ticket.usuario))

    if current_user.perfil != PerfilUsuario.ADMIN:
        query = query.filter(Ticket.usuario_id == current_user.id)

    tickets = query.order_by(Ticket.data_criacao.desc()).all()
    return [TicketResposta.from_orm_with_usuario(t) for t in tickets]


@app.post(
    "/tickets",
    response_model=TicketResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar ticket",
)
def criar_ticket(
    payload: TicketCriacao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResposta:
    """Abre um novo ticket de suporte.

    O ticket sempre começa com status **ABERTO** para respeitar o fluxo obrigatório.
    O morador autenticado é automaticamente associado como dono do ticket.
    """
    novo_ticket = Ticket(
        usuario_id=current_user.id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        imagem_url=payload.imagem_url,
        status=StatusTicket.ABERTO,
    )

    db.add(novo_ticket)
    db.commit()
    db.refresh(novo_ticket)

    # Recarrega com o relacionamento para incluir usuario_nome na resposta
    db.refresh(novo_ticket)
    novo_ticket.usuario = current_user

    logger.info("Ticket criado: id=%d usuario_id=%d", novo_ticket.id, current_user.id)
    return TicketResposta.from_orm_with_usuario(novo_ticket)


@app.put(
    "/tickets/{ticket_id}/status",
    response_model=TicketResposta,
    summary="Atualizar status do ticket",
)
def atualizar_status_ticket(
    ticket_id: int,
    payload: TicketStatusAtualizacao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TicketResposta:
    """Avança o status de um ticket seguindo o fluxo ABERTO → EM_ANDAMENTO → RESOLVIDO.

    Apenas usuários com perfil **ADMIN** podem alterar o status.
    Tentativas de pular etapas (ex: ABERTO → RESOLVIDO) são rejeitadas com 400.
    """
    if current_user.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem atualizar status de tickets",
        )

    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.usuario))
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nao encontrado")

    proximo_valido = _PROXIMO_STATUS_VALIDO[ticket.status]
    if payload.status != proximo_valido and payload.status != ticket.status:
        logger.warning(
            "Transição inválida no ticket %d: %s → %s (esperado: %s)",
            ticket_id,
            ticket.status,
            payload.status,
            proximo_valido,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fluxo invalido de status. Use ABERTO -> EM_ANDAMENTO -> RESOLVIDO",
        )

    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)

    logger.info("Ticket %d atualizado para status %s", ticket_id, payload.status)
    return TicketResposta.from_orm_with_usuario(ticket)


@app.get(
    "/locais-agendaveis",
    response_model=list[LocalAgendavelResposta],
    summary="Listar locais agendaveis",
)
def listar_locais_agendaveis(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LocalAgendavel]:
    return (
        db.query(LocalAgendavel)
        .filter(LocalAgendavel.ativo.is_(True))
        .order_by(LocalAgendavel.nome.asc())
        .all()
    )


@app.post(
    "/locais-agendaveis",
    response_model=LocalAgendavelResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar local agendavel",
)
def criar_local_agendavel(
    payload: LocalAgendavelCriacao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LocalAgendavel:
    if current_user.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem executar esta acao",
        )

    nome_normalizado = payload.nome.strip()
    existing_local = db.query(LocalAgendavel).filter(LocalAgendavel.nome == nome_normalizado).first()
    if existing_local:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local ja cadastrado")

    novo_local = LocalAgendavel(
        nome=nome_normalizado,
        descricao=payload.descricao.strip() if payload.descricao else None,
    )

    db.add(novo_local)
    db.commit()
    db.refresh(novo_local)

    logger.info("Local agendavel criado: id=%d nome=%s", novo_local.id, novo_local.nome)
    return novo_local


@app.get(
    "/agendamentos",
    response_model=list[ReservaLocalResposta],
    summary="Listar agendamentos",
)
def listar_agendamentos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReservaLocalResposta]:
    reservas = (
        db.query(ReservaLocal)
        .options(joinedload(ReservaLocal.local), joinedload(ReservaLocal.usuario))
        .order_by(ReservaLocal.inicio.asc())
        .all()
    )

    return [ReservaLocalResposta.from_orm_with_relations(reserva) for reserva in reservas]


@app.post(
    "/agendamentos",
    response_model=ReservaLocalResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar agendamento",
)
def criar_agendamento(
    payload: ReservaLocalCriacao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReservaLocalResposta:
    local = (
        db.query(LocalAgendavel)
        .filter(LocalAgendavel.id == payload.local_id, LocalAgendavel.ativo.is_(True))
        .first()
    )
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local agendavel nao encontrado")

    reserva_conflitante = (
        db.query(ReservaLocal)
        .filter(
            ReservaLocal.local_id == payload.local_id,
            ReservaLocal.inicio < payload.fim,
            ReservaLocal.fim > payload.inicio,
        )
        .first()
    )
    if reserva_conflitante:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Horario indisponivel para este local",
        )

    nova_reserva = ReservaLocal(
        local_id=payload.local_id,
        usuario_id=current_user.id,
        inicio=payload.inicio,
        fim=payload.fim,
        observacao=payload.observacao.strip() if payload.observacao else None,
    )

    db.add(nova_reserva)
    db.commit()
    db.refresh(nova_reserva)
    nova_reserva.local = local
    nova_reserva.usuario = current_user

    logger.info("Agendamento criado: id=%d local_id=%d usuario_id=%d", nova_reserva.id, local.id, current_user.id)
    return ReservaLocalResposta.from_orm_with_relations(nova_reserva)

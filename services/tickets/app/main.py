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
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models import PerfilUsuario, StatusTicket, Ticket, Usuario

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

"""Microsserviço de Comentários — CondoTicket.

Responsabilidade: chat/comentários dos tickets — listar, criar, editar e deletar mensagens.
Porta padrão: 8003 (exposta internamente; o nginx roteia /tickets/*/comentarios para cá).

Regras de permissão:
    - O morador lista e cria comentários apenas nos próprios chamados; o ADMIN, em todos.
    - Apenas o autor do comentário ou um ADMIN pode editar ou deletar.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models import ComentarioTicket, PerfilUsuario, Ticket, Usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CondoTicket — Comments Service",
    description="Chat e comentários dos tickets de suporte.",
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


def _as_utc(value: datetime) -> datetime:
    """Normaliza datas gravadas sem fuso como UTC antes de enviá-las ao cliente.

    As colunas DATETIME do MySQL guardam o horário UTC sem o offset. Sem esta
    normalização o cliente interpretaria a data como horário local e exibiria
    o comentário adiantado (podendo virar o dia).
    """
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class ComentarioTicketCriacao(BaseModel):
    """Payload para criar um novo comentário."""

    mensagem: str = Field(min_length=1, max_length=2000)


class ComentarioTicketEdicao(BaseModel):
    """Payload para editar a mensagem de um comentário existente."""

    mensagem: str = Field(min_length=1, max_length=2000)


class ComentarioTicketResposta(BaseModel):
    """Dados completos de um comentário, incluindo o nome do autor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    usuario_id: int
    mensagem: str
    data_envio: datetime
    usuario_nome: str | None = None

    @classmethod
    def from_orm_with_usuario(cls, comentario: ComentarioTicket) -> "ComentarioTicketResposta":
        """Constrói a resposta incluindo o nome do usuário que fez o comentário."""
        return cls(
            id=comentario.id,
            ticket_id=comentario.ticket_id,
            usuario_id=comentario.usuario_id,
            mensagem=comentario.mensagem,
            data_envio=_as_utc(comentario.data_envio),
            usuario_nome=comentario.usuario.nome if comentario.usuario else None,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_ticket_visivel(ticket_id: int, current_user: Usuario, db: Session) -> Ticket:
    """Retorna o ticket se o usuário puder vê-lo.

    Espelha a regra de ``GET /tickets``: o morador só enxerga os próprios chamados
    e o ADMIN enxerga todos. Sem esta checagem, bastava adivinhar o id do chamado
    para ler — e comentar — a conversa de outro morador.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket nao encontrado")

    if ticket.usuario_id != current_user.id and current_user.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissao para acessar os comentarios deste chamado",
        )

    return ticket


def _get_comentario_or_404(comentario_id: int, ticket_id: int, db: Session) -> ComentarioTicket:
    """Retorna o comentário do ticket ou lança 404 se não existir."""
    comentario = (
        db.query(ComentarioTicket)
        .filter(
            ComentarioTicket.id == comentario_id,
            ComentarioTicket.ticket_id == ticket_id,
        )
        .first()
    )
    if not comentario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario nao encontrado")
    return comentario


def _verificar_permissao(comentario: ComentarioTicket, current_user: Usuario, acao: str) -> None:
    """Lança 403 se o usuário não for o autor do comentário nem um ADMIN."""
    if comentario.usuario_id != current_user.id and current_user.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Sem permissao para {acao} este comentario",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.get(
    "/tickets/{ticket_id}/comentarios",
    response_model=list[ComentarioTicketResposta],
    summary="Listar comentários do ticket",
)
def listar_comentarios_ticket(
    ticket_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ComentarioTicketResposta]:
    """Retorna todos os comentários de um ticket em ordem cronológica crescente.

    O morador só enxerga os comentários dos chamados que abriu; o ADMIN, de todos.
    """
    _get_ticket_visivel(ticket_id, current_user, db)

    comentarios = (
        db.query(ComentarioTicket)
        .filter(ComentarioTicket.ticket_id == ticket_id)
        .order_by(ComentarioTicket.data_envio.asc())
        .all()
    )

    return [ComentarioTicketResposta.from_orm_with_usuario(c) for c in comentarios]


@app.post(
    "/tickets/{ticket_id}/comentarios",
    response_model=ComentarioTicketResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Criar comentário no ticket",
)
def criar_comentario_ticket(
    ticket_id: int,
    payload: ComentarioTicketCriacao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComentarioTicketResposta:
    """Adiciona um novo comentário/mensagem ao chat do ticket.

    O morador só comenta nos chamados que abriu; o ADMIN, em todos.
    O comentário é automaticamente associado ao usuário autenticado.
    """
    _get_ticket_visivel(ticket_id, current_user, db)

    novo_comentario = ComentarioTicket(
        ticket_id=ticket_id,
        usuario_id=current_user.id,
        mensagem=payload.mensagem,
    )

    db.add(novo_comentario)
    db.commit()
    db.refresh(novo_comentario)

    novo_comentario.usuario = current_user
    logger.info("Comentário criado: id=%d ticket_id=%d", novo_comentario.id, ticket_id)

    return ComentarioTicketResposta.from_orm_with_usuario(novo_comentario)


@app.put(
    "/tickets/{ticket_id}/comentarios/{comentario_id}",
    response_model=ComentarioTicketResposta,
    summary="Editar comentário",
)
def editar_comentario_ticket(
    ticket_id: int,
    comentario_id: int,
    payload: ComentarioTicketEdicao,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComentarioTicketResposta:
    """Edita a mensagem de um comentário existente.

    Apenas o **autor** do comentário ou um **ADMIN** podem editar.
    Retorna 403 se o usuário não tiver permissão e 404 se o comentário não existir.
    """
    _get_ticket_visivel(ticket_id, current_user, db)
    comentario = _get_comentario_or_404(comentario_id, ticket_id, db)
    _verificar_permissao(comentario, current_user, "editar")

    comentario.mensagem = payload.mensagem
    db.commit()
    db.refresh(comentario)

    logger.info("Comentário %d editado pelo usuario %d", comentario_id, current_user.id)
    return ComentarioTicketResposta.from_orm_with_usuario(comentario)


@app.delete(
    "/tickets/{ticket_id}/comentarios/{comentario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar comentário",
)
def deletar_comentario_ticket(
    ticket_id: int,
    comentario_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove permanentemente um comentário.

    Apenas o **autor** do comentário ou um **ADMIN** podem deletar.
    Retorna 204 No Content em caso de sucesso.
    Retorna 403 se o usuário não tiver permissão e 404 se o comentário não existir.
    """
    _get_ticket_visivel(ticket_id, current_user, db)
    comentario = _get_comentario_or_404(comentario_id, ticket_id, db)
    _verificar_permissao(comentario, current_user, "deletar")

    db.delete(comentario)
    db.commit()

    logger.info("Comentário %d deletado pelo usuario %d", comentario_id, current_user.id)

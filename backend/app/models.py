"""SQLAlchemy models for the CondoTicket domain."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class PerfilUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    MORADOR = "MORADOR"


class StatusTicket(str, enum.Enum):
    ABERTO = "ABERTO"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    RESOLVIDO = "RESOLVIDO"


class Usuario(Base):
    __tablename__ = "USUARIO"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str] = mapped_column(String(30), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        Enum(PerfilUsuario, name="perfil_usuario_enum"),
        nullable=False,
        default=PerfilUsuario.MORADOR,
    )
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    postagens_forum: Mapped[list["PostagemForum"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    comentarios_ticket: Mapped[list["ComentarioTicket"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    comentarios_forum: Mapped[list["ComentarioForum"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    reservas: Mapped[list["ReservaLocal"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    convites_enviados: Mapped[list["ConviteMorador"]] = relationship(back_populates="criado_por")


class Ticket(Base):
    __tablename__ = "TICKET"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[StatusTicket] = mapped_column(
        Enum(StatusTicket, name="status_ticket_enum"),
        nullable=False,
        default=StatusTicket.ABERTO,
    )
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="tickets")
    comentarios: Mapped[list["ComentarioTicket"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class PostagemForum(Base):
    __tablename__ = "POSTAGEM_FORUM"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="postagens_forum")
    comentarios: Mapped[list["ComentarioForum"]] = relationship(
        back_populates="postagem", cascade="all, delete-orphan"
    )


class ComentarioTicket(Base):
    __tablename__ = "COMENTARIO_TICKET"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("TICKET.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    data_envio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="comentarios")
    usuario: Mapped["Usuario"] = relationship(back_populates="comentarios_ticket")


class ComentarioForum(Base):
    __tablename__ = "COMENTARIO_FORUM"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    postagem_id: Mapped[int] = mapped_column(ForeignKey("POSTAGEM_FORUM.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    postagem: Mapped["PostagemForum"] = relationship(back_populates="comentarios")
    usuario: Mapped["Usuario"] = relationship(back_populates="comentarios_forum")


class LocalAgendavel(Base):
    __tablename__ = "LOCAL_AGENDAVEL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    reservas: Mapped[list["ReservaLocal"]] = relationship(back_populates="local", cascade="all, delete-orphan")


class ReservaLocal(Base):
    __tablename__ = "RESERVA_LOCAL"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("LOCAL_AGENDAVEL.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    fim: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    local: Mapped["LocalAgendavel"] = relationship(back_populates="reservas")
    usuario: Mapped["Usuario"] = relationship(back_populates="reservas")


class ConviteMorador(Base):
    __tablename__ = "CONVITE_MORADOR"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    unidade: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    data_expiracao: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_uso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("USUARIO.id"), nullable=False)

    criado_por: Mapped["Usuario"] = relationship(back_populates="convites_enviados")

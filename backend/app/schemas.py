"""Pydantic schemas used for request/response validation."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import PerfilUsuario, StatusReserva, StatusTicket


def validar_cpf(valor: str) -> str:
    """Valida o formato e os digitos verificadores de um CPF.

    Aceita CPF com ou sem mascara (ex.: ``123.456.789-09`` ou ``12345678909``)
    e retorna sempre os 11 digitos sem formatacao.
    """
    digitos = re.sub(r"\D", "", valor or "")

    if len(digitos) != 11:
        raise ValueError("CPF deve conter 11 digitos")
    if digitos == digitos[0] * 11:
        raise ValueError("CPF invalido")

    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        resto = (soma * 10) % 11
        digito = 0 if resto == 10 else resto
        if digito != int(digitos[tamanho]):
            raise ValueError("CPF invalido")

    return digitos


class UsuarioRegistro(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    unidade: str = Field(min_length=1, max_length=30)
    perfil: PerfilUsuario = PerfilUsuario.MORADOR


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    unidade: str
    perfil: PerfilUsuario
    data_cadastro: datetime


class LoginEntrada(BaseModel):
    email: EmailStr
    senha: str


class TokenResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResposta(TokenResposta):
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


class TicketCriacao(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descricao: str = Field(min_length=5)
    imagem_url: str | None = Field(default=None, max_length=500)


class TicketStatusAtualizacao(BaseModel):
    status: StatusTicket


class TicketResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    titulo: str
    descricao: str
    imagem_url: str | None
    status: StatusTicket
    data_criacao: datetime
    data_atualizacao: datetime


class ComentarioTicketCriacao(BaseModel):
    mensagem: str = Field(min_length=1, max_length=2000)


class ComentarioTicketResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    usuario_id: int
    mensagem: str
    data_envio: datetime
    usuario_nome: str | None = None

    @classmethod
    def from_orm_with_usuario(cls, comentario):
        """Helper para incluir o nome do usuário na resposta."""
        return cls(
            id=comentario.id,
            ticket_id=comentario.ticket_id,
            usuario_id=comentario.usuario_id,
            mensagem=comentario.mensagem,
            data_envio=comentario.data_envio,
            usuario_nome=comentario.usuario.nome if comentario.usuario else None,
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


class ConvidadoCriacao(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    cpf: str = Field(min_length=11, max_length=14)

    @field_validator("cpf")
    @classmethod
    def normalizar_cpf(cls, valor: str) -> str:
        return validar_cpf(valor)


class ConvidadoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reserva_id: int
    nome: str
    cpf: str


class ReservaLocalCriacao(BaseModel):
    local_id: int
    inicio: datetime
    fim: datetime
    observacao: str | None = Field(default=None, max_length=500)
    convidados: list[ConvidadoCriacao] = Field(default_factory=list, max_length=50)

    @field_validator("fim")
    @classmethod
    def validar_periodo(cls, fim: datetime, info):
        inicio = info.data.get("inicio")
        if inicio and fim <= inicio:
            raise ValueError("Horario final deve ser posterior ao horario inicial")
        return fim


class ReservaLocalAtualizacao(BaseModel):
    """Campos editaveis de uma reserva ainda nao confirmada (parte do CRUD)."""

    local_id: int | None = None
    inicio: datetime | None = None
    fim: datetime | None = None
    observacao: str | None = Field(default=None, max_length=500)
    convidados: list[ConvidadoCriacao] | None = Field(default=None, max_length=50)


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

    status: StatusReserva
    prazo_confirmacao: datetime | None
    convidados: list[ConvidadoResposta] = Field(default_factory=list)

    @classmethod
    def from_orm_with_relations(cls, reserva, incluir_convidados: bool = True):
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
            status=reserva.status,
            prazo_confirmacao=reserva.prazo_confirmacao,
            convidados=(
                [ConvidadoResposta.model_validate(c) for c in reserva.convidados]
                if incluir_convidados
                else []
            ),
        )

class ReservaDashboardResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    local_id: int
    local_nome: str
    inicio: datetime
    fim: datetime
    status: StatusReserva
    prazo_confirmacao: datetime | None
    posicao_fila: int | None = None
    total_convidados: int = 0
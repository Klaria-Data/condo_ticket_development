"""Pydantic schemas used for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import PerfilUsuario, StatusTicket


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


class TicketCriacao(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descricao: str = Field(min_length=5)
    imagem_url: str | None = Field(default=None, max_length=500)


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

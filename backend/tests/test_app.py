import os
import sys
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def reset_app_modules():
    """Reset imported app modules before each test so database configuration can change."""
    modules_to_remove = [name for name in sys.modules if name.startswith("app.") or name == "app"]
    for module_name in modules_to_remove:
        sys.modules.pop(module_name, None)
    yield


@pytest.fixture
def client(tmp_path):
    database_file = tmp_path / "test_condoticket.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_file}"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:4200"

    import app.main as main

    return TestClient(main.app)


def register_user(client, *, email: str, perfil: str = "MORADOR") -> dict:
    payload = {
        "nome": "Usuário de Teste",
        "email": email,
        "senha": "senha123456",
        "unidade": "101",
        "perfil": perfil,
    }

    response = client.post("/registro", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client, *, email: str, senha: str = "senha123456") -> dict:
    response = client.post("/login", json={"email": email, "senha": senha})
    return response


def create_ticket(client, token: str, *, titulo: str, descricao: str, imagem_url: str | None = None) -> dict:
    response = client.post(
        "/tickets",
        json={"titulo": titulo, "descricao": descricao, "imagem_url": imagem_url},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_comment(client, token: str, ticket_id: int, mensagem: str) -> dict:
    response = client.post(
        f"/tickets/{ticket_id}/comentarios",
        json={"mensagem": mensagem},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registrar_usuario_e_email_duplicado(client):
    email = "duplicado@teste.com"

    register_user(client, email=email)

    response = client.post(
        "/registro",
        json={
            "nome": "Outro Usuário",
            "email": email,
            "senha": "senha123456",
            "unidade": "102",
            "perfil": "MORADOR",
        },
    )

    assert response.status_code == 400
    assert "Email ja cadastrado" in response.json().get("detail", "")


def test_login_sucesso_e_senha_invalida(client):
    email = "login-sucesso@teste.com"
    register_user(client, email=email)

    response = login_user(client, email=email)
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["usuario_id"]
    assert data["perfil"] == "MORADOR"

    invalid = login_user(client, email=email, senha="senhaerrada")
    assert invalid.status_code == 401
    assert "Credenciais invalidas" in invalid.json().get("detail", "")


def test_criar_ticket_protegido_e_sem_autenticacao(client):
    email = "ticket-protegido@teste.com"
    register_user(client, email=email)
    token = login_user(client, email=email).json()["access_token"]

    ticket = create_ticket(
        client,
        token=token,
        titulo="Teste de ticket protegido",
        descricao="Descrição do ticket protegido.",
        imagem_url=None,
    )

    assert ticket["status"] == "ABERTO"
    assert ticket["titulo"] == "Teste de ticket protegido"

    response = client.post(
        "/tickets",
        json={
            "titulo": "Tentativa inválida",
            "descricao": "Sem token não deve permitir.",
            "imagem_url": None,
        },
    )

    assert response.status_code in {401, 403}


def test_listar_tickets_retorna_somente_do_usuario_non_admin(client):
    user1_email = "usuario1@teste.com"
    user2_email = "usuario2@teste.com"

    register_user(client, email=user1_email)
    token1 = login_user(client, email=user1_email).json()["access_token"]
    create_ticket(
        client,
        token=token1,
        titulo="Ticket do usuário 1",
        descricao="Ticket exclusivo do usuário 1.",
    )

    register_user(client, email=user2_email)
    token2 = login_user(client, email=user2_email).json()["access_token"]
    create_ticket(
        client,
        token=token2,
        titulo="Ticket do usuário 2",
        descricao="Ticket exclusivo do usuário 2.",
    )

    response = client.get("/tickets", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["titulo"] == "Ticket do usuário 1"


def test_atualizar_status_ticket_com_fluxo_valido_e_invalido(client):
    morador_email = "morador@teste.com"
    admin_email = "admin@teste.com"

    register_user(client, email=morador_email, perfil="MORADOR")
    register_user(client, email=admin_email, perfil="ADMIN")

    morador_token = login_user(client, email=morador_email).json()["access_token"]
    admin_token = login_user(client, email=admin_email).json()["access_token"]

    ticket = create_ticket(
        client,
        token=morador_token,
        titulo="Ticket para atualização de status",
        descricao="Ticket criado pelo morador.",
    )

    ticket_id = ticket["id"]

    response = client.put(
        f"/tickets/{ticket_id}/status",
        json={"status": "EM_ANDAMENTO"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "EM_ANDAMENTO"

    invalid = client.put(
        f"/tickets/{ticket_id}/status",
        json={"status": "ABERTO"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert invalid.status_code == 400
    assert "Fluxo invalido de status" in invalid.json().get("detail", "")


def test_criar_e_listar_comentarios_ticket(client):
    email = "comentario@teste.com"
    register_user(client, email=email)
    token = login_user(client, email=email).json()["access_token"]

    ticket = create_ticket(
        client,
        token=token,
        titulo="Ticket com comentário",
        descricao="Ticket para testar comentários.",
    )

    comment = create_comment(client, token=token, ticket_id=ticket["id"], mensagem="Primeiro comentário")
    assert comment["mensagem"] == "Primeiro comentário"
    assert comment["usuario_nome"] == "Usuário de Teste"

    response = client.get(
        f"/tickets/{ticket['id']}/comentarios",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    comments = response.json()
    assert len(comments) == 1
    assert comments[0]["mensagem"] == "Primeiro comentário"
    assert comments[0]["usuario_nome"] == "Usuário de Teste"

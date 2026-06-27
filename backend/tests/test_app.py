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


def create_bookable_place(client, token: str, *, nome: str = "Piscina") -> dict:
    response = client.post(
        "/locais-agendaveis",
        json={"nome": nome, "descricao": "Area compartilhada do condominio."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_resident_invite(client, token: str, *, email: str = "novo.morador@teste.com") -> dict:
    response = client.post(
        "/moradores/convites",
        json={"nome": "Novo Morador", "email": email, "unidade": "302"},
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
    assert comments[0]["ticket_id"] == ticket["id"]


def test_sindico_cria_local_agendavel_e_morador_nao_pode_criar(client):
    admin_email = "sindico-locais@teste.com"
    morador_email = "morador-locais@teste.com"

    register_user(client, email=admin_email, perfil="ADMIN")
    register_user(client, email=morador_email, perfil="MORADOR")

    admin_token = login_user(client, email=admin_email).json()["access_token"]
    morador_token = login_user(client, email=morador_email).json()["access_token"]

    local = create_bookable_place(client, admin_token, nome="Academia")
    assert local["nome"] == "Academia"
    assert local["ativo"] is True

    forbidden = client.post(
        "/locais-agendaveis",
        json={"nome": "Salao de festas"},
        headers={"Authorization": f"Bearer {morador_token}"},
    )
    assert forbidden.status_code == 403


def test_criar_agendamento_concorrente_entra_na_fila(client):
    # Requisito: o sistema NAO bloqueia reservas concorrentes, ele as enfileira.
    admin_email = "sindico-agendamento@teste.com"
    morador1_email = "morador301@teste.com"
    morador2_email = "morador302@teste.com"

    register_user(client, email=admin_email, perfil="ADMIN")
    register_user(client, email=morador1_email, perfil="MORADOR")
    register_user(client, email=morador2_email, perfil="MORADOR")

    admin_token = login_user(client, email=admin_email).json()["access_token"]
    morador1_token = login_user(client, email=morador1_email).json()["access_token"]
    morador2_token = login_user(client, email=morador2_email).json()["access_token"]

    local = create_bookable_place(client, admin_token, nome="Piscina")

    reserva = client.post(
        "/agendamentos",
        json={
            "local_id": local["id"],
            "inicio": "2027-01-02T13:00:00",
            "fim": "2027-01-02T17:00:00",
            "observacao": "Reserva do apartamento 301",
        },
        headers={"Authorization": f"Bearer {morador1_token}"},
    )
    assert reserva.status_code == 201, reserva.text
    assert reserva.json()["local_nome"] == "Piscina"
    assert reserva.json()["unidade"] == "101"
    # Primeiro a reservar (>48h) vira o detentor do slot.
    assert reserva.json()["status"] == "AGENDADO"

    concorrente = client.post(
        "/agendamentos",
        json={
            "local_id": local["id"],
            "inicio": "2027-01-02T14:00:00",
            "fim": "2027-01-02T16:00:00",
        },
        headers={"Authorization": f"Bearer {morador2_token}"},
    )
    # Nao bloqueia: a reserva concorrente entra na fila.
    assert concorrente.status_code == 201, concorrente.text
    assert concorrente.json()["status"] == "AGUARDANDO_FILA"

    # A agenda compartilhada mostra apenas o detentor ativo (nao quem esta na fila).
    listagem = client.get("/agendamentos", headers={"Authorization": f"Bearer {morador2_token}"})
    assert listagem.status_code == 200
    assert len(listagem.json()) == 1

    # O morador 2 ve sua reserva na fila e sua posicao no dashboard "Minhas Reservas".
    minhas = client.get("/agendamentos/me", headers={"Authorization": f"Bearer {morador2_token}"})
    assert minhas.status_code == 200
    fila = minhas.json()
    assert len(fila) == 1
    assert fila[0]["status"] == "AGUARDANDO_FILA"
    assert fila[0]["posicao_fila"] == 1


def test_sindico_cria_convite_e_morador_aceita_com_senha(client):
    admin_email = "sindico-convite@teste.com"
    novo_email = "convidado@teste.com"

    register_user(client, email=admin_email, perfil="ADMIN")
    admin_token = login_user(client, email=admin_email).json()["access_token"]

    convite = create_resident_invite(client, admin_token, email=novo_email)
    assert convite["email"] == novo_email
    assert convite["usado"] is False
    assert "/convite/" in convite["convite_url"]

    token = convite["convite_url"].rstrip("/").split("/")[-1]
    consulta = client.get(f"/convites/{token}")
    assert consulta.status_code == 200
    assert consulta.json()["unidade"] == "302"

    aceite = client.post(f"/convites/{token}/aceitar", json={"senha": "minhasenha123"})
    assert aceite.status_code == 200, aceite.text
    assert aceite.json()["perfil"] == "MORADOR"

    login = login_user(client, email=novo_email, senha="minhasenha123")
    assert login.status_code == 200
    assert login.json()["unidade"] == "302"

    segundo_aceite = client.post(f"/convites/{token}/aceitar", json={"senha": "outrasenha123"})
    assert segundo_aceite.status_code == 404


def test_morador_nao_pode_criar_convite(client):
    morador_email = "morador-sem-convite@teste.com"
    register_user(client, email=morador_email, perfil="MORADOR")
    morador_token = login_user(client, email=morador_email).json()["access_token"]

    response = client.post(
        "/moradores/convites",
        json={"nome": "Outro Morador", "email": "outro@teste.com", "unidade": "401"},
        headers={"Authorization": f"Bearer {morador_token}"},
    )

    assert response.status_code == 403

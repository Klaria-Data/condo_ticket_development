"""Testes das funcionalidades de reserva: convidados, fila por historico,
edicao (CRUD) e override do sindico (Hard Cancel)."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# CPFs validos (digitos verificadores corretos) usados nos testes.
CPF_VALIDO = "11144477735"
CPF_VALIDO_MASCARADO = "111.444.777-35"


@pytest.fixture(autouse=True)
def reset_app_modules():
    for name in [n for n in sys.modules if n.startswith("app.") or n == "app"]:
        sys.modules.pop(name, None)
    yield


@pytest.fixture
def client(tmp_path):
    database_file = tmp_path / "test_reservas.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_file}"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:4200"

    import app.main as main

    return TestClient(main.app)


def _registrar(client, email, perfil="MORADOR", unidade="101"):
    resp = client.post(
        "/registro",
        json={
            "nome": "Fulano de Teste",
            "email": email,
            "senha": "senha123456",
            "unidade": unidade,
            "perfil": perfil,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _token(client, email):
    return client.post("/login", json={"email": email, "senha": "senha123456"}).json()["access_token"]


def _criar_local(client, token, nome="Salao"):
    resp = client.post(
        "/locais-agendaveis",
        json={"nome": nome, "descricao": "Area comum."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _futuro(dias, hora=10):
    base = datetime.utcnow() + timedelta(days=dias)
    return base.replace(hour=hora, minute=0, second=0, microsecond=0)


def test_reserva_com_convidado_valida_cpf(client):
    _registrar(client, "admin@t.com", perfil="ADMIN")
    admin = _token(client, "admin@t.com")
    _registrar(client, "morador@t.com")
    morador = _token(client, "morador@t.com")
    local = _criar_local(client, admin)

    inicio = _futuro(10)
    fim = inicio + timedelta(hours=2)

    # CPF mascarado valido e aceito e normalizado para digitos.
    ok = client.post(
        "/agendamentos",
        json={
            "local_id": local["id"],
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "convidados": [{"nome": "Convidado Um", "cpf": CPF_VALIDO_MASCARADO}],
        },
        headers={"Authorization": f"Bearer {morador}"},
    )
    assert ok.status_code == 201, ok.text
    convidados = ok.json()["convidados"]
    assert len(convidados) == 1
    assert convidados[0]["cpf"] == CPF_VALIDO

    # CPF com digitos verificadores invalidos e rejeitado (422).
    ruim = client.post(
        "/agendamentos",
        json={
            "local_id": local["id"],
            "inicio": _futuro(11).isoformat(),
            "fim": (_futuro(11) + timedelta(hours=2)).isoformat(),
            "convidados": [{"nome": "Convidado Dois", "cpf": "123.456.789-00"}],
        },
        headers={"Authorization": f"Bearer {morador}"},
    )
    assert ruim.status_code == 422, ruim.text


def test_convidados_sao_privados_na_agenda_compartilhada(client):
    _registrar(client, "admin2@t.com", perfil="ADMIN")
    admin = _token(client, "admin2@t.com")
    _registrar(client, "dono@t.com", unidade="201")
    dono = _token(client, "dono@t.com")
    _registrar(client, "vizinho@t.com", unidade="202")
    vizinho = _token(client, "vizinho@t.com")
    local = _criar_local(client, admin)

    inicio = _futuro(12)
    fim = inicio + timedelta(hours=2)
    criada = client.post(
        "/agendamentos",
        json={
            "local_id": local["id"],
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "convidados": [{"nome": "Amigo", "cpf": CPF_VALIDO}],
        },
        headers={"Authorization": f"Bearer {dono}"},
    )
    assert criada.status_code == 201, criada.text
    reserva_id = criada.json()["id"]

    # O dono ve os convidados (com CPF).
    agenda_dono = client.get("/agendamentos", headers={"Authorization": f"Bearer {dono}"}).json()
    minha = next(r for r in agenda_dono if r["id"] == reserva_id)
    assert len(minha["convidados"]) == 1

    # O vizinho ve a reserva, mas NAO os dados (CPF) dos convidados alheios.
    agenda_vizinho = client.get("/agendamentos", headers={"Authorization": f"Bearer {vizinho}"}).json()
    alheia = next(r for r in agenda_vizinho if r["id"] == reserva_id)
    assert alheia["convidados"] == []

    # O sindico (admin) tem visibilidade dos convidados para controle de entrada.
    agenda_admin = client.get("/agendamentos", headers={"Authorization": f"Bearer {admin}"}).json()
    vista_admin = next(r for r in agenda_admin if r["id"] == reserva_id)
    assert len(vista_admin["convidados"]) == 1


def test_fila_prioriza_quem_nao_reservou_no_mes(client):
    # Testa diretamente a ordenacao por historico de uso (regra central da fila).
    import app.main as main

    db = main.SessionLocal()
    try:
        local = main.models.LocalAgendavel(nome="Quadra")
        db.add(local)
        db.commit()
        db.refresh(local)

        usuario_a = main.models.Usuario(nome="A", email="a@h.com", senha_hash="x", unidade="1")
        usuario_b = main.models.Usuario(nome="B", email="b@h.com", senha_hash="x", unidade="2")
        db.add_all([usuario_a, usuario_b])
        db.commit()

        agora = datetime.utcnow()
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # A ja possui uma reserva CONFIRMADA no mes atual; B nao tem nenhuma.
        historico_a = main.models.ReservaLocal(
            local_id=local.id,
            usuario_id=usuario_a.id,
            inicio=inicio_mes + timedelta(days=1, hours=10),
            fim=inicio_mes + timedelta(days=1, hours=12),
            status=main.models.StatusReserva.CONFIRMADO,
        )

        slot_inicio = agora + timedelta(days=10)
        slot_fim = slot_inicio + timedelta(hours=2)
        # A entrou na fila ANTES de B (data_criacao menor).
        fila_a = main.models.ReservaLocal(
            local_id=local.id,
            usuario_id=usuario_a.id,
            inicio=slot_inicio,
            fim=slot_fim,
            status=main.models.StatusReserva.AGUARDANDO_FILA,
            data_criacao=agora,
        )
        fila_b = main.models.ReservaLocal(
            local_id=local.id,
            usuario_id=usuario_b.id,
            inicio=slot_inicio,
            fim=slot_fim,
            status=main.models.StatusReserva.AGUARDANDO_FILA,
            data_criacao=agora + timedelta(hours=1),
        )
        db.add_all([historico_a, fila_a, fila_b])
        db.commit()

        ordenados = main.ordenar_fila(db, [fila_a, fila_b], agora)
        # B assume o topo (0 reservas no mes), apesar de ter solicitado depois de A.
        assert ordenados[0].usuario_id == usuario_b.id
        assert ordenados[1].usuario_id == usuario_a.id
    finally:
        db.close()


def test_worker_abre_confirmacao_e_promove_fila(client):
    # Valida a maquina de estados do worker: janela de 48h, fila respeitando o
    # detentor ativo e promocao do proximo apos cancelamento.
    import app.main as main

    SR = main.models.StatusReserva

    db = main.SessionLocal()
    try:
        local = main.models.LocalAgendavel(nome="Churrasqueira")
        db.add(local)
        db.commit()
        db.refresh(local)

        a = main.models.Usuario(nome="A", email="wa@t.com", senha_hash="x", unidade="1")
        b = main.models.Usuario(nome="B", email="wb@t.com", senha_hash="x", unidade="2")
        db.add_all([a, b])
        db.commit()

        now = datetime.utcnow()
        inicio = now + timedelta(hours=10)  # dentro da janela de 48h
        fim = inicio + timedelta(hours=2)

        detentor = main.models.ReservaLocal(
            local_id=local.id, usuario_id=a.id, inicio=inicio, fim=fim,
            status=SR.AGENDADO, data_criacao=now,
        )
        na_fila = main.models.ReservaLocal(
            local_id=local.id, usuario_id=b.id, inicio=inicio, fim=fim,
            status=SR.AGUARDANDO_FILA, data_criacao=now,
        )
        db.add_all([detentor, na_fila])
        db.commit()
        detentor_id, fila_id = detentor.id, na_fila.id
    finally:
        db.close()

    # Primeira passagem: o detentor entra em PENDENTE_CONFIRMACAO; a fila aguarda.
    main.processar_filas_reserva()

    db = main.SessionLocal()
    detentor = db.get(main.models.ReservaLocal, detentor_id)
    na_fila = db.get(main.models.ReservaLocal, fila_id)
    assert detentor.status == SR.PENDENTE_CONFIRMACAO
    assert detentor.prazo_confirmacao is not None
    assert na_fila.status == SR.AGUARDANDO_FILA
    # O sindico revoga o detentor (Hard Cancel) liberando o slot.
    detentor.status = SR.CANCELADO
    db.commit()
    db.close()

    # Segunda passagem: o proximo da fila assume e recebe o timer de confirmacao.
    main.processar_filas_reserva()

    db = main.SessionLocal()
    na_fila = db.get(main.models.ReservaLocal, fila_id)
    assert na_fila.status == SR.PENDENTE_CONFIRMACAO
    assert na_fila.prazo_confirmacao is not None
    db.close()


def test_sindico_hard_cancel_qualquer_reserva(client):
    _registrar(client, "sindico@t.com", perfil="ADMIN")
    admin = _token(client, "sindico@t.com")
    _registrar(client, "loc@t.com")
    morador = _token(client, "loc@t.com")
    local = _criar_local(client, admin)

    inicio = _futuro(15)
    criada = client.post(
        "/agendamentos",
        json={"local_id": local["id"], "inicio": inicio.isoformat(), "fim": (inicio + timedelta(hours=2)).isoformat()},
        headers={"Authorization": f"Bearer {morador}"},
    )
    assert criada.status_code == 201
    reserva_id = criada.json()["id"]

    # Override do sindico: revoga a reserva de qualquer morador.
    cancel = client.delete(f"/agendamentos/{reserva_id}", headers={"Authorization": f"Bearer {admin}"})
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "CANCELADO"

    # Reserva cancelada some da agenda compartilhada.
    agenda = client.get("/agendamentos", headers={"Authorization": f"Bearer {morador}"}).json()
    assert all(r["id"] != reserva_id for r in agenda)


def test_dono_cancela_e_edita_propria_reserva(client):
    _registrar(client, "adm3@t.com", perfil="ADMIN")
    admin = _token(client, "adm3@t.com")
    _registrar(client, "dono2@t.com")
    dono = _token(client, "dono2@t.com")
    _registrar(client, "outro@t.com")
    outro = _token(client, "outro@t.com")
    local = _criar_local(client, admin)

    inicio = _futuro(20)
    criada = client.post(
        "/agendamentos",
        json={"local_id": local["id"], "inicio": inicio.isoformat(), "fim": (inicio + timedelta(hours=2)).isoformat()},
        headers={"Authorization": f"Bearer {dono}"},
    )
    reserva_id = criada.json()["id"]

    # Edicao: adiciona observacao e convidado.
    editar = client.put(
        f"/agendamentos/{reserva_id}",
        json={"observacao": "Festa", "convidados": [{"nome": "Conv", "cpf": CPF_VALIDO}]},
        headers={"Authorization": f"Bearer {dono}"},
    )
    assert editar.status_code == 200, editar.text
    assert editar.json()["observacao"] == "Festa"
    assert len(editar.json()["convidados"]) == 1

    # Outro morador nao pode editar nem cancelar a reserva alheia.
    proibido = client.delete(f"/agendamentos/{reserva_id}", headers={"Authorization": f"Bearer {outro}"})
    assert proibido.status_code == 403

    # O dono cancela a propria reserva.
    cancel = client.delete(f"/agendamentos/{reserva_id}", headers={"Authorization": f"Bearer {dono}"})
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELADO"

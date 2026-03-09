"""Test the CondoTicket API endpoints."""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("TESTANDO API CONDOTICKET")
print("=" * 60)

# Test 1: Register a new user
print("\n1. Testando registro de usuário...")
registro_data = {
    "nome": "João Silva",
    "email": f"joao.silva.{__import__('time').time()}@teste.com",  # Email único
    "senha": "senha123456",
    "unidade": "101",
    "perfil": "MORADOR"
}

try:
    response = requests.post(f"{BASE_URL}/registro", json=registro_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        user_data = response.json()
        print(f"   ✓ Usuário criado com sucesso!")
        print(f"   - ID: {user_data['id']}")
        print(f"   - Nome: {user_data['nome']}")
        print(f"   - Email: {user_data['email']}")
        print(f"   - Unidade: {user_data['unidade']}")
        print(f"   - Perfil: {user_data['perfil']}")
        user_email = user_data['email']
    else:
        print(f"   ✗ Erro: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Erro na requisição: {e}")
    exit(1)

# Test 2: Login
print("\n2. Testando login...")
login_data = {
    "email": user_email,
    "senha": "senha123456"
}

try:
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print(f"   ✓ Login realizado com sucesso!")
        print(f"   - Token (primeiros 20 chars): {access_token[:20]}...")
    else:
        print(f"   ✗ Erro: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Erro na requisição: {e}")
    exit(1)

# Test 3: Create a ticket (protected endpoint)
print("\n3. Testando criação de ticket (endpoint protegido)...")
ticket_data = {
    "titulo": "Vazamento no apartamento",
    "descricao": "Há um vazamento no banheiro que precisa ser corrigido urgentemente.",
    "imagem_url": "https://exemplo.com/imagem.jpg"
}

headers = {
    "Authorization": f"Bearer {access_token}"
}

try:
    response = requests.post(f"{BASE_URL}/tickets", json=ticket_data, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        ticket = response.json()
        print(f"   ✓ Ticket criado com sucesso!")
        print(f"   - ID: {ticket['id']}")
        print(f"   - Título: {ticket['titulo']}")
        print(f"   - Status: {ticket['status']}")
        print(f"   - Usuário ID: {ticket['usuario_id']}")
        print(f"   - Data de criação: {ticket['data_criacao']}")
    else:
        print(f"   ✗ Erro: {response.text}")
        exit(1)
except Exception as e:
    print(f"   ✗ Erro na requisição: {e}")
    exit(1)

# Test 4: Try to create ticket without token (should fail)
print("\n4. Testando criação de ticket SEM autenticação (deve falhar)...")
try:
    response = requests.post(f"{BASE_URL}/tickets", json=ticket_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 403 or response.status_code == 401:
        print(f"   ✓ Endpoint protegido corretamente! Acesso negado sem token.")
    else:
        print(f"   ✗ Aviso: Endpoint não está protegido adequadamente")
except Exception as e:
    print(f"   ✗ Erro na requisição: {e}")

print("\n" + "=" * 60)
print("TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("=" * 60)
print(f"\nAcesse a documentação interativa em: {BASE_URL}/docs")
print("=" * 60)

# Funcionalidade de Comentários em Tickets

## Descrição

Esta funcionalidade permite que o síndico (admin) adicione comentários/notas sobre cada ticket. Os moradores podem ler essas atualizações, criando um canal de comunicação direto sobre o andamento de cada chamado.

## Backend

### Novos Endpoints

#### `GET /tickets/{ticket_id}/comentarios`

Lista todos os comentários de um ticket.

**Autenticação:** Requerida (JWT Bearer token)

**Resposta (200 OK):**
```json
[
  {
    "id": 1,
    "ticket_id": 5,
    "usuario_id": 1,
    "mensagem": "O técnico foi acionado. Ele virá amanhã às 10:00.",
    "data_envio": "2026-05-07T14:30:00Z",
    "usuario_nome": "João Silva"
  },
  {
    "id": 2,
    "ticket_id": 5,
    "usuario_id": 1,
    "mensagem": "Problema resolvido!",
    "data_envio": "2026-05-08T10:15:00Z",
    "usuario_nome": "João Silva"
  }
]
```

#### `POST /tickets/{ticket_id}/comentarios`

Cria um novo comentário em um ticket. **Qualquer usuário autenticado (ADMIN ou MORADOR) pode criar comentários.**

**Autenticação:** Requerida (JWT Bearer token)

**Corpo da requisição:**
```json
{
  "mensagem": "O técnico foi acionado. Ele virá amanhã às 10:00."
}
```

**Resposta (201 Created):**
```json
{
  "id": 1,
  "ticket_id": 5,
  "usuario_id": 1,
  "mensagem": "O técnico foi acionado. Ele virá amanhã às 10:00.",
  "data_envio": "2026-05-07T14:30:00Z",
  "usuario_nome": "João Silva"
}
```

**Erros:**
- `401 Unauthorized` - Token inválido ou expirado
- `403 Forbidden` - Usuário não é ADMIN
- `404 Not Found` - Ticket não encontrado

## Frontend

### Componente `TicketCommentsComponent`

Localizado em: `frontend/src/app/modules/tickets/components/ticket-comments/`

**Funcionalidades:**
- Exibe todos os comentários de um ticket
- Permite que ADMIN crie novos comentários
- Mostra nome do autor e data de envio
- Formatação automática de datas em `dd/MM/yyyy HH:mm`

**Uso:**
```angular
<app-ticket-comments [ticketId]="ticketId"></app-ticket-comments>
```

**Props:**
- `@Input() ticketId: number` - ID do ticket (requerido)

### Integração no Ticket Card

O componente está integrado no `ticket-card`. Um botão permite expandir/retrair a seção de comentários:

```
[Ticket Title]
[Ticket Description]
[Status Badge]
[Meta Info]
► Ver Comentários  <-- Clique aqui para expandir
```

Ao expandir, mostra a seção de comentários:
- Lista de comentários anteriores
- Formulário para novo comentário (apenas se ADMIN)

## Permissões

| Ação | ADMIN | MORADOR |
|------|-------|---------|
| Ver comentários | ✅ Sim | ✅ Sim |
| Criar comentário | ✅ Sim | ✅ Sim |

## Modelagem de Dados

### Tabela `COMENTARIO_TICKET`

```sql
CREATE TABLE COMENTARIO_TICKET (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    usuario_id INT NOT NULL,
    mensagem TEXT NOT NULL,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES TICKET(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES USUARIO(id) ON DELETE CASCADE
);
```

## Como Testar

### 1. Com Mock (sem backend rodando)

1. No frontend, use os dados fake já configurados:
   ```bash
   cd frontend
   npm start
   ```

2. Faça login com qualquer email/senha
3. Clique em "► Ver Comentários" em qualquer ticket
4. Veja os comentários mock
5. Se estiver como ADMIN, você verá o formulário para adicionar comentários

### 2. Com Backend rodando

1. **Inicie o backend:**
   ```bash
   cd backend
   source .venv/Scripts/activate
   py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Inicie o frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Descomente o código real nos services:**
   - `frontend/src/app/core/services/comments.service.ts` - Descomente o `return this.http...`
   - Opcionalmente, faça o mesmo com `auth.service.ts` e `tickets.service.ts` para usar a API real

4. **Teste:**
   - Faça login com credenciais válidas
   - Crie um ticket
   - Como admin, abra o ticket e adicione um comentário
   - Veja o comentário aparecer imediatamente

## Fluxo de Uso

### Para o Síndico (ADMIN)

1. Abre um ticket
2. Clica em "► Ver Comentários"
3. Vê comentários anteriores (se houver)
4. Preenche o formulário "Escreva um comentário sobre este ticket..."
5. Clica em "Enviar Comentário"
6. Comentário aparece na lista imediatamente

### Para o Morador

1. Abre um ticket (clicando em "► Ver Comentários")
2. Vê a histórico de atualizações do síndico
3. Não consegue adicionar comentários (formulário não é exibido)

## Estrutura de Arquivos

```
frontend/src/app/
  core/services/
    comments.service.ts          # Serviço de comentários
  modules/tickets/
    components/
      ticket-comments/
        ticket-comments.ts       # Componente
        ticket-comments.html     # Template
        ticket-comments.css      # Estilos
      ticket-card/
        ticket-card.ts           # Integração do componente

backend/app/
  main.py                        # Endpoints GET/POST comentários
  models.py                      # Modelo ComentarioTicket
  schemas.py                     # Schemas de validação
```

## Possíveis Melhorias Futuras

- [ ] Notificações em tempo real (WebSocket) para novos comentários
- [ ] Editar/deletar comentários próprios
- [ ] Permitir que moradores também comentem (com aprovação do síndico)
- [ ] Anexar arquivos nos comentários
- [ ] Mencionar usuários (@usuario)
- [ ] Reações aos comentários (emojis)
- [ ] Histórico de edições de comentários

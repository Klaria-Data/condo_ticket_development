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

Cria um novo comentário em um ticket. **O MORADOR comenta apenas nos chamados que abriu; o ADMIN, em todos.** Chamado de outro morador responde `403`.

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
- Formulário para novo comentário (qualquer usuário autenticado)

## Permissões

| Ação | ADMIN | MORADOR |
|------|-------|---------|
| Ver comentários | ✅ Todos os chamados | ✅ Só os próprios chamados |
| Criar comentário | ✅ Todos os chamados | ✅ Só os próprios chamados |
| Editar/excluir comentário | ✅ Qualquer autor | ✅ Só os próprios comentários |

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

1. Ligue o mock em `frontend/src/environments/environment.ts`:
   ```ts
   useMock: true
   ```
   O `mockInterceptor` responde às chamadas HTTP localmente. Não há código
   comentado nos services — o chaveamento é só essa flag.

2. Suba o frontend:
   ```bash
   cd frontend
   npm start
   ```

3. Faça login com qualquer email/senha
4. Clique em "► Ver Comentários" em qualquer ticket
5. Veja os comentários mock. O formulário de novo comentário aparece para
   qualquer usuário autenticado, não só para o ADMIN

### 2. Com a API real

O caminho principal é o de microsserviços, com o gateway na porta 8000:

```bash
docker compose up --build
```

Mantenha `useMock: false` em `environment.ts` (é o padrão).

Para usar o monolito de apoio `backend/`, siga uma das duas formas do
`backend/README.md`: pare o gateway (`docker compose stop nginx`) e suba o monolito
na 8000, ou suba-o na 8080 e troque a `apiUrl` do ambiente para essa porta.

> No monolito, **editar e excluir comentário não funcionam** — as rotas
> `PUT` e `DELETE /tickets/{id}/comentarios/{cid}` existem só em `services/`.
> Para testar esses dois botões, use os microsserviços.

**Teste:**
- Faça login com credenciais válidas
- Crie um chamado
- Abra o chamado e adicione um comentário
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

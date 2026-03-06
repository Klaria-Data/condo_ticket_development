export type TicketStatus = 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'CANCELADO';
export type UserRole = 'MORADOR' | 'SINDICO';
export type TicketFilter = 'TODOS' | TicketStatus;

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: TicketStatus;
  residentName: string;
  apartment: string;
  createdAt: string;
  avatarColor: string;
}
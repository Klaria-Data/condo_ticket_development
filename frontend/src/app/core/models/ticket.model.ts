export type TicketStatus = 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO';
export type ViewMode = 'MORADOR' | 'SINDICO';
export type TicketFilter = 'TODOS' | TicketStatus;

export interface Ticket {
  id: number;
  ownerId?: number;
  title: string;
  description: string;
  status: TicketStatus;
  residentName: string;
  apartment: string;
  createdAt: string;
  updatedAt?: string;
  createdAtRaw?: string;
  updatedAtRaw?: string;
  imageUrl?: string;
  imageFile?: File;
  avatarColor: string;
}

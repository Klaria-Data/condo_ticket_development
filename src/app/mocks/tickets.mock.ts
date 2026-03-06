import { Ticket } from '../core/models/ticket.model';

export const TICKETS_MOCK: Ticket[] = [
  {
    id: 1,
    title: 'Vazamento no banheiro',
    description: 'Há um vazamento constante na torneira do banheiro principal',
    status: 'ABERTO',
    residentName: 'João Silva',
    apartment: 'Apto 101',
    createdAt: '05 de dez.',
    avatarColor: '#10bcd6'
  },
  {
    id: 2,
    title: 'Lâmpada queimada na garagem',
    description: 'A lâmpada da vaga 25 está queimada há 3 dias',
    status: 'EM_ANDAMENTO',
    residentName: 'Maria Santos',
    apartment: 'Apto 205',
    createdAt: '04 de dez.',
    avatarColor: '#ff4fa3'
  },
  {
    id: 3,
    title: 'Portão automático com defeito',
    description: 'O portão da entrada principal não abre com o controle',
    status: 'ABERTO',
    residentName: 'Pedro Costa',
    apartment: 'Apto 302',
    createdAt: '03 de dez.',
    avatarColor: '#6b6df6'
  }
];
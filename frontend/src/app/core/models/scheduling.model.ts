export type StatusReserva =
  | 'AGUARDANDO_FILA'
  | 'AGENDADO'
  | 'PENDENTE_CONFIRMACAO'
  | 'CONFIRMADO'
  | 'EXPIRADO'
  | 'LIVRE_DEMANDA'
  | 'CANCELADO';

export interface BookablePlace {
  id: number;
  nome: string;
  descricao: string | null;
  ativo: boolean;
  data_criacao: string;
}

export interface Guest {
  id: number;
  reserva_id: number;
  nome: string;
  cpf: string;
}

export interface Reservation {
  id: number;
  local_id: number;
  local_nome: string;
  usuario_id: number;
  usuario_nome: string;
  unidade: string;
  inicio: string;
  fim: string;
  observacao: string | null;
  data_criacao: string;
  status: StatusReserva;
  prazo_confirmacao: string | null;
  convidados: Guest[];
}

/** Item do dashboard "Minhas Reservas" (endpoint GET /agendamentos/me). */
export interface DashboardReservation {
  id: number;
  local_id: number;
  local_nome: string;
  inicio: string;
  fim: string;
  status: StatusReserva;
  prazo_confirmacao: string | null;
  posicao_fila: number | null;
  total_convidados: number;
}

export interface GuestPayload {
  nome: string;
  cpf: string;
}

export interface CreateBookablePlacePayload {
  nome: string;
  descricao?: string | null;
}

export interface CreateReservationPayload {
  local_id: number;
  inicio: string;
  fim: string;
  observacao?: string | null;
  convidados?: GuestPayload[];
}

export interface UpdateReservationPayload {
  local_id?: number;
  inicio?: string;
  fim?: string;
  observacao?: string | null;
  convidados?: GuestPayload[];
}

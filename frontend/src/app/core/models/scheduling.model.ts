export interface BookablePlace {
  id: number;
  nome: string;
  descricao: string | null;
  ativo: boolean;
  data_criacao: string;
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
}

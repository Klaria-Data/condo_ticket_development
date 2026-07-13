export interface ResidentInvite {
  id: number;
  nome: string;
  email: string;
  unidade: string;
  usado: boolean;
  data_criacao: string;
  data_expiracao: string;
  data_uso: string | null;
  convite_url?: string | null;
}

export interface CreateResidentInvitePayload {
  nome: string;
  email: string;
  unidade: string;
}

export interface PublicResidentInvite {
  nome: string;
  email: string;
  unidade: string;
  data_expiracao: string;
}

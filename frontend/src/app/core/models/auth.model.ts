export type PerfilUsuario = 'ADMIN' | 'MORADOR';

export interface LoginRequest {
  email: string;
  senha: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  usuario_id: number;
  nome: string;
  unidade: string;
  perfil: PerfilUsuario;
}

export interface AuthUser {
  id: number;
  nome: string;
  unidade: string;
  perfil: PerfilUsuario;
}

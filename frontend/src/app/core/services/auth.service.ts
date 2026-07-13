import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { map, tap } from 'rxjs/operators';
import { Observable } from 'rxjs';

import { AuthUser, LoginRequest, LoginResponse } from '../models/auth.model';
import { environment } from '../../../environments/environment';

/**
 * Serviço de autenticação — gerencia login, logout e sessão do usuário.
 *
 * O token JWT e os dados do usuário são armazenados no localStorage.
 * O AuthInterceptor lê o token deste serviço e o injeta em todas as requisições HTTP.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly apiBaseUrl = environment.apiUrl;
  private readonly tokenKey = 'condoticket.jwt';
  private readonly userKey = 'condoticket.user';

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router,
  ) {}

  /**
   * Autentica o usuário com e-mail e senha.
   * Em caso de sucesso, armazena o token JWT e os dados do usuário no localStorage.
   */
  login(payload: LoginRequest): Observable<AuthUser> {
    return this.http.post<LoginResponse>(`${this.apiBaseUrl}/login`, payload).pipe(
      tap((response) => {
        localStorage.setItem(this.tokenKey, response.access_token);
        const user: AuthUser = {
          id: response.usuario_id,
          nome: response.nome,
          unidade: response.unidade,
          perfil: response.perfil,
        };
        localStorage.setItem(this.userKey, JSON.stringify(user));
      }),
      map((response) => ({
        id: response.usuario_id,
        nome: response.nome,
        unidade: response.unidade,
        perfil: response.perfil,
      })),
    );
  }

  /** Remove o token e os dados do usuário e redireciona para a tela de login. */
  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    void this.router.navigate(['/login']);
  }

  /** Retorna o token JWT armazenado ou null se não estiver autenticado. */
  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  /** Retorna true se houver token e dados de usuário válidos no localStorage. */
  isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getCurrentUser();
  }

  /** Retorna os dados do usuário logado ou null se não estiver autenticado. */
  getCurrentUser(): AuthUser | null {
    const raw = localStorage.getItem(this.userKey);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }
}

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { map, tap } from 'rxjs/operators';
import { Observable } from 'rxjs';

import { AuthUser, LoginRequest, LoginResponse } from '../models/auth.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly apiBaseUrl = 'http://127.0.0.1:8000';
  private readonly tokenKey = 'condoticket.jwt';
  private readonly userKey = 'condoticket.user';

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router,
  ) {}

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

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    void this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getCurrentUser();
  }

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

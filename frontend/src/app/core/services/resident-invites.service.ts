import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  CreateResidentInvitePayload,
  PublicResidentInvite,
  ResidentInvite,
} from '../models/resident-invite.model';
import { LoginResponse } from '../models/auth.model';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ResidentInvitesService {
  private readonly apiBaseUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  listInvites(): Observable<ResidentInvite[]> {
    return this.http.get<ResidentInvite[]>(`${this.apiBaseUrl}/moradores/convites`);
  }

  createInvite(payload: CreateResidentInvitePayload): Observable<ResidentInvite> {
    return this.http.post<ResidentInvite>(`${this.apiBaseUrl}/moradores/convites`, payload);
  }

  getInvite(token: string): Observable<PublicResidentInvite> {
    return this.http.get<PublicResidentInvite>(`${this.apiBaseUrl}/convites/${token}`);
  }

  acceptInvite(token: string, senha: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiBaseUrl}/convites/${token}/aceitar`, { senha });
  }
}

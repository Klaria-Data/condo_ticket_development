import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { mockInterceptor } from './core/interceptors/mock.interceptor';

/**
 * Configuração global da aplicação.
 *
 * O mockInterceptor deve vir antes do authInterceptor para que as requisições
 * de login (que ainda não têm token) sejam respondidas corretamente em modo mock.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([mockInterceptor, authInterceptor])),
  ],
};

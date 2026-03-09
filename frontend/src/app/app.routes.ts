import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginPageComponent } from './modules/auth/pages/login-page/login-page';
import { TicketsPageComponent } from './modules/tickets/pages/tickets-page/tickets-page';

export const routes: Routes = [
	{ path: 'login', component: LoginPageComponent },
	{ path: '', component: TicketsPageComponent, canActivate: [authGuard] },
	{ path: '**', redirectTo: '' },
];

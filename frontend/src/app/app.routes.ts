import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginPageComponent } from './modules/auth/pages/login-page/login-page';
import { AcceptInvitePageComponent } from './modules/residents/pages/accept-invite-page/accept-invite-page';
import { ResidentsPageComponent } from './modules/residents/pages/residents-page/residents-page';
import { SchedulingPageComponent } from './modules/scheduling/pages/scheduling-page/scheduling-page';
import { TicketsPageComponent } from './modules/tickets/pages/tickets-page/tickets-page';

export const routes: Routes = [
	{ path: 'login', component: LoginPageComponent },
	{ path: 'convite/:token', component: AcceptInvitePageComponent },
	{ path: '', component: TicketsPageComponent, canActivate: [authGuard] },
	{ path: 'agendamentos', component: SchedulingPageComponent, canActivate: [authGuard] },
	{ path: 'moradores', component: ResidentsPageComponent, canActivate: [authGuard] },
	{ path: '**', redirectTo: '' },
];

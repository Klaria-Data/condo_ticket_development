import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { LucideAngularModule, FileText, AlertCircle, Clock, CheckCircle2 } from 'lucide-angular';
import { Ticket } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-tickets-summary',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './tickets-summary.html',
  styleUrls: ['./tickets-summary.css']
})
export class TicketsSummaryComponent {
  @Input() tickets: Ticket[] = [];

  readonly FileText = FileText;
  readonly AlertCircle = AlertCircle;
  readonly Clock = Clock;
  readonly CheckCircle2 = CheckCircle2;

  private readonly now = new Date();

  get total(): number {
    return this.tickets.length;
  }

  get open(): number {
    return this.tickets.filter(ticket => ticket.status === 'ABERTO').length;
  }

  get inProgress(): number {
    return this.tickets.filter(ticket => ticket.status === 'EM_ANDAMENTO').length;
  }

  get resolved(): number {
    return this.tickets.filter(ticket => ticket.status === 'RESOLVIDO').length;
  }

  get totalTrendText(): string {
    return this.formatTrend(this.totalGrowthPercent, 'este mes');
  }

  get totalTrendClass(): string {
    return this.getTrendClass(this.totalGrowthPercent);
  }

  get openTrendText(): string {
    return this.formatTrend(this.openGrowthPercent, 'esta semana');
  }

  get openTrendClass(): string {
    return this.getTrendClass(this.openGrowthPercent);
  }

  get inProgressTrendText(): string {
    return this.formatTrend(this.inProgressGrowthPercent, 'esta semana');
  }

  get inProgressTrendClass(): string {
    return this.getTrendClass(this.inProgressGrowthPercent);
  }

  get resolvedTrendText(): string {
    return this.formatTrend(this.resolvedGrowthPercent, 'esta semana');
  }

  get resolvedTrendClass(): string {
    return this.getTrendClass(this.resolvedGrowthPercent);
  }

  private get totalGrowthPercent(): number {
    const currentMonth = this.countInCurrentMonth();
    const previousMonth = this.countInPreviousMonth();
    return this.calculateGrowthPercent(currentMonth, previousMonth);
  }

  private get openGrowthPercent(): number {
    const currentWeek = this.countInCurrentWeek('ABERTO');
    const previousWeek = this.countInPreviousWeek('ABERTO');
    return this.calculateGrowthPercent(currentWeek, previousWeek);
  }

  private get inProgressGrowthPercent(): number {
    const currentWeek = this.countInCurrentWeek('EM_ANDAMENTO');
    const previousWeek = this.countInPreviousWeek('EM_ANDAMENTO');
    return this.calculateGrowthPercent(currentWeek, previousWeek);
  }

  private get resolvedGrowthPercent(): number {
    const currentWeek = this.countInCurrentWeek('RESOLVIDO');
    const previousWeek = this.countInPreviousWeek('RESOLVIDO');
    return this.calculateGrowthPercent(currentWeek, previousWeek);
  }

  private countInCurrentMonth(status?: Ticket['status']): number {
    const start = new Date(this.now.getFullYear(), this.now.getMonth(), 1);
    const end = new Date(this.now.getFullYear(), this.now.getMonth() + 1, 1);
    return this.countByPeriod(start, end, status);
  }

  private countInPreviousMonth(status?: Ticket['status']): number {
    const start = new Date(this.now.getFullYear(), this.now.getMonth() - 1, 1);
    const end = new Date(this.now.getFullYear(), this.now.getMonth(), 1);
    return this.countByPeriod(start, end, status);
  }

  private countInCurrentWeek(status?: Ticket['status']): number {
    const { start, end } = this.getCurrentWeekRange();
    return this.countByPeriod(start, end, status);
  }

  private countInPreviousWeek(status?: Ticket['status']): number {
    const { start, end } = this.getCurrentWeekRange();
    const prevStart = new Date(start);
    prevStart.setDate(prevStart.getDate() - 7);
    const prevEnd = new Date(end);
    prevEnd.setDate(prevEnd.getDate() - 7);
    return this.countByPeriod(prevStart, prevEnd, status);
  }

  private getCurrentWeekRange(): { start: Date; end: Date } {
    const day = this.now.getDay();
    const diffToMonday = day === 0 ? 6 : day - 1;
    const start = new Date(this.now);
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - diffToMonday);

    const end = new Date(start);
    end.setDate(end.getDate() + 7);
    return { start, end };
  }

  private countByPeriod(start: Date, end: Date, status?: Ticket['status']): number {
    return this.tickets.filter((ticket) => {
      if (status && ticket.status !== status) {
        return false;
      }

      const createdAt = this.parseTicketDate(ticket);
      if (!createdAt) {
        return false;
      }

      return createdAt >= start && createdAt < end;
    }).length;
  }

  private parseTicketDate(ticket: Ticket): Date | null {
    if (ticket.createdAtRaw) {
      const date = new Date(ticket.createdAtRaw);
      return Number.isNaN(date.getTime()) ? null : date;
    }

    const fallback = new Date(ticket.createdAt);
    return Number.isNaN(fallback.getTime()) ? null : fallback;
  }

  private calculateGrowthPercent(current: number, previous: number): number {
    if (previous === 0) {
      return current === 0 ? 0 : 100;
    }

    return ((current - previous) / previous) * 100;
  }

  private formatTrend(value: number, label: string): string {
    const rounded = Math.round(Math.abs(value));
    const arrow = value >= 0 ? '↑' : '↓';
    return `${arrow} ${rounded}% ${label}`;
  }

  private getTrendClass(value: number): string {
    if (value > 0) {
      return 'positive';
    }

    if (value < 0) {
      return 'negative';
    }

    return 'neutral';
  }
}
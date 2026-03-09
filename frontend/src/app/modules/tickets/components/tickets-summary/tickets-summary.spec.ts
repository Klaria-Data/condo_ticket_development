import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TicketsSummary } from './tickets-summary';

describe('TicketsSummary', () => {
  let component: TicketsSummary;
  let fixture: ComponentFixture<TicketsSummary>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TicketsSummary],
    }).compileComponents();

    fixture = TestBed.createComponent(TicketsSummary);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

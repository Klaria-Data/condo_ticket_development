import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TicketCard } from './ticket-card';

describe('TicketCard', () => {
  let component: TicketCard;
  let fixture: ComponentFixture<TicketCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TicketCard],
    }).compileComponents();

    fixture = TestBed.createComponent(TicketCard);
    component = fixtureInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

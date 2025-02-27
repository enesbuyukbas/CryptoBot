import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SignalTableComponent } from './signal-table.component';

describe('SignalTableComponent', () => {
  let component: SignalTableComponent;
  let fixture: ComponentFixture<SignalTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SignalTableComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SignalTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

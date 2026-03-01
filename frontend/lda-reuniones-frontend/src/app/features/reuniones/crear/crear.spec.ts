import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Crear } from './crear';

describe('Crear', () => {
  let component: Crear;
  let fixture: ComponentFixture<Crear>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Crear]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Crear);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

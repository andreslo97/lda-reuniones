import { ComponentFixture, TestBed } from '@angular/core/testing';
import ConsultaComponent from './consulta';

describe('ConsultaComponent', () => {
  let component: ConsultaComponent;
  let fixture: ComponentFixture<ConsultaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsultaComponent], // standalone component
    }).compileComponents();

    fixture = TestBed.createComponent(ConsultaComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

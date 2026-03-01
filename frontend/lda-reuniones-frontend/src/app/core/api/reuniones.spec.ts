import { TestBed } from '@angular/core/testing';

import { Reuniones } from './reuniones';

describe('Reuniones', () => {
  let service: Reuniones;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Reuniones);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

import { TestBed } from '@angular/core/testing';

import { Catalogos } from './catalogos';

describe('Catalogos', () => {
  let service: Catalogos;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Catalogos);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

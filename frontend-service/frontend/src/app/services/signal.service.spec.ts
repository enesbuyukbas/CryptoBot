/// <reference types="jasmine" />
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { SignalService } from './signal.service';

describe('SignalService', () => {
  let service: SignalService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(SignalService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

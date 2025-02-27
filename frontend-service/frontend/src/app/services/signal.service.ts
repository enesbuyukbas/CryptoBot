import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = 'http://localhost:5008/api/signals'; // Backend API URL

  constructor(private http: HttpClient) {}

  getSignals(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}`);
  }

  getTopSignals(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/top`);
  }
}

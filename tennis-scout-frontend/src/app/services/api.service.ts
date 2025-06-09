import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment.development';
import { ApiResponse } from '../models/api-response.interface';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;
  private connectionStatus = new BehaviorSubject<boolean>(true);

  constructor(private http: HttpClient) {
  }

  get isConnected$(): Observable<boolean> {
    return this.connectionStatus.asObservable();
  }

  checkConnection(): Observable<boolean> {
    return this.http.get<any>(`${this.baseUrl}/health`).pipe(
      map(response => {
        const isConnected = response.status === 'ok';
        this.connectionStatus.next(isConnected);
        console.log(`🔌 Connection check: ${isConnected ? 'Connected' : 'Disconnected'}`);
        return isConnected;
      }),
      catchError(error => {
        console.warn('🔌 Connection check failed:', error.message);
        this.connectionStatus.next(false);
        return throwError(error);
      })
    );
  }

  get<T>(endpoint: string): Observable<ApiResponse<T>> {
    return this.http.get<ApiResponse<T>>(`${this.baseUrl}/${endpoint}`).pipe(
      catchError(this.handleError)
    );
  }

  post<T>(endpoint: string, data?: any): Observable<ApiResponse<T>> {
    return this.http.post<ApiResponse<T>>(`${this.baseUrl}/${endpoint}`, data).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      if (error.error && error.error.message) {
        errorMessage = error.error.message;
      } else {
        errorMessage = `Server Error: ${error.status} - ${error.message}`;
      }
    }

    console.error('API Error:', error);
    return throwError({
      success: false,
      message: errorMessage,
      status: error.status
    });
  }
}
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

export interface ProcessedMatch {
  id: string;
  video_id: string;
  title: string;
  duration?: number;
  processed_at: string;
  status: 'completed' | 'processing' | 'failed' | 'pending';
  thumbnail_url?: string;
  players_detected?: string[];
  transcript_length?: number;
  error_message?: string;
  tournament?: string;
  azure_search_indexed?: boolean;
}

export interface MatchesResponse {
  success: boolean;
  matches: ProcessedMatch[];
  total: number;
  message?: string;
}

export interface DeleteMatchResponse {
  success: boolean;
  message: string;
}

export interface ReprocessMatchResponse {
  success: boolean;
  message: string;
  job_id?: string;
}

@Injectable({
  providedIn: 'root'
})
export class MatchesService {
  private readonly apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) {}

  getAllMatches(): Observable<ProcessedMatch[]> {
    console.log('🔍 Fetching all processed matches...');
    
    return this.http.get<MatchesResponse>(`${this.apiUrl}/matches`).pipe(
      map(response => {
        if (response.success) {
          console.log(`✅ Found ${response.matches.length} matches`);
          return response.matches;
        } else {
          throw new Error(response.message || 'Failed to fetch matches');
        }
      }),
      catchError(this.handleError)
    );
  }

  getMatchById(id: string): Observable<ProcessedMatch> {
    console.log(`🔍 Fetching match details for ID: ${id}`);
    
    return this.http.get<{success: boolean, match: ProcessedMatch, message?: string}>(`${this.apiUrl}/matches/${id}`).pipe(
      map(response => {
        if (response.success) {
          console.log(' Match details fetched');
          return response.match;
        } else {
          throw new Error(response.message || 'Failed to fetch match details');
        }
      }),
      catchError(this.handleError)
    );
  }

  deleteMatch(id: string): Observable<boolean> {
    console.log(` Deleting match: ${id}`);
    
    return this.http.delete<DeleteMatchResponse>(`${this.apiUrl}/matches/${id}`).pipe(
      map(response => {
        if (response.success) {
          console.log('✅ Match deleted successfully');
          return true;
        } else {
          throw new Error(response.message || 'Failed to delete match');
        }
      }),
      catchError(this.handleError)
    );
  }

  reprocessMatch(id: string): Observable<string | null> {
    console.log(` Reprocessing match: ${id}`);
    
    return this.http.post<ReprocessMatchResponse>(`${this.apiUrl}/matches/${id}/reprocess`, {}).pipe(
      map(response => {
        if (response.success) {
          console.log('✅ Match reprocessing started');
          return response.job_id || null;
        } else {
          throw new Error(response.message || 'Failed to start reprocessing');
        }
      }),
      catchError(this.handleError)
    );
  }

  getMatchesByStatus(status: 'completed' | 'processing' | 'failed'): Observable<ProcessedMatch[]> {
    console.log(`🔍 Fetching matches with status: ${status}`);
    
    return this.http.get<MatchesResponse>(`${this.apiUrl}/matches?status=${status}`).pipe(
      map(response => {
        if (response.success) {
          console.log(`✅ Found ${response.matches.length} ${status} matches`);
          return response.matches;
        } else {
          throw new Error(response.message || `Failed to fetch ${status} matches`);
        }
      }),
      catchError(this.handleError)
    );
  }

  searchMatches(query: string): Observable<ProcessedMatch[]> {
    console.log(`🔍 Searching matches with query: ${query}`);
    
    return this.http.get<MatchesResponse>(`${this.apiUrl}/matches/search?q=${encodeURIComponent(query)}`).pipe(
      map(response => {
        if (response.success) {
          console.log(`✅ Found ${response.matches.length} matches for query`);
          return response.matches;
        } else {
          throw new Error(response.message || 'Failed to search matches');
        }
      }),
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    console.error('❌ Matches service error:', error);
    
    let errorMessage = 'An error occurred while processing your request';
    
    if (error.status === 0) {
      errorMessage = 'Cannot connect to server. Please check if the backend is running.';
    } else if (error.status === 404) {
      errorMessage = 'Matches endpoint not found. Please implement the backend endpoint.';
    } else if (error.error?.message) {
      errorMessage = error.error.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    return throwError(() => new Error(errorMessage));
  }
}
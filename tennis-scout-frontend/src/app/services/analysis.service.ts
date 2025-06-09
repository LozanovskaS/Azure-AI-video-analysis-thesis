import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { ApiService } from './api.service';
import { AnalysisRequest, AnalysisResponse } from '../models/analysis.interface';

@Injectable({
  providedIn: 'root'
})
export class AnalysisService {
  private isAnalyzing = new BehaviorSubject<boolean>(false);
  private analysisHistory = new BehaviorSubject<AnalysisResponse[]>([]);

  private quickQuestions = [
    "What are {player}'s serving patterns on break points?",
    "How does {player} handle aggressive baseline rallies?",
    "What are {player}'s weaknesses when pulled wide?",
    "How does {player}'s strategy change in decisive moments?",
    "What is {player}'s preferred shot selection under pressure?",
    "How effective is {player}'s net game?",
    "What are {player}'s movement patterns on court?",
    "How does {player} handle tiebreak situations?"
  ];

  constructor(private apiService: ApiService) {}

  get isAnalyzing$(): Observable<boolean> {
    return this.isAnalyzing.asObservable();
  }

  get analysisHistory$(): Observable<AnalysisResponse[]> {
    return this.analysisHistory.asObservable();
  }

  analyzeQuestion(request: AnalysisRequest): Observable<AnalysisResponse> {
    this.isAnalyzing.next(true);
    
    return new Observable(observer => {
      this.apiService.post<AnalysisResponse>('chat/query', request).subscribe({
        next: (response) => {
          this.isAnalyzing.next(false);
          console.log('Analysis response:', response);
          
          if (response.success) {
            const analysisResult = response as AnalysisResponse;
            const currentHistory = this.analysisHistory.value;
            this.analysisHistory.next([analysisResult, ...currentHistory.slice(0, 9)]);
            
            observer.next(analysisResult);
          } else {
            observer.error(response);
          }
          observer.complete();
        },
        error: (error) => {
          this.isAnalyzing.next(false);
          observer.error(error);
        }
      });
    });
  }

  getQuickQuestions(players: string[] = []): string[] {
    if (players.length === 0) {
      return this.quickQuestions.map(q => q.replace('{player}', 'the player'));
    }

    const questions: string[] = [];
    players.forEach(player => {
      this.quickQuestions.slice(0, 4).forEach(template => {
        questions.push(template.replace('{player}', player));
      });
    });

    return questions;
  }

  getAnalysisHistory(): Observable<any> {
    return this.apiService.get('chat/history');
  }

  getAnalysisStats(): Observable<any> {
    return this.apiService.get('chat/stats');
  }

  clearLocalHistory(): void {
    this.analysisHistory.next([]);
  }

  validateQuestion(question: string): { valid: boolean; message?: string } {
    const trimmed = question.trim();
    
    if (!trimmed) {
      return { valid: false, message: 'Please enter a question' };
    }
    
    if (trimmed.length < 5) {
      return { valid: false, message: 'Question is too short' };
    }
    
    if (trimmed.length > 500) {
      return { valid: false, message: 'Question is too long (max 500 characters)' };
    }
    
    return { valid: true };
  }

  extractPlayersFromQuestion(question: string): string[] {
    const commonPlayers = [
      'Alcaraz', 'Sinner', 'Djokovic', 'Nadal', 'Federer',
      'Swiatek', 'Sabalenka', 'Gauff', 'Rybakina', 'Pegula',
      'Medvedev', 'Zverev', 'Tsitsipas', 'Rublev', 'Ruud'
    ];
    
    const detected: string[] = [];
    const lowerQuestion = question.toLowerCase();
    
    commonPlayers.forEach(player => {
      if (lowerQuestion.includes(player.toLowerCase())) {
        detected.push(player);
      }
    });
    
    return detected;
  }
}
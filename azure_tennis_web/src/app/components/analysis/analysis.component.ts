import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';
import { Subject, takeUntil } from 'rxjs';

import { AnalysisService } from '../../services/analysis.service';
import { AnalysisRequest, AnalysisResponse } from '../../models/analysis.interface';

interface AnalysisResult extends AnalysisResponse {
  question: string;
  timestamp: Date;
}

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatChipsModule
  ],
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.scss']
})
export class AnalysisComponent implements OnInit, OnDestroy {
  analysisForm: FormGroup;
  isAnalyzing = false;
  analysisResults: AnalysisResult[] = [];
  selectedPlayer = '';
  showAllResults = false;
  
  private destroy$ = new Subject<void>();

  quickQuestions = [
    "What were the key moments that decided this match?",
    "How did the players handle pressure situations?",
    "What tactical changes did the players make during the match?",
    "Which player controlled the pace of the match better?",
    "What were the most exciting rallies in this match?",
    "How did the crowd affect the players' performance?",
    "What made this match special or memorable?",
    "Which player showed better mental strength?"
  ];

  popularPlayers = [
    'Alcaraz', 'Sinner', 'Djokovic', 'Nadal', 'Swiatek', 'Sabalenka'
  ];

  constructor(
    private fb: FormBuilder,
    private analysisService: AnalysisService,
    private snackBar: MatSnackBar
  ) {
    this.analysisForm = this.fb.group({
      question: ['', [
        Validators.required, 
        Validators.minLength(5), 
        Validators.maxLength(500)
      ]]
    });
  }

  ngOnInit(): void {
    this.analysisService.isAnalyzing$
      .pipe(takeUntil(this.destroy$))
      .subscribe(analyzing => {
        this.isAnalyzing = analyzing;
      });

    this.loadAnalysisHistory();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get latestResult(): AnalysisResult | null {
    return this.analysisResults.length > 0 ? this.analysisResults[0] : null;
  }

  getOlderResults(): AnalysisResult[] {
    return this.analysisResults.slice(1);
  }

  onSubmit(): void {
    if (this.analysisForm.valid && !this.isAnalyzing) {
      const question = this.analysisForm.get('question')?.value.trim();
      this.askQuestion(question);
    }
  }

  askQuestion(question: string): void {
    const request: AnalysisRequest = {
      query: question,
      conversation_history: []
    };

    window.scrollTo({ top: 0, behavior: 'smooth' });

    this.analysisService.analyzeQuestion(request)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          const analysisResult: AnalysisResult = {
            ...result,
            question: question,
            timestamp: new Date()
          };
          
          this.analysisResults.unshift(analysisResult);
          
          if (this.analysisResults.length > 10) {
            this.analysisResults = this.analysisResults.slice(0, 10);
          }

          this.analysisForm.reset();
          
          setTimeout(() => {
            const latestResultElement = document.querySelector('.latest-result-section');
            if (latestResultElement) {
              latestResultElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
              });
            }
          }, 500);
          
          this.snackBar.open('✅ Analysis complete!', 'Close', {
            duration: 3000,
            panelClass: ['success-snackbar']
          });
        },
        error: (error) => {
          console.error('Analysis error:', error);
          this.snackBar.open('❌ Analysis failed: ' + (error.message || 'Unknown error'), 'Close', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
        }
      });
  }

  setQuestion(question: string): void {
    this.analysisForm.patchValue({ question });
    
    setTimeout(() => {
      const formElement = document.querySelector('.question-form');
      formElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }

  selectPlayer(player: string): void {
    this.selectedPlayer = this.selectedPlayer === player ? '' : player;
  }

  getPlayerQuestions(player: string): string[] {
    return [
      `What made ${player}'s performance special in this match?`,
      `How did ${player} handle the big moments?`,
      `What was ${player}'s most effective strategy?`,
      `What challenges did ${player} face during the match?`,
      `How did ${player} adapt their game throughout the match?`,
      `What were ${player}'s best shots in this match?`
    ];
  }

  askFollowUp(originalQuestion: string): void {
    const followUpText = `Following up on: "${originalQuestion.substring(0, 50)}..." - `;
    this.analysisForm.patchValue({ question: followUpText });
    
    setTimeout(() => {
      const formElement = document.querySelector('.question-form');
      formElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      
      const textarea = document.querySelector('textarea');
      if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(followUpText.length, followUpText.length);
      }
    }, 100);
  }

  copyAnalysis(result: AnalysisResult): void {
    const textToCopy = `
Question: ${result.question}

Analysis: ${result.response}

Players: ${result.players_detected?.join(', ') || 'None detected'}
Processing Time: ${result.processing_time_ms}ms
Sources: ${result.sources?.length || 0} matches
Generated: ${result.timestamp.toLocaleString()}
    `.trim();

    navigator.clipboard.writeText(textToCopy).then(() => {
      this.snackBar.open('📋 Analysis copied to clipboard!', 'Close', {
        duration: 2000
      });
    }).catch(() => {
      this.snackBar.open('❌ Failed to copy to clipboard', 'Close', {
        duration: 2000
      });
    });
  }

  toggleAllResults(): void {
    this.showAllResults = !this.showAllResults;
  }

  viewAllResults(): void {
    this.showAllResults = true;
    setTimeout(() => {
      const allResultsElement = document.querySelector('.all-results-section');
      if (allResultsElement) {
        allResultsElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }
    }, 100);
  }

  formatResponse(response?: string): string {
    if (!response) return '';
    
    return response
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');
  }

  getRelativeTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
  }

  private loadAnalysisHistory(): void {
    this.analysisService.analysisHistory$
      .pipe(takeUntil(this.destroy$))
      .subscribe(history => {
        const convertedHistory = history.map(item => ({
          ...item,
          question: 'Previous analysis',
          timestamp: new Date()
        }));

        if (this.analysisResults.length === 0 && convertedHistory.length > 0) {
          this.analysisResults = convertedHistory;
        }
      });
  }
}